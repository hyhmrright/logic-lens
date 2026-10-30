# Experimental offline entry and path exploration

Opt-in prototype on draft PR #16. It reads Python AST/text; it never imports or runs
subject files. No formal skill, release default, model provider, real benchmark or main
branch changes. It does not infer business contracts or establish real bug recall.

```bash
python3 scripts/logic_lens.py explore \
  --source examples/path-exploration/subject.py \
  --tests examples/path-exploration/test_subject.py \
  --window 0 15 --out /tmp/new-path-plan.json

# Explicitly trusted synthetic qualification + static stdlib integration only:
python3 tests/qualify_path_exploration.py /tmp/new-path-qualification
```

The first command is always static, including for real source. The second executes
only the checked-in synthetic `subject.py` using Python and records a separate static
readout for two rule-selected local stdlib modules. Never substitute arbitrary code
in the qualification fixture. It has no OS sandbox. Existing `investigate` and its
trusted-synthetic execution flag remain unchanged; `explore` has no execution flag.
The new static scheduler does not silently enable the older must-return oracle.

## Entry and exact-example evidence

Inventory all top-level public functions, literal list/tuple `__all__` exports that
resolve to functions, and private functions referenced by supported tests. Exports of
classes/imports and dynamic export lists remain unresolved. Record each call site,
local-name resolution and unresolved external/attribute/callback call expressions.
Public visibility is an entry candidate, not proof of valid input or a public API.

Optional test text supports direct `from <module> import f` aliases or `<module>.f`
references, one literal integer argument, simple top-level `test_*` functions without
fixtures/decorators/setup, equality assertions with an integer expected result,
standalone calls and a narrow `with ...raises(ValueError)` shape. Rebinding/shadowing
is conservatively excluded. More complex/class-based tests, reversed assertions,
bytes/string data, parameterization, package-relative ownership and environment/setup
are unsupported. Known calls without extractable obligations get unknown records.
This is deliberately narrower than a full pytest/unittest interpreter.

Evidence records exact input, expected return/outcome, test line/context and a
conditional applicability label. A successful example never creates a valid-input
interval. Different expected values or returned/rejected outcomes for one input are
conflicts, excluded from verification scheduling; a plain successful return is
compatible with an exact return assertion. Test monkeypatching/import side effects and
exception-context ownership are not proven. An `example_disagreement` is a review
lead, not a confirmed bug. All unseen input validity remains unknown.

## Cross-call conditions and representation facts

Validate each local function dependency closure with the existing restricted facts
interpreter. Preserve original line locations. Do not execute module initialization,
imports, decorators or dependencies; annotations/defaults/unsupported signatures
block closure qualification. Missing globals/imported calls and dynamic dispatch are
unsupported. Initialization statements are inventoried as unmodeled. An isolated
slice result assumes its function definitions and builtins are the ones modeled;
it is not a claim about module import/runtime behavior.

For each checked integer, preserve calls, caller/call-site positions, actual affine
argument expressions, representation units, entry outcome and evaluated comparison
trace. Reuse `python_facts`, rather than duplicating its expression semantics.
Single affine comparisons record both operands in entry-input coordinates across
local calls. Short-circuit booleans produce only evaluated predicates. Chained/type
comparisons and unsupported tracing shapes get gaps. Sequence repetition's implicit
negative-count clamp also gets a path predicate, preventing its piecewise quantity
model from being extrapolated outside the recorded path.

For each recorded decision, keep its preceding predicate prefix, invert that decision,
and enumerate the finite investigation window for a feasible witness. This is exact
bounded integer filtering, not an SMT solver or whole-program symbolic execution.
If no checked point already discharges the alternative, queue the nearest witness.
Iterate as new points reveal helper-only conditions. Every task reruns interpretation
and retains the resulting path; alternate paths cannot be assumed reached merely
because a task was queued. Empty alternatives mean infeasible only under that
supported prefix in this finite window. Gaps, unknown calls and unobserved paths
never imply global unreachability. All-integer universes are a current restriction;
no string/object input synthesis, nonlinear constraints, state or concurrency.

## Scheduling and bounds

Two queues: exact nonconflicting test examples (`verify`) and window seeds/new branch
witnesses (`explore`). Alternate queue preference each round; round-robin roots;
fall back to the nonempty queue. Deduplicate by entry/input across queues. Prefer
roots referenced by tests, then exports, then name. This is cheap structural coverage,
not severity, expected bug yield or semantic independence ranking.

Defaults/caps:8 analyzed entry slices,32 admitted point tasks/entry,32 interpreted
points/entry, integer window of at most128 values inside [-10000,10000]. Static roots
rejected before admission retain unsupported records. All remaining entry records,
pending tasks, overflow attempts and partial observations are preserved. Overflow
counts attempts, not necessarily unique missing paths. Seeds are window endpoints
and contained -1/0/1 values. Early queue admission can consume the task cap before a
later valuable path; this is exposed, not solved by the current heuristic.

Source <=128KiB and12000 AST nodes for inventory; closure validation inherits4000
AST nodes,2000 steps/input, depth4 and128-bit coefficient limits. Test text exceeding
its128KiB/12000-node budget is explicitly blocked while source inventory continues.
No whole-process memory/time quota. Default window0..100 is an investigation choice,
not a discovered contract or representative real input type.

## Output and offline verification

One new JSON file, never overwrite: source/test text hashes, entry/call inventory,
exact evidence/conflicts, original locations, unmodeled initialization, unsupported
records, observations/quantity facts, conditions, dispatch order, pending/overflow,
finite infeasible alternatives and conditional example checks. `bounded_complete`
means queues drained for this mode/window, not complete path coverage; even seed-only
mode can have this status while missing interior paths. `partial_trace` and
`partial_unsupported` expose gaps. CLI exit0 means output was produced, not a pass.

The synthetic qualification driver compares seed-only, evidence+seeds and full path
exploration under equal maximum budgets (actual point consumption differs). The
independent evaluator exhausts8 roots*16 integers using real Python and trace events;
its labels are never passed to exploration. Selected full-mode tasks also get actual
replay, capped at64 attempted dispatches; the evaluator's128 calls and unit-test calls
are separate verification work. No retry; replay disagreement stops before real
integration. The independent test checks branch decisions, affine argument quantities,
representation units, values and outcomes against actual Python calls. It covers
rename/split/equivalent-arithmetic transformations, allowed refusal, conflicts,
unsupported dispatch, finite infeasibility and budget/queue behavior.

Real selection is frozen in the plan: first2 eligible locally installed stdlib files,
alphabetically, with literal exports and >=3 public top-level functions, <=128KiB.
Never replace unsupported picks. Source and sibling test text are archived with PSF
license, hashes and a deterministic review sample including unsupported/unresolved
records. Those copies are reference text, not an execution workspace. Host Python
version changes selection; recorded hashes define this readout. Tool/runtime stdlib
use is separate from invoking selected files as analysis subjects.
