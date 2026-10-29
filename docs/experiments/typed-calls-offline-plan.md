# Typed calls — synthetic-only qualification plan

2026-10-29, draft #16 only. No formal skill/model/real subject execution/main merge.
The 12 synthetic packages are organized by semantics, not previous real-module names:
bytes/defaults, unittest binding, allowed refusal, relative source, reexports,
shadowed names, lifecycle context, contract conflicts, mutable defaults, external
boundary, unsupported content and equal-length/different-content bytes.

Static unit tests never execute these subject functions. Only the explicit trusted
qualification driver can execute them. One published diagnostic batch: <=64 total
scheduler root-call attempts and <=128 total independent evaluator root-call attempts,
including binding-error attempts. Separate counters increment before each attempt;
no retry. Module loading is restricted to reviewed checked-in synthetic source hashes,
never real targets or test files. Existing historical regression tests are separate
from this diagnostic and do not dispatch the new fixture functions.

All static plans are frozen before any actual call. Equal-length bytes retain full
content. Omitted/explicit defaults canonicalize for conflicts but preserve provenance.
Test evidence is exact and conditional; generated families do not establish validity.
Same queue limits across packages, 8 static tasks/package, <=64 static tasks total.
Unsupported/context-unknown/conflicting evidence cannot execute. Static unsupported
body observations remain blocked; do not substitute cases to fill execution budget.

Independent finite evaluator: length0..8 for six supported fixture roots, including
both enabled values for the keyword-only case and both A/B fills for the content case:
72 calls. Also ten fixed Python binding checks (omitted/explicit immutable defaults,
positional-only/keyword-only, None, missing/duplicate/unknown/extra arguments), total82.
Labels and evaluator outputs never feed planning. Compare actual Python values,
exceptions, parameter binding and nested call argument values with static facts.
Stop on disagreement/unexpected exception/import/hash change; retain remaining work.

Pass requires supported observations/binding to agree, unknowns not promoted to
confirmed bugs, and tests for aliases/relative provenance/shadowing/conflicts/class
context/budget preservation plus rename/default-spelling/function-move transformations.
No inference of real usefulness, oracle generalization or model token savings.
