# Frozen relation generalization — synthetic pass, real integration blocked

2026-10-30. User authorized new transformations and static Python integration only.
Draft #16; no formal skill changes, models, real target/test invocation, main merge,
release, sample replacement or selector fix. Frozen selector remains e20f548.

## Freeze chronology and selection

- `3649a9c`: protocol and two-phase driver committed before preparation/results.
- `40566cd`: new input strings/labels, real selection ledger, installed source/test
  snapshots and implementation hashes committed before any selector invocation.
- Preparation selected **ast and bdb** without invoking either selector. It examined
  32 filenames:27 exclusions,2 insufficient public-function counts (abc, antigravity),
  1 AST-budget exclusion (argparse),2 selections. No supported-body or test-availability
  filter. Earlier annotationlib/base64 targets were excluded in advance.

Provenance is installed CPython3.15.2 source, interpreter/build/path in the manifest;
the upstream Git revision is unknown. Source/test bytes and PSF license are archived.
The fixed `test/test_ast.py` path is absent; that does not mean CPython has no ast
tests. The protocol did not search alternative directories or construct new bindings.

The running stdlib ast module is also the infrastructure parser imported before
selection. No frozen snapshot was loaded/imported as a target, and no real target
test/function was invoked for validation. Parsing necessarily uses installed parser
infrastructure; this is not a hermetic external assessment of the ast implementation.

## New transformation results

Constants derive from the frozen SHA256 rule, without looking at outputs. Inputs
are fresh relative to earlier selector development; the implementation did not change
after their results. They remain same-author development samples, not external blind
evaluation or new real-bug cases. Labels use independent handwritten arithmetic and
48 finite evaluations, not the inverse/interval routines or target execution.

| Pair | Canonical/transformed result | Checked transition |
|---|---|---:|
| Positive affine reassociation/rename |Invariant/pass |11 |
| Negative coefficient + unittest/default spelling |Invariant/pass |12 |
| Reversed comparison + test class |Invariant/pass |12 |
| Helper split/move/import alias |Invariant/pass |14 |
| Sequence repeat/concatenation reordering |Invariant/pass |15 |
| Contradictory caller route, moved consumer |Invariant/pass: inner true outcome unreachable |15, deliberately not selected |
| Nonlinear negative control |Invariant but unsupported in both forms |None inferred |

For the first5 pairs, both variants select the independently checked transition
and neighbors; old fixed families select lengths1,0,2,3 and miss that transition.
Each supported instance uses4 static dispatches per arm:10/10 reachable synthetic
consumer transitions selected by the new arm versus0/10 by old. These denominators
are constructed semantic instances, not independent defects. The route pair also
uses4 vs4, preserves its outer cut and declines the unreachable inner cut in both
forms. Unsupported controls use1 new vs4 old dispatches each, not padded to equality.

All6 supported-intent pairs preserve normalized parameter-coordinate predicates,
transition, supported conditional route reachability, status and proposed quantities.
Raw source hashes/relation IDs appropriately differ after moves/renames. Unsupported
results are kept, not included among successful boundaries. All generated inputs
still have unknown validity and no newly inferred normative property.

Completed synthetic accounting: old56/56 maximum dispatches, new50/56; independent
arithmetic48/48. Equal caps are not equal total work; the per-instance comparisons
above use actual counts. No efficiency, cost-saving or real bug-recall claim follows.

## Real check failure and bounded stop

The batch stopped during its first real module, **ast**. Raw `failure.json`, the
attempt record and preceding synthetic outputs are retained. There is no successful
batch summary from the driver. `post-stop-audit/audit.json` is explicitly a later
manual/AST reconstruction, not a fabricated successful terminal record.

The prototype failure has a source-backed trace:

- **Premises:** ast.py line23 has `from _ast import *`. Frozen `Project.symbol`
  conservatively returns unknown for names in a namespace containing star imports.
  Public synchronous definitions such as parse still appear in the initial inventory.
- **Trace:** missing sibling test leads to the specified source-only fallback.
  `select` inventories a public definition, resolves its target as unknown, then calls
  `Project.function(target)` in the no-examples branch, outside its exception handler.
- **Divergence:** `Unsupported: target not a local function` escapes instead of
  producing a visible unresolved entry. Source uncertainty becomes a tool failure.
- **Trigger:** a public definition in a star-import namespace, with no exact binding.
- **Remedy:** in a later revision, preserve unresolved entry identity/reason and skip
  callable-only analysis until resolution qualifies. Do not turn star imports into
  guessed local ownership. No fix or replay was made in this frozen round.

This is a defect in our prototype's unknown-state handling, not a discovered bug in
CPython. Per preregistration, unexpected failure stops the batch: retries0, ast output
reports missing, bdb selector integration **not attempted**. Neither is counted as a
successful extraction or silently scored as zero bug yield. The old ast arm returned
in memory before the new arm failed; its report was not persisted. No real interpreter
dispatch report is available. Source inspection shows the failing path precedes new
dispatch, but that inference is distinguished from an instrumented completed report.

## Post-stop source audit — no additional selector run

Independent text/AST review of both frozen modules completed without executing them:

| Module | Public top-level functions | Raw comparisons/calls, whole AST | Static check disposition |
|---|---:|---:|---|
| ast |14 |57 /194 |Star import; expected test file absent; selector fails before delivering inventory |
| bdb |6 |87 /198 |Not attempted by selector after stop; source/test audit only |

Audit retains first/last public definition, first public comparison/call and the
ast star-import source span. ast.parse uses compiler flags and optional arguments;
ast.main depends on argparse, file I/O and dynamic options. No supported isolated
entry contract is inferred from those signatures. There is no tool inventory to
compare against for ast, so source-span agreement is not claimed as a passed gate.

bdb's archived test file has46207 bytes/6291 AST nodes and fits the unchanged source
limits. It contains13 classes,37 test_* methods and1 raw `assert` (not a count of all
framework assertions). The first test uses instance expectation state and TracerRun
before `tracer.runcall`; the first/last public source functions use object methods
and tracing. These are context challenges, not proof that the extractor would return
zero usable obligations. Its actual evidence/searchable relation counts remain
**unmeasured**. No replacement module, synthetic real contract or fabricated success.

## Decision and limits

The fresh synthetic transformation gate passes on its frozen subset. Real static
integration is **not qualified**: one failed module and one unattempted module,
zero established searchable real relations, with missing results explicitly retained.
The latter is an evidence count, not a measured0/2 recall rate. Overall promotion
gate remains open, and no model diagnostic is justified automatically.

Next work should first make unresolved entry inventory fail closed into unknown
records, with offline regressions for star imports/rebinding. Then seek separately
scoped integration completion, preserving this failed round and distinguishing new
revision regression checks from a fresh holdout. Do not expand syntax support or
spend model tokens to disguise this integration failure.

## Artifacts and repository checks

`offline-relation-generalization-2026-10-30/prepared/`: frozen ledger, source/test
snapshots, portfolio, protocol/driver/implementation hashes and PSF license.
`results/`: all28 synthetic arm reports,7 pair adjudications, attempt/failure and
SHA256 manifest. `post-stop-audit/`: explicitly later source audit and reconstructed
counts with its own manifest. No files overwritten; all hashes verified, including
unchanged implementation/protocol/driver.188 repository offline tests, validation,
shell lint and whitespace checks pass. These do not turn the failed real check green.
Actual analyzed-subject calls0, model evaluation calls0; implementation/chat tokens
are separate and no evaluation token-saving claim is made.
