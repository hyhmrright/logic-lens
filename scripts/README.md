# Development utilities

Python 3.11+ and the standard library are sufficient for the maintained CLI. No model
SDK, Claude login, plugin cache or npm install is required. Codex is the default
execution backend; use the normalized command adapter for other CLIs.

```bash
python3 scripts/logic_lens.py review --help
python3 scripts/logic_lens.py bundle --help
python3 scripts/logic_lens.py eval --help
python3 scripts/logic_lens.py discovery --help
python3 scripts/logic_lens.py verify --help
python3 scripts/logic_lens.py search --help
```

- `run_review.py`: read-only review/explain/diff/locate/health; writes reports and raw events.
- `skill_bundle.py`: compile complete prompts or export a portable six-skill directory.
- `llm_runner.py`: isolated execution, normalized Codex/command result events, bounded concurrency.
- `command_bridge.py`: wrap a stdin/plain-stdout CLI; unknown usage/tools remain unknown.
- `run_evals.py content`: run the unchanged 104-case content suite, then grade offline.
- `run_evals.py routing`: evaluate description routing, separately from native activation.
- `discovery_eval.py`: freeze plain/prior/candidate plans, run repository-context reviews, summarize adjudications.
- `verify_discovery.py`: independently verify target source pairs using evaluator-only probes.
- `property_search.py`: experimental finite local property search, no model calls;
  [protocol and limitations](../docs/PROPERTY_SEARCH.md).
- `run_probes.py`: run legacy real-code probes through the same provider interface.
- `grade-iteration.py`: existing offline keyword/contract regression grader; not a discovery oracle.
- `bump-version.py`: synchronize six version locations and validate; add CHANGELOG manually.

`run-content-evals.sh`, `run-trigger-evals.sh` and `evals/real-world/run-real-world.sh`
are compatibility wrappers around the Python runners. `MODEL`, `PROVIDER`, `EFFORT`
and `ADAPTER` environment variables select the backend; default model is gpt-6.1-sol.

```bash
SMOKE=1 TAG=codex-smoke npm run content-evals
CASES="1 101" PARALLEL=2 TAG=codex-review npm run content-evals
PROVIDER=command ADAPTER=/path/adapter.json MODEL=your-model TAG=other npm run content-evals
npm run trigger-evals -- review
```

Content output directories refuse a different provider/model/effort/instruction snapshot.
Existing outputs are reused only when completion metadata is present. `SKIP_GRADE=1`
skips grading; regrade later with `python3 scripts/grade-iteration.py <iteration-dir>`.
`SMOKE=1` is six real model calls, not an offline test. Routing evaluates all selected
queries and consumes quota; it no longer invokes a provider-specific description-tuning
loop. Preserve explicit model/provider provenance when comparing any runs.

Offline checks:

```bash
npm run validate
npm run unit-tests
npm run lint-shell
```

Structural/version checks do not establish skill effectiveness. See
[discovery protocol](../evals/discovery/README.md) and
[tool compatibility](../docs/TOOL_COMPATIBILITY.md) for rigorous comparisons, adapters,
isolation limits and costs. Case-level deltas need repeated matched measurements;
never relax the old grader to make a candidate pass.

### Offline constraint relation planner (experimental)

`python3 scripts/logic_lens.py constraints --spec RELATIONS.json --workspace SOURCE --out NEW.json`
turns manually sourced integer-affine producer/consumer relations into property
candidates, finite inverse-boundary domains and selection reasons. It never invokes
a model or runs a subject. See [schema and limitations](../docs/CONSTRAINT_PLAN.md)
and `examples/constraint-plan/relations.json`. Kept in draft PR #16, not the default
review skill or proof of improved bug discovery.
