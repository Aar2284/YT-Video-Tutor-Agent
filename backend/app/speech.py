import base64
import json
import httpx
from .config import SARVAM_API_KEY, DEEPGRAM_API_KEY

SARVAM_BASE = "https://api.sarvam.ai"
DEEPGRAM_BASE = "https://api.deepgram.com"


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


class SpeechError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


async def text_to_speech(text: str, language: str = "en-IN", speaker: str = "shubh") -> bytes:
    """Convert text to speech using Deepgram Aura. Returns audio bytes."""
    async with httpx.AsyncClient(timeout=30) as client:
        payload = json.dumps({"text": text[:2500]})
        resp = await client.post(
            f"{DEEPGRAM_BASE}/v1/speak",
            headers={
                "Authorization": f"Token {DEEPGRAM_API_KEY}",
                "Content-Type": "application/json",
            },
            content=payload.encode(),
        )
        if resp.status_code == 402:
            raise SpeechError(402, "TTS service quota exhausted. Please try again later.")
        resp.raise_for_status()
        return resp.content
