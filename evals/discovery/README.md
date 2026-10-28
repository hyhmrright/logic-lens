# Repository discovery experiment (not a release benchmark)

This experiment asks whether the candidate review process finds historical defects
with repository context, compared with a plain model and the prior skill. It does
not replace the existing 104-case content regression suite or change its grader.
The candidate must not be released on offline checks alone.

## Corpus and limits

`catalog.json` pins 20 historical fixes and their first parents: 10 HTTPX, 10 Requests.
Each entry cites an upstream commit, source files, expected behavior, and changed
regression-test paths where present. These are real upstream defects, not generated
fixtures. `oracles.py` contains evaluator-only probes adapted from those sources.
HTTPX probe adaptations are under BSD-3-Clause (`LICENSE.httpx`); Requests probe
adaptations are under Apache-2.0 (`LICENSE.requests`). Upstream copyright notices
and licenses are preserved in those files. No upstream repository code is vendored.

All seeds were visible while designing this experiment; they are **development
cases**, not an independent held-out validation set. Historical public code may
also be in model training data. Add prospective cases from other repositories and
reserve whole projects/defect families before tuning further. Both sources are
Python HTTP clients, so this corpus cannot establish cross-language/business-domain
coverage. Results must be reported per project/family, not just as a single total.

The model is given a target file plus the pre-fix repository context. This measures
**targeted discovery**, not recall from an unbounded full-repository audit. Repaired
snapshots overlay only the changed implementation files on the original parent;
parent tests, docs and configuration remain identical (including any pre-existing
incorrect expectations), preventing future tests and
release notes from leaking the answer. The model receives no issue, patch, fix SHA,
expected behavior, variant label, or catalog. Git history, project agent instructions,
hooks and symlinks are removed. Files receive opaque workspace names.

The three arms receive the same prompt, source variant, tools, model, effort and
per-call budget. Baseline instructions are pinned at `baseline_skill_commit`;
candidate instructions are captured at prepare time. Skills plus relevant shared
resources are explicitly included in the system prompt, identically for both skill
arms. This deliberately tests **instruction effectiveness with guaranteed delivery**,
not automatic skill discovery, progressive-loading reliability or plugin dispatch.
`plain` receives no skill instructions. Delivery hashes are not proof of compliance.

The initial model protocol is **read-only** (`Read`, `Glob`, `Grep`), including for
all arms. Runtime verification is independently performed by the evaluator, not
claimed as a model capability. Integration-capable review needs a separate protocol
using a disposable container with appropriately isolated execution, and must not be
mixed into this baseline. Claude `--bare --restricted` removes ambient settings,
hooks, plugin loading, memory and external MCP servers; the CLI's file-tool scope
restrictions enforce workspace reads. Inspect `events.jsonl` for actual tool use and the init event's available tools; CLI versions may expose a different read-tool set. A comparison is invalid if actual tool availability differs between arms.
Do not add outside directories or enable command tools to work around a failed run.

## Verify the ground truth first (no model calls)

Clone sources to an ignored workspace (full history required for the pinned parents):

```bash
git clone --filter=blob:none --no-checkout https://github.com/encode/httpx.git skills-workspace/discovery-sources/httpx
git clone --filter=blob:none --no-checkout https://github.com/psf/requests.git skills-workspace/discovery-sources/requests
python3.11 -m venv skills-workspace/discovery-venv
skills-workspace/discovery-venv/bin/pip install -r evals/discovery/requirements.txt
python3 scripts/verify_discovery.py \
  --sources skills-workspace/discovery-sources \
  --python skills-workspace/discovery-venv/bin/python \
  --out skills-workspace/discovery-oracles
```

Use Python 3.11 for historical HTTPX; the requests-01 wrapper/protocol defect is
version-dependent (not reproduced on 3.11, reproduced on 3.15). Run that case in a
separate compatible environment via `--cases requests-01`.

Each probe imports the actual exported project, checks module provenance, and runs
in a fresh subprocess with a 10-second timeout. `environment.txt` records installed
dependencies. **Nonzero → zero alone is insufficient**: inspect the failing traceback
against the stated defect before marking the pair verified. Setup/import failures
are blockers, not detections. requests-07 requires Windows; never count a platform
skip as a passing pair. Probes use temporary files/in-process transports rather than
production services. Some internal transport stubs deliberately inject failures;
interpret them as boundary-level checks, not end-to-end network proofs.

## Prepare and run

After edits, perform the repository's cache-sync gate before any content evals:

```bash
bash .claude/skills/sync-skill-cache/scripts/sync-cache.sh
```

Discovery runs themselves use immutable explicit instruction snapshots, not the cache.
Prepare is offline once source objects are available; partial Git clones may fetch
missing objects. The full default matrix is **360 calls** (20 × 2 variants × 3 arms ×
3 repeats). Start with two cases and inspect the plan before running a full matrix:

```bash
python3 scripts/discovery_eval.py prepare \
  --sources skills-workspace/discovery-sources \
  --out skills-workspace/discovery-smoke \
  --cases httpx-09 requests-06 --repeats 1 \
  --model claude-sonnet-4-6 --effort high --budget 1
python3 scripts/discovery_eval.py run --out skills-workspace/discovery-smoke --limit 1
```

Use a new output directory for each candidate; prepare refuses overwrites. Repeat
with `--repeats 3` for comparisons. The run order is randomized with a saved seed.
Each call has a saved budget and timeout, and failures stop the run; complete outputs
are resumable, failed outputs never count as reviews. `--limit` bounds the number
of additional calls. The current `--bare` Claude CLI requires API/provider credentials;
interactive account login alone may not supply bare-mode authentication. Do not
store credentials in any run artifact or repo file.

`plan.json` stores private arm/polarity metadata, revision and instruction hashes.
`events.jsonl` stores actual tool calls and the CLI's terminal usage/cost result;
`report.md` is the review text. Hash drift invalidates a run. Source workspaces must
remain unchanged. Keep all artifacts under ignored `skills-workspace/`.

## Adjudication and release gate

Have a reviewer read randomized reports against the upstream evidence, initially
without the arm label. Match the **root cause and consequence**, not keywords,
L-code spelling, field labels or any-finding detection. Adjudicate other discoveries
separately: a repaired snapshot may contain unrelated real defects. A claimed target
defect on the repaired variant counts as a false positive if the repair actually
removes it. Mere correct-code silence does not establish discovery ability.

Create a JSON object keyed by opaque run ID, with every completed review covered:

```json
{
  "<run_id>": {
    "target_detected": true,
    "false_positive_count": 0,
    "rationale": "Matched the target root cause and its observable consequence."
  }
}
```

On buggy variants, `target_detected` means the actual target was correctly found;
on repaired variants it is normally false. Count invalid claims in
`false_positive_count`, not valid unrelated findings. Keep miss-stage notes alongside
the rationale: context / hypothesis / contract / reachability / verification /
reporting / environment. Do not supply these answers to the reviewing model.

```bash
python3 scripts/discovery_eval.py summarize \
  --out skills-workspace/discovery-smoke --judgments /path/to/judgments.json
```

The summary reports target recall, false positives per adjudicated review, cost,
and completed/adjudicated denominators separately. Completed-run costs exclude
failed attempts, which may still be billable; failures are listed explicitly. Missing results are `null`, not
0% accuracy. Partial or unmatched arm results cannot establish improvement. Before
shipping, require the same cases and at least three paired repeats for each arm,
inspect per-case variance and project/family slices, and evaluate a prospective
held-out set. Predeclare an acceptable false-positive/cost budget before looking at
results. Also run the unchanged content regression suite; record oracle disputes
(such as existing eval-279's assumption that mutate-and-return is intrinsically a
bug) separately rather than editing old assertions to lift the candidate score.
