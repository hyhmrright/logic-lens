# docs/

Auxiliary documentation. The skills themselves live in `skills/`; this directory is background,
evidence, and outreach material.

| Path | What it is |
|------|------------|
| [`MODEL_COMPATIBILITY.md`](MODEL_COMPATIBILITY.md) | Which host models actually invoke the skills, and the measured cost of the ones that don't. Read this before interpreting any benchmark number. |
| [`research-references.md`](research-references.md) | The papers behind the methodology, risk taxonomy, and scoring model — each entry notes which part of the tool it shaped. |
| [`case-studies/01-checkout-module/`](case-studies/01-checkout-module/) | A synthetic 8-file Python checkout service with one canonical bug per L-code (L1–L6), the real `/logic-health` output, and a narrative walkthrough. Reproducible. |
| [`superpowers/specs/`](superpowers/specs/) | Design specs for experiments, including ones that were tried and reverted. The Step 7.5 self-check post-mortem lives here. |
| [`MARKETING-ROADMAP.md`](MARKETING-ROADMAP.md) | Outreach plan and status. |
| [`announcement/`](announcement/) | Historical submission and announcement drafts, kept for reference. Numbers in these files are frozen at the version they were written for — do not cite them as current. |

Benchmark data is not here: frozen run summaries are in `benchmarks/runs/`, human-readable
reports in `benchmarks/reports/`, and the catalog in `benchmarks/index.json`.
