# Python facts/declaration audit — offline qualification

Date: 2026-10-29. User authorized a minimal Python source fact extractor and declaration
difference checker on synthetic programs, kept in draft PR #16. No formal skill
changes, model evaluations, new real cases, main merge, provider calls or automation.

## Implementation and interpretation

`python3 scripts/logic_lens.py facts` uses a restricted, bounded AST interpreter. It
independently derives symbolic affine quantities and checks every exact integer in
an explicitly supplied analysis window. Declaration coefficients, units and routes do
not influence that derivation/window. It never imports or executes the subject. This
is finite-scope interpretation with symbolic quantities, **not whole-program symbolic
proof**. See [protocol and exact limits](../PYTHON_FACTS.md).

Recorded facts include consumer-reaching intervals, rejection-before-consumer
intervals, reached affine/representation variants, source function spans and consumer
call sites. A narrow implementation capacity guard can be recognized. Neither the
implementation guard nor rejected input range is promoted to a normative contract or
the public valid domain. No property-search execution/automatic plan approval is added.

## Offline outcomes

| Check | Result and boundary |
|---|---|
| Earlier wrong-coefficient negative control | Correct source quote + falsely declared scale1 is now a coefficient mismatch; source independently yields3*n+2, with a real differing quantity witness in the checked window |
| Offset/local reassignment/equivalent expression | Wrong offset detected; local overwrite and equivalent constant/addition/multiplication forms retain the correct quantity |
| Literal length | `b'xy'*(3*n+2)` yields6*n+4, rather than copying the visible inner coefficients |
| Representation units | Byte/Unicode-character confusion detected; arbitrary business units remain unknown, not inferred from names |
| Route too narrow/too broad | Both omitted actually reachable inputs and falsely claimed reachable inputs are reported |
| Nested/early/alternate routes | Complete supported control flow affects consumer reachability; unreachable consumer leaves coefficient unknown |
| Premature rejection | Rejected inputs remain an implementation observation; the public valid contract is not silently narrowed |
| Negative repetition | Actual zero-length branch is retained instead of extending an invalid affine formula |
| Unsupported constructs | Encoding, nonlinear multiplication, dynamic calls, loops, imports/global state, annotations/decorators, shadowing and resource stops do not become matches |
| Witness integrity | A coefficient difference on singleton n=0 does not manufacture a numeric counterexample when observed quantities agree |
| Independent execution | Four trusted synthetic source variants ×13 inputs =52 executions; real consumer types/quantities and before/after rejection outcomes match the independent AST interpreter |
| CLI/evidence | No-overwrite/source-output placement rules, source/spec hashes and no subject module-side-effect execution checked |

**16 new tests pass;127 total repository tests pass locally.** Repository validation,
shell lint and authored diff whitespace checks pass. All six formal skill snapshots
and portable exports are unchanged from task-start HEAD. Compiled review SHA256 remains
`d429f5d89726d00cf166644a238849b0fce2e9f1a75197f0d106d5ac5fe6de37`.
No model-backed discovery/content/routing check ran. Evaluation model calls/tokens are
zero; chat/implementation usage is outside that accounting.

The example request and reproducible audit are in `examples/python-facts/`. The
companion evidence JSON hashes implementation/tests/source/request/result and records
an offline difference matrix. Prior prototype/frozen experiments are unchanged.

## Limits that remain

- Python only, small supported syntax, direct same-module calls, finite integer window.
  No claims for floats, booleans, overloaded objects, other inputs or unvisited paths
  outside that window. Supported scope is not automatic whole-function approval.
- Business semantics/units, public validity, policy applicability, required error
  behavior and contract conflict resolution remain manual. Implementation facts do
  not determine what behavior should be required. Raw scalar arguments lose quantity
  dimension provenance in this first implementation and retain unknown units.
- Consumer location is supplied, not automatically discovered or prioritized. The
  tool cannot demonstrate that it would select a previously neglected relationship.
- Symbolic quantity variants and finite route checks depend on the restricted
  interpreter's correctness;52 independent executions are useful cross-checks, not a
  general soundness proof or coverage of arbitrary Python semantics.
- No adapter bridge to `search`, automatic qualified relation inventory, improved
  discovery/precision/token-saving claim or new paid-stage authorization follows.
  Unknown/unsupported records cannot be relabeled verified to feed the old planner.

The previous declaration-planner negative control remains valuable: the old planner
still trusts bad annotations, while this new separate audit rejects that coefficient
on supported checked inputs. That is a narrower, measured offline improvement in
annotation checking, not evidence of better autonomous bug discovery.
