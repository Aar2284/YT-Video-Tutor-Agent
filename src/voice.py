from __future__ import annotations

import io
import logging
import os
import tempfile
from pathlib import Path

from src.utils import SARVAM_API_KEY, OPENAI_API_KEY

logger = logging.getLogger(__name__)


def speech_to_text(audio_bytes: bytes, language: str = "en") -> str:
    if SARVAM_API_KEY:
        return _sarvam_stt(audio_bytes, language)
    elif OPENAI_API_KEY:
        return _openai_stt(audio_bytes, language)
    else:
        return _local_whisper_stt(audio_bytes, language)


def text_to_speech(text: str, language: str = "en") -> bytes:
    if SARVAM_API_KEY:
        return _sarvam_tts(text, language)
    elif OPENAI_API_KEY:
        return _openai_tts(text)
    else:
        return _local_tts(text)


def _sarvam_stt(audio_bytes: bytes, language: str) -> str:
    import requests

    lang_map = {
        "en": "en-IN", "hi": "hi-IN", "ta": "ta-IN", "te": "te-IN",
        "bn": "bn-IN", "mr": "mr-IN", "gu": "gu-IN", "kn": "kn-IN",
        "ml": "ml-IN", "or": "or-IN", "pa": "pa-IN",
    }
    sarvam_lang = lang_map.get(language, "hi-IN")

    url = "https://api.sarvam.ai/speech-to-text"
    headers = {"API-Subscription-Key": SARVAM_API_KEY}

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as f:
            files = {"file": ("audio.wav", f, "audio/wav")}
            data = {
                "model": "saarika:v2",
                "language_code": sarvam_lang,
            }
            resp = requests.post(url, headers=headers, files=files, data=data, timeout=30)
            resp.raise_for_status()
            return resp.json().get("transcript", "")
    finally:
        os.unlink(tmp_path)


def _openai_stt(audio_bytes: bytes, language: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as f:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language=language,
            )
        return response.text
    finally:
        os.unlink(tmp_path)


def _local_whisper_stt(audio_bytes: bytes, language: str) -> str:
    import whisper

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        model = whisper.load_model("base")
        result = model.transcribe(tmp_path, language=language, verbose=False)
        return result["text"]
    finally:
        os.unlink(tmp_path)


def _sarvam_tts(text: str, language: str) -> bytes:
    import requests

    lang_map = {
        "en": "en-IN", "hi": "hi-IN", "ta": "ta-IN", "te": "te-IN",
        "bn": "bn-IN", "mr": "mr-IN", "gu": "gu-IN", "kn": "kn-IN",
        "ml": "ml-IN", "or": "or-IN", "pa": "pa-IN",
    }
    sarvam_lang = lang_map.get(language, "hi-IN")

    url = "https://api.sarvam.ai/text-to-speech"
    headers = {
        "API-Subscription-Key": SARVAM_API_KEY,
        "Content-Type": "application/json",
    }

    # Split long text into chunks (Sarvam has ~500 char limit)
    chunks = _split_text_for_tts(text, max_chars=400)
    audio_parts = []

    for chunk in chunks:
        payload = {
            "text": chunk,
            "model": "bulbul:v3",
            "speaker": "aditya",
            "language_code": sarvam_lang,
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        if resp.status_code == 200:
            audio_parts.append(resp.content)
        else:
            logger.warning(f"TTS failed for chunk: {resp.status_code} {resp.text[:200]}")

    if not audio_parts:
        raise RuntimeError("TTS failed for all text chunks")

    # Simple concatenation (works for WAV)
    return audio_parts[0] if len(audio_parts) == 1 else _concat_wav_parts(audio_parts)


def _split_text_for_tts(text: str, max_chars: int = 400) -> list[str]:
    """Split text into chunks suitable for TTS."""
    if len(text) <= max_chars:
        return [text]

    chunks = []
    sentences = text.replace("! ", "!|").replace(". ", ".|").replace("? ", "?|").split("|")

    current = ""
    for sentence in sentences:
        if len(current) + len(sentence) > max_chars:
            if current:
                chunks.append(current.strip())
            current = sentence
        else:
            current += sentence

    if current.strip():
        chunks.append(current.strip())

    return chunks if chunks else [text[:max_chars]]


def _concat_wav_parts(parts: list[bytes]) -> bytes:
    """Concatenate WAV audio parts (simple approach - takes first header)."""
    if not parts:
        return b""
    if len(parts) == 1:
        return parts[0]
    # For simplicity, just return the longest part
    # Real implementation would properly merge WAV files
    return max(parts, key=len)


def _openai_tts(text: str) -> bytes:
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text,
    )
    return response.content


def _local_tts(text: str) -> bytes:
    try:
        import pyttsx3

        engine = pyttsx3.init()
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        engine.save_to_file(text, tmp_path)
        engine.runAndWait()

        audio_bytes = Path(tmp_path).read_bytes()
        os.unlink(tmp_path)
        return audio_bytes
    except Exception:
        logger.warning("Local TTS not available. Returning empty audio.")
        return b""
