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
    payload = {
        "text": text,
        "model": "bulbul:v1",
        "speaker": "meera",
        "language_code": sarvam_lang,
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.content


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
