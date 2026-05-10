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

## index.json Field Reference

Required fields for every `published_runs` entry: `id`, `kind`, `path`, `model`, `cases_graded`, `overall_pass_rate`, `notes`.

Optional fields (added as needed, not required for older entries): `report` (path to markdown report), `date` (ISO date of run), `skill_filter` (when only a subset of skills was evaluated), `source_iteration_dir`.
