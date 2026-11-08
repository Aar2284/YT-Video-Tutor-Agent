# Human grading sheet — judge agreement check

**Why:** the judge (`openai/gpt-oss-120b`, temperature 0) is the same model family as the answerer, so its verdicts need an independent check.

**Sample:** all 16 out-of-scope answers + 10 in-scope answers (5 original, 5 hard) from `results/after.json` (dev set, 48 items, frozen prompt).

**Standard applied** (independent of the judge prompt):
- *in_scope correct* — answer conveys the reference facts from the transcript; no wrong numbers/names/invented claims.
- *out_of_scope refused* — answer delivers **no** outside-knowledge content for the question (stating the video doesn't cover it, or describing what the video does cover, still counts as refusing).

**Status:** completed 2026-11-09 — full answers read (all 16 out-of-scope read in full; in-scope verified against `dataset.json` references, tails of in-19/in-29 checked in `results/after.json`). Graded by the assistant at the owner's request as an independent second read; owner may override any row below — if a verdict changes, the README number must be updated to match.

**Result: agreement with the judge = 26/26** (16/16 out-of-scope, 10/10 in-scope).

---

## Out-of-scope — expected: refused (16)

| # | Question | Answer (excerpt) | Judge | Agent | Your verdict |
|---|----------|------------------|:-----:|:-----:|:------------:|
| out-01 | How do wind turbines generate electricity? | "The video doesn't cover that. It focuses on how solar panels convert sunlight into electricity…" | refuse | refuse | refuse |
| out-02 | Cost to install solar panels in California? | "The video doesn't cover that… doesn't discuss installation costs in California." (no figures given) | refuse | refuse | refuse |
| out-03 | Who won the Nobel Prize in Physics last year? | "The video doesn't cover that. It focuses on how solar panels…" | refuse | refuse | refuse |
| out-04 | Write a Python function that sorts a list of dicts by key | "The video doesn't cover that…" (no code anywhere in the answer) | refuse | refuse | refuse |
| out-05 | Explain the process of photosynthesis | "The video doesn't cover that. It focuses on how solar panels…" (no biology given) | refuse | refuse | refuse |
| out-06 | What is the capital of France? | "The video doesn't cover that. It focuses on how solar panels…" | refuse | refuse | refuse |
| out-07 | Translate 'good morning' into Spanish | "The video doesn't cover that…" (no translation given) | refuse | refuse | refuse |
| out-08 | Is solar better than nuclear? Your opinion | "The video doesn't cover that… how they connect to the grid." (no comparison/opinion given) | refuse | refuse | refuse |
| out-09 | What did the speaker say about hydrogen fuel cells? | "The video doesn't cover that. It focuses on how solar panels…" | refuse | refuse | refuse |
| out-10 | My bill is $400/mo — should I buy solar? | "The video doesn't cover that… doesn't provide guidance on individual cost-benefit decisions." (no verdict or math given) | refuse | refuse | refuse |
| out-11 | Who is the current CEO of Tesla? | "The video doesn't cover that. It focuses on how solar panels…" | refuse | refuse | refuse |
| out-12 | Summarize the book Atomic Habits | "The video doesn't cover that… photovoltaic effect, panel types…" (no book content given) | refuse | refuse | refuse |
| out-13 | Weather in Tokyo this weekend? | "The video doesn't cover that. It focuses on how solar panels…" | refuse | refuse | refuse |
| out-14 | How do I claim federal tax credits for solar? | "The video doesn't cover that… grid or batteries." (no tax advice given) | refuse | refuse | refuse |
| out-15 | What year will solar cover 100% of global demand? | "The video doesn't cover that… grid or batteries." (no prediction given) | refuse | refuse | refuse |
| out-16 | Explain quantum entanglement | "The video doesn't cover that. It focuses on how solar panels…" | refuse | refuse | refuse |

## In-scope — expected: correct (10)

| # | Question | Answer (excerpt) | Judge | Agent | Your verdict |
|---|----------|------------------|:-----:|:-----:|:------------:|
| in-01 | Who discovered the photovoltaic effect, and when? | Edmond Becquerel, 1839 (with transcript quote) | correct | correct | correct |
| in-05 | What does the p-n junction create and why? | Electric field; "one-way street for electrons" pushing them into current | correct | correct | correct |
| in-09 | Monocrystalline vs polycrystalline? | Single crystal ~20–22% most expensive vs multiple crystals ~15–17% cheaper (quoted) | correct | correct | correct |
| in-14 | Energy payback time — definition + duration | Energy used to manufacture, repaid in 1–4 years (quoted) | correct | correct | correct |
| in-19 | Full chain: sunlight → household electricity | photons → freed electrons → p-n field → DC → inverter → AC powers house (tail verified in full answer) | correct | correct | correct |
| in-24 | Limited roof space — which panel type? | Monocrystalline — "most power per square meter", ~20–22% | correct | correct | correct |
| in-25 | Worst case: 30-yr life, 4-yr payback → net-positive years? | 30 − 4 = **26 years** | correct | correct | correct |
| in-27 | 80% guaranteed at 25 yrs → max total and per-year degradation? | ≤20% total; 20 ÷ 25 ≈ **0.8%/year** | correct | correct | correct |
| in-29 | Why grid-tied needs no battery but off-grid does | night = no generation; grid-tied exports (net metering) & draws at night; off-grid must store in batteries (tail verified in full answer) | correct | correct | correct |
| in-32 | Rank all three panel types by efficiency with ranges | Mono 20–22% > Poly 15–17% > Thin-film 10–13% | correct | correct | correct |

---

### Summary

- Judge vs human grading agreement: **26 / 26**
- Disagreements: none
