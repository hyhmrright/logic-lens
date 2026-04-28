# Logic-Lens — Semi-Formal Reasoning Guide

This guide operationalizes the semi-formal reasoning methodology from
*Agentic Code Reasoning* (Ugare & Chandra, 2026, arXiv:2603.01896)
for practical code review, explanation, and fault localization.

---

## Why Semi-Formal?

Unstructured reasoning ("this function looks fine") permits the analyst to skip
cases, make unsubstantiated assumptions, and reach confident wrong answers. The
paper's core finding: models using unstructured chain-of-thought achieve 76–78%
accuracy on code semantics tasks; semi-formal tracing achieves 87–93%, with the
largest gains on subtle interprocedural bugs that require following function calls
rather than guessing their behavior.

Semi-formal means: more structured than prose, less formal than a proof system.
The goal is a **certificate** — a trace that any reader can follow step by step
to verify the conclusion.

---

## Premises Construction

Before tracing execution, enumerate the premises explicitly using the four-section checklist in **`semiformal-checklist.md`**: Name Resolution, Type Contracts, State Preconditions, Control Flow Assumptions. The checklist is a single source — all skill guides reference it rather than re-listing.

A trace without explicit premises is not a valid trace: skip the checklist and you forfeit the certificate property that distinguishes semi-formal reasoning from intuition.

---

## Execution Trace Discipline

A valid trace is sequential and interprocedural:

```
1. [line N] Expression E is evaluated.
2. Name `f` resolves to [actual definition, with module/class path].
3. Arguments: arg1 has type T1 (traced from line M), arg2 has value V.
4. Inside `f` at line P: condition C evaluates to [True/False] because [reason].
5. [line Q] Side effect: variable X is mutated to Y.
6. `f` returns Z (type: T).
7. [line R] The returned Z is used as [role]; assumption was [expected value/type].
```

Rules for valid traces:
- **Do not summarize.** "The function processes the input" is not a trace step.
- **Resolve every name before using it.** Never write "calls `format()`" — write "calls the module-level `format()` defined at `dateformat.py:12`, which expects a datetime object."
- **State types explicitly.** "Passes `self.data.year`" should be "passes `self.data.year`, which has type `int`."
- **Cross function boundaries.** If the bug is in a callee, trace into the callee.
- **Stop at the divergence.** The trace ends when you've identified the exact step where the premise breaks. You don't need to trace the entire program — just far enough to confirm the finding.

### Minimum thresholds (mechanical check)

A trace below either threshold is **incomplete**: drop the finding, or downgrade to **Suggestion** with an explicit `manual verification recommended` note. Do not promote to Critical or Warning.

- **≥ 3 substantive steps.** Each step is a distinct evaluation, name resolution, type transition, mutation, branch decision, or callee return. Restating the same step in different words does not count.
- **Line / location anchor on at least 2 of the steps.** Either `[line N]`, `[file.py:N]`, a function-boundary marker (`→ enter callee X`, `→ return from X`), or for non-line code (config / docs) a section/key reference. A trace with no anchors is unverifiable by a reader and forfeits the certificate property.

Optional config: `.logic-lens.yaml` can override the defaults via `trace.min_steps` and `trace.require_anchors`. See `common.md` §12.

---

## Divergence Identification

A divergence is a single, specific point where a premise is falsified by the trace:

```
Divergence: Line 42 — `format(self.data.year, "04d")` calls the module-level
`format(obj, format_string)` (resolved in Premises), passing an `int` where
a datetime is expected. This raises `AttributeError: 'int' object has no
attribute 'strftime'` at runtime. The error is masked in tests that mock
`format` or use the standard library's `format`.
```

A divergence must specify:
1. The exact location (line number, expression, or function call)
2. The premise that was violated
3. What actually happens instead
4. The observable consequence (exception type, wrong return value, corrupted state)

---

## Language-Specific Tracing Notes

### Python
- Check `from module import name` for builtin shadowing (L1)
- Check mutable default arguments: `def f(x=[])` shares the list across calls (L4)
- Check `None` returns from methods that sometimes don't return explicitly (L2, L6)
- `for i, x in enumerate(lst)` modifying `lst` inside loop (L4)
- `except Exception` catching more than intended, swallowing the real error (L5)

### JavaScript / TypeScript
- `var` hoisting and closure capture of loop variable (`for (var i = 0; ...)`) — L4 if handlers fire sequentially after the loop; L7 if registered as concurrent listeners
- Implicit coercion: `"5" + 3 === "53"`, `"5" - 3 === 2` (L2)
- `undefined` vs `null` distinction — methods exist on one but not the other (L2, L3)
- Promise rejection not caught: `async` function with no `try/catch` (L5)
- Prototype chain method lookup for L1 (method defined on Object.prototype shadows expected behavior)

### Java / Kotlin
- `equals()` vs `==` for object comparison (L2)
- Integer overflow in arithmetic without explicit widening cast (L2, L3)
- Checked exception catching at wrong level, swallowing and returning null (L5, L6)
- Subclass method hiding a parent method (different from overriding) (L1)

### Go
- Named return values and `defer` with closures — captured variables evaluated at defer time, not declaration (L4)
- Nil interface vs nil pointer — an interface holding a nil pointer is not nil (L2)
- Goroutine closure capturing loop variable by reference — L4 if the goroutines are sequential; L7 if they read the captured variable concurrently
- Error ignored with `_` — callee contract not checked (L6)

### Rust
- `unwrap()` / `expect()` on `Option`/`Result` — explicit acknowledgment of potential panic, but trace whether the None/Err case can actually occur (L3)
- Interior mutability (`RefCell`, `Mutex`) — borrow at runtime, potential panic (L4)
- Iterator adapters are lazy — if `.collect()` is missing, no work happens (L6)

### SQL (embedded in application code)
- `NULL` propagation: any arithmetic with `NULL` produces `NULL` (L3)
- `NOT IN` with a subquery that can return `NULL` — the entire `NOT IN` evaluates to unknown, returning no rows (L3)
- Implicit type coercion in `WHERE` clause disabling index use and potentially matching unexpected rows (L2)
- `TIMESTAMP` vs `TIMESTAMP WITH TIME ZONE` mismatch on insert/compare (L9)
- Transaction left open on early-return path (L8)

### Concurrency / async (cross-language, L7)
- Read of shared state across an `await` / `yield` / channel boundary without re-checking (L7)
- Non-reentrant lock acquired twice by the same context; lock released on a path that did not acquire it (L7, often co-occurring with L8)
- Cancellable task that mutates shared state mid-operation, leaving partial updates (L7)
- "Send after cancel": producer writes to a channel/queue after the consumer was cancelled (L7)

### Resource lifecycle (cross-language, L8)
- Resource acquired but released only on the success path (try without finally / with / defer) (L8)
- Resource released twice on overlapping cleanup paths (L8)
- Ownership returned to caller without updating the caller's release plan (L8)
- Long-lived subscription/listener whose unsubscribe captures a stale handle (L8)

### Time / locale (cross-language, L9)
- Naive datetime compared with timezone-aware datetime (L9)
- Wall-clock arithmetic across a DST boundary (L9)
- `toLowerCase` / `sort` whose result depends on the active locale (L9)
- Date parsed without an explicit zone — defaults differ across runtimes (L9)
- Numeric parse / format that assumes `.` decimal separator under a locale that uses `,` (L9)

---

## Interprocedural Reasoning

The most valuable — and most often skipped — part of semi-formal reasoning is
**crossing function boundaries**. Standard review looks at a function in isolation.
Semi-formal review follows calls outward.

When a function `f` calls `g(x)`, do not assume `g` behaves as its name implies.
Instead:

1. Find `g`'s actual definition (check imports, monkey-patching, dependency injection).
2. Read `g`'s implementation for the specific argument `x`.
3. Note any conditions under which `g` behaves differently from the caller's assumption.
4. Return to `f`'s trace with the actual behavior of `g` substituted.

This is where the paper's 10-point accuracy gains come from. The bug is almost
never in the function the developer is looking at — it is in the interaction
between two functions where each looks correct in isolation.
