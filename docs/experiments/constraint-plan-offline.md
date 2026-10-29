# Constraint relation planner — minimal offline qualification

Date: 2026-10-29. User authorized a minimal offline prototype and synthetic tests,
kept in draft PR #16. No formal skill changes, model evaluations, new real-case
selection, main merge, provider calls, retries or background runs.

## Scope

`python3 scripts/logic_lens.py constraints` consumes manually declared, sourced
integer-affine producer/consumer relationships and emits property candidates, bounded
input domains, predicted control/partitions and source-based selection reasons.
This is a separate opt-in command, not a new default review path. See
[the schema, algorithm and limits](../CONSTRAINT_PLAN.md) and
`examples/constraint-plan/relations.json` / `expected-plan.json`.

The actual synthetic packet program converts record count to bytes (`3*n+2`), while
the consumer has a17-byte capacity. Public valid inputs are0..10. Generated domain
is `[0,4,5,6,7,10]`; the boundary is inverted to input units, rather than using17
as an input. Tests execute every generated point against the actual program, and
observed success/capacity failure matches the predicted partitions. This is an
intentionally inconsistent synthetic route with a valid passing control; no real
historical defect, patch or evaluator reproduction is used.

## Offline outcomes

| Required mechanism | Evidence | Outcome |
|---|---|---|
| Effective valid domain | Public intervals intersect route guards; gapped domains retain holes; points outside either set excluded | Pass |
| Unit conversion | Explicit record→byte affine conversion; actual packet encoding and consumer execution at generated inputs; signed exact arithmetic checked separately | Pass within supported model |
| Unreachable boundary | Correctly guarded alternate route executes successfully for all11 public inputs; candidate reflects only consumer-reaching inputs; impossible branch has empty intersection and never dispatches | Pass |
| Contract conflict | Explicit sourced allow/deny statements with overlapping applicable scopes block selection; denied-valid inconsistency and missing allowed scope also block; conflict off the route does not block this route | Pass for declared scopes |
| Search selection | Two candidates on overlapping producer/consumer spans do not consume both slots when a distinct qualified edge exists; unknown/unsupported/budget-blocked candidates cannot fill slots | Pass for declared span heuristic |

Additional checks cover no predicted passing control, unit mismatch, unsupported
nonlinear models, source quote/path failures, integer/interval/slot limits, domain
budget refusal without silent truncation, CLI source-write/overwrite refusal and
stable output. Independent exhaustive enumeration of108 signed affine models with
a gapped domain checks that generated points represent every reachable truth partition;
this validates this algebra, not source extraction or semantic oracle correctness.

**Deliberate negative control:** Keep an exact quote from `3*n+2`, but incorrectly
annotate the coefficient as1. The planner predicts the entire public domain safe and
does not select it, while actual input6 still fails. The test passes by exposing this
limitation: quote matching does not prove annotations true. Do not call this a
successful automatic source-understanding test. The planner cannot currently detect
this semantic mismatch on its own.

Sixteen new behavioral tests pass; **111 total repository tests pass locally**.
Repository validation and shell lint pass; authored diff whitespace checks pass.
All six portable skill snapshots and exports are unchanged from task-start HEAD.
Compiled review SHA256 remains
`d429f5d89726d00cf166644a238849b0fce2e9f1a75197f0d106d5ac5fe6de37`.
The companion `constraint-plan-offline-evidence.json` hashes implementation, tests,
synthetic subject, input and expected output. No model-backed content/routing/discovery
check ran, and no evaluation tokens were consumed. Chat/implementation usage is not
reported as zero.

## What remains unresolved

1. **Extraction and applicability remain manual.** The program neither finds missing
   relationships nor proves coefficients, units, guards or policy contexts from source.
   An incomplete or inaccurate inventory can still miss the important path, as the
   deliberate negative control demonstrates. This was the main concern in the failed
   model diagnostic and is not solved by this prototype.
2. **One narrow relation family.** Only finite one-variable integer-affine conversions
   feeding a `<=` consumer precondition are modeled. Nonlinear/text transforms,
   protocol semantics, aliasing, state, scheduling and ownership are unsupported.
3. **No executable-property bridge.** Output describes the observation and predicate;
   it is not yet a runnable adapter/spec for `search`. No subject execution or bug
   confirmation occurs in the planner. Predicted controls require actual verification.
4. **Selection is mechanical, not calibrated.** Span overlap is not semantic novelty
   or defect independence. Smaller domains are only a deterministic cost tie-breaker.
   All-safe/all-unsafe cases are ineligible for this particular crossing selector,
   not proof of correctness or permission to ignore valuable manual leads.
5. **No effectiveness or token-saving claim.** Synthetic mechanism tests, generated
   maps and explicit status fields do not demonstrate autonomous investigation-path
   improvement, real bug recall or superiority over direct Codex. No paid continuation
   is authorized by this offline pass.

The next offline question is whether a small source-reading layer can reproduce
faithful declarations and reject inaccurate ones without leaking known answers or
expanding into a whole-program analyzer. Preserve these mechanism checks and the
negative control before considering any model-backed experiment. Propose scope and
budget separately; do not resume earlier plans or merge this prototype into main.
