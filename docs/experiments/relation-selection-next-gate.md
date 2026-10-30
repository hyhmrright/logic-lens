# Next gate: select a relation before generating inputs

Status: offline design, not an effectiveness result. Continues draft PR #16.
No formal skill change, model invocation, target execution, or main promotion.

## Evidence and diagnosis

The completed v2 comparison found 9/12 targets in each arm. Later path-selection
and property-search diagnostics did not recover their original target. Synthetic
typed-call qualification establishes bounded semantic agreement, not bug recall.

At revision 58523f3, `scripts/typed_investigation.py` has three structural limits:

1. Lines 137–146 admit only exact conditional test targets, in sorted order.
   An untested public entry cannot become a typed investigation target.
2. Lines 154–166 generate fixed length families and integers -1/0/1. Observed
   downstream comparisons do not feed back into input generation. The earlier
   integer explorer has refinement machinery; this typed pipeline does not reuse
   it. Completing call binding did not complete relation-directed search.
3. Lines 173–177 assess expectations only at the original exact argument binding.
   New inputs usually have no oracle. More successful interpretation alone cannot
   establish a new defect.

Admission also caps 32 distinct points before dispatch. Later parameter families
can be discarded before the shared round-robin scheduler can make them fair.
These observations explain capability gaps; they do not prove the cause of every
historical model miss or imply the Python prototype solves the earlier JS target.

## Smallest next implementation

Use a relation obligation as the scheduling unit, with explicit fields:
entry, source-backed call chain, producer expression, consumer predicate,
path conditions, quantity kind, evidence scope, searchability and oracle status.
Retain unresolved edges. Keep relation identity separate from generated points.

Start with only integer quantities and lengths of builtin immutable sequences,
affine local transformations and statically resolved local calls. Preserve existing
value, file, depth and dispatch limits. Do not drop annotation/context uncertainty
to make an entry searchable; a source relation may remain visible but blocked.
Nonlinear transforms, content-dependent lengths, dynamic calls and conflicting
units remain unsupported/unknown, with reasons.

Inventory public entries separately from test expectations. Missing tests must
not hide a source relation; missing input binding or contract may still block its
execution or assessment. A comparison in implementation is a path predicate,
not independent proof of intended behavior.

For supported relations, invert the consumer cut into the entry quantity. Intersect
with known route conditions and independently evidenced input restrictions. Mark
restriction provenance: proven, conditional or unknown. Unknown validity does not
become invalidity or a must-succeed contract. Propose predecessor, cut and successor
only when representable within unchanged bounds; report out-of-budget boundaries
without clamping them into misleading substitute points.

Admit relation families round-robin before admitting their points. Reserve space
for exact examples, then choose at most one point per independent relation before
expanding neighbors. Record deferred relations and why. Rank searchable, evidenced
relations by uncovered consumer branch and source-supported reachability, with a
stable tie-breaker; do not claim this heuristic predicts defect yield.

Use exact examples to check the interpreter. Assess new inputs only against a
separately supported property. Otherwise output a boundary observation or unresolved
lead. A reached branch, generated refusal or difference from another version is
not automatically a bug. Do not infer units from variable names or normative
contracts from the same implementation being investigated.

## Offline validation, frozen before running

Compare current fixed-family selection with relation selection under the same
64 static dispatch cap. Keep trusted synthetic execution and independent evaluator
counts separate; any later actual qualification retains caps 64 and128 respectively.
No execution is part of this design-only change.

Freeze semantic families and independent labels before implementing selection:
affine scaling, shifted cut, negative coefficient, nested helper, contradictory
route, two-parameter competition, untested entry, incompatible quantity kinds,
unsupported transform and missing normative oracle. Vary constants and rename/move
functions across families; never branch on fixture names or historical benchmark
identities. Include boundaries outside representation limits and several relations
competing for a small admission budget. Keep a transformation subset unused during
implementation; any tuning after its inspection invalidates its holdout status.

Report separate denominators for discovered relations, qualified relations,
reachable cuts selected within budget, unknown/unsupported relations and normative
properties available. Compare points and actual dispatch counts, not just percentages.
An independent finite-domain evaluator checks reachability and boundary inversion
on the fixed synthetic universe; it must not share the selection inverse routine.

Pass only if supported cuts and impossible routes agree with independent labels,
unknown cases never acquire invented contracts, late families receive their first
turn when budget permits, and held-out transformations retain relation identity
and status. Show at least one fixed-family miss corrected at equal dispatch budget;
publish every regression and unresolved case. This demonstrates the selection
mechanism on the defined subset, not real bug-finding superiority.

After that gate, freeze an independently selected real-project **static-only**
integration protocol before inspecting outcomes. Record repository revisions,
source hashes, deterministic selection and all rejected/blocked modules; do not
replace poor results with easier examples. Real code and tests remain unexecuted.
Static relation applicability still cannot establish real bug recall.

Only if these gates justify it, propose a separately budgeted model diagnostic to
the user. No model-backed call, retry or fresh-case evaluation follows automatically.
Keep all experimental changes outside main; coordinate extracted tools with draft
PR #19 before any later promotion. Stop expanding syntax support if the relation
selection gate fails: reassess the method rather than count more passing unit tests.
