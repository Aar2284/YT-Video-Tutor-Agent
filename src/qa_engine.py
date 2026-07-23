from __future__ import annotations

import logging
from dataclasses import dataclass, field

from src.transcript import Transcript
from src.chunking import Chunk, find_relevant_chunks

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are a Video Tutor Agent. You help users understand video content by answering their questions based on the transcript.

Your job is to be HELPFUL. Answer the question using whatever relevant information exists in the transcript.

RULES:
1. Use ONLY the transcript below as your source.
2. If the question relates to ANY topic discussed in the video, answer it using that information.
3. When answering, cite timestamps where information was found (e.g., "Around 2:34 in the video...").
4. Give COMPLETE answers - mention ALL relevant points, not just the first one.
5. If the question is completely unrelated to the video (e.g., "what is 2+2"), then say: "This question is not related to the video content. I can only help with questions about the video."
6. Use the same language as the question.
7. If a question asks about steps, processes, or how-to guidance that the video covers, provide those steps with timestamps.

TRANSCRIPT:
{transcript_context}
"""


@dataclass
class QAResponse:
    answer: str
    sources: list[str] = field(default_factory=list)
    is_refusal: bool = False


class QAEngine:
    def __init__(self, transcript: Transcript, chunks: list[Chunk] | None = None):
        self.transcript = transcript
        self.chunks = chunks or []

    def answer(
        self,
        question: str,
        conversation_history: list[dict] | None = None,
        use_chunks: bool = True,
    ) -> QAResponse:
        # Use chunks but send enough context (Groq free tier = 6000 TPM)
        if use_chunks and self.chunks:
            relevant = find_relevant_chunks(self.chunks, question, top_k=8)
            context = self._build_chunk_context(relevant)
            sources = [c.timestamp_range for c in relevant]
        else:
            context = self._build_full_context()
            sources = ["Full transcript"]

        system_msg = SYSTEM_PROMPT.format(transcript_context=context)

        messages = [{"role": "system", "content": system_msg}]
        if conversation_history:
            messages.extend(conversation_history[-6:])
        messages.append({"role": "user", "content": question})

        raw_answer = self._call_llm(messages)

        is_refusal = "not covered" in raw_answer.lower() or "i cannot" in raw_answer.lower()

        return QAResponse(
            answer=raw_answer,
            sources=sources,
            is_refusal=is_refusal,
        )

    def _build_chunk_context(self, chunks: list[Chunk]) -> str:
        parts = []
        for chunk in chunks:
            parts.append(
                f"[Timestamp: {chunk.timestamp_range}]\n{chunk.text}"
            )
        return "\n\n".join(parts)

    def _build_full_context(self) -> str:
        lines = []
        for seg in self.transcript.segments:
            lines.append(f"[{seg.timestamp}] {seg.text}")
        return "\n".join(lines)

    def _call_llm(self, messages: list[dict]) -> str:
        from src.utils import GROQ_API_KEY, OPENAI_API_KEY

        if GROQ_API_KEY:
            try:
                return self._call_groq(messages)
            except Exception as e:
                logger.warning(f"Groq failed: {e}. Falling back.")
        if OPENAI_API_KEY:
            try:
                return self._call_openai(messages)
            except Exception as e:
                logger.warning(f"OpenAI failed: {e}. Falling back.")
        return self._call_local_llm(messages)

    def _call_groq(self, messages: list[dict]) -> str:
        from openai import OpenAI
        from src.utils import GROQ_API_KEY

        client = OpenAI(
            api_key=GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
        )
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            temperature=0.3,
            max_tokens=2048,
        )
        return response.choices[0].message.content

    def _call_openai(self, messages: list[dict]) -> str:
        from openai import OpenAI
        from src.utils import OPENAI_API_KEY

        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.3,
            max_tokens=1024,
        )
        return response.choices[0].message.content

    def _call_local_llm(self, messages: list[dict]) -> str:
        try:
            from openai import OpenAI

            client = OpenAI(
                base_url="http://localhost:11434/v1",
                api_key="ollama",
            )
            response = client.chat.completions.create(
                model="llama3.2",
                messages=messages,
                temperature=0.3,
                max_tokens=1024,
            )
            return response.choices[0].message.content
        except Exception:
            return self._fallback_keyword_search(messages[-1]["content"])

    def _fallback_keyword_search(self, question: str) -> str:
        stop_words = {"what", "is", "the", "a", "an", "about", "this", "that", "how",
                       "why", "when", "where", "who", "which", "does", "do", "can",
                       "could", "would", "should", "tell", "me", "in", "on", "at",
                       "to", "for", "of", "and", "or", "not", "it", "from", "with"}

        question_words = set(question.lower().split()) - stop_words
        if not question_words:
            return "I'm sorry, but this topic is not covered in this video. I can only answer questions about the video content."

        best_score = 0
        best_segs = []

        for seg in self.transcript.segments:
            seg_words = set(seg.text.lower().split())
            score = len(question_words & seg_words)
            if score > best_score:
                best_score = score
                best_segs = [seg]
            elif score == best_score and score > 0:
                best_segs.append(seg)

        match_ratio = best_score / len(question_words) if question_words else 0

        if match_ratio < 0.3:
            return "I'm sorry, but this topic is not covered in this video. I can only answer questions about the video content."

        timestamps = [f"{s.timestamp}" for s in best_segs[:3]]
        text = " ".join(s.text for s in best_segs[:3])
        return f"Based on the video (around {', '.join(timestamps)}): {text}"
