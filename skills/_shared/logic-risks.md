# Logic-Lens — Logic Risk Taxonomy (L1–L6)

Derived from the semi-formal reasoning methodology in *Agentic Code Reasoning*
(Ugare & Chandra, 2026, arXiv:2603.01896) and extended to cover common
interprocedural logic failure modes across all programming languages.

---

## L1 — Shadow Override

**What it is:** An identifier resolves to a different entity than the code author assumed. A local definition, import, class attribute, or scope-level binding silently overrides a builtin, inherited, or otherwise-expected name.

**Why it matters:** The code executes without error in the common case, but calls the wrong function or reads the wrong variable. Tests written with the same assumption will also pass, making the bug invisible until a specific execution context triggers it.

**How to detect via tracing:**
1. For every identifier used in a function call or attribute access, walk the scope chain outward: local → enclosing → module → builtins.
2. Check imports: does any `from X import Y` or `import X as Y` bind a name that shadows a builtin or another module's export?
3. Check class hierarchies: does a subclass define an attribute that hides a parent's method?

**Symptom pattern:** Code calls `f(x)` assuming `f` is builtin/standard-library `f`, but `f` is actually a project-local function with a different signature or semantics.

**Canonical example (from paper):** Django's `dateformat.py` defines a module-level `format()` function. Code inside that module calling `format(self.data.year, "04d")` invokes the module's own `format`, not Python's builtin, causing `AttributeError` because the module's `format` expects a datetime object, not an integer.

**Common in:** Python (import shadowing, `__builtins__` override), JavaScript (prototype chain, closure variable shadowing), Ruby (method aliasing), Lua (global environment mutation).

---

## L2 — Type Contract Breach

**What it is:** A function, operator, or expression receives a value of a type it cannot correctly process. The mismatch may be implicit (a value arrives through a chain of calls) or conditional (only certain code paths pass the wrong type).

**Why it matters:** Dynamic languages defer type checking to runtime. Even statically typed languages can have implicit coercions or interface widening that masks a type mismatch until a specific method is called on the value.

**How to detect via tracing:**
1. For the function under review, state the type expected by each parameter (from documentation, type hints, or usage patterns).
2. Trace the type of the actual argument from its origin: declaration site → transformations → call site.
3. Check every operator and method call along the path for implicit conversions that could produce an unexpected type.

**Symptom pattern:** A value enters as type A, is silently treated as type B by an operator or intermediary function, and arrives at a call expecting type C as type B.

**Common in:** Python (`None` passed where `str` expected), JavaScript (number/string implicit coercion), Go (interface satisfaction at runtime), Java (unchecked casts).

---

## L3 — Boundary Blindspot

**What it is:** The code's logic is correct for the typical case but does not handle one or more boundary conditions: empty collections, zero or negative numbers, maximum/minimum representable values, `null`/`nil`/`None`/`undefined`, single-element sequences, or the first/last iteration of a loop.

**Why it matters:** Boundary conditions are often excluded from the "happy path" tests that developers write first. The bug exists in the code from the start but is only triggered when real-world data hits the edge.

**How to detect via tracing:**
1. For each collection, numeric value, or optional reference in scope, ask: what happens when it is empty / zero / null / at its maximum?
2. Trace the execution path specifically for that boundary value — do not assume the happy-path trace covers it.
3. Check loop indices, slice ranges, and division operations for off-by-one and divide-by-zero conditions.

**Symptom pattern:** `items[0]` or `total / count` without a prior guard for `len(items) == 0` or `count == 0`.

**Common in:** All languages. Especially common with array indexing, pagination, aggregation, and date arithmetic.

---

## L4 — State Mutation Hazard

**What it is:** Shared mutable state (a variable, object field, collection, or external resource) is read or written in an order that produces incorrect results. This includes: mutations that affect an ongoing iteration, aliased references that cause unexpected sharing, and ordering dependencies between async operations.

**Why it matters:** State mutation bugs are often order-dependent and timing-sensitive, making them hard to reproduce. The code may pass all tests in isolation but fail when called in a specific sequence or concurrently.

**How to detect via tracing:**
1. Identify all mutable state touched by the code: local variables passed by reference, object fields, global state, closures capturing mutable variables.
2. Trace every read and write to that state in execution order.
3. Ask: does any read occur after a write that invalidated the assumption the read was based on? Does any alias cause two names to point to the same mutable object?
4. For async/concurrent code: identify operations that must happen before others; check if any await/yield point breaks the assumed ordering.

**Symptom pattern:** A collection is modified during iteration over it; a variable is read after being reset by a side-effecting call; two async operations race on a shared resource.

**Common in:** Python (mutable default arguments, list modification during iteration), JavaScript (closure over loop variable, async race), Go (map concurrent read/write), Java (shared mutable fields in multithreaded code).

---

## L5 — Control Flow Escape

**What it is:** An early exit — `return`, `raise`/`throw`, `break`, `continue`, `goto`, or an unhandled exception — causes the code to skip a required operation: a resource release, a state update, a commit, or a notification.

**Why it matters:** The "normal" path works correctly, but error handling, edge case handling, or refactored exit points leave the system in an inconsistent state.

**How to detect via tracing:**
1. List all required post-conditions for the function or block: resources that must be released, state that must be updated, cleanup that must happen.
2. Enumerate every possible exit point (including implicit raises from called functions).
3. For each exit point, verify that all required post-conditions are met before the exit.

**Symptom pattern:** A file is opened but only closed on the happy path; a database transaction is committed on success but the connection is leaked on exception; a lock is acquired but not released on early return.

**Common in:** All languages. Especially common in code that was refactored to add early returns, or in exception handlers that don't mirror the resource acquisition path.

---

## L6 — Callee Contract Mismatch

**What it is:** The calling code assumes behavioral guarantees from a function (return value semantics, exception behavior, idempotency, ordering of side effects) that the function does not actually provide.

**Why it matters:** This is the interprocedural form of the other risks. The caller's logic is locally coherent, but it depends on a callee behaving in a specific way that the callee does not guarantee — and the callee's actual behavior only diverges in specific conditions.

**How to detect via tracing:**
1. For each external function call, state what the caller assumes: what does it expect the return value to be? What exceptions does it assume the callee will or will not raise? Does it assume the callee is idempotent?
2. Trace into the callee's implementation (or consult its documentation/contract) and verify each assumption.
3. Pay special attention to: functions that return `None`/`null` under certain conditions the caller doesn't check; functions that raise exceptions the caller doesn't catch; functions whose side effects the caller relies on but that are not guaranteed.

**Symptom pattern:** `result = get_user(id)` followed by `result.name` without checking if `get_user` can return `None`; a retry loop calling a non-idempotent function; code that assumes a sorting function is stable when it isn't.

**Common in:** All languages. Especially common at API boundaries, ORM interactions, and third-party library integrations.

---

## Custom Risk Codes (Cx)

Projects can define custom logic risks in `.logic-lens.yaml` using codes `C1`, `C2`, etc. When a custom risk is active, treat it with the same Premises → Trace → Divergence → Remedy discipline as built-in codes. Custom codes appear in findings as `[C1]`, `[C2]`, etc.
