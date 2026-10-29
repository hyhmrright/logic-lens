# Eval Data

`evals/` contains the canonical benchmark inputs.

## Layout

```text
evals/
├── content/v2/evals-v2.json          # Content-eval cases used by scripts/run-content-evals.sh
├── trigger/v2/trigger-evals-*.json    # Trigger-eval suites used by scripts/run-trigger-evals.sh
└── v1/                               # Legacy archive
```

## Notes

- `evals/content/v2/evals-v2.json` is the source of truth for content benchmarks.
- `evals/trigger/v2/trigger-evals-*.json` is the source of truth for trigger optimization.
- `scripts/grade-iteration.py` reads the content-eval suite directly and writes per-run summaries under `skills-workspace/`.

## Repository discovery experiment

`discovery/` contains 20 pinned upstream defect pairs and an evaluator-only oracle
set. Its three-arm protocol measures targeted discovery with repository context,
separately from report-format compliance. See [discovery/README.md](discovery/README.md)
for source preparation, costs, adjudication and limitations.
