# Experimental source-relation boundary selection

Opt-in static prototype in draft #16. No formal skill/default changes, model calls,
target imports/execution or main promotion. Extracted offline tools in draft #19
do not automatically receive this change.

```bash
python3 scripts/logic_lens.py select-relations \
  --workspace /explicit/small/python/source/root \
  --tests test_subject --out /tmp/new-relation-plan.json

# Static qualification only; creates a new directory, never executes subjects:
python3 tests/qualify_relation_selection.py /tmp/new-static-qualification
```

Source indexing uses the existing typed layer: <=16 Python files,128KiB/12000 AST
nodes each, no imports, symlink escapes or ambiguous module identities. Output must
be new and outside the source root. Test module identities are optional. No tests
means visible public inventory with missing bindings, not guessed runtime types.

## Supported mechanism

Exact, nonconflicting conditional test evidence supplies typed entry bindings.
Untested public definitions, their comparison sites and unresolved/unbound calls
remain visible separately. They are not automatically searchable. Unknown test
contexts and conflicting expectations cannot supply eligible seeds.

Symbolic AST traversal follows local imports/calls with the existing signature binder,
immutable defaults, integer affine arithmetic, builtin sequence lengths, concatenation
and nonnegative literal repetition. Comparison sites retain producer text, consumer
predicate, source span, call chain, quantity representation and path conditions.
Integer quantities and byte/string/tuple lengths are distinct representation kinds;
combining incompatible kinds blocks. These are not recovered business units: an
integer might represent bytes, but this prototype cannot establish that equivalence.

Simple integer comparisons invert to an integer transition and adjacent points.
Routes intersect exactly supported inequalities/equalities, including excluded
integer points. Other parameters remain fixed to the first exact example: reachability
is conditional on that slice and the isolated-source model, not global feasibility.
Integer search is [-10000,10000]; byte/string lengths0..64, tuple lengths0..8.
Outside-domain/route boundaries are recorded without clamping. Unsupported routes,
multivariate cuts and nonlinear transforms do not acquire invented inverses.

One exact point per eligible entry is reserved first. Searchable relation families
are ordered by predicted missing branch coverage, round-robin across entries, then
given their first point before any neighbor expansion. Duplicate points share relation
references. Extra exact examples follow the relation turns; their deferred state is
visible. At most8 eligible entries,32 relations/entry,32 dispatched points/entry,
64 total interpreter dispatches,2000 symbolic steps/entry and call depth4.
All interpreter observations are in the counted dispatch list. Ranking evaluates
derived affine formulas only, not extra interpreter calls. No target runtime calls.

Generated sequence points retain only a first-element fill, with an explicit unknown
validity status. Exact examples check the bounded interpreter conditionally; new
points have no normative property. A boundary observation, refusal or mismatch does
not automatically become a bug report. No arbitrary source guard is a public contract.

## Important limitations

This is deliberately narrower than Python. Bool/None symbolic inputs, annotations,
decorators, loops, mutable state, dynamic calls, content-dependent transforms,
arbitrary exceptions and path-dependent helper return values are unsupported.
A stopped scan can retain earlier valid predicates but misses later relations;
issues remain explicit, and no completeness claim follows. Public untested wrappers
show their calls but do not recursively infer missing parameter types or contracts.

Only the first exact binding supplies the exploration slice. Alternative type and
content families, interacting parameters and alternative seed slices remain outside
search. Source initialization, dependency runtime availability and side effects are
not modeled. No real-code bug finding or superiority over plain Codex is established.

Qualification and initial accounting correction are disclosed in
[the result](experiments/relation-selection-offline.md). The inspected transformation
subset is now a regression set; the independent holdout gate remains open. Do not
promote based on these synthetic checks or automatically run a model diagnostic.

The [fresh frozen transformation and real static check](experiments/relation-generalization-offline.md)
passes the six supported synthetic transformation pairs, but real integration stops
on unresolved-entry handling in ast; bdb selection remains unattempted. This is an
explicit failed integration gate, not qualification for deployment or model evaluation.
