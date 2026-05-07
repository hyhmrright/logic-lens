# Logic-Lens — Premises Construction Checklist (Single Source)

This is the **single source of truth** for the Premises step. Skill guides cite this file — directly in review/explain/diff, indirectly in locate/health/fix-all. Run every applicable bullet before producing a Trace.

When the user writes in Chinese (per `common.md` §1), produce the trace in Chinese; this checklist is language-neutral.

---

## 1. Name Resolution

For every non-trivial identifier in a function call, attribute access, or expression:

- **Full qualified name.** What does the identifier resolve to? Local → enclosing scope → module → builtins/global. State the exact definition site (`module.py:12`, `class Foo.method`).
- **Shadowing check.** Is there a local definition, import, class attribute, or enclosing-scope name that hides a builtin or expected name? (`from module import name` / `import module as alias` / subclass attribute hiding parent method)
- **Method dispatch.** For `receiver.method(...)`, what is the **runtime type** of the receiver? Which class's `method` dispatches?

---

## 2. Type Contracts

- **Expected type** at declaration/call site (annotations, docstrings, usage patterns).
- **Actual type** at each call: trace from origin — declaration, return of another function, parsed input, deserialized data — noting every transformation.
- **Implicit coercion/widening.** Does any operator or method call along the path implicitly convert types?
- **Nullable.** Can the value be `None`/`null`/`undefined`/`nil`? Under which branch?

---

## 3. State Preconditions

- What state must be initialized/non-null/non-empty before this code runs?
- Is that initialization guaranteed? By whom? Under what conditions might it be absent?
- For mutable state: what was the prior value, and does this code depend on a specific prior state?
- For external state (DB, file, network, lock, transaction): is it acquired and in the assumed state?
- For resource ownership: who must release/rollback/close/unsubscribe, and does ownership transfer to another caller or object?

---

## 4. Control Flow Assumptions

- **Conditional branches.** For each `if`/`switch`/pattern match: which branch executes for the relevant inputs? Is it provably reachable?
- **Loops.** How many iterations? What terminates it? Can it run zero times? Unboundedly?
- **Early exits.** Are there `return`/`raise`/`throw`/`break`/`continue`/unhandled-exception escapes the caller might not anticipate? Do they skip non-lifecycle post-conditions (L5) or resource lifecycle obligations (L8)?
- **Async ordering.** For async/concurrent code: which `await`/`yield`/channel-send/callback/task-spawn is the happens-before boundary the rest of the trace depends on?

---

## What is NOT a Premise (anti-patterns)

Rewrite before continuing if the Premises field contains any of:

- **Goal restatement.** "The function is supposed to remove all inactive users" — this is intent, not an assumption the code makes.
- **Test-suite expectations.** "The test asserts the result equals 42" — this is what the trace must explain, not a premise.
- **Author intent from naming.** "The author probably meant X because the function is named `remove_all`" — state what the *code* assumes.
- **Unverified library behavior.** "`requests.get` raises on 5xx" without checking — mark as "unverified" and downgrade confidence.
- **The fix as a premise.** "Premises: the list should not be mutated during iteration" — this is the remedy in disguise.
- **Vacuous restatement.** "Premises: the function takes a list and a boolean" with no claim about contents, nullability, or origin.

A premise is valid when it is **falsifiable by the trace**: the trace can either confirm or contradict it.
