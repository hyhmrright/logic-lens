# Logic-Lens development

The source of truth is tool-neutral Markdown under `skills/`. Python 3.11+ provides
portable packaging, CLI adapters and evaluation; no npm runtime packages or model
SDKs are required. `package.json` supplies optional command shortcuts and version
metadata. Codex is the default tested CLI, and other tools can consume exported
prompts or implement the command adapter protocol in `docs/TOOL_COMPATIBILITY.md`.
Claude is not required for development, testing, installation or evaluation.

## Layout

- `skills/_shared/`: shared language rules, Iron Law, L1–L9 definitions, traces and templates.
- `skills/logic-*/`: discovery entry plus detailed guide; fix-all has phase-specific guides.
- `scripts/logic_lens.py`: public CLI (`review`, `bundle`, `eval`, `discovery`, `verify`).
- `scripts/llm_runner.py`: Codex/command execution, isolation, bounded concurrency and event parsing.
- `scripts/skill_bundle.py`: complete prompt compilation and portable skill packs.
- `evals/content/v2/`: unchanged synthetic content regression suite and its legacy grader.
- `evals/trigger/v2/`: description-routing inputs; host-native activation is a separate question.
- `evals/discovery/`: pinned historical source pairs, independent oracles, comparison protocol.
- `benchmarks/`: frozen historical summaries/reports. Preserve model/provider provenance.
- `tests/`: offline unit/integration tests for grading and runner integrity.
- `skills-workspace/`: ignored source clones, isolated environments and paid-run artifacts.
- `.codex-plugin/`, `gemini-extension.json`: optional native distribution metadata.
- `.claude-plugin/`, `commands/`, `hooks/`, `.claude/`: legacy optional host integration;
  their cache and multi-agent iteration workflows are not prerequisites for the generic runner.

## Maintained conventions

- Share framework content through `_shared/`, not copied into per-skill guides.
- Findings use Premises → Trace → Divergence → Trigger → Remedy, with L1–L9/Cx codes.
- SKILL.md has name/description frontmatter, clear exclusions, and 5–7 guide-linked steps.
- Preserve investigation evidence, source versions and runtime limitations. Do not infer
  skill activation from literal report labels or infer correctness from a score of 100.
- Explicit prompt snapshots remove the old plugin-cache synchronization requirement.
  Native-host cache management, if used, is that integration's responsibility.
- Existing content assertions/grader must not be relaxed to lift a candidate score.
- Skill effectiveness needs same-provider/model/tool comparisons and per-case repeated
  measurements. Public development cases are not a prospective holdout.
- Use separate iteration directories with a final report, never overwrite prior evidence.
- Keep provider-specific names out of shared skill logic. Use capability detection and
  explicit limitations rather than claiming every host supports the same tools.

## Validation and commands

```bash
npm run validate
npm run unit-tests
npm run lint-shell
python3 scripts/logic_lens.py bundle --pack --out skills-workspace/portable-pack
python3 scripts/logic_lens.py review --workspace /path/to/repo --out /tmp/review-run \
  --model gpt-6.1-sol --prompt /path/to/request.txt
SMOKE=1 TAG=codex-smoke npm run content-evals
```

Provider defaults: `PROVIDER=codex`, `MODEL=gpt-6.1-sol`, `EFFORT=high`. Override them
explicitly and preserve the choice in run metadata. Generic command adapters require
`PROVIDER=command ADAPTER=/absolute/path/to/adapter.json`. No Claude login/cache is used.
Routing evals evaluate which skill a model would choose; they do not claim to measure
an editor's native activation mechanism. Do not merge the two measurements.

Before releasing, run source-backed discovery comparisons, inspect false positives,
and validate unseen projects/families. When authentication/runtime access is blocked,
commit the experiment with the blocker documented rather than inventing a gain.

## Versioning and adding skills

`package.json` is the version source. `npm run bump-version -- X.Y.Z` updates five
JSON manifests and the README badge, then validates. Add CHANGELOG manually. Use
patch for guide improvements, minor for new capabilities, major for methodology
changes. An experimental branch can remain Unreleased pending qualification.

New skills need a guide, eval cases and portable bundle registration in
`scripts/skill_bundle.py`; native host registrations/wrappers are optional and must
be kept accurate if supplied. New risk codes require a non-overlapping definition,
tracing methodology, examples in two languages, severity rationale and eval cases.

## Current experiment authorization

The completed v2 comparison is immutable. Revision 3 remains in draft PR #16 as a development candidate,
not a qualified release or the main branch default. The user has limited tokens and explicitly requires approval
before **any new model-backed experiment**, including development-set diagnostics,
smoke/content/trigger evals, retries and fresh-case comparisons. Offline validation,
bundling and existing-evidence analysis are authorized. Present the frozen revision,
run count, provider/model, budgets and known/unknown cost estimate before requesting
approval. A passing development gate does not authorize the next stage. Do not create
a model-running heartbeat or CI experiment. The proposed revision-3 stages remain on the experiment branch in PR #16.

## Proposed experimental offline tools

The optional offline commands are split from draft #16 without its skill changes,
model harness changes or model reports. See docs/TYPED_INVESTIGATION.md and related
protocol guides. Qualification drivers require an explicit trusted-synthetic flag;
never run them on real repositories. Existing historical evidence remains in #16.
No new model evaluation or automatic retry is authorized. A static real-project
integration assessment remains a promotion gate; keep this PR draft until reviewed.
