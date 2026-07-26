import os
import tempfile
from youtube_transcript_api import YouTubeTranscriptApi
from .config import GROQ_API_KEY


def _whisper_transcribe(video_id: str) -> str:
    from pytubefix import YouTube
    from groq import Groq

    yt = YouTube(f"https://www.youtube.com/watch?v={video_id}")
    stream = yt.streams.filter(only_audio=True).order_by("abr").desc().first()
    if stream is None:
        raise RuntimeError("No audio stream available")

    tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    try:
        stream.download(output_path=os.path.dirname(tmp.name), filename=os.path.basename(tmp.name))
        client = Groq(api_key=GROQ_API_KEY)
        with open(tmp.name, "rb") as f:
            result = client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=f,
            )
        return result.text
    finally:
        os.unlink(tmp.name)


def get_transcript(video_id: str) -> str:
    ytt_api = YouTubeTranscriptApi()

    # Try youtube-transcript-api first (fast, free)
    try:
        try:
            transcript = ytt_api.fetch(video_id)
        except Exception:
            available = list(ytt_api.list(video_id))
            if not available:
                raise
            transcript = ytt_api.fetch(video_id, languages=[available[0].language_code])
        return " ".join(s.text for s in transcript)
    except Exception:
        pass

    # Fallback: download audio + Groq Whisper
    return _whisper_transcribe(video_id)
