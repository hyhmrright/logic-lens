# Logic Review — Step-by-Step Guide

## Step 1: Establish Claimed Behavior

Read any comments, docstrings, test names, or commit message. Write one sentence:
"This code is supposed to [verb] [what], given [inputs], producing [output/side effect]."

This sentence is the reference point: anything the trace contradicts is a candidate finding. If no documentation exists, flag its absence as a Suggestion.

## Step 2: Build Premises

Run through every applicable item in **`../_shared/semiformal-checklist.md`** — Name Resolution, Type Contracts, State Preconditions, Control Flow Assumptions. Read its "What is NOT a Premise" section before writing.

Write premises **before** starting the trace.

**Good premise example:** "`users` is a `list[User]` passed by reference; `users.remove(x)` mutates the list in place; the `for user in users` iterator does not re-index after a mutation, so removing element at position `i` causes element at original position `i+1` to be skipped."

## Step 3: Trace the Normal Execution Path

Trace the most common execution path step by step:

```
1. [line N] [expression evaluated] → [result]
2. `name` resolves to [full qualified definition] at [file:line]
3. Arguments passed: arg1 = [value/type], arg2 = [value/type]
4. Inside [callee] at [line]: [key operation] → [result]
5. Returns [value/type] to caller at [line]
6. [line N+k] Result used as [role]
```

**Minimum thresholds** (per `../_shared/semiformal-guide.md`): ≥ 3 substantive steps and ≥ 2 location anchors. Below either threshold, downgrade the finding to Suggestion with `manual verification recommended`.

**Good trace example:**
```
1. [service.py:6] `result = charge(order)` — `charge` resolves to `payments.gateway.charge` (imported at line 1).
2. [gateway.py:3] Inside `charge`: condition `order.amount == 0` evaluates to True for this input.
3. [gateway.py:4] Returns `None` (early return; no dict constructed).
4. [service.py:7] `result['transaction_id']` evaluates `None['transaction_id']` → raises `TypeError`.
```

## Step 4: Trace Edge Cases

For each boundary condition relevant to the code's risk profile, trace separately:

- Empty/null/zero inputs (L3)
- Maximum or minimum values (L3)
- Inputs that trigger the else-branch or catch block (L5)
- Re-entrant calls in a single context (L4); concurrent calls across threads/tasks (L7)
- Callee returning `null`/`None`/`undefined` (L6)

## Step 5: Identify Divergences

For each point where a premise is violated, write a finding using the four-field format with the L-code that best describes the cause.

**Severity:**
- 🔴 Critical: causes exception, data corruption, incorrect output, or security-relevant behavior in a reachable path.
- 🟡 Warning: reachable but only under uncommon inputs or a specific sequence of prior operations.
- 🟢 Suggestion: requires unusual/currently-impossible conditions, or consequence is minor.

If the trace does not conclusively confirm a divergence, flag as Suggestion with `manual verification recommended`.

## Step 6: Apply Iron Law

Premises, Trace, and Divergence must all be complete before writing a Remedy.

**Good remedy example:** "On line 42, replace `format(self.data.year, '04d')` with `builtins.format(self.data.year, '04d')` to avoid dispatching to the module-level `format()` that expects a datetime object."

## Step 7: Compute Score and Output

1. Start at 100. Deduct per confirmed finding (Critical −15, Warning −7, Suggestion −2).
2. Fill in the Report Template from `report-template.md`.
3. Summary: most critical finding, recommended next action, whether the logic is safe to ship.
