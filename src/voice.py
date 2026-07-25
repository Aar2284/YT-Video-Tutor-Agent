from __future__ import annotations

import asyncio
import base64
import io
import logging
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Awaitable, Callable, TypeVar

import httpx

from src.utils import OPENAI_API_KEY, SARVAM_API_KEY

logger = logging.getLogger(__name__)
STT_URL = "https://api.sarvam.ai/speech-to-text"
TTS_URL = "https://api.sarvam.ai/text-to-speech"
OPENAI_STT_URL = "https://api.openai.com/v1/audio/transcriptions"
OPENAI_TTS_URL = "https://api.openai.com/v1/audio/speech"
TIMEOUT = httpx.Timeout(30.0, connect=5.0)
MAX_RETRIES = 3
T = TypeVar("T")


@dataclass(frozen=True)
class VoiceResult:
    """Structured, non-throwing result for provider operations."""
    value: str | bytes
    provider: str
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


def normalize_audio(audio_bytes: bytes) -> bytes:
    """Decode WebM/Ogg/MP3/WAV and return trimmed 16 kHz mono PCM WAV."""
    if not audio_bytes:
        raise ValueError("Audio payload is empty")
    from pydub import AudioSegment
    from pydub.silence import detect_nonsilent

    audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
    audio = audio.set_frame_rate(16_000).set_channels(1).set_sample_width(2)
    nonsilent = detect_nonsilent(audio, min_silence_len=150, silence_thresh=-45)
    if nonsilent:
        start = max(0, nonsilent[0][0] - 20)
        end = min(len(audio), nonsilent[-1][1] + 20)
        audio = audio[start:end]
    padding = AudioSegment.silent(duration=200, frame_rate=16_000)
    output = io.BytesIO()
    (padding + audio + padding).export(output, format="wav")
    return output.getvalue()


async def _retry(operation: Callable[[], Awaitable[T]], provider: str) -> T:
    for attempt in range(MAX_RETRIES):
        try:
            return await operation()
        except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPStatusError) as exc:
            status = exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else None
            if not (status is None or status == 429 or status >= 500) or attempt == MAX_RETRIES - 1:
                raise
            retry_after = exc.response.headers.get("Retry-After") if isinstance(exc, httpx.HTTPStatusError) else None
            delay = float(retry_after) if retry_after and retry_after.isdigit() else 0.25 * (2 ** attempt)
            logger.warning("%s failed (%s), retrying in %.2fs", provider, status or type(exc).__name__, delay)
            await asyncio.sleep(delay)
    raise RuntimeError("retry loop exhausted")


def _language(language: str) -> str:
    languages = {"en": "en-IN", "hi": "hi-IN", "ta": "ta-IN", "te": "te-IN", "bn": "bn-IN", "mr": "mr-IN", "gu": "gu-IN", "kn": "kn-IN", "ml": "ml-IN", "or": "or-IN", "od": "or-IN", "pa": "pa-IN"}
    return languages.get(language, "en-IN")


async def speech_to_text_result(audio_bytes: bytes, language: str = "en") -> VoiceResult:
    try:
        wav = await asyncio.to_thread(normalize_audio, audio_bytes)
    except Exception as exc:
        logger.warning("Audio normalization failed: %s", exc)
        return VoiceResult("", "normalizer", f"invalid audio: {exc}")
    if SARVAM_API_KEY:
        return await _sarvam_stt(wav, language)
    if OPENAI_API_KEY:
        return await _openai_stt(wav, language)
    return await asyncio.to_thread(_local_whisper_stt, wav, language)


async def text_to_speech_result(text: str, language: str = "en") -> VoiceResult:
    if not text.strip():
        return VoiceResult(b"", "none", "text is empty")
    if SARVAM_API_KEY:
        return await _sarvam_tts(text, language)
    if OPENAI_API_KEY:
        return await _openai_tts(text)
    return await asyncio.to_thread(_local_tts, text)


async def speech_to_text(audio_bytes: bytes, language: str = "en") -> str:
    """Async, non-blocking STT entry point; returns empty text on safe fallback."""
    result = await speech_to_text_result(audio_bytes, language)
    if result.error:
        logger.warning("STT fallback from %s: %s", result.provider, result.error)
    return str(result.value)


async def text_to_speech(text: str, language: str = "en") -> bytes:
    """Async, non-blocking TTS entry point; returns empty audio on failure."""
    result = await text_to_speech_result(text, language)
    if result.error:
        logger.warning("TTS fallback from %s: %s", result.provider, result.error)
    return bytes(result.value)


async def _sarvam_stt(wav: bytes, language: str) -> VoiceResult:
    async def request() -> str:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(STT_URL, headers={"api-subscription-key": SARVAM_API_KEY}, files={"file": ("audio.wav", wav, "audio/wav")}, data={"model": "saaras:v3", "language_code": _language(language), "input_audio_codec": "wav"})
            response.raise_for_status()
            return response.json().get("transcript", "")
    try:
        return VoiceResult(await _retry(request, "Sarvam STT"), "sarvam")
    except Exception as exc:
        return VoiceResult("", "sarvam", str(exc))


async def _openai_stt(wav: bytes, language: str) -> VoiceResult:
    async def request() -> str:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(OPENAI_STT_URL, headers={"Authorization": f"Bearer {OPENAI_API_KEY}"}, files={"file": ("audio.wav", wav, "audio/wav")}, data={"model": "whisper-1", "language": language})
            response.raise_for_status()
            return response.json().get("text", "")
    try:
        return VoiceResult(await _retry(request, "OpenAI STT"), "openai")
    except Exception as exc:
        return VoiceResult("", "openai", str(exc))


async def _sarvam_tts(text: str, language: str) -> VoiceResult:
    async def request(chunk: str) -> list[bytes]:
        async def send() -> list[bytes]:
            payload = {"text": chunk, "model": "bulbul:v3", "speaker": "aditya", "language_code": _language(language)}
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                response = await client.post(TTS_URL, headers={"api-subscription-key": SARVAM_API_KEY}, json=payload)
                response.raise_for_status()
                return [base64.b64decode(item) for item in response.json().get("audios", [])]
        return await _retry(send, "Sarvam TTS")
    try:
        groups = await asyncio.gather(*(request(chunk) for chunk in _split_text_for_tts(text)))
        parts = [part for group in groups for part in group]
        return VoiceResult(await asyncio.to_thread(_merge_wav_audio, parts), "sarvam") if parts else VoiceResult(b"", "sarvam", "provider returned no audio")
    except Exception as exc:
        return VoiceResult(b"", "sarvam", str(exc))


async def _openai_tts(text: str) -> VoiceResult:
    async def request() -> bytes:
        payload = {"model": "tts-1", "voice": "alloy", "input": text, "response_format": "wav"}
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(OPENAI_TTS_URL, headers={"Authorization": f"Bearer {OPENAI_API_KEY}"}, json=payload)
            response.raise_for_status()
            return response.content
    try:
        return VoiceResult(await _retry(request, "OpenAI TTS"), "openai")
    except Exception as exc:
        return VoiceResult(b"", "openai", str(exc))


def _local_whisper_stt(wav: bytes, language: str) -> VoiceResult:
    try:
        import whisper
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(wav)
            path = tmp.name
        try:
            return VoiceResult(whisper.load_model("base").transcribe(path, language=language, verbose=False)["text"], "local")
        finally:
            os.unlink(path)
    except Exception as exc:
        return VoiceResult("", "local", str(exc))


def _local_tts(text: str) -> VoiceResult:
    try:
        import pyttsx3
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            path = tmp.name
        engine = pyttsx3.init()
        engine.save_to_file(text, path)
        engine.runAndWait()
        try:
            return VoiceResult(Path(path).read_bytes(), "local")
        finally:
            os.unlink(path)
    except Exception as exc:
        return VoiceResult(b"", "local", str(exc))


def _split_text_for_tts(text: str, max_chars: int = 400) -> list[str]:
    chunks, current = [], ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if current and len(candidate) > max_chars:
            chunks.append(current)
            current = word
        else:
            current = candidate
    return chunks + ([current] if current else [])


def _merge_wav_audio(parts: list[bytes]) -> bytes:
    from pydub import AudioSegment
    merged = AudioSegment.empty()
    for part in parts:
        merged += AudioSegment.from_file(io.BytesIO(part))
    output = io.BytesIO()
    merged.export(output, format="wav")
    return output.getvalue()


def run_sync(coro: Awaitable[T]) -> T:
    """Use only from synchronous UI code; FastAPI handlers should await directly."""
    return asyncio.run(coro)
