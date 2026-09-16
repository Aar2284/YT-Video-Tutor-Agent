# Eval harness

Measures the two claims the README makes about grounding: **answers correctly from the transcript** and **refuses out-of-scope questions**. No eval existed before this; numbers here are the evidence.

## Files

| File | Purpose |
|---|---|
| `dataset.json` | 40 questions: 24 `in_scope` (answerable only from the transcript), 16 `out_of_scope` (must be refused). Each in-scope item has a `reference` answer and `expected_facts` used by the judge. |
| `transcript.txt` | Fixed transcript fixture (a YouTube video about how solar panels work). Every answerable question is answerable *only* from this text. |
| `prompts/baseline.txt` | Verbatim copy of the original system prompt, so "before" runs stay reproducible after you edit `graph.py`. |
| `prompts/grounded_v2.txt` | Candidate stricter prompt (explicit refusal format, no outside knowledge, empty-context rule). |
| `run_eval.py` | Runner + LLM judge + metrics + before/after comparison. |
| `results/` | JSON output per run: full questions/answers/verdicts plus aggregate metrics. Auditable — every number traces to logged answers. |

## Metrics

| Metric | Definition |
|---|---|
| In-scope accuracy | % of the 24 answerable questions judged correct |
| Over-refusal | % of answerable questions the tutor refused anyway |
| Refusal accuracy | % of the 16 out-of-scope questions correctly refused |
| Hallucination rate | 1 − refusal accuracy: out-of-scope questions answered with outside knowledge |
| Grounded score | (correct answers + correct refusals) / 40 — single headline number |

Scoring is LLM-as-judge (`openai/gpt-oss-120b`, temperature 0) against the authored reference answer with a strict rubric; every verdict is logged with a rationale in `results/*.json` for spot-checking.

## Run it

Requires `GROQ_API_KEY` in `.env` at the repo root (the eval calls the same Groq model the app uses).

```bash
# BEFORE: score the original prompt (use the saved copy, works even after you edit graph.py)
python evals/run_eval.py run --label before --prompt-file evals/prompts/baseline.txt

# change the prompt in backend/app/graph.py (or test a file first)

# AFTER: score the current prompt in graph.py
python evals/run_eval.py run --label after

# compare — prints deltas in percentage points and every flipped verdict
python evals/run_eval.py compare evals/results/before.json evals/results/after.json
```

Useful flags:

```bash
python evals/run_eval.py run --label smoke --limit 5   # quick smoke test
python evals/run_eval.py run --label noctx --no-context # empty transcript: hallucination stress test
python evals/run_eval.py run --label v2 --prompt-file evals/prompts/grounded_v2.txt  # try a prompt without editing graph.py
```

Cost/runtime: ~80 Groq calls per condition (40 answers + 40 judge calls), roughly 2–4 minutes.

## Adding questions

Append to `dataset.json`. In-scope items need `question`, `reference` (the correct answer, written from the transcript), and `expected_facts` (short lowercase substrings the judge looks for). Out-of-scope items need a `reference` stating the tutor must refuse. Keep out-of-scope questions genuinely absent from the transcript — including "related but not covered" traps (`related_absent`, `absent_detail`) and subjective/personal questions.
