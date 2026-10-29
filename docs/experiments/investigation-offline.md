# Offline investigation scheduler — synthetic closed-loop qualification

Date: 2026-10-29. The user authorized the smallest offline investigation loop in
draft PR #16: relation discovery, fact validation, selection and property execution
on synthetic programs only. No formal skill changes, model evaluations, new real
cases, main merge or background work. No discovery/precision/token-saving claim.

## Implemented boundary

`python3 scripts/logic_lens.py investigate` joins the existing facts, constraint
planner and property engine, with a fixed trusted-synthetic executor. Default is
planning only; `--execute-trusted-synthetic` opts into actual local execution. The
request supplies public entries, independently sourced valid domains/outcome contracts
and source hash, not suspicious consumers, models, routes or failure examples.
See [exact algorithm, schema and limitations](../INVESTIGATION.md).

New `facts` explicit-point support preserves old contiguous-window behavior and
records gaps as unassessed. The scheduler enumerates candidate consumer call sites,
interprets seed points, derives inverse-boundary points in one refinement round,
checks enlarged points, feeds the planner and checks its transferred declarations
against source. Search inputs must remain checked and contract-valid. The fixed
adapter's oracle is the entry must-return contract, **never the derived internal
threshold/coefficient**. Interpreted facts are compared with actual execution; any
contradiction blocks the result and stops dispatch rather than generating a bug.

The planner's precondition IR describes a structural investigation lead only. It is
not an automatically recovered public obligation. Facts/bridge checks reuse one
interpreter and provide consistency gates; real execution provides the independent
cross-check. Business contract applicability and trusted-fixture review remain manual.

## Archived closed-loop example

All raw evidence is preserved in `offline-investigation-2026-10-29/`, including
request, source snapshot, implementation hashes, inventories, points/facts, bridge
checks, property specifications, fixed adapter/config, cases, observations, source
integrity, summaries and SHA256 manifests. Generated absolute paths refer to the
original temporary run; archived relative files preserve the data and hashes.

| Stage | Observed result |
|---|---|
| Inventory |5 actual consumer-call relationships under supplied entries; unused consumer excluded |
| Refinement | First entry seed points `[0,1,9,10]` expand to `[0,1,4,5,6,7,9,10]`; boundary input6 was not a seed |
| Eligibility/selection |2 qualified relations from distinct entries selected;3 others deferred with reasons |
| Actual execution |2 source-derived finite searches produce entry-contract counterexamples |
| Local calls |5 +6 =11 total adapter invocations, including controls and reduction |
| Guarded alternative | Deferred: no predicted contract-distinguishing outcome on checked points |
| Allowed refusal | Deferred: permitted ValueError supplies no must-return violation oracle |
| Unobserved branch | Deferred as not observed in checked points, never globally unreachable |
| Integrity | Original source before/after digests equal; execution-copy integrity and artifact hashes verified |

This is an intentionally constructed synthetic portfolio, not a new real-case dataset
or evidence the selector finds the most valuable real bugs. A counterexample is an
entry-contract violation under the supplied trusted fixture; causal root attribution
is not automatically proven by the relation that led to it.

## Behavioral qualification

19 new tests (18 scheduler tests and1 explicit-point facts test) pass, bringing the
repository total to **146 passing tests locally**. They cover:

- Automatic call inventory and exclusion of uncalled consumers; default no-execution.
- Two-pass refinement beyond seeds and contract/checked-point domain preservation.
- Distinct-entry slots versus related candidates; independent qualified entry remains
  available when another is unsupported; unknown/allowed-refusal candidates cannot
  fill slots just to exhaust budget.
- All-predicted-unsafe relation gets one actual direct probe without a fake control.
- Premature entry rejection is checked against the unchanged public valid domain.
- Corrupted planner coefficient, unit, route and unchecked input domains block transfer.
- Actual execution/fact disagreement blocks qualification; first block/setup failure
  stops later dispatch, preserves failure/missing records and never retries.
- Unsupported syntax, budget overflow, hash drift, forbidden request hints, overwrite
  and source-output placement refuse/defer rather than becoming success claims.
- Renamed consumer, equivalent arithmetic and removal of an unrelated function preserve
  discovery of the two corresponding relations in this portfolio. Stable-ID tie
  preference is not promised invariant for arbitrary tied candidate sets.
- Explicit facts point sets do not imply their enclosing gaps were checked.

Repository validation, shell lint and authored diff checks pass. All six formal skill
snapshots and portable exports remain unchanged from task-start HEAD; review SHA256
`d429f5d89726d00cf166644a238849b0fce2e9f1a75197f0d106d5ac5fe6de37`.
The companion evidence JSON records hashes and example outcomes. Prior model plans,
reports and oracles remain unchanged. No model call/evaluation token use; chat and
implementation usage are outside that accounting.

## Remaining limits

- One restricted Python module, affine sequence quantities and recognized literal
  upper-bound consumers. No nonlinear/text/state/concurrency/cross-module discovery.
- Entries and public contracts remain manual; quotes/hashes cannot prove semantic
  applicability or resolve conflicting business policies.
- Initial seeds use entry-level scalar comparisons; helper-only interior branches
  can stay unobserved. One refinement round and finite points cannot prove complete
  route coverage or global unreachability.
- Selection is one relation per entry plus domain cost/stable ID, not calibrated
  importance, semantic independence or expected bug yield. Distinct valuable relations
  within one entry may be deferred; entry-only failures without a recognized consumer
  are not covered. Multiple models/sites sharing one consumer can be over-deferred.
- The actual executor is for explicitly reviewed trusted synthetic programs only,
  not an OS sandbox. Fixed forwarding observation is checked for this pure subset;
  it is not a general instrumentation-equivalence guarantee.
- `complete` means the bounded workflow finished, not correctness or comprehensive
  audit. No paid follow-up, main promotion or improved real bug recall follows from
  this synthetic offline pass.
