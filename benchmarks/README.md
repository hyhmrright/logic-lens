# Benchmark Runs

`benchmarks/runs/` stores frozen benchmark summaries for published or cited runs.

## Layout

```text
benchmarks/
├── index.json           # catalog of known benchmark artifacts
├── reports/             # human-readable markdown reports, grouped by version tag
│   └── v0.6.5/
│       └── haiku-logic-review.md
└── runs/
    ├── v0.6.4-haiku-baseline.json
    ├── v0.6.4-haiku-after-skillmd-rewrite.json
    ├── v0.6.4-sonnet-eval-9-in-session.json
    └── v0.6.5-haiku-logic-review.json
```

## Notes

- These files are snapshots, not live outputs.
- New benchmark runs should be generated into `skills-workspace/` first, then copied here once you decide they are worth freezing.
- `index.json` is the lightweight manifest for the published runs and the current benchmark suite shape.

## Methodology: Multi-Run Averaging for Case-Level Decisions

Per-case pass rates are noisy. In the v0.6.6 noise study (2 cases × 4 samples, n=8), the deviation between a single run and the 4-run mean reached **±25pp**. This is an empirical observation on a small sample, not a framework constant — but the implication is concrete:

- **Do not act on a single-run case-level delta.** Before declaring a case-level regression or improvement (and before back-propagating the conclusion into a SKILL.md change), collect **at least 3 runs** of that case and report the mean.
- **Suite-level totals are more stable** than case-level scores; multi-run averaging is most critical when zooming into individual cases or L-code groupings driven by 1–2 cases.
- **Distinguish verified vs inferred noise.** When a delta in a report is explained by sampling noise, state whether reproductions were actually run (verified) or whether the same noise model is being extrapolated from a related case (inferred). Reports should make this split explicit.

Reports may cite this section instead of re-deriving the rule.

## Metric Hierarchy: the logic sub-score is the headline

The grader splits each case into a **logic** sub-score (reasoning / bug-detection — did the skill find the bug, classify the L-code, recommend a fix) and a **contract** sub-score (Iron Law compliance — does the report carry the literal `Premises:` / `Trace:` / `Divergence:` field labels + correct output language). These are orthogonal axes.

- **Judge skill effectiveness by the logic sub-score only.** It is the clean signal of reasoning ability.
- **`overall_pass_rate` mixes both** (contract assertions are ~25% of total assertions), so contract noise alone can swing overall by ~25pp with reasoning unchanged. Treat overall as a combined record, **not** a reasoning-quality trend.
- **The contract sub-score is a binary, high-variance compliance gate** (non-`zh-` cases have a single contract rule → per-case contract is 0% or 100%). Useful as a floor check; do not chase it as an optimization target. Changing format rules to lift it has repeatedly net-regressed — see `docs/superpowers/specs/2026-05-30-contract-self-check-design.md`.

## index.json Field Reference

Required fields for every `published_runs` entry: `id`, `kind`, `path`, `model`, `cases_graded`, `overall_pass_rate`, `notes`.

Optional fields (added as needed, not required for older entries): `report` (path to markdown report), `date` (ISO date of run), `skill_filter` (when only a subset of skills was evaluated), `source_iteration_dir`.
