# Logic-Lens — Logic Risk Taxonomy (L1–L9)

## L1 — Shadow Override
An identifier resolves to a different entity than assumed — local/import/class binding silently overrides a builtin or expected name.
**Detect:** (1) Walk scope chain for every call/access: local→enclosing→module→builtins. (2) Check `from X import Y` / `import X as Y` for builtin shadowing. (3) Check subclass attributes hiding parent methods. If a name cannot be uniquely resolved, that itself is a finding.
**Symptom:** `f(x)` calls project-local `f` not builtin `f`; tests pass because they mock the same wrong name.
**Common in:** Python (import shadowing), JavaScript (prototype chain), Ruby (method aliasing), Lua (global mutation).

---

## L2 — Type Contract Breach
A function/operator receives a value of a type it cannot correctly process; the mismatch may be implicit or conditional.
**Detect:** (1) State the expected type for each parameter (hints/docs/usage). (2) Trace actual argument type from origin through every transformation to call site. (3) Check for implicit coercions or interface widening along the path. (4) Note nullable paths: when can the value be `None`/`null`/`undefined`?
**Symptom:** Value enters as type A, is treated as type B by an operator/intermediary, and arrives at a call expecting type C.
**Common in:** Python (`None` where `str` expected), JavaScript (numeric/string coercion), Go (nil interface vs nil pointer), Java (unchecked cast).

---

## L3 — Boundary Blindspot
Logic is correct for typical inputs but does not handle boundary conditions: empty collections, zero/negative numbers, null/None, single-element sequences, first/last loop iterations.
**Detect:** (1) For each collection/numeric/optional: trace the empty/zero/null path explicitly — do not assume happy-path trace covers it. (2) Check loop indices, slice ranges, division operations for off-by-one and divide-by-zero. (3) Check first/last element of sequences separately.
**Symptom:** `items[0]` or `total / count` without a guard for `len(items) == 0` or `count == 0`.
**Common in:** All languages. Especially array indexing, pagination, aggregation, date arithmetic.

---

## L4 — State Mutation Hazard
Shared mutable state is read or written in a **single execution context** in an order producing incorrect results. Includes mutations affecting ongoing iterations, aliased references causing unexpected sharing, read-after-side-effect ordering. For multi-context hazards, see L7.
**Detect:** (1) Identify all mutable state touched: local refs passed by reference, object fields, global state, closure captures. (2) Trace every read and write in execution order. (3) Ask: does any read occur after a write that invalidated its assumption? Do any aliases point to the same mutable object? (4) **Aliased-return check:** does the function mutate its input argument AND also return that same reference? If so, callers who write `result = f(x)` discover `x` was also mutated — neither the pure-function contract (`sorted()` returns a new copy) nor the in-place contract (`list.sort()` returns `None`) is satisfied. This dual-contract footgun is L4.
**Symptom:** Collection modified during iteration; variable read after being reset by side effect; alias mutated through one name and observed through another; function sorts/modifies in-place AND returns the same object.
**Common in:** Python (mutable default args, list mutation during `for` loop, in-place-sort returning self), JavaScript (closure over `var` loop variable), Go (slice aliasing across `append`), Java (mutating `Collection` while iterating).

---

## L5 — Control Flow Escape
An early exit (`return`, `raise`/`throw`, `break`, `continue`, unhandled exception) skips a required non-lifecycle operation: state update, validation, commit marker, audit event, notification, or invariant restoration. For acquire/use/release imbalance, use L8.
**Detect:** (1) List all required post-conditions for the function/block: state updated, invariant restored, commit marker written, notification emitted. (2) Enumerate every exit point including implicit raises from callees. (3) Verify each exit path meets all non-lifecycle post-conditions. (4) If the skipped operation is a resource release/rollback/unsubscribe/close, classify as L8 instead.
**Symptom:** Status flag updated only on the happy path; audit event skipped on exception; validation bypassed by an early `return`; `continue` skips a required accumulator update.
**Common in:** All languages. Especially code refactored to add early returns, or exception handlers that don't mirror the acquisition path.

---

## L6 — Callee Contract Mismatch
Calling code assumes behavioral guarantees (return value semantics, exception behavior, idempotency, side-effect ordering) that the callee does not actually provide.
**Detect:** (1) For each local or external call, state what the caller assumes: return value, exceptions, idempotency, side effects, ordering. (2) Trace into the callee's implementation when local, or docs when external, and verify each assumption. (3) Flag: `None`/`null` returns the caller doesn't check; exceptions the caller doesn't catch; side effects the caller relies on but aren't guaranteed.
**Symptom:** `result = get_user(id)` then `result.name` without checking if `get_user` can return `None`; retry calling a non-idempotent function; assuming sort is stable when it isn't.
**Common in:** All languages. Especially at API boundaries, ORM interactions, third-party integrations.

---

## L7 — Concurrency / Async Hazard
Code under concurrency (threads, goroutines, async tasks, event loops) violates a single-thread assumption: atomicity of read-modify-write, happens-before across `await`/yield/channel boundaries, message ordering, cancellable operation progress. Distinct from L4 — L7 requires **more than one execution context**.
**Detect:** (1) Enumerate every concurrency boundary: `await`, `yield`, channel send/receive, lock acquire/release, callback, `Promise.then`, goroutine/task spawn. (2) For each boundary: which shared state is observable on both sides? Can another context mutate it between read and use? (3) For locks: trace acquire→use→release on every exit path. (4) For ordering: identify the synchronization enforcing it — "usually happens first" is not enforcement. (5) For cancellable tasks: trace partial-update state.
**Subtype — AV (Atomicity Violation):** A code region implicitly assumed to execute atomically is interleaved by another context (Detect step 2). Pattern: thread A performs read₁ … write₁ on variable V; thread B can execute between read₁ and write₁ and mutate V, making write₁ operate on a stale read. Check: (a) find every multi-step read-modify-write on shared state; (b) confirm another context can observe the variable between those steps; (c) verify a lock or atomic primitive protects the entire sequence, not just individual operations.
**Subtype — OV (Order Violation):** Code assumes operation A always completes before operation B, but no explicit synchronization enforces that order (Detect step 4). Pattern: initialization flag set by goroutine A is read by goroutine B before A has run. Check: (a) for every "A must happen before B" assumption, name the concrete synchronization primitive (mutex, channel, WaitGroup, Promise chain); (b) if none exists, the ordering is accidental — classify as L7/OV.
**Symptom:** Counter incremented as `x = x + 1` from multiple coroutines loses updates; value read before `await` used as if unchanged after; producer sends after consumer cancelled; init function assumed complete before first use without a barrier.
**Common in:** JavaScript (Promise races, missing `await`), Python (asyncio task interleaving), Go (concurrent map access, goroutine leaks), Java (visibility without `volatile`/synchronized), Rust (`unsafe` blocks, `Mutex` poisoning).

---

## L8 — Resource Lifecycle Hazard
A resource (file handle, DB connection, lock, transaction, subscription, buffer, process, listener) has a broken acquire/use/release lifecycle: missing release, double release, wrong-order release, or ownership transferred without updating the release plan. Distinct from L5 — L8 covers the full pairing discipline including double-release and ownership transfer.
**Detect:** (1) List every resource the code acquires. (2) Identify the matching release and when it must run (always / on success only / exactly once). (3) Trace every exit path; verify release runs the correct number of times. (4) Check ownership transfer: if resource is returned/stored/passed elsewhere, verify the new owner releases it.
**Symptom:** Connection released only on success path; transaction neither committed nor rolled back on exception; subscription registered in mount but unsubscribe references stale handle.
**Common in:** All languages. Python (`with` not used), JavaScript (listeners on long-lived DOM), Java (try-with-resources omitted in chain), Go (`defer` after possible early `return`), C/C++ (`free`/`delete` across function boundaries).

---

## L9 — Time / Locale Hazard
Code makes implicit assumptions about time zones, calendars, locale-dependent ordering, character encodings, or numeric locale conventions that hold on the developer's machine but break elsewhere.
**Detect:** (1) Every datetime: trace naive vs timezone-aware at every hop — naive↔aware comparison/arithmetic is L9. (2) Datetime arithmetic: can a DST transition fall inside the interval? Wall vs monotonic clock? (3) String comparison/ordering: locale-dependent? (4) Encoding conversion: explicit or guessed? Round-trip preserving? (5) Numeric parse/format: `.` vs `,` decimal separator?
**Symptom:** `new Date('2025-03-09T02:30:00')` in `America/Los_Angeles` lands in a non-existent hour; `datetime.now()` (naive) compared with timezone-aware DB value raises `TypeError`; `"i".upper() == "I"` fails in Turkish locale.
**Common in:** Python (`datetime` naive vs aware), JavaScript (`Date` always wall-time), Java (`java.util.Date` vs `java.time`), Go (`time.Time` Location), SQL (`TIMESTAMP` vs `TIMESTAMP WITH TIME ZONE`).

---

## Custom Risk Codes (Cx)
Projects define custom codes in `.logic-lens.yaml` using `C1`, `C2`, etc. Treat with the same Premises→Trace→Divergence→Remedy discipline as built-ins. Appear in findings as `[C1]`, `[C2]`, etc.

---

## Quick Disambiguation Table

| If the bug requires | Use |
|---------------------|-----|
| more than one execution context to manifest | **L7**, not L4 |
| lock-acquisition order differs between two functions, deadlock requires concurrent goroutines/threads | **L7**, not L4 |
| resource lifecycle imbalance (missing/double release, ownership transfer) | **L8**, not L5 |
| control-flow exit skipping required non-lifecycle code in a single sequential path | **L5** |
| sequential aliasing or mutation-during-iteration | **L4** |
| function mutates its argument AND returns the same reference (dual-contract footgun) | **L4** |
| timezone, DST, locale, or encoding to trigger | **L9**, not L2 or L3 |
| name resolution to a different definition than expected | **L1** |
| callee behavior under specific inputs not matching caller's assumption | **L6** |
| lock/mutex acquire-release imbalance under concurrency | **L7 + L8** jointly |
