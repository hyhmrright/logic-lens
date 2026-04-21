# Semantic Diff — Step-by-Step Guide

## Step 1: Identify the Shared Specification

Two code versions are semantically equivalent if and only if they produce identical behavior for all inputs in the shared specification. Start by establishing what that specification is:

- What inputs are both versions expected to handle?
- What outputs or side effects should both produce for each input?
- Are there inputs that one version handles and the other doesn't? (This may itself be the divergence.)

If the user hasn't stated the specification, derive it from: test cases that both versions share, the commit message or PR description, or the function's documented contract. State the derived specification explicitly.

## Step 2: Build Independent Premises for Each Version

For Version A and Version B separately, apply the full Premises checklist from `semiformal-guide.md`:

- Name resolution: same identifier, same resolution in both versions?
- Type contracts: do both versions make the same type assumptions at call sites?
- State preconditions: do both versions require the same preconditions?
- Control flow: do both versions take the same branches for the same inputs?

This step often surfaces the divergence before the trace begins — a renamed import, a changed conditional, a different default value.

## Step 3: Trace Both Versions for the Common Case

Trace Version A and Version B through the normal execution path in parallel:

```
Scenario: [describe the input]

Version A — Trace:
1. [step]
2. [step]
Result: [value / side effect]

Version B — Trace:
1. [step]
2. [step]
Result: [value / side effect]

Verdict: [Equivalent / Divergent at step N]
```

If both traces produce the same result, proceed to Step 4. If they diverge, jump to Step 5.

## Step 4: Trace Boundary Cases

For each boundary condition relevant to the code:
- Trace Version A and Version B separately.
- This is where semantically equivalent-looking code most commonly diverges: one version handles the empty case, the other returns `None`.

Prioritize:
- Empty / null / zero inputs (catches L3 divergences)
- Maximum values (integer overflow in one version but not the other)
- Error inputs (which version raises, which returns a default?)
- First and last elements of collections (off-by-one in one version)

## Step 5: Identify Semantic Divergences

A semantic divergence is a scenario where Version A and Version B produce different behavior. Classify each divergence:

**Type of divergence:**
- Bug in Version A corrected in Version B (intended)
- Regression: Version B breaks something Version A handled (unintended)
- Behavioral change: both versions work, but differently — the user must decide which is correct
- Scope expansion: Version B handles inputs Version A didn't (may or may not be intended)

For each divergence, write a finding using the standard four-field format with the risk code that best describes the cause of the divergence.

## Step 6: Classify Equivalence

Based on the traced scenarios:

- **Semantically Equivalent:** No divergence found. Both versions produce identical behavior for all traced scenarios.
- **Conditionally Equivalent:** Equivalent for all common cases. Diverges only when [specific condition] — state the condition precisely.
- **Semantically Divergent:** Confirmed behavioral difference at [location] for [scenario].

Note: "No divergence found" is not the same as "provably equivalent." State clearly which scenarios were traced and acknowledge that untested scenarios may still diverge.

## Step 7: Output

Use the standard Report Template from `common.md`. Replace the Logic Score with the equivalence verdict. In the Summary, state:
1. The verdict (equivalent / conditionally equivalent / divergent)
2. The most significant divergence found (or "no divergences found under traced scenarios")
3. Any scenarios that were not traced and should be verified manually
