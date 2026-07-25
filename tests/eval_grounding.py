"""Synthetic QA grounding benchmark. Run: pytest tests/eval_grounding.py -s"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
from dataclasses import dataclass
from typing import Callable, Literal
from src.chunking import chunk_transcript
from src.qa_engine import QAEngine, QAResponse
from src.transcript import Transcript, TranscriptSegment

Category = Literal["direct", "out_of_scope", "adversarial"]
Expectation = Literal["answer", "refuse", "correct_or_refuse"]

@dataclass(frozen=True)
class GroundingCase:
    category: Category
    question: str
    expectation: Expectation
    ground_truth: tuple[str, ...] = ()

@dataclass(frozen=True)
class CaseResult:
    case: GroundingCase
    response: QAResponse
    passed: bool

@dataclass(frozen=True)
class GroundingMetrics:
    precision_score: float
    hallucination_rate: float
    refusal_precision: float
    adversarial_grounding_rate: float

def build_mock_transcript() -> Transcript:
    return Transcript("synthetic-garden-video", "en", [
        TranscriptSegment("Welcome to this basil care tutorial. We cover water, sunlight, and fertilizer.", 0, 5),
        TranscriptSegment("Water a basil plant every two days, preferably in the morning.", 5, 5),
        TranscriptSegment("Keep the basil pot where it receives six hours of sunlight each day.", 10, 5),
        TranscriptSegment("Never add sugar as fertilizer. Use compost instead.", 15, 5),
    ])

BENCHMARK_CASES: tuple[GroundingCase, ...] = (
    # In-Scope / Direct Fact
    GroundingCase("direct", "How often should I water the basil plant?", "answer", ("every two days",)),
    GroundingCase("direct", "How much sunlight does the basil need?", "answer", ("six hours",)),
    GroundingCase("direct", "Does the tutorial say to use compost fertilizer?", "answer", ("compost",)),
    # Out-of-Scope / Irrelevant
    GroundingCase("out_of_scope", "What is the capital of Japan?", "refuse"),
    GroundingCase("out_of_scope", "How do I configure a PostgreSQL database?", "refuse"),
    GroundingCase("out_of_scope", "Who won the 2022 World Cup?", "refuse"),
    # Adversarial / Trick Questions: false premises must be corrected or refused.
    GroundingCase("adversarial", "Does the video say basil needs no sunlight?", "correct_or_refuse", ("six hours",)),
    GroundingCase("adversarial", "Why does the tutorial recommend sugar as fertilizer?", "correct_or_refuse", ("never add sugar",)),
    GroundingCase("adversarial", "Does the speaker say to water basil only once a month?", "correct_or_refuse", ("every two days",)),
)

def is_refusal(response: QAResponse) -> bool:
    answer = response.answer.lower()
    return response.is_refusal or "not covered" in answer or "not related to the video" in answer

def evaluate_case(case: GroundingCase, response: QAResponse) -> bool:
    if case.expectation == "refuse":
        return is_refusal(response)
    grounded = all(term.lower() in response.answer.lower() for term in case.ground_truth)
    return (not is_refusal(response) and grounded) if case.expectation == "answer" else (is_refusal(response) or grounded)

def calculate_metrics(results: list[CaseResult]) -> GroundingMetrics:
    def group(category: Category) -> list[CaseResult]:
        return [result for result in results if result.case.category == category]
    def percent(value: int, total: int) -> float:
        return round(100 * value / total, 2) if total else 0.0
    direct, out_of_scope, adversarial = group("direct"), group("out_of_scope"), group("adversarial")
    correct_refusals = sum(is_refusal(result.response) for result in out_of_scope)
    return GroundingMetrics(
        percent(sum(result.passed for result in direct), len(direct)),
        percent(len(out_of_scope) - correct_refusals, len(out_of_scope)),
        percent(correct_refusals, len(out_of_scope)),
        percent(sum(result.passed for result in adversarial), len(adversarial)),
    )

def run_benchmark(
    response_generator: Callable[[QAEngine, str], QAResponse] | None = None,
) -> tuple[list[CaseResult], GroundingMetrics]:
    """Default pytest mode is deterministic; use engine.answer for a live LLM."""
    transcript = build_mock_transcript()
    engine = QAEngine(transcript, chunk_transcript(transcript, max_chunk_tokens=100))
    if response_generator is None:
        response_generator = lambda active_engine, question: QAResponse(active_engine._fallback_keyword_search(question))
    results = []
    for case in BENCHMARK_CASES:
        response = response_generator(engine, case.question)
        response = QAResponse(response.answer, response.sources, response.is_refusal or "not covered" in response.answer.lower())
        results.append(CaseResult(case, response, evaluate_case(case, response)))
    return results, calculate_metrics(results)

def display_report(results: list[CaseResult], metrics: GroundingMetrics) -> None:
    print("\nSynthetic QA grounding benchmark")
    print("-" * 72)
    for result in results:
        print(f"[{'PASS' if result.passed else 'FAIL'}] {result.case.category}: {result.case.question}")
        print(f"       {result.response.answer}")
    print("-" * 72)
    print(f"Precision Score:              {metrics.precision_score:.2f}%")
    print(f"Hallucination Rate:           {metrics.hallucination_rate:.2f}%")
    print(f"Refusal Precision:            {metrics.refusal_precision:.2f}%")
    print(f"Adversarial Grounding Rate:   {metrics.adversarial_grounding_rate:.2f}%")

def test_synthetic_grounding_benchmark() -> None:
    results, metrics = run_benchmark()
    display_report(results, metrics)
    assert all(result.passed for result in results)
    assert metrics.precision_score == 100.0
    assert metrics.hallucination_rate == 0.0
    assert metrics.refusal_precision == 100.0

def main() -> None:
    parser = argparse.ArgumentParser(description="Run the synthetic grounding benchmark.")
    parser.add_argument("--live-llm", action="store_true", help="Use QAEngine.answer instead of the offline fallback.")
    args = parser.parse_args()
    generator = (lambda engine, question: engine.answer(question)) if args.live_llm else None
    display_report(*run_benchmark(generator))

if __name__ == "__main__":
    main()
