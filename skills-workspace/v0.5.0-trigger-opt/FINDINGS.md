# v0.5.0 Trigger Optimization — Findings (Negative Result)

Date: 2026-04-25
Model: `claude-sonnet-4-6` (run_loop default)
Iterations cap: 2 per skill
Eval set: `evals/v2/trigger-evals-{skill}.json` (10 positive + 10 negative per skill, 60% train / 40% test split, 3 replicas per case)

## Summary table

| Skill | Iter 1 train | Iter 1 test | Iter 2 train | Iter 2 test | Best score | Improved? |
|---|---|---|---|---|---|---|
| review   | 18/36 (50%) | 12/24 (50%) | 18/36 (50%) | 12/24 (50%) | 4/8 (iter 1) | No |
| explain  | 18/36 (50%) | 12/24 (50%) | 18/36 (50%) | 12/24 (50%) | 4/8 (iter 1) | No |
| diff     | 18/36 (50%) | 12/24 (50%) | 18/36 (50%) | 12/24 (50%) | 4/8 (iter 1) | No |
| locate   | 18/36 (50%) | 12/24 (50%) | 18/36 (50%) | 12/24 (50%) | 4/8 (iter 1) | No |
| health   | 18/36 (50%) | 12/24 (50%) | 18/36 (50%) | 12/24 (50%) | 4/8 (iter 1) | No |
| fix-all  | 18/36 (50%) | 12/24 (50%) | (crashed)   | (crashed)   | 4/8 (iter 1) | No |

Every single skill produced **`precision=100%, recall=0%, accuracy=50%`** for every iteration.

`fix-all` iteration 2 aborted with `RuntimeError: claude -p exited 1` from a third-party `SessionEnd` hook (claude-mem plugin) — unrelated to the skill description itself; first iteration completed normally with the same recall=0% result.

## What the metric actually says

- **precision=100%** — when the judge does say "trigger this skill," it is always right (negatives are filtered out correctly).
- **recall=0%** — the judge never says "trigger this skill" on any positive case. Not for any of 10 positive prompts × 3 replicas = 30 trials per skill.

This is not a description-quality signal. It is a methodology artifact: skill-creator's `run_loop.py` evaluates triggers in a context where the judge model is presented with an isolated prompt and a single description, and asked "would this skill trigger?" Without the rest of the skill ecosystem (and without the actual harness's routing semantics), the judge defaults to "no" for any prompt that could plausibly be served by general-purpose Claude.

The rewritten descriptions proposed by `run_loop.py` (e.g. for `logic-review`, more inline-prompt phrases like "review 一下", "看起来不对劲") look reasonable in isolation, but produce identical recall=0% — proving the metric saturates and provides no learning signal under this methodology.

## Decision

**Do NOT apply the rewritten descriptions to `SKILL.md` files.** Reasoning:

1. No measured improvement (4/8 → 4/8 across all 6 skills).
2. The descriptions in v0.4.x were already validated functionally by 58/58 assertions across 9 cases × multiple skills × Opus 4.7 + Sonnet 4.6 (see `skills-workspace/iteration-2/` and `iteration-3/`). Real-world routing works.
3. Replacing a known-good description on the strength of a saturated metric is net-negative risk.

## What to do instead (deferred to v0.6.x)

The trigger-evaluator methodology needs to change before another optimization pass is meaningful:

- **Multi-skill judge context**: present all 6 skill descriptions at once and ask the judge to pick one (or none). This matches how the real harness routes.
- **Real harness instead of LLM-judge**: instrument actual Claude Code / Codex / Gemini runs with the 60-prompt set and record which skill (if any) was invoked. Slower and more expensive, but produces ground-truth labels.
- **Stratify by language**: report EN-only and ZH-only recall separately. The current EN+ZH mix masks any per-language deficit.
- **Calibrate the judge prompt**: a small held-out set with hand-labeled "obvious yes" cases should hit recall ≥ 80% before we trust the score on harder prompts.

## Artifacts in this directory

- `review.log`, `explain.log`, `diff.log`, `locate.log`, `health.log` — full 2-iteration logs (628 lines each, JSON state at the bottom).
- `fix-all.log` — partial (iteration 1 only, iteration 2 aborted at hook).

These are kept for reproducibility and for diffing against the next methodology revision.

## Status

`v0.5.0` ships **without** description changes. The release scope is community / outreach artifacts (marketplace drafts, case study) plus this documented negative result.
