# Experimental constraint relation → property/domain planner

This optional offline prototype remains in draft PR #16. It neither changes the
formal review skill nor invokes a model. It consumes **manually supplied, sourced
relationship declarations**; it does not extract facts or contracts from code.
The prototype supports one relation family: a reachable integer input passes through
an affine quantity conversion into a consumer with a `<=` precondition.

```bash
python3 scripts/logic_lens.py constraints \
  --spec examples/constraint-plan/relations.json \
  --workspace examples/constraint-plan/workspace \
  --out /tmp/new-constraint-plan.json
```

Output refuses overwrite and placement inside the source workspace. No subject code,
adapter, model or external service is executed by this command. The complete output
retains declarations, source spans/file hashes, canonical spec SHA256, generated
property descriptions, finite domains, predicted partitions and selection reasons.
The short CLI response only lists selected relation IDs and the artifact path. This
is not yet an executable `search` specification or a model-session integration.

## Declaration schema

The example JSON is the complete runnable form. Top-level `schema_version:1`,
`relations` (1..16), `search_slots` (1..4, default2) and `max_domain_points`
(1..64, default32). Every relation needs a unique nonempty `id` and five blocks:

| Block | Required declarations |
|---|---|
| `contract` | `source`, `status` (`supported`, `unknown`, `conflict`), `obligation:consumer_precondition`, `claims` |
| `input` | `source`, `unit`, `valid` closed integer intervals |
| `producer` | `source`, `kind:integer_affine`, `input_unit`, `output_unit`, nonzero integer `scale`, integer `offset` |
| `consumer` | `source`, `unit`, `operator:<=`, integer `bound` |
| `route` | `source`, `guard` closed integer intervals over the same input parameter |

A `source` is `{path,start,end,quote}`, relative to workspace, one-based inclusive.
Quotes must match exactly; path traversal/out-of-tree symlinks are refused. Matching
quotes and hashes establish provenance, **not semantic truth**. A reviewer must check
that the selected code implements the declared conversion, that units/route conditions
are correct, and that the contract really requires the consumer precondition here.
A handled/rejected/alternate route must not be labeled as unconditionally reaching
this consumer. Implementation facts choose search points, not the expected outcome.

Each supported contract has1..8 explicitly sourced claims:
`{effect:allow|deny, scope:[[lo,hi],...], source:{...}}`. They describe public input
permission under the declared applicable context. The prototype computes overlapping
allow/deny scopes on the reachable route and returns an unresolved conflict. It also
blocks denied inputs mislabeled valid and gaps in allowed scope. It does not read
prose to infer applicability, reconcile precedence/version differences, or discover a
missing opposing policy. Claims from different contexts must not be incorrectly
combined; that annotation remains manual. Unknown/declared-conflicting contracts
stay unresolved before any domain is selected.

Each interval list contains1..8 finite integer intervals. Endpoints, coefficients,
offset and bound are integers in [-1e9,1e9], excluding booleans. Overlapping/adjacent
intervals are merged. Nonlinear transformations, constant producers, open/unbounded
intervals, floats, other comparison operators and multi-variable/stateful constraints
are unsupported; the tool refuses or explicitly defers rather than guessing.

## Generation and eligibility

1. Intersect public validity with the declared route guard. Empty intersection is
   `unreachable`, not a bug or tested pass.
2. Check declaration compatibility: producer input unit matches public input unit;
   output unit matches consumer unit. There is no implicit unit conversion.
3. Resolve permission-scope conflict/gaps on that route. Do not silently pick a policy.
4. Form the candidate property: on a supported reachable input, the **actual argument
   supplied to the identified consumer** satisfies the sourced precondition. The
   affine model is used only to select distinguishing inputs; checking its predicted
   output against itself would be a circular oracle.
5. Invert `scale*n+offset <= bound` using exact integer arithmetic, including negative
   slopes. Keep reachable interval endpoints and nearby inverse-boundary integers;
   filter every point by public validity and the route guard. Domain holes remain
   holes. Units are explicit, so internal byte limits never become record counts.
6. Record predicted safe/unsafe partitions and a predicted passing control. Neither
   is execution verification. An entirely safe domain has no distinguishing crossing;
   an entirely unsafe domain has no passing control. Both remain visible, ineligible
   for this narrowly scoped boundary-search selector, not discarded as uninteresting
   or labeled correct. The latter can still be a valuable manual lead.
7. Exceeding the domain point budget is `budget_blocked`; no silent truncation.

No generated property is automatically a confirmed bug. The current planner does
not execute it, validate a real control, check defenses or complete an Iron Law report.
The existing `search` engine also cannot be credited with running these plans until
a separately implemented and tested bridge supplies faithful adapters.

## Selection

Select only a supported ready candidate with a predicted passing control and a
reachable opposite partition. Under the slot budget, admit at most one candidate per
overlapping producer/consumer source edge, then smaller domain size and stable ID.
There is no severity score, model probability or calibrated bug-yield estimate.
Known/unresolved/blocked routes cannot fill empty slots just to reach a quota.

Two edges are considered the same if **both** producer spans and consumer spans
overlap in the same hashed files. This is a conservative span heuristic, not semantic
independence or root-cause deduplication. Disjoint spans in one function can escape
it; broad spans can group distinct behaviors. Incorrect/manual/incomplete relation
inventories remain the main limitation. Unselected qualified entries retain a
`same_edge_deferred` or `budget_deferred` reason; noneligible entries explain why.
No historical model result, project name or known real-case reproduction is encoded.

## Synthetic validation boundary

`tests/test_constraint_plan.py` checks actual synthetic packet conversion/consumption,
a correctly guarded alternate route and a truly unreachable route, plus constraint
algebra, contract scopes, selection, source provenance and CLI behavior. A separate
finite enumeration checks generated partition coverage for108 signed affine models
with a gapped valid domain. Tests use the actual synthetic implementation when
checking execution behavior; algebra tests intentionally exercise declared models.
None of this measures autonomous source extraction, useful relationship discovery,
real-project bug recall, precision or superiority to direct Codex.
