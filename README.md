# Logic-Lens

Logic-first bug investigation for coding assistants: establish behavioral contracts,
follow real callers and dependencies, trace failure paths, and report reproducible
violations with evidence.

![Version](https://img.shields.io/badge/version-0.6.10-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

The core is **tool-neutral Markdown**, with an optional Python CLI for reviews,
portable packaging and evaluations. Codex is the default tested execution backend.
Other coding tools can read the same skill pack or use a command adapter.
**No Claude account, CLI, plugin cache, vendor SDK or npm dependencies are required.**

## Quickstart

Prerequisites for CLI execution: Python 3.11+, Git and an authenticated Codex CLI.
For manual use in an editor/assistant, only the exported Markdown pack is needed.

```bash
git clone https://github.com/hyhmrright/logic-lens.git
cd logic-lens
python3 scripts/logic_lens.py bundle --pack --out /tmp/logic-lens-pack
```

Add `/tmp/logic-lens-pack/LOGIC-LENS.md` and its directory to your coding assistant's
context, or attach one compiled prompt from `prompts/` alongside the code.

Check local capabilities with `python3 scripts/logic_lens.py doctor` (no model call).
To run a read-only repository review with Codex:

```bash
printf '%s\n' 'Review src/service.py for behavioral bugs and investigate its dependencies.' > /tmp/request.txt
python3 scripts/logic_lens.py review --workspace /path/to/project \
  --prompt /tmp/request.txt --out /tmp/logic-review-run --model gpt-6.1-sol
```

The result contains `report.md`, raw execution events and usage metadata. The runner
reviews an isolated source copy with a read-only policy. It does not edit your checkout.
Model and effort are explicit options; `--provider command --adapter adapter.json`
connects other CLIs. See [tool compatibility](docs/TOOL_COMPATIBILITY.md) for the
protocol, portable use in editors, and the distinction between exported instructions
and tested native integrations.

## Six skills

| Skill | Input and purpose |
|---|---|
| `logic-review` | File/function target; investigate contracts, dependencies and behavioral bugs |
| `logic-explain` | Specific entry/input; explain its actual execution path |
| `logic-diff` | Two versions; check observable behavioral equivalence |
| `logic-locate` | Confirmed failure; trace backward to the root cause and forward to confirm |
| `logic-health` | Module/repository scope; summarize scoped logic risks |
| `logic-fix-all` | Authorized audit/fix/verify pipeline in a write-capable host |

Example: `--skill locate`, `--skill diff`, or `--skill health`. The read-only runner
refuses fix-all; use its exported skill in a host with appropriate edit capabilities.
Optional native host metadata remains in `.codex-plugin/`, `gemini-extension.json`
and legacy plugin files. Native activation varies by host; a loaded prompt or report
field alone does not prove a skill was followed.

## How investigation works

The candidate review process starts from sourced invariants and operation sequences,
not just a checklist of familiar code patterns. It follows caller/callee/config/state
dependencies as needed and records missing evidence as unresolved investigations.
A non-reproducing experiment does not automatically disprove a suspected bug.

Every confirmed finding follows the Iron Law:

**Premises → Trace → Divergence → Trigger → Remedy**

Critical/Warning findings describe concrete expected/actual consequences, a triggering
input or sequence, a minimal remedy and an honest verification status. Runtime evidence
must exercise the real behavior in dispute; static evidence and blocked experiments
are labeled separately. Unresolved leads are not confirmed bugs or automatic fixes.

## Risk taxonomy

| Code | Risk |
|---|---|
| L1 | Shadow/name override |
| L2 | Type contract breach |
| L3 | Boundary blindspot |
| L4 | State mutation violating an actual contract |
| L5 | Control-flow escape skipping required work |
| L6 | Caller/callee contract mismatch |
| L7 | Concurrency/async hazard |
| L8 | Resource lifecycle hazard |
| L9 | Time/locale/encoding hazard |

Definitions live in [skills/_shared/logic-risks.md](skills/_shared/logic-risks.md).
`.logic-lens.yaml` may customize focus, severity and project-specific Cx risks;
see [the shared framework](skills/_shared/common.md). A high score describes the
inspected slice and confirmed findings, not whole-project correctness or shipping safety.

## Evidence and evaluation

The repository includes 104 synthetic content cases, description-routing cases,
real-code probes, and a 20-pair historical repository discovery development corpus.
Discovery compares **plain model / prior skill / candidate skill** with the same
provider, model, tools, budget and source snapshots. Root-cause adjudication and
false positives are separate from report-format compliance.

```bash
npm run validate
npm run unit-tests
npm run lint-shell
SMOKE=1 TAG=codex-smoke npm run content-evals
```

The first three are offline; model evals consume the selected provider's quota.
No npm install is needed. Content evals now default to Codex and compile instructions
from source, removing the old plugin-cache dependency. For discovery preparation,
repeated comparisons, costs, caveats and outstanding release gates, read
[the discovery protocol](evals/discovery/README.md) and [experiment status](evals/discovery/STATUS.md).

A [72-review Codex development pilot](benchmarks/reports/codex-discovery-2026-10-28/REPORT.md)
found 7/12 exact known-regression confirmations for plain Codex, 6/12 for the prior
skill and 7/12 for the candidate. The candidate did not establish superiority over
plain Codex. The report discloses additional findings, resource use, adjudication
and sample limitations. Add `--plain` to the review command for the direct-model control.

The [completed revision-2 comparison](benchmarks/reports/codex-discovery-v2-final-2026-10-28/REPORT.md)
used four newly selected historical defects and a candidate frozen before inspecting
their fixes. All three arms tied at 9/12 target detections across 72 delivered reviews.
The revised skill produced fewer unsupported assertions under author adjudication,
but more output and longer observed durations. Bug-discovery superiority remains
unproven; no release promotion follows.

Historical Claude benchmark records remain in [benchmarks/](benchmarks/README.md)
with their original model/version provenance. They do not establish Codex performance,
head-to-head benefit, or effectiveness of the experimental candidate. Do not infer
bug recall from keyword/format scores. Public development cases are not a prospective
held-out set; unseen projects and independent adjudication remain important.

## Development

Start with [DEVELOPMENT.md](DEVELOPMENT.md), [CONTRIBUTING.md](CONTRIBUTING.md) and
[AGENTS.md](AGENTS.md). Shared instructions are under `skills/_shared/`; individual
skills reference them on demand. `package.json` is the version source; use
`npm run bump-version -- X.Y.Z` to synchronize metadata for a qualified release.
The current discovery candidate remains experimental until its release gates pass.

MIT licensed. Third-party evaluator probe attributions are under `evals/discovery/`.
