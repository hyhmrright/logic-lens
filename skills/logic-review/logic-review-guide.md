# Logic Review — Step-by-Step Guide

## Step 1: Establish Claimed Behavior

Before tracing, understand what the code is supposed to do:
- Read any comments, docstrings, or test names that describe intended behavior.
- If reviewing a PR/diff, read the commit message or PR description.
- If none of these exist, infer from function/variable names — but flag the absence of documentation as a Suggestion.

Write one sentence: "This code is supposed to [verb] [what], given [inputs], producing [output/side effect]."

This sentence becomes the reference point for divergence: anything the trace reveals that contradicts it is a candidate finding.

## Step 2: Build Premises

For each function or block under review, explicitly state:

**2a. Name resolution**
List every non-trivial identifier (function calls, class references, imported names) and resolve it to its actual definition:
- Check `import` statements at the top of the file.
- Check if any local variable or parameter shadows an outer-scope name.
- For method calls, confirm the runtime type of the receiver and which class's method is dispatched.

**2b. Type contracts**
For each function parameter and return value:
- What type is expected? (from annotations, documentation, or usage)
- What type is actually passed at the call site? Trace from the declaration of the argument.

**2c. State preconditions**
- What must be true before this code runs? (non-null references, initialized fields, acquired locks, database connection open)
- Is each precondition guaranteed? By whom?

**2d. Control flow assumptions**
- For each conditional: what values cause which branch?
- For each loop: what terminates it, and can it run zero times or indefinitely?

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

## Step 4: Trace Edge Cases

For each boundary condition relevant to the code's risk profile, trace separately:

- Empty / null / zero inputs (L3 detection)
- Maximum or minimum values (L3)
- Inputs that trigger the else-branch or the catch block (L5)
- Re-entrant or concurrent calls (L4)
- The case where a callee returns `null`/`None`/`undefined` (L6)

Do not trace every possible input — focus on the ones most likely to diverge from the claimed behavior.

## Step 5: Identify Divergences

For each point in the trace where a premise is violated:

1. Name the risk code (L1–L6) that best describes the divergence.
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

Before writing any Remedy:
- Verify that Premises, Trace, and Divergence are all present for the finding.
- The Remedy must address the specific divergence, not the general "class of problem."

Bad Remedy: "Add more input validation."
Good Remedy: "On line 42, replace `format(self.data.year, '04d')` with `builtins.format(self.data.year, '04d')` to avoid dispatching to the module-level `format()` that expects a datetime object."

## Step 7: Compute Score and Output

1. Start at 100. Deduct per confirmed finding (Critical −15, Warning −7, Suggestion −2).
2. Fill in the Report Template from `common.md`.
3. Write the Summary: most critical finding, recommended next action, and whether the logic is safe to ship.
