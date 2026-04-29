# Logic-Lens — Semi-Formal Reasoning Guide

Semi-formal means: more structured than prose, less formal than a proof system. The goal is a **certificate** — a trace any reader can follow step by step to verify the conclusion.

---

## Premises Construction

Before tracing, enumerate premises explicitly using the four-section checklist in **`semiformal-checklist.md`**: Name Resolution, Type Contracts, State Preconditions, Control Flow Assumptions. That file is the single source — all skill guides reference it rather than re-listing.

A trace without explicit premises is not valid: skip the checklist and you forfeit the certificate property.

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

Rules:
- **Do not summarize.** "The function processes the input" is not a trace step.
- **Resolve every name.** Never write "calls `format()`" — write "calls the module-level `format()` defined at `dateformat.py:12`, which expects a datetime object."
- **State types explicitly.** "Passes `self.data.year`" → "passes `self.data.year`, type `int`."
- **Cross function boundaries.** If the bug is in a callee, trace into the callee.
- **Stop at the divergence.** The trace ends when you've identified the exact step where the premise breaks.

### Minimum thresholds

A trace below either threshold is **incomplete**: drop the finding or downgrade to **Suggestion** with `manual verification recommended`. Do not promote to Critical or Warning.

- **≥ 3 substantive steps.** Each step is a distinct evaluation, name resolution, type transition, mutation, branch decision, or callee return.
- **≥ 2 location anchors.** `[line N]`, `[file.py:N]`, a function-boundary marker (`→ enter callee X`), or for non-line code a section/key reference.

Optional config: `.logic-lens.yaml` can override via `trace.min_steps` and `trace.require_anchors` (see `common.md` §12).

---

## Divergence Identification

A divergence names: location (line/expression), violated premise, actual behavior, and observable consequence:

```
Divergence: Line 42 — `format(self.data.year, "04d")` calls the module-level
`format(obj, format_string)` (resolved in Premises), passing an `int` where
a datetime is expected. This raises `AttributeError: 'int' object has no
attribute 'strftime'` at runtime.
```

---

## Language-Specific Tracing Notes

### Python
- `from module import name` — does `module` redefine a builtin called `name`? (L1)
- Mutable default arguments: `def f(x=[])` shares the list across calls (L4)
- `None` returns from methods that sometimes don't return explicitly (L2, L6)
- `for i, x in enumerate(lst)` modifying `lst` inside loop (L4)
- `except Exception` swallowing the real error (L5)

### JavaScript / TypeScript
- `var` hoisting and closure capture of loop variable — L4 if handlers fire sequentially; L7 if concurrent listeners
- Implicit coercion: `"5" + 3 === "53"`, `"5" - 3 === 2` (L2)
- `undefined` vs `null` — methods exist on one but not the other (L2, L3)
- Promise rejection not caught in `async` function (L5)
- Prototype chain method lookup (L1)

### Java / Kotlin
- `equals()` vs `==` for object comparison (L2)
- Integer overflow without explicit widening cast (L2, L3)
- Checked exception caught at wrong level, returning null (L5, L6)
- Subclass method hiding a parent method (L1)

### Go
- Named return values and `defer` with closures — captured variables evaluated at defer time (L4)
- Nil interface vs nil pointer — an interface holding a nil pointer is not nil (L2)
- Goroutine closure capturing loop variable — L4 if sequential; L7 if concurrent
- Error ignored with `_` (L6)

### Rust
- `unwrap()` / `expect()` — trace whether the None/Err case can actually occur (L3)
- Interior mutability (`RefCell`, `Mutex`) — runtime borrow, potential panic (L4)
- Iterator adapters are lazy — missing `.collect()` means no work happens (L6)

### SQL (embedded)
- `NULL` propagation: any arithmetic with `NULL` produces `NULL` (L3)
- `NOT IN` with a subquery that can return `NULL` — entire expression evaluates to unknown (L3)
- Implicit type coercion in `WHERE` disabling index (L2)
- `TIMESTAMP` vs `TIMESTAMP WITH TIME ZONE` mismatch (L9)
- Transaction left open on early-return path (L8)

### Concurrency / async (cross-language, L7)
- Read of shared state across `await`/`yield`/channel boundary without re-checking
- Non-reentrant lock acquired twice by same context; lock released on path that did not acquire it
- Cancellable task mutating shared state mid-operation, leaving partial updates
- Producer writes to channel/queue after consumer was cancelled

### Resource lifecycle (cross-language, L8)
- Resource acquired but released only on success path (try without finally/with/defer)
- Resource released twice on overlapping cleanup paths
- Ownership returned to caller without updating caller's release plan
- Long-lived subscription whose unsubscribe captures a stale handle

### Time / locale (cross-language, L9)
- Naive datetime compared with timezone-aware datetime
- Wall-clock arithmetic across a DST boundary
- `toLowerCase`/`sort` whose result depends on active locale
- Date parsed without explicit zone — defaults differ across runtimes
- Numeric parse/format that assumes `.` decimal separator under a locale that uses `,`

---

## Interprocedural Reasoning

When `f` calls `g(x)`, do not assume `g` behaves as its name implies. Instead:

1. Find `g`'s actual definition (check imports, monkey-patching, dependency injection).
2. Read `g`'s implementation for the specific argument `x`.
3. Note any conditions under which `g` behaves differently from the caller's assumption.
4. Return to `f`'s trace with the actual behavior of `g` substituted.

The bug is most often in the interaction between two functions, not in the function being looked at in isolation.
