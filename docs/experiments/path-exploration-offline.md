# Automatic evidence and cross-call path exploration — offline result

2026-10-29. Draft PR #16, no main merge, formal skill change, model evaluation,
real target import/execution, dependency installation or background job.

## Result

The synthetic path mechanism improves within the supported finite fixture: seed-only
and automatic-evidence+seeds cover12 of18 exhaustive branch signatures; cross-call
exploration covers16 of18. The2 remaining signatures are in explicitly unsupported
dynamic dispatch. Restricted to7 supported roots, coverage increases12/16 to16/16.
This is finite constructed-path coverage, not real bug recall or superiority over
Codex. No new public-validity interval or confirmed bug is inferred from a rejection.

Real read-only integration does **not** qualify the mechanism for actual modules.
The frozen selection rule picks installed CPython `annotationlib.py` and `base64.py`.
It inventories29 entry candidates, but extracts0 usable exact test obligations and
qualifies0 roots for complete supported path exploration. Keep those selections;
do not substitute easier modules or increase budgets to obtain a positive outcome.

## Mechanism and evidence

New `python3 scripts/logic_lens.py explore` statically joins public/export/test-call
entry inventory, conditional exact test evidence, local dependency slices, existing
facts interpretation, cross-call affine comparisons and two alternating queues.
A helper's condition is expressed in the entry parameter, inverted with its path
prefix, and used to enqueue a new witness. New input validity remains unknown.
Unlike the older `investigate` selector, an unobserved path need not first have a
predicted contract violation or recognized upper-bound consumer to receive attention.

The source/test pair supplies8 synthetic roots automatically, without a handwritten
entry/contract request. It contains8 extracted exact obligations across7 roots;
the contradictory expectations at one input remain conflict, never an oracle.
Allowed ValueError matches its exact test; correct alternate paths stay correct;
unknown-input ValueError remains a lead. Distinct consumer sites and byte quantity
models remain separate. A negative-count repetition guard prevents incorrect
extrapolation of a piecewise affine length model. Business units are not inferred.

Full raw artifact: `offline-path-exploration-2026-10-29/`. It includes all3 plans,
independent exhaustive actual-Python evaluator, selected-task replay, real AST
readouts, deterministic audit samples, source/test reference text plus PSF license,
selection log, environment and implementation/source/test hashes. `sha256.json`
covers the final attempt; `published-sha256.json` additionally covers the initial
partial attempt and failure record. The original frozen plan is unchanged.

## Synthetic comparison

Investigation window0..15, same maximum budgets:8 entry slices,32 admitted tasks and
32 checked points per slice. No oracle labels feed planning. Actual point use differs;
this comparison does not establish equal-cost efficiency or savings.

| Mode | Interpreted points | All branch signatures | Hidden helper | Nested converted helper | Multiple consumer sites |
|---|---:|---:|---:|---:|---:|
| Seeds only |24 |12/18 |1/2 |2/4 |2/3 |
| Automatic exact evidence + seeds |26 |12/18 |1/2 |2/4 |2/3 |
| Plus cross-call conditions / exploration queue |34 |16/18 |2/2 |4/4 |3/3 |

The2 missing full-mode signatures belong to `dynamic`, with unsupported observations
rather than success. The correct alternative, permitted refusal and finite infeasible
route retain their expected classification. Queue tests separately demonstrate
round-robin entry dispatch, verify/explore preference alternation and visible pending,
overflow and unadmitted entries. No calibrated priority/semantic novelty claim.

Independent real Python exhausts8*16=128 evaluator calls, checking outputs and branch
signatures. Full-mode replay performs31 actual trusted-synthetic calls;3 unsupported
tasks are recorded without execution. All31 agree, no retries or missing replay tasks.
Unit tests independently compare interpreter call quantities, representation types,
branch decisions, values and outcomes with actual call/line trace events. Evaluator
calls and unit-test repetitions are separate from the <=64 scheduler-dispatch cap;
159 is the published run's total actual synthetic calls, not64. The earlier plan's
wording "64 total local synthetic execution calls" was ambiguous: implementation
bounds dispatch at64 while exhaustive verification is additional. No claim that
all offline verification consumed <=64 calls. No paid calls/usage.

Rename, helper-split and equivalent-arithmetic checks preserve hidden-path discovery.
The deliberately conflicting test obligation is not treated as a bug. Static source
containing a module-level raise is never imported/executed and is reported as an
isolated slice with unmodeled initialization. These controls constrain interpretation;
they do not prove arbitrary module isolation is semantically valid.

## Real-module read-only integration

Selection was frozen before inspecting outcomes: first2 alphabetically eligible
locally installed top-level stdlib files, <=128KiB, literal exports and >=3 public
functions. Runtime was Python3.15.2; exact paths/hashes are in the raw summary.
Public definition candidates include functions absent from `__all__`; inventory is
broader than a confirmed public API. Tool/runtime use of the standard library is
separate from invoking these source snapshots as analysis targets.

| Module | Candidate entries | Exact obligations | Signature/closure unsupported | Partial unsupported | Real target executions |
|---|---:|---:|---:|---:|---:|
| annotationlib |6 |0 |3 |3 |0 |
| base64 |23 |0 |21 |2 |0 |

- `annotationlib`: the installed sibling test exceeds the12000-node evidence budget.
  Its evidence extraction is explicitly budget-blocked; source inventory continues.
  Signatures, dictionary comprehensions, try blocks, object/global state and callbacks
  exceed the restricted model. Nonfunction exports remain unresolved.
- `base64`: tests are present, but class methods, bytes/string inputs, helpers and
  setup are outside the tiny exact-integer/top-level-test extractor. Known test calls
  without extractable obligations are recorded unknown. Defaults/keyword signatures,
  multi-argument entry points and C-extension/object calls block deeper qualification.
  `decodebytes` and `encodebytes` reach unsupported expression statements immediately.
- Default integer window0..100 is merely an investigation window. It does not model
  either module's real object/bytes input domain, and is not a useful bug search here.
- Local functions are resolved lexically for inventory, not as a cross-module import
  graph. External calls such as `binascii.b2a_base64` remain unresolved; no import or
  C-extension behavior is guessed. Module initialization effects remain unmodeled.

Manual audit read the recorded first/last public function, first unsupported and
partially unsupported root and first unresolved call in each module. Source spans
agree: annotationlib's callback/annotations functions and base64's b64encode/main
are inventoried at actual locations; callback and C-extension call ownership stays
unresolved. The sample contains failed/unsupported entries, not just successes.
Original selected source hashes are unchanged. Reference snapshots are never used
as an execution workspace. No real tests were run.

First integration development attempt stopped on the large test AST rather than
producing partial inventory. Its artifact/failure is preserved. Handling was fixed
to record the evidence budget block while retaining source inventory. Selection,
limits and success criteria were not relaxed; no model/service retry occurred.

## Validation and next boundary

15 new tests /161 total pass locally. Repository validation, shell lint, authored
whitespace checks and archived manifests pass. Formal skills and historical frozen
plans/reports are unchanged. No model-evaluation token use; chat/implementation
usage is outside that accounting. No main promotion follows from this result.

Improvement demonstrated: automatic entry/evidence inventory for the supported test
shape, active helper-path discovery, finite prefix filtering, representation-fact
preservation and exploration budget allocation. Not demonstrated: practical contract
extraction or useful path exploration for either selected real module.

The next useful offline increment is typed concrete test-input/call binding, including
unittest class methods and safely bound literal/default arguments; then import/alias
provenance and explicit summaries for a narrowly supported dependency boundary.
Do not solve this by assuming all exceptions are bugs, inferring validity from
implementation guards, executing real dependencies or adding more reviewer prompts.
Business contract generalization, arbitrary strings/objects/state, unsupported hidden
paths, queue admission bias and complete coverage remain unsolved. Further code,
real execution, model calls or main merge require their own authorized scope.
