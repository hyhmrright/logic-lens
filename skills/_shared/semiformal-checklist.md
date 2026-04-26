# Logic-Lens — Premises Construction Checklist (Single Source)

This is the **single source of truth** for the Premises step of semi-formal tracing. Skill guides (review / explain / diff / locate / health / fix-all) cite this file — directly in review / explain / diff, indirectly in locate / health / fix-all via their "build premises at each step" instructions. Run through every applicable bullet before producing a Trace.

When the user writes in Chinese (per `common.md` §1), think internally in Chinese and produce the trace in Chinese; the structure of the checklist itself is language-neutral.

---

## 1. Name Resolution

For every non-trivial identifier used in a function call, attribute access, or expression:

- **Full qualified name.** What does the identifier resolve to? Local variable → enclosing scope → module → builtins / global. State the exact definition site (`module.py:12`, `class Foo.method`, etc.).
- **Shadowing check.** Is there a local definition, import, class attribute, or enclosing-scope name that hides a builtin or another expected name?
  - `from module import name` — does `module` redefine a builtin called `name`?
  - `import module as alias` — is `alias` reused elsewhere with a different meaning?
  - Class subclass attribute hiding a parent method?
- **Method dispatch.** For `receiver.method(...)`, what is the **runtime type** of the receiver? Which class's `method` actually dispatches?

If you cannot uniquely resolve a name, that itself is a finding worth recording (often L1 or L6).

---

## 2. Type Contracts

For every parameter and return value of the code under analysis:

- **Expected type** at the declaration / call site (from annotations, docstrings, or usage patterns).
- **Actual type** at each call: trace the value from its **origin** — variable declaration, return of another function, parsed user input, deserialized data — and note every transformation along the way (string parsing, numeric conversion, attribute access, `.unwrap()`, etc.).
- **Implicit coercion / widening.** Does any operator (`+`, `==`, `<<`, comparison) or method call along the path implicitly convert types?
- **Nullable.** Can the value be `None` / `null` / `undefined` / `nil`? Under which branch?

---

## 3. State Preconditions

- What state must be **initialized / non-null / non-empty** before this code runs?
- Is that initialization **guaranteed**? By whom? Under what conditions might it be absent (lazy init, conditional setup, error path)?
- For mutable state: what was its prior value, and does this code depend on a specific prior state?
- For external state (database, file, network, lock, transaction): is it acquired and in the assumed state?

---

## 4. Control Flow Assumptions

- **Conditional branches.** For each `if` / `switch` / pattern match: which branch executes for the relevant inputs? Is it provably reachable?
- **Loops.** How many times will each loop run? What terminates it? Can it run zero times? Can it run unboundedly?
- **Early exits.** Are there `return` / `raise` / `throw` / `break` / `continue` / unhandled-exception escapes that the caller might not anticipate? See L5.
- **Async ordering.** For async / concurrent code: which `await` / `yield` / channel-send is the visibility / happens-before boundary the rest of the trace depends on?

---

## Why each item matters (anti-cheat)

The temptation is to **skip** premises and jump straight to "this looks fine / this looks broken." That move is the single biggest source of false negatives and false positives in code review.

The checklist's purpose is to force you to write down assumptions you would otherwise leave implicit — so that when the Trace contradicts them, the Divergence is unambiguous and the Remedy is targeted.

A finding without explicit Premises is not actionable: the reader cannot tell whether the bug is in the premise, the trace, or your interpretation of either. Always state Premises first, even when they seem obvious.
