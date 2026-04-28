# Logic Review — Step-by-Step Guide

## Step 1: Establish Claimed Behavior

Before tracing, understand what the code is supposed to do:
- Read any comments, docstrings, or test names that describe intended behavior.
- If reviewing a PR/diff, read the commit message or PR description.
- If none of these exist, infer from function/variable names — but flag the absence of documentation as a Suggestion.

Write one sentence: "This code is supposed to [verb] [what], given [inputs], producing [output/side effect]."

This sentence becomes the reference point for divergence: anything the trace reveals that contradicts it is a candidate finding.

## Step 2: Build Premises

For each function or block under review, run through every applicable item in the **Premises Construction Checklist** at `../_shared/semiformal-checklist.md` — Name Resolution, Type Contracts, State Preconditions, Control Flow Assumptions. That file is the single source; do not re-list its items here. Read its **"What is NOT a Premise"** anti-pattern section before writing your first premise.

Write the premises down explicitly before starting the trace. A premise you were not willing to state is a premise the trace cannot validate or contradict, so any "finding" resting on it is speculation.

**❌ Bad premise:** "The function is supposed to remove all inactive users." (Restates the goal, not an assumption the code makes.)

**✅ Good premise:** "`users` is a `list[User]` passed by reference; `users.remove(x)` mutates the list in place; the `for user in users` iterator does not re-index after a mutation, so removing element at position `i` causes element at original position `i+1` to be skipped on the next iteration."

The good premise is **falsifiable by the trace**: the trace can either confirm or contradict each clause. The bad premise cannot be contradicted by anything — it's a wish.

## Step 3: Trace the Normal Execution Path

With premises established, trace the most common execution path step by step.

Format:
```
1. [line N] [expression evaluated] → [result]
2. `name` resolves to [full qualified definition] at [file:line]
3. Arguments passed: arg1 = [value/type], arg2 = [value/type]
4. Inside [callee] at [line]: [key operation] → [result]
5. Returns [value/type] to caller at [line]
6. [line N+k] Result used as [role]
```

Stop when you have traced far enough to confirm that the normal path produces the claimed behavior — or to discover a divergence.

**Minimum thresholds** (per `../_shared/semiformal-guide.md`): a trace must have **≥ 3 substantive steps** and **≥ 2 location anchors** (`[line N]`, `file.py:N`, or function-boundary markers). Below either threshold, downgrade the finding to Suggestion with `manual verification recommended`.

**❌ Bad trace:** "Calls `charge(order)` which returns `None`, then accesses `result['transaction_id']` which fails." (One run-on sentence; no anchors; collapses caller, callee, and divergence into one line — a reader cannot independently verify any step.)

**✅ Good trace:**
```
1. [service.py:6] `result = charge(order)` — `charge` resolves to `payments.gateway.charge` (imported at line 1).
2. [gateway.py:3] Inside `charge`: condition `order.amount == 0` evaluates to True for the input scenario.
3. [gateway.py:4] Function returns `None` (early return; no dict constructed).
4. [service.py:7] `result['transaction_id']` evaluates `None['transaction_id']` → raises `TypeError: 'NoneType' object is not subscriptable`.
```
Four steps, four anchors, one cross-file boundary, one explicit name resolution. A reader can re-walk this and either confirm or contradict it.

## Step 4: Trace Edge Cases

For each boundary condition relevant to the code's risk profile, trace separately:

- Empty / null / zero inputs (L3 detection)
- Maximum or minimum values (L3)
- Inputs that trigger the else-branch or the catch block (L5)
- Re-entrant calls in a single execution context (L4); concurrent calls across threads / async tasks (L7)
- The case where a callee returns `null`/`None`/`undefined` (L6)

Do not trace every possible input — focus on the ones most likely to diverge from the claimed behavior.

## Step 5: Identify Divergences

For each point in the trace where a premise is violated:

1. Name the risk code (L1–L9) that best describes the divergence.
2. Write the finding using the four-field format:
   - **Premises:** the specific assumption that was made
   - **Trace:** the relevant steps that revealed the violation
   - **Divergence:** the exact line and consequence
   - **Remedy:** the minimal concrete fix

**Severity assignment:**
- 🔴 Critical: the divergence causes an exception, data corruption, incorrect output, or security-relevant behavior in a reachable execution path.
- 🟡 Warning: the divergence is reachable but only under uncommon inputs or requires a specific sequence of prior operations.
- 🟢 Suggestion: the divergence exists but requires unusual or currently impossible conditions, or the consequence is minor (a wrong log message, a slightly imprecise result).

If the trace does not conclusively confirm a divergence, do not promote to Critical or Warning. Flag as Suggestion with a note that manual verification is recommended.

## Step 6: Apply Iron Law

Apply the Iron Law from `common.md`: Premises, Trace, and Divergence must all be complete before a Remedy is written.

The Remedy must address the specific divergence, not the general "class of problem":

Bad Remedy: "Add more input validation."
Good Remedy: "On line 42, replace `format(self.data.year, '04d')` with `builtins.format(self.data.year, '04d')` to avoid dispatching to the module-level `format()` that expects a datetime object."

## Step 7: Compute Score and Output

1. Start at 100. Deduct per confirmed finding (Critical −15, Warning −7, Suggestion −2).
2. Fill in the Report Template from `common.md`.
3. Write the Summary: most critical finding, recommended next action, and whether the logic is safe to ship.
