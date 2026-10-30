# Relation-first selection — offline implementation result

2026-10-30. Draft #16 only. Implements the next-gate design on a deliberately narrow
subset. Formal skills unchanged; no model evaluation, real source/test execution,
main merge or release. This is not evidence of increased real bug recall.

## Mechanism result

The typed evidence extractor now has an optional relation-first consumer, rather
than changes to the existing fixed-family selector. It inventories untested public
definitions, preserves unbound call edges, follows supported affine local call
chains, intersects route conditions and selects relation boundaries before neighbors.
No fixture identity or historical benchmark constant appears in the selector.

At equal4-dispatch budgets per case, the existing selector chooses lengths1,0,2,3.
Relation selection chooses1 and the transition with its two neighbors:

| Family | Independently checked transition | Old selects transition | New selects transition |
|---|---:|---|---|
| Scale3*x>30 |11 |No |Yes |
| Shift2*x+5>=31 |13 |No |Yes |
| Negative40-2*x<10 |16 |No |Yes |
| Nested2*(x+3)>32 |14 |No |Yes |
| Renamed/moved helper4*x+7>59, regression only |14 |No |Yes |

Independent arithmetic evaluation uses25 fixed integers per family (125 total).
Its handwritten predicates do not use the inverse/interval implementation and are
not supplied to selection. It validates this finite domain, not all integer inputs
or arbitrary Python semantics. No synthetic subject was imported or executed.

The five-parameter competition case gives all5 relations their first turn in6
dispatches including the exact seed. The prior scheduler also uses6 dispatches;
the new result demonstrates first-turn fairness on this case, not universally
optimal scheduling. An impossible inner true branch stays unreachable in the
supported conditional route; out-of-domain neighbors are not replaced by clamped
points. Nonlinear and incompatible-representation expressions remain unsupported.
An untested public comparison remains visible with missing binding and no dispatch.
All generated points have unknown input validity and0 new normative properties.

Across11 executable-shape static cases, old dispatch40/64, new37/64. Actual counts
differ because unsupported/out-of-domain new families are not padded. Only the
stated4-vs4 and6-vs6 comparisons are equal-dispatch comparisons. New inventory has
16 relations:12 searchable,2 unsupported,2 outside the bounded route/domain.
The untested case is separate, with1 unbound predicate. These are source relations,
not confirmed defects, independent semantic classes or bug-recall denominators.

## Corrections and holdout status

One development fairness test initially dispatched4 rather than6 points: routes
mentioning other parameters were blocked wholesale. The implementation now evaluates
those other parameters at the unchanged exact seed and labels the result as a
conditional single-parameter slice, not a global reachability proof.

The initial qualification reported pass, but review found interpreter calls used for
coverage ranking outside its dispatch counters. That invalidates the initial
equal-budget accounting. Both its raw artifacts and frozen implementation hashes
are retained under `initial-pre-accounting-fix/`; do not use it as the final result.

Ranking now evaluates affine formulas without interpreter dispatch. A regression
test counts every interpreter invocation and requires equality with the dispatch
list. The final static batch above passed after the correction. Since transformed
cases were already inspected before this implementation correction, their
`held_out_valid` is explicitly false. They were also authored as part of this
development portfolio, not independently selected real cases. The final pass means
the enumerated mechanism checks passed; **the full independent-holdout/promotion
gate remains incomplete**. No negative result was replaced with a new sample.

## Validation and accounting

11 new static tests cover independent integer restriction checks (all6 comparison
operators, positive/negative coefficients, complements and excluded points), exact
examples, affine transitions, helper provenance, route infeasibility, admission
fairness, untested inventory, unsupported units/nonlinearity, annotation/import
boundaries, conflict gating, limits and absence of hidden interpreter dispatch.
188 repository tests, repository validation, shell lint and whitespace checks pass.

Final qualification:37 new and40 baseline static interpreter dispatches,125
independent arithmetic evaluations; actual scheduler root calls0, independent subject
root calls0, model calls0. The earlier batch is separately archived and is not silently
excluded from history or combined into a claim of a single execution batch. Unit
test arithmetic/AST checks are separate from the qualification counters. Chat and
implementation tokens are not evaluation usage; no token-saving claim follows.

Raw source strings, frozen portfolio hash, implementation hashes, plans, both arms,
independent truth vectors, summaries and SHA256 manifests are in
`offline-relation-selection-2026-10-30/`. No reports or earlier experiment snapshots
were overwritten. The existing formal skill remains unchanged.

## Remaining work

Missing normative properties remain the main barrier to new bug confirmation.
The selector cannot independently infer intended contracts. Public-entry inventory
does not yet supply types/bindings for untested paths; unsupported syntax can stop
discovery early; alternate seeds and content-dependent/multivariate boundaries are
not explored. These restrictions are exposed, not counted as misses or bugs.

Next, independently freeze and assess a fresh static-only integration set and
uninspected relation transformations before more syntax expansion. Do not execute
real targets. Keep poor/blocked results and stop if selection does not generalize.
Only then consider a separately proposed, user-approved model diagnostic with a
token budget. Nothing in this result authorizes a model run or main promotion.
