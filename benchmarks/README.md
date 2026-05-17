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

## index.json Field Reference

Required fields for every `published_runs` entry: `id`, `kind`, `path`, `model`, `cases_graded`, `overall_pass_rate`, `notes`.

Optional fields (added as needed, not required for older entries): `report` (path to markdown report), `date` (ISO date of run), `skill_filter` (when only a subset of skills was evaluated), `source_iteration_dir`.
