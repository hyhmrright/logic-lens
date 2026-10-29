# Typed call evidence, binding and provenance — synthetic-only result

2026-10-29. User authorized typed evidence/binding/static dependency source resolution,
existing queue integration and trusted synthetic validation only. Keep draft #16.
No formal skill changes, model evaluations, real-code execution, main merge, new
real cases, real-module readout or automatic retries.

## What improved

New opt-in `typed-investigate` reads an explicit source root and test-module identities.
It does not require manually listing entries/valid domains/contracts. It extracts exact
conditional calls from supported plain/unittest test classes, preserves bytes content,
bool/None/tuples, binds positional/keyword/default arguments, resolves supported local
imports/reexports and schedules verification plus finite single-argument exploration.

Parameter origins survive canonicalization: omitted defaults and equal explicit values
share an obligation/conflict identity, but remain distinguishable evidence. Relative
imports/reexports carry source positions and identities; outside behavior stays unknown.
The typed and prior integer explorers share one alternating round-robin queue. The
prior integer path algorithm/semantics remain intact, covered by its regression tests.

This addresses concrete supported-shape blockers from the previous prototype. It does
not show better real-module extraction, new hidden-path coverage, real bug recall or
superiority over Codex. No claim based on retesting the two previously selected modules;
neither was loaded/read as a target in this round. No benchmark-specific branch exists.

## Frozen synthetic portfolio

Twelve packages defined by semantics, with source/test hashes pinned before execution.
The prior prototype's single-integer/top-level-test assumptions are not used as input.

| Family | Observed result |
|---|---|
| Plain test class + local bytes + literal default | Exact conditional call, full content/default binding, actual match |
| Aliased unittest.TestCase + pos-only/kw-only + bool/None |2 exact calls, omitted/explicit keyword behavior preserved |
| assertRaises(ValueError), helper capacity | Allowed refusal matches; generated rejection supplies no new oracle |
| Relative package import, helper dependency | Entry and nested helper resolve to source, actual call values agree |
| Module alias + reexport | Full identity chain reaches backend definition, actual match |
| Rebound imported function | dependency_unknown, no eligible queue entry |
| setUp/lifecycle state | context_unknown, no eligible queue entry |
| Omitted/explicit-default contradictory expectations |2 conflict records, no eligible queue entry |
| Mutable default | unsupported, no eligible queue entry |
| External dependency behavior | Exact expectation retained, body observations unsupported, no actual execution |
| Unsupported byte slicing | Exact expectation retained, body observations unsupported, no actual execution |
| Equal-length different-content bytes + tuple default |2 distinct exact calls preserved; expected outputs1 and2 both match |

15 extracted call records:10 exact_conditional,2 conflict,1 dependency_unknown,
1 context_unknown,1 unsupported. Exact expectations for unsupported bodies remain
visible; evidence extraction success does not qualify execution semantics.

## Execution accounting — one actual batch, no retries

All static plans completed before any actual subject invocation. Static dispatch64:
48 supported observations and16 unsupported observations. Unit tests for the new
pipeline are static and do not call these subject functions. Existing historical
synthetic regression execution is separate and does not dispatch this portfolio.

| Counter | Actual attempts | Cap | Result |
|---|---:|---:|---|
| Scheduler root invocations |48 |64 |48 actual/static agreements |
| Independent finite-domain root invocations |72 |part of128 |72 actual/static agreements |
| Independent Python binding root-call attempts |10 |part of128 |10 agreements, including invalid-call attempts |
| Independent total |82 |128 |Within cap |

The published batch executed130 root attempts total, in **two separately bounded
categories**, not a combined64 cap. Nested helper calls are traced but do not count
as additional root attempts. The two counters persist before calls; no failed
service/model attempts, retries, unexpected execution failure or disagreement.
The16 unsupported static tasks were never actually executed or replaced to fill
unused budget. All64 planned static dispatches have a recorded disposition.

Actual Python values, returned/ValueError outcomes and nested call parameter values
match the static facts. Python signature binding independently checks original test
argument spelling/default application;10 cases cover defaults, None, positional-only,
keyword-only, missing/extra/duplicate/unknown arguments. The independent72-point
universe was fixed in the plan and not fed to scheduling. It does not exhaust all
possible tuples/bytes or all generated parameter interactions.

Queues remain bounded:67 pending admitted tasks and2 overflow attempts across the
portfolio. `complete` is diagnostic completion, not exhaustive investigation. The
keyword/default fixture fills admission capacity early; this is an exposed queue
bias, not claimed optimal selection.

## Validation and provenance

16 new static tests /177 total pass locally, including typed codecs/default binding,
class contexts, actual source identities, unknown dependency boundaries, conflicting
cross-file examples, equal-length content, budget/pending preservation, fake framework
ownership, local shadowing and rename/explicit-default/function-move transformations.
Static module-level import/raise sentinels do not execute. The actual batch separately
provides independent Python execution; unit tests do not pretend to be that oracle.

Repository validation, shell lint, authored whitespace checks and all archived hashes
pass. Formal skill files/metadata/defaults and prior immutable reports/plans remain
unchanged. Model evaluation calls0; chat/implementation tokens are separate. No main
merge or release promotion. No model-running background work was created.

Protocol: `../TYPED_INVESTIGATION.md`. Frozen qualification plan:
`typed-calls-offline-plan.md`. Raw plans, trusted source/test snapshots, attempt logs,
counters, dispatch/evaluator/binding results and implementation/artifact hashes:
`offline-typed-investigation-2026-10-29/`. The initial planning-only preflight had0
actual calls; the published execution is the single completed batch.

## Remaining limits

- Exact tests remain conditional on their environment. No automatic normative public
  contract, valid-input interval, dependency runtime availability or import side-effect
  proof. A mismatch is a lead, not automatically a confirmed bug.
- Test fixtures/state/custom assertions/helper setup/complex inheritance and parameterized
  tests remain unknown. Simple test-class syntax support is not full framework execution.
- Literal immutable defaults only. Computed/mutable defaults, annotations/decorators,
  variadics/unpacking, local alias assignment and more complex parameter construction
  remain unsupported; even overridden unsupported defaults conservatively block binding.
- Source identity resolution is limited to the explicit-root file budget and simple
  imports/reexports. No C-extension/third-party summaries or arbitrary global state.
- Typed backend is bounded concrete interpretation. It does not reuse affine symbolic
  inversion for byte contents; finite first-element families miss mixed contents and
  interacting arguments. It is not a general byte/string property solver.
- The typed scheduler starts from eligible test-derived targets, so untested public
  entries remain outside it. Existing exact tests provide no new oracle for most
  generated inputs; this stage does not establish autonomous new-bug discovery.
- Entry/admission order and early length families can starve useful later tasks. Pending,
  overflow and unsupported paths remain visible; no completeness or calibrated priority.
- Trusted execution is not an OS sandbox. No arbitrary real source/test import or run
  is authorized by this pass. No new paid diagnostic/main promotion follows from it.

Next useful work is to assess **static** integration on independently selected typed
call shapes, and to improve context applicability and fair family admission, rather
than assume these synthetic passes establish real-project readiness. Further stages
need a separately authorized scope; no automatic follow-up is scheduled.
