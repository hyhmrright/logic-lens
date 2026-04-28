# Logic-Lens — Logic Risk Taxonomy (L1–L9)

Derived from the semi-formal reasoning methodology in *Agentic Code Reasoning*
(Ugare & Chandra, 2026, arXiv:2603.01896) and extended to cover common
interprocedural logic failure modes across all programming languages.

**Five-section skeleton:** every risk code is documented as *What it is / Why it matters / How to detect via tracing / Symptom pattern / Common in*. L1 additionally cites the canonical example from the source paper; subsequent codes do not.

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

**What it is:** Shared mutable state (a variable, object field, collection, or external resource) is read or written in an order that produces incorrect results within a **single execution context**. This includes: mutations that affect an ongoing iteration, aliased references that cause unexpected sharing, and read-after-side-effect ordering hazards. For hazards that require more than one execution context (threads, goroutines, async tasks) to manifest, see L7.

**Why it matters:** Sequential mutation bugs often pass tests that exercise each operation in isolation but fail when the operations run in the order the calling code uses. Aliasing in particular makes the bug invisible at the local read site — the write happens through a different name.

**How to detect via tracing:**
1. Identify all mutable state touched by the code: local variables passed by reference, object fields, global state, closures capturing mutable variables.
2. Trace every read and write to that state in execution order.
3. Ask: does any read occur after a write that invalidated the assumption the read was based on? Does any alias cause two names to point to the same mutable object?

**Symptom pattern:** A collection is modified during iteration over it; a variable is read after being reset by a side-effecting call; an alias unexpectedly shared between two names is mutated through one and observed through the other.

**Common in:** Python (mutable default arguments, list modification during iteration), JavaScript (closure over `var` loop variable observed sequentially), Go (slice aliasing across `append`), Java (mutating a `Collection` while iterating over it).

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

## L7 — Concurrency / Async Hazard

**What it is:** Code that runs under concurrency (threads, goroutines, async tasks, event loops, message handlers) violates an assumption that only holds in single-threaded execution: atomicity of a multi-step read-modify-write, happens-before across an `await` / yield / channel boundary, ordering of message delivery, or progress of a non-cancellable operation. Distinct from L4 — L4 covers sequential aliasing/mutation hazards; L7 covers hazards that only manifest when more than one execution context interleaves.

**Why it matters:** Concurrency bugs are non-deterministic and rarely surface in single-threaded unit tests. They can pass CI for months and reproduce only under production load, specific scheduling, or one customer's usage pattern. Async code in particular hides the hazard because the syntax looks sequential.

**How to detect via tracing:**
1. Enumerate every concurrency boundary in the code under review: `await`, `yield`, channel send/receive, lock acquire/release, callback registration, `Promise.then`, `spawn`/`go`/`Task.create`, message handler entry.
2. For each boundary, list which shared state is observable on both sides. Ask: between read at point A and use at point B, can another execution context have mutated the state?
3. For locks: trace acquire → use → release on every path. A second `acquire` of a non-reentrant lock by the same context, or a release on a path where it was never acquired, are both L7.
4. For ordering: when correctness depends on operation X happening before operation Y, identify the synchronization that enforces it. "It usually happens first" is not enforcement.
5. For cancellation: when a task can be cancelled mid-execution, trace what state is left partially updated.

**Symptom pattern:** A counter incremented as `x = x + 1` from multiple coroutines loses updates; a value read before `await` is used as if unchanged after the `await`; a producer sends on a channel after the consumer was cancelled and the send blocks forever.

**Common in:** JavaScript (Promise race conditions, missing `await`), Python (asyncio task interleaving across `await`, GIL-released sections in C extensions), Go (concurrent map access, goroutine leaks), Java (visibility without `volatile`/synchronized, double-checked locking), Rust (correctness usually enforced by `Send`/`Sync`, but `unsafe` blocks and `Mutex` poisoning can still bite).

---

## L8 — Resource Lifecycle Hazard

**What it is:** A resource (file handle, database connection, lock, transaction, subscription, allocated buffer, spawned process, event listener) is acquired but the acquire / use / release lifecycle is broken: a release path is missing, a release happens twice, releases occur in the wrong order, or ownership is transferred without updating the caller's release plan. Distinct from L5 — L5 covers control-flow escapes that skip required code; L8 covers the broader pairing discipline including double-release, out-of-order release, ownership transfer, and resource exhaustion.

**Why it matters:** Resource leaks accumulate silently — a single missed `close()` per request looks fine until the connection pool is exhausted in production. Double-releases can silently corrupt state shared with other consumers (releasing a connection back to a pool while another caller still holds it).

**How to detect via tracing:**
1. List every resource the code acquires (file open, lock acquire, connection borrow, transaction begin, listener subscribe, allocation).
2. For each resource, identify the matching release operation and the contract for when it must run (always, on success only, exactly once).
3. Trace every exit path of the function/scope and verify the release runs the correct number of times. Pay attention to `try/finally`, `with`, `defer`, `using`, RAII destructors, and what happens when an exception fires inside the cleanup itself.
4. Check ownership transfer: if the resource is returned, stored, or passed to another function, the release responsibility moves with it — verify the new owner releases it.

**Symptom pattern:** A connection acquired with `pool.borrow()` is released only on the success path; a transaction is committed on success but neither committed nor rolled back on exception; a subscription is registered in `componentDidMount` but the unsubscribe in `componentWillUnmount` references a stale handle.

**Common in:** All languages. Especially common in Python (`with` not used), JavaScript (event listeners on long-lived DOM nodes), Java (try-with-resources omitted for one resource in a chain), Go (`defer` placed after a possible early `return`), C/C++ (manual `free`/`delete` paired across function boundaries).

---

## L9 — Time / Locale Hazard

**What it is:** Code makes implicit assumptions about time, time zones, calendars, locale-dependent ordering, character encodings, or numeric locale conventions that hold in the developer's environment but break elsewhere. Includes naive vs timezone-aware datetimes, DST transitions, monotonic vs wall clocks, locale-specific case folding and sorting, encoding round-trips, and decimal separator differences.

**Why it matters:** These bugs ship cleanly through unit tests (the developer's machine has one timezone, one locale) and surface in production after deploys to new regions, on DST transition days, or when a user's input contains an unexpected locale. They are a frequent source of "works for me" incidents.

**How to detect via tracing:**
1. For every datetime value, trace whether it is naive or timezone-aware at every hop. Naive ↔ aware comparison or arithmetic is L9.
2. For every datetime arithmetic operation, ask: can a DST transition fall inside the interval? Does the operation use wall time (subject to DST jumps) or monotonic time?
3. For every string comparison or ordering, ask: does it depend on locale? `"İ".lower()` differs in Turkish locale; `sort()` order differs by locale collation.
4. For every encoding conversion (`encode`, `decode`, `Buffer.toString`, `JSON.stringify` with unicode), trace whether the encoding is explicit or guessed; whether the round-trip preserves the value.
5. For every numeric parse from string, ask: does the source use `.` or `,` as decimal separator? Was the formatter locale-aware?

**Symptom pattern:** `new Date('2025-03-09T02:30:00')` in `America/Los_Angeles` lands in a non-existent hour and the API returns "Invalid Date"; `datetime.now()` (naive) compared with a timezone-aware database value raises `TypeError`; `"i".upper() == "I"` fails in Turkish locale.

**Common in:** Python (`datetime` naive vs aware), JavaScript (`Date` always wall-time, no built-in zone), Java (`java.util.Date` legacy vs `java.time`), Go (`time.Time` carries Location, but parsing without zone defaults to UTC), SQL (`TIMESTAMP` vs `TIMESTAMP WITH TIME ZONE`).

---

## Custom Risk Codes (Cx)

Projects can define custom logic risks in `.logic-lens.yaml` using codes `C1`, `C2`, etc. When a custom risk is active, treat it with the same Premises → Trace → Divergence → Remedy discipline as built-in codes. Custom codes appear in findings as `[C1]`, `[C2]`, etc.

---

## Quick Disambiguation Table

When a finding could plausibly map to two codes, use the more specific one:

| If the bug requires | Use |
|---------------------|-----|
| more than one execution context (thread / coroutine / goroutine / async task) to manifest | **L7**, not L4 |
| a resource lifecycle imbalance (missing/double release, ownership transfer) | **L8**, not L5 |
| a control-flow exit that skips required code in a single sequential path | **L5** |
| a sequential aliasing or mutation-during-iteration hazard | **L4** |
| timezone, DST, locale, or encoding to trigger | **L9**, not L2 or L3 |
| name resolution to a different definition than expected | **L1** |
| a callee's behavior under specific inputs not matching the caller's assumption | **L6** |
| a lock / mutex acquire-release imbalance under concurrency | **L7 + L8** jointly (lock is both a concurrency primitive and a resource) |
