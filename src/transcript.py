from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path
from dataclasses import dataclass, field

from youtube_transcript_api import YouTubeTranscriptApi

from src.utils import extract_video_id, DATA_DIR

logger = logging.getLogger(__name__)


@dataclass
class TranscriptSegment:
    text: str
    start: float
    duration: float

    @property
    def end(self) -> float:
        return self.start + self.duration

    @property
    def timestamp(self) -> str:
        from src.utils import format_timestamp
        return format_timestamp(self.start)


@dataclass
class Transcript:
    video_id: str
    language: str
    segments: list[TranscriptSegment] = field(default_factory=list)

    @property
    def full_text(self) -> str:
        return " ".join(seg.text for seg in self.segments)

    def get_context_window(self, segment_idx: int, window: int = 3) -> str:
        start = max(0, segment_idx - window)
        end = min(len(self.segments), segment_idx + window + 1)
        return " ".join(
            f"[{self.segments[i].timestamp}] {self.segments[i].text}"
            for i in range(start, end)
        )


def fetch_transcript(url: str, languages: list[str] | None = None) -> Transcript:
    if languages is None:
        languages = ["en", "hi", "ta", "te", "bn", "mr", "gu", "kn", "ml", "or", "pa"]

    video_id = extract_video_id(url)
    if not video_id:
        raise ValueError(f"Could not extract video ID from URL: {url}")

    try:
        return _fetch_captions(video_id, languages)
    except Exception as e:
        logger.warning(f"Captions failed: {e}. Falling back to yt-dlp + STT.")
        return _fetch_via_ytdlp(video_id)


def _fetch_captions(video_id: str, languages: list[str]) -> Transcript:
    ytt_api = YouTubeTranscriptApi()
    transcript_list = ytt_api.list(video_id)

    # Try manually created transcripts first, then generated
    found_transcript = None
    used_lang = None

    for lang in languages:
        if lang in transcript_list._manually_created_transcripts:
            found_transcript = transcript_list._manually_created_transcripts[lang]
            used_lang = lang
            break
        if lang in transcript_list._generated_transcripts:
            found_transcript = transcript_list._generated_transcripts[lang]
            used_lang = lang
            break

    # Fallback: try any available transcript
    if not found_transcript:
        if transcript_list._manually_created_transcripts:
            used_lang = next(iter(transcript_list._manually_created_transcripts))
            found_transcript = transcript_list._manually_created_transcripts[used_lang]
        elif transcript_list._generated_transcripts:
            used_lang = next(iter(transcript_list._generated_transcripts))
            found_transcript = transcript_list._generated_transcripts[used_lang]
        else:
            raise RuntimeError("No transcript available for this video.")

    raw = found_transcript.fetch().to_raw_data()
    segments = [
        TranscriptSegment(
            text=entry["text"],
            start=entry["start"],
            duration=entry["duration"],
        )
        for entry in raw
    ]

    return Transcript(
        video_id=video_id,
        language=used_lang or found_transcript.language_code,
        segments=segments,
    )


def _fetch_via_ytdlp(video_id: str) -> Transcript:
    import yt_dlp

    url = f"https://www.youtube.com/watch?v={video_id}"
    audio_path = DATA_DIR / f"{video_id}.wav"

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(DATA_DIR / f"{video_id}.%(ext)s"),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "wav",
            "preferredquality": "192",
        }],
        "quiet": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    if not audio_path.exists():
        for f in DATA_DIR.glob(f"{video_id}.*"):
            if f.suffix in (".wav", ".mp3", ".m4a", ".webm"):
                audio_path = f
                break

    if not audio_path.exists():
        raise FileNotFoundError(f"Audio download failed for {video_id}")

    segments = _transcribe_audio(str(audio_path))
    return Transcript(video_id=video_id, language="unknown", segments=segments)


def _transcribe_audio(audio_path: str) -> list[TranscriptSegment]:
    try:
        return _transcribe_with_local_whisper(audio_path)
    except Exception as e:
        logger.warning(f"Local Whisper failed: {e}")
        raise RuntimeError(
            "No captions available and local Whisper failed. "
            "Please provide an OPENAI_API_KEY or SARVAM_API_KEY."
        )


def _transcribe_with_local_whisper(audio_path: str) -> list[TranscriptSegment]:
    import whisper

    model = whisper.load_model("base")
    result = model.transcribe(audio_path, verbose=False)

    segments = []
    for seg in result["segments"]:
        segments.append(TranscriptSegment(
            text=seg["text"].strip(),
            start=seg["start"],
            duration=seg["end"] - seg["start"],
        ))
    return segments


def save_transcript(transcript: Transcript, path: Path | None = None) -> Path:
    if path is None:
        path = DATA_DIR / f"{transcript.video_id}_transcript.json"

    data = {
        "video_id": transcript.video_id,
        "language": transcript.language,
        "segments": [
            {"text": s.text, "start": s.start, "duration": s.duration}
            for s in transcript.segments
        ],
    }
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def load_transcript(path: Path) -> Transcript:
    data = json.loads(path.read_text(encoding="utf-8"))
    segments = [
        TranscriptSegment(**seg) for seg in data["segments"]
    ]
    return Transcript(
        video_id=data["video_id"],
        language=data["language"],
        segments=segments,
    )
