# Fault Locate — Step-by-Step Guide

## Step 1: Understand the Failure

Before locating the fault, precisely characterize it:

**Observed behavior:** What actually happens? (error message, wrong output, hang, crash — be specific about the exact value or exception)
**Expected behavior:** What should happen? (from the test assertion, documentation, or user description)
**Reproduction path:** Under what conditions does the failure occur? Which inputs, which environment, which sequence of operations?

If a stack trace is available, read it carefully — it is not the fault, but it is the most precise description of where the execution deviated. Note the innermost frame (the actual crash point) separately from the function that caused it (which may be higher in the stack).

## Step 2: Identify the Entry Point

Find the closest code entry point to the failure:
- If there is a failing test: the test function is the entry point.
- If there is a stack trace: the outermost application frame (not the library frame) is the entry point.
- If the user describes a symptom ("the API returns 500"): the request handler is the entry point.

Do not start from `main()` or the application root — start from the function closest to the failure. You will trace backward (or inward) from there.

## Step 3: Trace Backward from the Failure Point

Working from the failure site (the exception, the wrong value, the missed side effect), trace backward through the call chain to find where the incorrect value or incorrect state originated.

**Backward tracing discipline:**
- At each step, ask: "Where did this value/state come from?"
- Follow it to its origin: declaration, assignment, return from a callee, read from external state.
- Build premises at each step: what was assumed about this value at this point? What is its actual value?

This is the inverse of forward tracing. You know the symptom; you are finding the cause.

## Step 4: Trace Forward to Confirm

Once you have a hypothesis about the root cause, trace forward from it:
- Starting from the suspected fault location, does the execution reach the failure site?
- Does the fault produce exactly the observed symptom?

If yes, the hypothesis is confirmed. If not, revise — the actual fault may be earlier or in a different branch.

## Step 4b: Interprocedural Tracing

If the backward trace implicates a callee's behavior, trace into it:
- Does the callee return `None` under the conditions observed?
- Does the callee raise an exception that the caller doesn't handle?
- Does the callee mutate shared state that affects the caller's subsequent behavior?

The fault is often not in the function the user is looking at — it is in a callee that doesn't behave as the caller assumed (L6), or in a name that resolves differently than expected (L1).

## Step 5: Identify the Root Divergence

State the root fault precisely:
- The specific line or expression where the divergence originates (not the crash site — the cause of the crash)
- The premise that was violated (what the code assumed)
- The actual value or behavior (what actually happened)
- Why this propagated to the observed failure

This is the Primary Fault. There may also be Contributing Factors — conditions that enabled the fault to occur (e.g., a missing precondition check that would have caught the bad value earlier).

## Step 6: Classify and Output

1. Assign the L-code that best describes the root fault (L1–L6).
2. Assess Fault Confidence:
   - **High:** the trace fully confirms the fault — the premises, trace, and divergence form a complete chain from cause to symptom.
   - **Medium:** the trace strongly implicates the fault, but one step relies on an assumption that could not be fully verified (e.g., a library function's behavior under edge conditions).
   - **Low:** the trace identifies a plausible fault, but alternative causes cannot be ruled out without executing the code.
3. Output the focused report:
   - Primary Fault: the four-field finding for the root cause
   - Contributing Factors: conditions that enabled the fault (not findings in their own right, but context for the fix)
   - Remedy: the minimal fix that addresses the root cause
