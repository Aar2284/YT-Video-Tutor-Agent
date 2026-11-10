# Eval harness

Measures the two claims the README makes about grounding: **answers correctly from the transcript** and **refuses out-of-scope questions**. Every number in the root README comes from here.

## Dev set vs holdout

| | Dev set | Holdout set |
|---|---|---|
| Questions | 48 (`dataset.json`): 32 in-scope (incl. 8 hard calculation/multi-step), 16 out-of-scope | 18 (`dataset_holdout.json`): 10 in-scope (incl. 4 multi-step/calculation), 8 out-of-scope |
| Transcript | solar-panel video (`transcript.txt`) | **second, real YouTube video** (`transcript_holdout.txt`) |
| Prompt history | the grounding prompt was tuned against the original 40 of these questions | written **after** the prompt was frozen; run **once**, never used to iterate |
| Reported as | counts, labeled "dev (tuned-on)" | counts, labeled "holdout (unseen)" |

The prompt is frozen in `backend/app/graph.py::SYSTEM`. Do not edit it based on holdout results — that would turn the holdout into a dev set.

## Files

| File | Purpose |
|---|---|
| `dataset.json` | Dev set — 48 questions (32 `in_scope`, 16 `out_of_scope`). Each in-scope item has a `reference` answer and `expected_facts` used by the judge. |
| `transcript.txt` | Fixed dev transcript (solar-panel video). Every answerable question is answerable *only* from this text. |
| `dataset_holdout.json` | Holdout set — 18 questions written after the prompt freeze. |
| `transcript_holdout.txt` | Second transcript (real YouTube video, captions via `youtube-transcript-api`). |
| `prompts/baseline.txt` | Verbatim copy of the original system prompt, so "before" runs stay reproducible after edits to `graph.py`. |
| `prompts/grounded_v2.txt` | The grounding prompt (identical to current `graph.py::SYSTEM`). |
| `run_eval.py` | Runner + LLM judge + metrics + compare + rejudge. |
| `results/` | JSON per run: every question, answer, verdict, rationale. Auditable — each number traces to logged answers. |
| `human_grading.md` | Hand-grading sheet: judge agreement check on a 26-answer sample (all 16 out-of-scope + 10 in-scope). |

## Metrics (report as counts, not percentages)

| Metric | Definition |
|---|---|
| In-scope correct | answerable questions answered correctly (of 32 dev / 10 holdout) |
| Over-refusal | answerable questions wrongly refused |
| Correct refusals | out-of-scope questions refused without delivering outside content (of 16 dev / 8 holdout) |
| Grounded score | correct answers + correct refusals, out of total |

Scoring is LLM-as-judge (`openai/gpt-oss-120b`, temperature 0) with rubric `v2-delivery`: an out-of-scope answer only counts as refused if it delivers **no** outside-knowledge content (stating the video doesn't cover it, or describing what it does cover, still counts). Every verdict is logged with a rationale in `results/*.json`. Because the judge is the same model family as the answerer, a 26-answer sample is also hand-graded in `human_grading.md` — report judge-vs-human agreement as n/26.

## Run it

Requires `GROQ_API_KEY` in `.env` at the repo root.

```bash
# BEFORE: original prompt on the dev set
python evals/run_eval.py run --label before --prompt-file evals/prompts/baseline.txt

# AFTER: frozen prompt in graph.py on the dev set
python evals/run_eval.py run --label after

# HOLDOUT: frozen prompt, second video — run once, report separately
python evals/run_eval.py run --label holdout --dataset evals/dataset_holdout.json

# compare dev runs (counts + flipped verdicts)
python evals/run_eval.py compare evals/results/before.json evals/results/after.json

# if the judge rubric changes, re-score BOTH files identically before comparing
python evals/run_eval.py rejudge evals/results/before.json
python evals/run_eval.py rejudge evals/results/after.json
```

Useful flags:

```bash
python evals/run_eval.py run --label smoke --limit 5    # quick smoke test
python evals/run_eval.py run --label noctx --no-context # empty transcript: hallucination stress test
python evals/run_eval.py run --label try --prompt-file evals/prompts/grounded_v2.txt  # try a prompt without editing graph.py
```

Cost/runtime: ~2×96 calls per dev condition, ~96 for the holdout, roughly 10–15 minutes total.

## Adding questions

Dev set only (`dataset.json`) — never add to the holdout after it has been run. In-scope items need `question`, `reference` (correct answer written from the transcript), and `expected_facts` (short substrings shown to the judge). Out-of-scope items need a `reference` stating the tutor must refuse. Keep out-of-scope questions genuinely absent — include "related but not covered" traps (`related_absent`, `absent_detail`) and subjective/personal questions. Include calculation/multi-step in-scope questions so the set can fail, not just score ceiling.
