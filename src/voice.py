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
    import base64

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

    # Split long text into chunks (Sarvam has ~400 char limit)
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
            data = resp.json()
            # Response is JSON with "audios" list containing base64 strings
            for audio_b64 in data.get("audios", []):
                audio_bytes = base64.b64decode(audio_b64)
                audio_parts.append(audio_bytes)
        else:
            logger.warning(f"TTS failed for chunk: {resp.status_code} {resp.text[:200]}")

    if not audio_parts:
        raise RuntimeError("TTS failed for all text chunks")

    # Return single audio or merge multiple
    if len(audio_parts) == 1:
        return audio_parts[0]
    return _merge_wav_audio(audio_parts)


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


def _merge_wav_audio(parts: list[bytes]) -> bytes:
    """Merge multiple WAV audio parts into one."""
    import struct

    if not parts:
        return b""
    if len(parts) == 1:
        return parts[0]

    # Parse WAV headers from first part
    # RIFF header: 4 bytes "RIFF", 4 bytes size, 4 bytes "WAVE"
    # fmt chunk: 4 bytes "fmt ", 4 bytes size, 2 bytes format, ...
    # data chunk: 4 bytes "data", 4 bytes size, then audio data

    all_data = []
    sample_rate = None
    bits_per_sample = None
    num_channels = None

    for part in parts:
        if part[:4] != b'RIFF':
            continue

        # Find "fmt " chunk
        pos = 12  # Skip RIFF header
        fmt_data = None
        while pos < len(part) - 8:
            chunk_id = part[pos:pos+4]
            chunk_size = struct.unpack('<I', part[pos+4:pos+8])[0]

            if chunk_id == b'fmt ':
                fmt_data = part[pos+8:pos+8+chunk_size]
                num_channels = struct.unpack('<H', fmt_data[2:4])[0]
                sample_rate = struct.unpack('<I', fmt_data[4:8])[0]
                bits_per_sample = struct.unpack('<H', fmt_data[14:16])[0]
            elif chunk_id == b'data':
                audio_data = part[pos+8:pos+8+chunk_size]
                all_data.append(audio_data)

            pos += 8 + chunk_size
            if chunk_size % 2 != 0:
                pos += 1  # Pad to even boundary

    if not all_data or not sample_rate:
        return parts[0]  # Fallback to first part

    # Merge all audio data
    merged_data = b''.join(all_data)

    # Build new WAV file
    num_channels = num_channels or 1
    sample_width = bits_per_sample // 8 or 2
    byte_rate = sample_rate * num_channels * sample_width
    data_size = len(merged_data)
    block_align = num_channels * sample_width

    header = struct.pack('<4sI4s', b'RIFF', 36 + data_size, b'WAVE')
    fmt_chunk = struct.pack('<4sIHHIIHH', b'fmt ', 16, 1, num_channels,
                           sample_rate, byte_rate, block_align, bits_per_sample)
    data_header = struct.pack('<4sI', b'data', data_size)

    return header + fmt_chunk + data_header + merged_data


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
