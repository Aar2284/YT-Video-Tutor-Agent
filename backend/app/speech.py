import base64
import httpx
from .config import SARVAM_API_KEY

SARVAM_BASE = "https://api.sarvam.ai"


async def speech_to_text(audio_bytes: bytes, filename: str) -> str:
    """Transcribe audio using Sarvam Saaras v3."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{SARVAM_BASE}/speech-to-text",
            headers={"api-subscription-key": SARVAM_API_KEY},
            files={"file": (filename, audio_bytes, "audio/wav")},
            data={"model": "saaras:v3", "mode": "transcribe"},
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("transcript", "")


async def text_to_speech(text: str, language: str = "en-IN", speaker: str = "shubh") -> bytes:
    """Convert text to speech using Sarvam Bulbul v3. Returns WAV bytes."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{SARVAM_BASE}/text-to-speech",
            headers={
                "api-subscription-key": SARVAM_API_KEY,
                "Content-Type": "application/json",
            },
            json={
                "text": text[:2500],
                "target_language_code": language,
                "speaker": speaker,
                "model": "bulbul:v3",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        combined = "".join(data.get("audios", []))
        return base64.b64decode(combined) if combined else b""
