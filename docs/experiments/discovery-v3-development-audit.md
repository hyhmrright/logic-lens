# Revision 3 — offline development audit

Status: structural check only; no new Codex reviews, model calls or behavioral
experiments. Gate B remains pending user approval. Existing cases are development
evidence. This document records predicted decision changes, not observed improvement.

## Evidence and changes

The [complete v2 record](../../benchmarks/reports/codex-discovery-v2-final-2026-10-28/REPORT.md)
and [trace analysis](discovery-v2-final-analysis.md) show all arms find three targets
and miss the fourth across all repeats. The candidate reads the relevant parser and
regex and runs probes; some later calls validate remedies. This supports testing
allocation and hypothesis generation, not blaming missing source access or claiming
an isolated cause. Both skills have zero unsupported assertions under the existing
unblinded judgments; retain that evidence discipline.

The candidate changes are:

- Replace long scenario lists and ledger fields with transformation → supported
  invariant → distinguishing check → result/next unknown.
- Choose valid inputs around boundaries in the actual implementation, with a control;
  do not assume every representation, operation order or rejection is equivalent.
- After a finding, return to unresolved obligations. Defer executable repair and
  broad remedy regression to a fix task; retain a concrete final remedy and disclosed
  mental check. The old Step 5 required executing a minimal remedy and nearby tests,
  contradicting the intended discovery-before-polish priority.
- Remove the shared fallback suggesting names establish intent for logic-review;
  its main guide already required sourced contracts. No weakened oracle standard.

## Replay of all existing target mechanisms

| Development target | Existing evidence | New next-check obligation | What this audit cannot establish |
|---|---|---|---|
| dateutil inequality | All arms find the foreign-operand fallback violation | Follow operator dispatch to the observable comparison; compare supported foreign-operand fallback with its control | That shorter instructions preserve this detection |
| dateutil midnight | All arms find rollover lost during normalization | Check time normalization against the date consumer and an ordinary neighboring time; use the documented rollover oracle | That a new model run generates or verifies this pair |
| semver diff | All arms find prerelease graduation overriding a release change | Track early return to classification; compare a release-component change with a same-component control | That allocation changes improve this already-found case |
| semver build | All arms miss bounded stripping with a retained numeric tail | Inspect the actual bounded transform, exercise its boundary with valid equivalent metadata and compare parsed release components | That the model notices the bound or constructs this discriminating family unaided |

These evaluator-known examples stay in this audit, not the generic skill. Nearby
hyphen-metadata bugs are not accepted as the long-tail target. Invalid-input rejection
without a contract remains unsupported. The diagnostic must use original frozen
oracles, not replace them with these descriptions in reviewer prompts.

## Structural gate and remaining overhead

Before editing, the entry and guide contained 2,397 whitespace-delimited words;
after editing they contain 1,335 (44.3% less). This is word count, not tokenizer
measurement or a prediction of output/price. The compiler still includes all five
shared resources, so full compiled context is reduced by much less. Compared with frozen 32151b0, the complete review snapshot changes from 9,822 to
8,770 words and from 69,641 to 62,235 UTF-8 bytes (about 10.7% fewer words).
Lazy-loading language does not make the current compiled snapshot lazy.

Do not silently drop shared rules to improve this ratio: report templates, trace
requirements and risk definitions have cross-skill consumers. A selective compiler
would be another intervention requiring separate integrity and behavioral validation.
This candidate leaves the compiler and other skill guides unchanged. It does not
optimize model pricing, invent hard token caps, relax the existing grader or claim
all coding hosts have been tested.

Gate A passes if links/bundles and offline repository checks pass and the final
candidate still preserves contract, trace, rebuttal, uncertainty, localization and
remedy rules. Gate B is explicitly **not passed** by this document. No new-case
curation, `discovery prepare/run`, model-backed content/trigger eval or automatic
retry is part of this task. See the [approval-gated draft](discovery-v3-preregistration.md).

## Offline validation record — 2026-10-28

- `npm run validate`: passed; its generic “release-ready” message is a structural
  validator result, not experimental qualification.
- `npm run unit-tests`: all 76 tests passed, including immutable v2 evidence checks
  and portable bundle/runner tests. No paid content/trigger/discovery eval ran.
- Portable export: all six skills compiled/exported in a temporary directory; no
  model invocation and no overwrite of existing experiment snapshots.
- `git diff --check`: passed before commit.
- Skill-creator `quick_validate.py`: blocked by missing PyYAML in both the default
  and bundled Python. No package was installed. Entry frontmatter/name/description,
  guide references and absence of scaffold placeholders were inspected directly;
  this does not replace a successful run of that validator.

Complete new review snapshot SHA-256:
`9dd5e4c50d47cd71fca3d04abc006690759e8510cdbce705a9853c4a61685e0a`.
The commit containing this audit identifies the initial candidate source; any
subsequent behavioral diagnostic must first verify its freshly compiled SHA.
The current package version remains 0.6.10; no release or performance claim follows.
