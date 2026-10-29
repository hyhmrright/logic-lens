# Experimental Python source facts and declaration differences

This offline prototype lives in draft PR #16 and changes no formal skill. It analyzes
source **independently of the proposed coefficient, unit and route declaration**,
then compares those fields. It never imports/executes the subject, invokes a model,
installs dependencies or calls external services. It interprets a small AST subset;
it is not a general Python analyzer or a sound whole-program verifier.

```bash
python3 scripts/logic_lens.py facts \
  --spec examples/python-facts/check.json \
  --workspace examples/constraint-plan/workspace \
  --out /tmp/new-python-facts.json
```

The example selects `routed_transfer` and `consume`. In the explicitly checked integer
window [-1,11], actual consumer reachability is0..5; -1 and11 are rejected before
reaching the consumer, while6..10 take another route. The byte quantity is3*n+2.
The source implementation rejects a packet length above17. These are implementation
facts, not public-validity/required-behavior oracles. Business input units remain
unknown. Output contains function spans and consumer call-site lines/expressions,
source/spec hashes, observations for every integer, affine variants and field-level
checks. Output refuses overwrite and placement in the source directory.

## Scope: exact finite inputs, symbolic quantities

The analysis window is mandatory, separate from the declaration's route, and includes
at most128 exact built-in integers in [-10000,10000]. Every integer in the window is
interpreted, not sampled. Input type, route decisions and observed quantities are
checked for those integers only. No claim is made for floats, bools, overloaded types
or inputs outside the window. Rejected inputs remain recorded; they never redefine
what the public contract should allow.

Quantities are derived by symbolic affine operations, not fitted from observations:
addition/subtraction, multiplication by a constant, local assignment/reassignment,
fixed byte/string repetition and built-in `len`. For `b'xy'*(3*n+2)`, the consumer's
length is6*n+4. Python's negative repetition produces zero: the interpreter retains
that actual zero branch rather than extending the positive affine expression.
Multiple reached branches can produce multiple affine variants; a declaration must
match all of them to match within scope.

Control flow supports integer comparisons/chains, explicit boolean `and/or/not`,
`if/else`, direct same-module calls, return and literal `raise ValueError(...)`.
Nested branches and early exits affect actual consumer reachability. The route check
reports both `omitted_reachable` and `falsely_reachable` integer intervals. A path
unsupported for any checked input makes the whole audit unsupported; partial evidence
is retained but no declaration checks are qualified. Unexecuted branches outside the
window remain unassessed, even when unsupported syntax occurs there.

The consumer is named in the spec, not discovered automatically. Its implementation
upper bound is recognized only from the narrow `if len(parameter)>constant: raise
ValueError(...)` guard shape. It is not a recovered normative contract. Several
consumer observations per input are possible and all must match coefficient/unit
checks; route membership means at least one observation on that integer input.

## Units and results

Known representation units are `byte` for literal bytes repetition and `character`
for literal strings repetition, propagated through same-module calls. Raw scalar
arguments have unknown units; this first prototype does not retain a dimension tag
through an intermediate scalar `len` result. There is no
business-unit inference: records, milliseconds, money and arbitrary unit labels
stay `unknown`. Units are not guessed from variable/function names. The comparator
recognizes the `element` declaration label but this first interpreter has no list
quantity extraction; it cannot validate arbitrary container semantics. Encoding
calls and nonlinear conversions are unsupported, not assumed constant factors.

Field statuses:

- `matched_in_scope`: the sourced implementation model matches the declaration on
  supported consumer-reaching paths in the checked integer window.
- `mismatch`: source-derived coefficient/offset, representation unit, bound or actual
  route differs. This diagnoses the **declaration**, not a subject bug.
- `unknown`: no consumer observation, unresolved business unit or missing supported
  quantity/bound model. No fake match is produced when a route is unreachable.

A coefficient can differ structurally even when all actual values at a singleton
window agree (e.g. n=0). An executable quantity witness is emitted only when the
observed quantity differs from the declared full affine expression. No fabricated
numeric witness is attached to a purely structural difference.

Overall status is `mismatch`, `checked_with_unknowns`, or `unsupported`. Successful
CLI exit0 means an audit artifact was produced, not that declarations are approved.
Malformed requests/output errors use exit2. Unknown business units are deliberately
preserved even when the other fields match. The tool does **not** automatically
approve an existing constraint plan or turn the result into an executable search.

## Deliberate exclusions and budgets

Only modules consisting of unique plain function definitions and docstrings are
accepted. Imports, module assignments/executable statements, decorators, annotations,
default/variadic/keyword/positional-only signatures and builtin shadowing are rejected.
The interpreter does not evaluate annotations/defaults/decorators. Local call-target
shadowing, dynamic/attribute calls, nonlinear multiplication, loops, exceptions other
than the allowed literal rejection, mutation and other unsupported statements on an
executed path stop qualification. There is no recursive dependency scan or global
configuration/descriptor/operator model.

Bounds: source128KiB, AST4000 nodes,128 input integers,2000 interpreter steps per
input, call depth4, at most8 consumer observations per input and128-bit affine
coefficients/offsets. An interpreter budget stop is unsupported, never a proof of unreachability.
Oversized source/window requests are refused with exit2 before interpretation.
This does not provide a hard OS wall-time/memory sandbox for parsing untrusted text;
it interprets no arbitrary subject code. Syntax/recursion/request failures are not
subject bug evidence.

## Independent offline validation

`tests/test_python_facts.py` independently runs **trusted synthetic programs only**
in subprocesses with5-second timeouts. A test-owned observer records real consumer
arguments, representation types and whether rejection occurs before/after the call.
It compares every input against the AST interpreter for four source variants (52
input executions). No declaration is used to manufacture that observation. The
production `facts` command has no execution/calibration option.

Separate checks cover wrong coefficients/offsets, byte-literal multiplicity, equivalent
expressions/local reassignment, bytes versus Unicode characters, route widening/
narrowing, nested/early exits, unreachable consumers, negative repetition, unsupported
encoding/nonlinearity/dynamic calls, shadowing, scope and resource limits, and CLI
integrity. The earlier wrong-coefficient negative control is now a detected declaration
mismatch, without embedding a real-case reproduction.

These tests increase confidence in this restricted interpreter. They do not establish
soundness for general Python, automatic contract interpretation, automatic relationship
selection, improved bug recall or token savings. Any future language extension,
search bridge or model diagnostic needs separate qualification and authorization.

## Explicit-point extension for offline scheduling

The new scheduler may supply `analysis_points` instead of `analysis_domain`:1..128
explicit unique bounded integers, sorted/deduplicated for interpretation. Output
includes `checked_points`; `checked_scope` is just their enclosing range. It does
**not** imply the gaps were checked. Route comparison is projected onto the listed
points only. The original contiguous-window request/output behavior is retained.
