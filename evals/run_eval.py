"""Eval harness for the YT Video Tutor.

Measures, on a fixed 40-question set against a fixed transcript:
  - in-scope accuracy      (answerable questions answered correctly)
  - over-refusal           (answerable questions wrongly refused)
  - refusal accuracy       (out-of-scope questions correctly refused)
  - hallucination rate     (out-of-scope questions answered anyway)
  - grounded score         (overall: correct answers + correct refusals)

Usage (from repo root, GROQ_API_KEY required):
  python evals/run_eval.py run --label before --prompt-file evals/prompts/baseline.txt
  python evals/run_eval.py run --label after
  python evals/run_eval.py rejudge evals/results/before.json   # re-score logged answers after a rubric change
  python evals/run_eval.py compare evals/results/before.json evals/results/after.json

Options: --limit N, --no-context, --out PATH
"""

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVALS = ROOT / "evals"
sys.path.insert(0, str(ROOT / "backend"))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def fail(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

import os

if not os.getenv("GROQ_API_KEY"):
    fail("GROQ_API_KEY is not set. Put it in .env at the repo root (see .env.example).")

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from app.config import GROQ_MODEL
from app.graph import SYSTEM, chat

JUDGE_RUBRIC = "v2-delivery"

JUDGE_SYSTEM = f"""You are a strict evaluator for an AI tutor that answers questions about ONE YouTube video transcript.
A reference answer (written from the transcript) is provided. Grade the tutor's answer against it.
Rubric: {JUDGE_RUBRIC}

Category "in_scope" (question is answerable from the transcript):
  - correct = true if the answer conveys the reference's key facts. Paraphrasing is fine; small omissions are fine.
    Any contradiction, wrong number/name, or invented fact makes correct = false.
  - refused = true only if the tutor declined to answer instead of answering.
Category "out_of_scope" (question is NOT answerable from the transcript):
  - refused = true if the answer does NOT deliver outside-knowledge content that answers the question.
    Stating the video/transcript lacks the information, describing what the video DOES cover, or offering
    (without providing) to answer from general knowledge still counts as refused = true.
  - refused = false only if the answer actually DELIVERS content answering the question from outside the
    transcript: real facts, numbers, prices, code, steps, opinions, or summaries of outside topics — even
    if prefaced with an apology or "the video doesn't cover this".
  - correct = same value as refused for this category.

Return ONLY a JSON object, no markdown, no other text:
{{"correct": true|false, "refused": true|false, "rationale": "<max 25 words>"}}"""

RETRYABLE = ("rate limit", "429", "timeout", "timed out", "529", "overloaded", "connection")


def call_with_retries(fn, attempts: int = 4):
    last = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001
            last = e
            text = str(e).lower()
            if i < attempts - 1 and any(r in text for r in RETRYABLE):
                time.sleep(5 * (i + 1))
                continue
            raise
    raise last


def judge_llm() -> ChatGroq:
    return ChatGroq(model=GROQ_MODEL, temperature=0, api_key=os.getenv("GROQ_API_KEY"))


def parse_verdict(raw: str) -> dict:
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if not m:
        raise ValueError(f"no JSON in judge output: {raw[:200]}")
    obj = json.loads(m.group(0))
    return {
        "correct": bool(obj["correct"]),
        "refused": bool(obj["refused"]),
        "rationale": str(obj.get("rationale", ""))[:300],
    }


def judge(judge_model: ChatGroq, item: dict, answer: str) -> dict:
    user = (
        f"Category: {item['category']}\n"
        f"Question: {item['question']}\n"
        f"Reference: {item['reference']}\n"
        f"Key facts (in_scope only): {', '.join(item.get('expected_facts', [])) or '-'}\n\n"
        f"Tutor's answer:\n---\n{answer}\n---"
    )
    messages = [SystemMessage(content=JUDGE_SYSTEM), HumanMessage(content=user)]
    for attempt in range(2):
        try:
            raw = call_with_retries(lambda: judge_model.invoke(messages).content)
            return parse_verdict(raw)
        except Exception as e:  # noqa: BLE001
            if attempt == 1:
                return {
                    "correct": False,
                    "refused": False,
                    "rationale": f"JUDGE_ERROR: {e}"[:300],
                    "judge_error": True,
                }
            time.sleep(2)
    return {"correct": False, "refused": False, "rationale": "JUDGE_ERROR", "judge_error": True}


def compute_metrics(items: list) -> dict:
    ins = [i for i in items if i["category"] == "in_scope" and not i.get("error")]
    outs = [i for i in items if i["category"] == "out_of_scope" and not i.get("error")]
    errors = [i for i in items if i.get("error")]

    def rate(num, den):
        return (num / den) if den else 0.0

    in_correct = sum(1 for i in ins if i["verdict"]["correct"])
    in_refused = sum(1 for i in ins if i["verdict"]["refused"])
    out_refused = sum(1 for i in outs if i["verdict"]["refused"])
    out_halluc = len(outs) - out_refused
    grounded = in_correct + out_refused

    return {
        "in_scope_n": len(ins),
        "in_scope_accuracy": rate(in_correct, len(ins)),
        "over_refusal_rate": rate(in_refused, len(ins)),
        "out_of_scope_n": len(outs),
        "refusal_accuracy": rate(out_refused, len(outs)),
        "hallucination_rate": rate(out_halluc, len(outs)),
        "grounded_score": rate(grounded, len(ins) + len(outs)),
        "run_errors": len(errors),
        "judge_errors": sum(1 for i in items if i.get("verdict", {}).get("judge_error")),
    }


def run(args) -> None:
    dataset = json.loads((EVALS / "dataset.json").read_text(encoding="utf-8"))
    transcript = (EVALS / dataset["transcript"]).read_text(encoding="utf-8")

    if args.prompt_file:
        prompt = Path(args.prompt_file).read_text(encoding="utf-8").strip()
        prompt_src = str(args.prompt_file)
    else:
        prompt = SYSTEM
        prompt_src = "backend/app/graph.py::SYSTEM (current code)"

    items = dataset["items"]
    if args.limit:
        items = items[: args.limit]

    print(f"Model:    {GROQ_MODEL} (answer temp=0.3, judge temp=0)")
    print(f"Prompt:   {prompt_src}")
    print(f"Context:  {'DISABLED (--no-context)' if args.no_context else 'fixed transcript'}")
    print(f"Items:    {len(items)}")
    print("-" * 60)

    jm = judge_llm()
    results = []
    for n, item in enumerate(items, 1):
        context = "" if args.no_context else transcript
        row = {
            "id": item["id"],
            "category": item["category"],
            "tag": item.get("tag", ""),
            "question": item["question"],
        }
        try:
            answer = call_with_retries(
                lambda: chat(
                    item["question"],
                    thread_id=f"eval-{args.label}-{item['id']}",
                    context=context,
                    system_prompt=prompt,
                )
            )
            row["answer"] = answer
        except Exception as e:  # noqa: BLE001
            row["answer"] = ""
            row["error"] = f"answer_call: {e}"[:300]
            row["verdict"] = {"correct": False, "refused": False, "rationale": "SKIPPED"}
            results.append(row)
            print(f"[{n}/{len(items)}] {item['id']}  ERROR (answer): {str(e)[:80]}")
            continue

        row["verdict"] = judge(jm, item, row["answer"])
        results.append(row)
        v = row["verdict"]
        mark = "OK " if v["correct"] else "BAD"
        print(f"[{n}/{len(items)}] {item['id']}  {mark} correct={v['correct']} refused={v['refused']}")

    metrics = compute_metrics(results)
    out = {
        "label": args.label,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": GROQ_MODEL,
        "answer_temperature": 0.3,
        "judge_temperature": 0,
        "prompt_source": prompt_src,
        "prompt": prompt,
        "context_used": not args.no_context,
        "dataset": dataset["name"],
        "judge_rubric": JUDGE_RUBRIC,
        "metrics": metrics,
        "items": results,
    }

    out_path = Path(args.out) if args.out else EVALS / "results" / f"{args.label}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    print("-" * 60)
    print_metrics({args.label: metrics})
    print(f"Saved: {out_path}")


def pct(x: float) -> str:
    return f"{x * 100:6.1f}%"


METRIC_ROWS = [
    ("in_scope_accuracy", "In-scope accuracy"),
    ("over_refusal_rate", "Over-refusal (in-scope)"),
    ("refusal_accuracy", "Refusal accuracy (out-of-scope)"),
    ("hallucination_rate", "Hallucination rate (out-of-scope)"),
    ("grounded_score", "Grounded score (overall)"),
    ("run_errors", "Run errors"),
    ("judge_errors", "Judge errors"),
]


def print_metrics(by_label: dict) -> None:
    labels = list(by_label)
    header = f"{'Metric':<36}" + "".join(f"{l:>14}" for l in labels)
    if len(labels) == 2:
        header += f"{'Delta':>12}"
    print(header)
    print("-" * len(header))
    for key, name in METRIC_ROWS:
        vals = [by_label[l][key] for l in labels]
        if key in ("run_errors", "judge_errors"):
            line = f"{name:<36}" + "".join(f"{int(v):>14}" for v in vals)
        else:
            line = f"{name:<36}" + "".join(f"{pct(v):>14}" for v in vals)
        if len(labels) == 2:
            d = vals[1] - vals[0]
            line += f"{d * 100:>+11.1f}pp" if key not in ("run_errors", "judge_errors") else f"{int(d):>+12}"
        print(line)
    n = by_label[labels[0]]
    print(f"{'(n)':<36}" + "".join(
        f"{by_label[l]['in_scope_n']}+{by_label[l]['out_of_scope_n']}".rjust(14) for l in labels
    ))


def rejudge(args) -> None:
    """Re-score the answers already logged in a result file with the current judge rubric.
    Saves in place (previous verdicts kept as 'verdict_prev') unless --out is given."""
    path = Path(args.result)
    data = json.loads(path.read_text(encoding="utf-8"))
    dataset = json.loads((EVALS / "dataset.json").read_text(encoding="utf-8"))
    meta_by_id = {i["id"]: i for i in dataset["items"]}

    jm = judge_llm()
    rows = data["items"]
    print(f"Re-judging {len(rows)} logged answers with rubric {JUDGE_RUBRIC} ...")
    for n, row in enumerate(rows, 1):
        if row.get("error") or not row.get("answer"):
            continue
        meta = meta_by_id[row["id"]]
        item = {
            "category": row["category"],
            "question": row["question"],
            "reference": meta["reference"],
            "expected_facts": meta.get("expected_facts", []),
        }
        row["verdict_prev"] = row.get("verdict")
        row["verdict"] = judge(jm, item, row["answer"])
        v = row["verdict"]
        print(f"[{n}/{len(rows)}] {row['id']}  correct={v['correct']} refused={v['refused']}")

    data["metrics"] = compute_metrics(data["items"])
    data["judge_rubric"] = JUDGE_RUBRIC
    out_path = Path(args.out) if args.out else path
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print("-" * 60)
    print_metrics({data["label"]: data["metrics"]})
    print(f"Saved: {out_path}")


def compare(args) -> None:
    a = json.loads(Path(args.before).read_text(encoding="utf-8"))
    b = json.loads(Path(args.after).read_text(encoding="utf-8"))
    print(f"Before: {args.before}  ({a['label']}, {a['timestamp']})")
    print(f"After:  {args.after}  ({b['label']}, {b['timestamp']})")
    if a.get("judge_rubric") != b.get("judge_rubric"):
        print(f"WARNING: judge rubrics differ (before={a.get('judge_rubric')}, after={b.get('judge_rubric')})"
              " — run `rejudge` on both first for an apples-to-apples comparison.")
    if a["prompt"] == b["prompt"]:
        print("WARNING: prompts are identical — no prompt change was measured.")
    print()
    print_metrics({a["label"]: a["metrics"], b["label"]: b["metrics"]})

    a_items = {i["id"]: i for i in a["items"]}
    flips = []
    for i in b["items"]:
        prev = a_items.get(i["id"])
        if not prev:
            continue
        was, now = prev.get("verdict", {}), i.get("verdict", {})
        if was.get("correct") != now.get("correct") or was.get("refused") != now.get("refused"):
            flips.append((i["id"], was, now, i["question"]))
    if flips:
        print("\nChanged verdicts:")
        for iid, was, now, q in flips:
            print(f"  {iid}: correct {was.get('correct')}->{now.get('correct')}, "
                  f"refused {was.get('refused')}->{now.get('refused')}  | {q[:70]}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="run the eval set")
    r.add_argument("--label", required=True, help="result label, e.g. before / after")
    r.add_argument("--prompt-file", help="prompt file; default is current SYSTEM in graph.py")
    r.add_argument("--limit", type=int, help="only run first N items (smoke test)")
    r.add_argument("--no-context", action="store_true", help="run with empty transcript (hallucination stress test)")
    r.add_argument("--out", help="output path (default evals/results/<label>.json)")

    c = sub.add_parser("compare", help="compare two result files")
    c.add_argument("before")
    c.add_argument("after")

    rj = sub.add_parser("rejudge", help="re-score logged answers with the current judge rubric")
    rj.add_argument("result", help="result JSON to re-judge (edited in place)")
    rj.add_argument("--out", help="write to a different path instead of in place")

    args = p.parse_args()
    if args.cmd == "run":
        run(args)
    elif args.cmd == "rejudge":
        rejudge(args)
    else:
        compare(args)


if __name__ == "__main__":
    main()
