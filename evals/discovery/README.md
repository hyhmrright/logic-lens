# Repository discovery experiment

Compare plain model / frozen prior skill / candidate skill on the same historical
source snapshots, using Codex by default or a generic command adapter. No Claude
account, plugin cache or model SDK is required. The old 104-case content suite and
grader remain separate and unchanged.

## Corpus and validity

`catalog.json` pins 20 upstream fixes and first parents (HTTPX and Requests), target
files, expected behavior, source-only repair overlays and test provenance. The model
never receives the catalog, fix commit, answer or new regression tests. Parent tests,
docs and configuration remain identical in both variants, including any pre-existing
incorrect expectations. Snapshot exports remove history, symlinks and agent controls.
The runner copies the source to an opaque temporary directory outside this repository.

All seeds were visible during development; this is **targeted discovery on a public
development corpus**, not independent prospective validation or unbounded-repository
recall. Both projects are Python HTTP clients. Public-history memorization remains
possible. Repair removes the target defect, not necessarily other legitimate bugs.
Adjudicate unrelated findings individually rather than assuming repaired files are clean.

## Verify the target defects without model calls

```bash
git clone --filter=blob:none --no-checkout https://github.com/encode/httpx.git skills-workspace/discovery-sources/httpx
git clone --filter=blob:none --no-checkout https://github.com/psf/requests.git skills-workspace/discovery-sources/requests
python3.11 -m venv skills-workspace/discovery-venv
skills-workspace/discovery-venv/bin/pip install -r evals/discovery/requirements.txt
python3 scripts/logic_lens.py verify --sources skills-workspace/discovery-sources \
  --python skills-workspace/discovery-venv/bin/python --out skills-workspace/discovery-oracles
```

Evaluator-only `oracles.py` imports actual exported code, verifies module provenance,
and runs each probe in a fresh bounded subprocess. Inspect the failure location, not
just the exit code: setup/import failures do not verify a bug. The catalog records
19 inspected failure→pass pairs. requests-01 reproduces on Python 3.15 but not 3.11;
use a separate environment for that case. requests-07 needs Windows and is blocked.
Environment snapshots and oracle hashes are recorded. HTTPX/Requests probe adaptations
retain BSD-3-Clause/Apache-2.0 attribution in `LICENSE.httpx` and `LICENSE.requests`.

## Prepare and run with Codex

```bash
python3 scripts/logic_lens.py discovery prepare \
  --sources skills-workspace/discovery-sources --out skills-workspace/discovery-run \
  --cases httpx-03 httpx-10 requests-02 requests-06 --repeats 3 \
  --provider codex --model gpt-6.1-sol --effort high --timeout 360
python3 scripts/logic_lens.py discovery run \
  --out skills-workspace/discovery-run --jobs 4
```

This four-case matrix contains 72 reviews: 4 cases × 2 variants × 3 arms × 3 repeats.
Omit `--cases` for 360 calls over all 20 cases. Start small. `--limit N` on run bounds
additional calls; timeout/concurrency are bounded and failures stop further dispatch.
In-flight calls may finish. A timeout kills the process group on Unix and preserves
partial logs. There is no enforced Codex dollar cap; token counts are recorded and
dollar cost remains null when unknown. Do not interpret old `budget_usd` metadata
as a real spend limit. Raw artifacts stay under ignored `skills-workspace/`.

A new output directory freezes each candidate's instructions, model, provider, effort,
source hashes, randomization seed and timeout. Preparation does not call a model.
Runs are resumable only for this exact plan; never overwrite a candidate's snapshots.
Baseline instructions come from `baseline_skill_commit`, not installed skills.
Both skill arms receive compiled instructions through the same stdin channel; plain
receives none. This measures instruction effectiveness with explicit delivery, not
native activation or progressive-loading reliability.

Codex uses a temporary home with only an auth symlink, ignores ambient configuration,
rules, saved skills and parent project controls, and runs with a read-only shell and
no web search. See [tool compatibility](../../docs/TOOL_COMPATIBILITY.md) for the
precise isolation limitations. The common request asks for at most 10 tool calls and
1600 report words; these are soft investigation limits, not enforced token caps.
Actual commands, terminal status and token usage are recorded from JSONL events.

For another CLI, select `--provider command --adapter /path/adapter.json` at prepare
time, then keep that provider/adapter/model fixed across the three arms. The generic
adapter's tool/isolation claims need separate validation; do not mix providers in one
comparison. Integration-capable evaluation needs a separate isolated protocol.

## Adjudicate root causes, not report tokens

Read randomized reports against real source and oracle evidence. A finding must name
the actual cause and observable consequence; L-code/label/keyword matches alone do
not count. Valid unrelated discoveries are not false positives. Distinguish asserted
defects from explicitly unresolved leads. For each run, record:

```json
{
  "<opaque-run-id>": {
    "target_detected": true,
    "false_positive_count": 0,
    "rationale": "Actual root cause and consequence matched against source evidence."
  }
}
```

On repaired variants `target_detected` is normally false. A false claim about the
repaired target belongs in `false_positive_count`. Record optional miss-stage notes
(context/hypothesis/contract/reachability/verification/reporting/environment), and
state whether adjudication was independent human review or assistant review with
access to answers. Neither is an automatic model-judged or regex-derived truth.

```bash
python3 scripts/logic_lens.py discovery summarize \
  --out skills-workspace/discovery-run --judgments /path/judgments.json
```

Summaries separate denominators, target recall and false positives. Missing results
are null, not 0% accuracy. Costs cover completed calls only; failed attempts may be
billable. Inspect per-case repeated results and actual tool/usage evidence before
any conclusion. A partial/mismatched comparison cannot qualify a release.

Release gates: repeated same-provider gains without increased false positives,
reasonable resource use, untouched content-regression assertions, prospective unseen
projects/families and independent validation. Operational criteria do not by themselves
establish statistical significance. Existing oracle disputes such as eval-279 must be
reported, not silently rewritten to lift a score. Current results and caveats belong
in `STATUS.md`; cross-provider historical numbers are not a direct baseline.

## Frozen revision-2 validation

The [revision-2 preregistration](../../docs/experiments/discovery-v2-preregistration.md)
uses a candidate frozen before new dateutil/node-semver cases were inspected.
`catalog-v2.json` records semantic matching obligations and one pre-run exclusion.
`probes_v2.py` contains evaluator-only assertions against the real exported modules.
All four targets were inspected as behavior failure → success pairs; these are
not replacement cases for the old content grader.

```bash
git clone --filter=blob:none --no-checkout https://github.com/dateutil/dateutil.git skills-workspace/discovery-sources/dateutil
git clone --filter=blob:none --no-checkout https://github.com/npm/node-semver.git skills-workspace/discovery-sources/node-semver
# Use a Python 3.11 virtual environment with six==1.17.0; Node.js is also required.
python3 scripts/logic_lens.py discovery prepare --catalog evals/discovery/catalog-v2.json \
  --sources skills-workspace/discovery-sources --out skills-workspace/discovery-v2 \
  --repeats 3 --provider codex --model gpt-6.1-sol --effort high --timeout 360
python3 scripts/logic_lens.py discovery run --out skills-workspace/discovery-v2 --jobs 4
```

For reproduction on another machine, make a copy of the catalog and set its
`protocol.runtime_note` to the available Python interpreter/dependency path before
preparation; keep this identical across arms. The published catalog preserves the
exact runtime note used in the recorded experiment. The original plan schema without
`protocol.local_probes` retains its previous prompt. Revision 2 explicitly permits
pure local probes on every arm, so cross-experiment rate changes are not attributable
solely to the skill. Python bytecode writes are disabled. No target assertion or
future regression test is installed in the reviewer workspace.

For recovery, `run --skip-failed` leaves failed rows untouched while completing
unattempted rows; the summary stays incomplete. `run --run-id OPAQUE_ID --limit 1`
selects an existing frozen trial without changing its plan or instructions. Retrying
a failed row automatically moves its old logs to `failed-attempts/ID-attemptN` before
starting the new attempt. Do not delete failures or treat unfilled rows as clean reviews.
The [revision-2 partial record](../../benchmarks/reports/codex-discovery-v2-partial-2026-10-28/REPORT.md)
is explicitly incomplete because of model capacity errors and timeouts.

The [62-report recovery checkpoint](../../benchmarks/reports/codex-discovery-v2-checkpoint-2026-10-28-62/REPORT.md)
preserves later progress without replacing the original partial artifact. All 72
trials have been attempted; ten remain undelivered. The candidate can reach at most
10 target detections versus plain Codex's completed 9, so the preregistered +3
improvement threshold is already unreachable. Missing reports remain missing,
not scored as misses. Continue the frozen plan for delivery and cost accounting.
