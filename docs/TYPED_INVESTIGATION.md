# Experimental typed call evidence and investigation

Draft PR #16 only. Opt-in static tool; no formal skill/default/provider change.
Never imports or executes analyzed source or test files. No automatic real execution,
model calls, main promotion, bug-recall or token-saving claim.

```bash
python3 scripts/logic_lens.py typed-investigate \
  --workspace examples/typed-investigation/02-unittest-binding \
  --tests test_subject --out /tmp/new-typed-plan.json

# Plans all 12 reviewed synthetic packages, no execution:
python3 tests/qualify_typed_investigation.py /tmp/new-typed-preflight

# Executes only the fixed, hashed trusted synthetic portfolio; never real modules:
python3 tests/qualify_typed_investigation.py /tmp/new-typed-diagnostic \
  --execute-trusted-synthetic
```

Do not replace or edit the qualification source/manifest to execute arbitrary code.
The executor is trusted-fixture-only, not an OS sandbox. Static CLI accepts an explicit
source root and test module identities; output must be new and outside the source.
No automatic retries/overwrite. Qualification is separate from unit-test discovery;
CI never dispatches these new synthetic subjects. Historical regression tests retain
their own existing fixtures and are outside this diagnostic's counters.

## Typed evidence and parameter binding

`typed_calls.py` supports concrete builtin int (<=128 bits), bool, None, bytes (<=64
bytes), str (<=64 characters) and immutable tuples (<=8 items, nesting<=4). Bytes store
exact hexadecimal content and length; str stores exact text and character length.
Bool/int and bytes/str have different identities. Expected assertion equality follows
Python equality, so expected True and1 are compatible assertions where applicable.
No custom objects, mutable containers, arbitrary constructors or evaluation of source.

Call records retain original syntax/source span/context, resolution/provenance chain,
explicit typed arguments, expectation, normalized complete binding and parameter
origins (`positional`, `keyword`, `default`). A no-value assertion is distinguished
from an assertion expecting None. Bound-call identity ignores omitted-vs-explicit
spelling of equivalent defaults while retaining original provenance. Conflicting
outcomes/expected values are conservatively detected within and across test files.
No successful sample is generalized into a valid-input interval or same-length policy.

The AST binder supports positional-only, positional/keyword, keyword-only and required
parameters, immutable literal defaults, missing/extra/unknown/duplicate arguments and
explicit None. Unknown/mutable/computed defaults, even if explicitly overridden,
variadic signatures and dynamic unpacking remain unsupported. Default expressions
are never executed/recomputed; only the literal immutable subset is modeled. Binding
errors are evidence states, not automatically subject bugs. The facts backend still
rejects decorators/annotations rather than executing their definition-time context.

## Tests and context boundaries

Recognize top-level `test_*` functions and `test_*` methods in plain `Test*` classes
or classes whose single base statically resolves to canonical external
`unittest.TestCase`. Support local immutable assignments, direct/reversed equality
assertions, narrow unoverridden `self.assertEqual` and `self.assertRaises(ValueError)`,
and canonical external pytest.raises(ValueError). Standalone return observations are
conditional; unmodeled expression-call setup downgrades surrounding obligations.

Class initialization/state, lifecycle/helper/override methods, inheritance beyond the
single recognized TestCase base, decorators, fixtures, unsupported setup/control flow,
local rebinding and fake local unittest/pytest definitions prevent trusted extraction.
Calls can remain visible with `context_unknown`, `dependency_unknown`, `unsupported`
or `binding_error`; contradictory exact expectations become `conflict`. Complex
framework semantics, monkeypatching, module initialization/import availability and
canonical framework installation are not proven. `exact_conditional` always means
an exact test expectation subject to that environment, never an established public
business contract. Unknown contexts do not enter the executable-eligible queue.

## Static source provenance

`Project` indexes <=16 explicit-root Python files, <=128KiB/12000 AST nodes each.
No find_spec/importlib/inspect use for target resolution. Relative imports need
package __init__ identities; the source root contains packages/modules, not an
implicit package __init__ itself. Ambiguous module paths and symlink escapes refuse.
No automatic dependency installation or source search outside the explicit root.

Resolve direct/aliased imports, simple package reexports and direct local function
identities. Record import/definition locations and chain, including external boundary
identity. Conditional/rebound/star/cyclic/deep aliases and object attributes remain
unknown. Function-local values/parameters shadow imported names. Namespace and
package initialization effects are unmodeled; a source match does not prove a runtime
import succeeds or a callable's behavior. External calls have no guessed summaries.

## Queue/facts bridge

`typed_investigation.py` uses the **same** `investigation_queue` generator as the older
integer path explorer: alternating verify/explore preference, fallback on empty,
round-robin entry groups and explicit total/per-entry caps. Existing integer path
exploration still uses its original affine predicates/refinement algorithm.

Only eligible test-derived targets enter this typed scheduler; untested public
definitions remain outside it (the older inventory is separate). Exact nonconflicting
bound calls enter verification. Finite exploration changes one
parameter at a time; bytes/str vary lengths0..8 using a recorded fixed first-element
fill (zero fill for an empty example), ints use -1/0/1; all other bound arguments stay
fixed. Original exact content is never replaced in verification. Generated validity
is unknown. These families do not cover arbitrary same-length contents or combined
argument interactions, nor do they inherit a must-return oracle.

Caps:8 entry groups,32 admitted tasks/entry,32 interpreted points/entry and64 total
static dispatches. Pending and overflow attempts remain explicit. Early parameter
families can fill the cap before later useful families; overflow counts attempts,
not necessarily distinct missing paths. No severity/semantic independence ranking.

A separate bounded concrete AST backend models those typed builtin values, local
assignment, if/return/literal ValueError, supported equality/integer comparisons,
bytes/string concatenation/repetition/len and statically resolved local calls with
the same binder. <=2000 steps/input, call depth4, encoded value caps. Rebinding of
len/ValueError blocks builtin modeling. Imports/global state/loops/handlers, content
indexing, encodings and external dependencies are unsupported. It records complete
call bindings and concrete comparisons; it is **not** a generalized symbolic byte
solver, replacement of the affine engine, or recovered business-unit model.

Static observations preserve unknown/error reasons. Exact-example comparisons are
conditional leads; generated rejection alone is never a confirmed bug. Only the
trusted qualification driver actually executes any subject, compares actual Python
values/exceptions/call arguments and parameter binding, and stops on disagreement.

## Qualification budgets and artifacts

Frozen plan: `experiments/typed-calls-offline-plan.md`. Twelve synthetic packages,
static8 tasks/package and64 total; unsupported records are retained, not replaced.
All static plans are generated before actual execution. Source/portfolio hashes are
checked against the fixed trusted manifest before loading/execution. Only synthetic
subject modules are loaded; test class methods and real packages are never executed.
Module loading is reviewed immutable definitions/local imports; limits count **root
invocation attempts**, including invalid binding attempts, not nested helper calls.

Two independent hard counters, incremented and persisted before each attempted call:
<=64 dispatch calls; <=128 independent evaluator calls. The fixed independent set is
72 finite-domain calls plus10 binding calls. Inspect is used only on already-loaded
trusted synthetic functions for independent Python binding comparison. No evaluator
labels feed planning. Unexpected error/disagreement/hash drift stops without retry;
source plans, counters, partial observations/failure and undispatched counts persist.
Unsupported static bodies are not executed. There is no complete OS time/memory cap.

Artifacts: all12 plans, source/test text, portfolio/manifest, counters, attempt log,
actual dispatch results, independent results, binding results, summary, implementation
hashes and artifact SHA256 manifest. `complete` means the bounded diagnostic finished,
not all pending generated inputs were examined. Published results and remaining
limits: `experiments/typed-calls-offline.md`. No real-module readout in this round.
