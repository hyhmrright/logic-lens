# Benchmark Runs

`benchmarks/runs/` stores frozen benchmark summaries for published or cited runs.

## Layout

```text
benchmarks/
├── index.json        # catalog of known benchmark artifacts
└── runs/
    ├── v0.6.4-haiku-baseline.json
    ├── v0.6.4-haiku-after-skillmd-rewrite.json
    └── v0.6.4-sonnet-eval-9-in-session.json
```

## Notes

- These files are snapshots, not live outputs.
- New benchmark runs should be generated into `skills-workspace/` first, then copied here once you decide they are worth freezing.
- `index.json` is the lightweight manifest for the published runs and the current benchmark suite shape.
