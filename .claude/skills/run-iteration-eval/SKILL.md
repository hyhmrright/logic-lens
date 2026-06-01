---
name: run-iteration-eval
description: Run the Logic-Lens content-eval pipeline for one iteration and produce a scored summary.json — use to measure a skill change. Wraps scripts/run-content-evals.sh (runner, costs tokens) and scripts/grade-iteration.py (grader, free, re-runnable). ALWAYS sync the plugin cache first. Use when the user wants to "run the evals", "score this iteration", "measure the skill change", "smoke-test before the full run", or "re-grade existing outputs".
disable-model-invocation: true
---

# run-iteration-eval

Measures a skill change by running the content cases in `evals/content/v2/evals-v2.json` through
`claude -p` and grading the outputs. Outputs land in `skills-workspace/iteration-<TAG>/`.

The runner and grader are split on purpose: **running** calls Claude and costs tokens; **grading**
is pure regex Python and is free to re-run on outputs that already exist. Never re-run the runner
just to re-score — re-grade instead.

## Steps

1. **Sync the cache first — non-negotiable.** The runner loads the skill from the plugin cache,
   not `skills/`. Run the `sync-skill-cache` skill (or its script directly). If you skip this, the
   eval grades the previously-published skill and the entire run is wasted:
   ```bash
   bash .claude/skills/sync-skill-cache/scripts/sync-cache.sh
   ```

2. **Pick a scope.** Full runs cost real tokens; scope down while iterating:
   ```bash
   SMOKE=1 bash scripts/run-content-evals.sh              # one case per mode (~$0.10) — fast sanity
   CASES="200 201 202" bash scripts/run-content-evals.sh  # only the cases a diagnosis flagged
   TAG=myfix bash scripts/run-content-evals.sh            # full run, named tag
   bash scripts/run-content-evals.sh                      # full run, tag = git short SHA
   ```
   The runner is idempotent — a case with an existing `output.md` is skipped. Delete the
   `eval-<id>/` dir to force a re-run of that case.

3. **Read `summary.json`** in the iteration dir. It carries overall pass rate plus the per-mode and
   **per-subscore (logic vs format)** breakdown. The `logic` subscore reflects reasoning quality;
   `format` reflects Output-Skeleton compliance and is the historical bottleneck with high
   single-run variance. Judge a change on the right subscore — a format wobble is not a reasoning
   regression.

4. **Re-grade without re-running** (free) after editing the grader or to recompute on existing
   outputs:
   ```bash
   python3 scripts/grade-iteration.py skills-workspace/iteration-<TAG>
   ```

5. **Single-iteration grade without the full suite** — when you already have outputs and only want
   the score table, `grade-iteration.py <iteration-dir>` is the cheapest path (see `scripts/README.md`).

## Variance caveat

logic-review single-run scores are variance-dominated (see project memory). One run is a signal,
not a verdict — for a decision near the margin, run the affected cases 2–3× or widen the case set
before concluding a change helped or hurt. Hand the result to `iteration-guard` for the
ship/rollback call rather than eyeballing a single number.
