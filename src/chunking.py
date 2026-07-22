from __future__ import annotations

import numpy as np
from dataclasses import dataclass

from src.transcript import Transcript, TranscriptSegment


@dataclass
class Chunk:
    text: str
    segments: list[TranscriptSegment]
    start_time: float
    end_time: float
    index: int

    @property
    def timestamp_range(self) -> str:
        from src.utils import format_timestamp
        return f"{format_timestamp(self.start_time)} - {format_timestamp(self.end_time)}"


def chunk_transcript(
    transcript: Transcript,
    max_chunk_tokens: int = 300,
    overlap_tokens: int = 50,
) -> list[Chunk]:
    if not transcript.segments:
        return []

    chunks: list[Chunk] = []
    current_segments: list[TranscriptSegment] = []
    current_token_count = 0
    chunk_idx = 0

    for seg in transcript.segments:
        seg_tokens = len(seg.text.split())

        if current_token_count + seg_tokens > max_chunk_tokens and current_segments:
            chunks.append(_make_chunk(current_segments, chunk_idx))
            chunk_idx += 1

            overlap_segs = []
            overlap_count = 0
            for s in reversed(current_segments):
                overlap_count += len(s.text.split())
                if overlap_count > overlap_tokens:
                    break
                overlap_segs.insert(0, s)

            current_segments = overlap_segs
            current_token_count = sum(len(s.text.split()) for s in current_segments)

        current_segments.append(seg)
        current_token_count += seg_tokens

    if current_segments:
        chunks.append(_make_chunk(current_segments, chunk_idx))

    return chunks


def _make_chunk(segments: list[TranscriptSegment], index: int) -> Chunk:
    return Chunk(
        text=" ".join(seg.text for seg in segments),
        segments=segments,
        start_time=segments[0].start,
        end_time=segments[-1].end,
        index=index,
    )


def find_relevant_chunks(
    chunks: list[Chunk],
    query: str,
    top_k: int = 3,
) -> list[Chunk]:
    if not chunks:
        return []

    query_words = set(query.lower().split())

    scored: list[tuple[float, Chunk]] = []
    for chunk in chunks:
        chunk_words = set(chunk.text.lower().split())
        if not chunk_words:
            score = 0.0
        else:
            overlap = query_words & chunk_words
            score = len(overlap) / max(len(query_words), 1)

            for i, c in enumerate(chunks):
                if i == chunk.index:
                    continue
                if _segments_overlap(chunk.segments, c.segments):
                    chunk_words_extra = set(c.text.lower().split())
                    score += 0.1 * len(query_words & chunk_words_extra) / max(len(query_words), 1)

        scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [chunk for _, chunk in scored[:top_k]]


def _segments_overlap(segs_a: list[TranscriptSegment], segs_b: list[TranscriptSegment]) -> bool:
    if not segs_a or not segs_b:
        return False
    a_start = segs_a[0].start
    a_end = segs_a[-1].end
    b_start = segs_b[0].start
    b_end = segs_b[-1].end
    return a_start < b_end and b_start < a_end
