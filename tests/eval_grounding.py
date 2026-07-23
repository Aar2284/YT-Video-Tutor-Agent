from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.transcript import fetch_transcript, Transcript
from src.chunking import chunk_transcript, find_relevant_chunks
from src.qa_engine import QAEngine


TEST_VIDEOS = {
    "english_captions": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "short_tutorial": "https://www.youtube.com/watch?v=aircAruvnKk",
}


def test_transcript_fetch():
    print("=" * 60)
    print("TEST: Transcript Fetching")
    print("=" * 60)

    for label, url in TEST_VIDEOS.items():
        print(f"\n--- {label}: {url} ---")
        try:
            transcript = fetch_transcript(url)
            print(f"  Language: {transcript.language}")
            print(f"  Segments: {len(transcript.segments)}")
            print(f"  First segment: [{transcript.segments[0].timestamp}] {transcript.segments[0].text[:80]}...")
            print(f"  PASS")
        except Exception as e:
            print(f"  FAIL: {e}")


def test_chunking():
    print("\n" + "=" * 60)
    print("TEST: Chunking")
    print("=" * 60)

    url = list(TEST_VIDEOS.values())[0]
    try:
        transcript = fetch_transcript(url)
        chunks = chunk_transcript(transcript, max_chunk_tokens=200)
        print(f"  Chunks created: {len(chunks)}")
        for i, chunk in enumerate(chunks[:3]):
            print(f"  Chunk {i}: [{chunk.timestamp_range}] {chunk.text[:80]}...")
        print(f"  PASS")
    except Exception as e:
        print(f"  FAIL: {e}")


def test_qa_grounding():
    print("\n" + "=" * 60)
    print("TEST: Q&A Grounding (In-scope vs Out-of-scope)")
    print("=" * 60)

    url = list(TEST_VIDEOS.values())[0]
    try:
        transcript = fetch_transcript(url)
        chunks = chunk_transcript(transcript)
        engine = QAEngine(transcript, chunks)

        in_scope_q = "What is this video about?"
        print(f"\n  Q (in-scope): {in_scope_q}")
        resp = engine.answer(in_scope_q)
        print(f"  A: {resp.answer[:200]}...")
        print(f"  Refusal: {resp.is_refusal}")

        out_scope_q = "What is the capital of France?"
        print(f"\n  Q (out-of-scope): {out_scope_q}")
        resp = engine.answer(out_scope_q)
        print(f"  A: {resp.answer[:200]}...")
        print(f"  Refusal: {resp.is_refusal}")

        if resp.is_refusal:
            print(f"  PASS - Correctly refused out-of-scope question")
        else:
            print(f"  WARNING - Did not refuse out-of-scope question")
    except Exception as e:
        print(f"  FAIL: {e}")


if __name__ == "__main__":
    test_transcript_fetch()
    test_chunking()
    test_qa_grounding()
    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETE")
    print("=" * 60)
