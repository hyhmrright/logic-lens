# Logic Review — Step-by-Step Guide

## Step 1: Establish Claimed Behavior

Read any comments, docstrings, test names, or commit message. Write one sentence:
"This code is supposed to [verb] [what], given [inputs], producing [output/side effect]."

This sentence is the reference point: anything the trace contradicts is a candidate finding. If no documentation exists, infer intent from the function signature, caller usage, tests, and names. Do not emit a documentation-gap finding unless the missing contract directly prevents a logic conclusion.

Select the review entry point before tracing:
- Single function input: trace that function and any local callees reached from it.
- Single file input: identify public/exported functions, functions changed recently, and functions touching external state. If the file exceeds `common.md` §9 limits, choose at most 3 high-risk functions and state the uncovered functions in Scope.
- Pasted snippet without line numbers: anchor trace steps to function names and expressions; do not invent line numbers.

## Step 2: Build Premises

Run through every applicable item in **`../_shared/semiformal-checklist.md`** — Name Resolution, Type Contracts, State Preconditions, Control Flow Assumptions. Read its "What is NOT a Premise" section before writing.

Write premises **before** starting the trace.

**Good premise example:** "`users` is a `list[User]` passed by reference; `users.remove(x)` mutates the list in place; the `for user in users` iterator does not re-index after a mutation, so removing element at position `i` causes element at original position `i+1` to be skipped."

For logic-review, premises must cover both sides of each important boundary:
- **Caller contract:** What values can enter this function from real call sites? If call sites are unavailable, mark this premise as partial.
- **Callee contract:** What can each local callee return, raise, mutate, or skip? Trace into local callees when the finding depends on their behavior.
- **State lifetime:** Which state survives across calls, iterations, awaits, callbacks, or retries?
- **Observable consequence:** What output, mutation, exception, persisted value, or externally visible side effect would make the bug real?

## Step 3: Build the Risk Path Ledger

Before writing any finding, enumerate candidate paths. This prevents the review from anchoring on the happy path.

Create a short internal ledger with one row per path:

```
[risk code] [entry point] [input/state condition] [branch/callee/resource involved] [why this path is reachable or not] [Class A | Class B]
```

Tag each **retained** candidate with a **Reachability Class** (discarded candidates need no tag):
- **Class A (Self-evident):** triggering condition is visible in local code — e.g., dereference after explicit nil check, index beyond bounds, unchecked type assertion, resource with no release on a visible exit path.
- **Class B (Invariant-dependent):** triggering condition requires an implicit external assumption to be false — e.g., "all groups always contain at least one alias" or "callers never pass nil here." Requires a reachability probe in Step 5 before reporting.

Example ledger rows:
```
L3  parseCSV  empty input  len(rows)==0 guard absent      always reachable from callers  Class A
L5  filterPkgVulns  all groups ignored  len(newGroups)==0 guard  depends on "vuln always in ≥1 group" invariant  Class B
```

Minimum ledger coverage:
- **Normal path:** the common valid input path.
- **Boundary paths (L3):** empty/null/zero, single item, first/last item, max/min, divide/slice/index boundaries.
- **Type/name paths (L1/L2):** shadowed identifiers, dynamic dispatch, coercions, nullable values, deserialized input.
- **Callee paths (L6):** local callees returning null/None/undefined, raising, mutating arguments, or returning a different shape.
- **Control/resource paths (L5/L8):** every early return, throw/raise, catch/except, break/continue after acquisition or required post-condition.
- **State/concurrency paths (L4/L7):** mutation during iteration, shared mutable defaults, aliases, closures, await/callback/task boundaries. For L4 also check: does the function mutate its argument AND return it (aliased-return dual contract)? For L7: does the hazard require two concurrent execution contexts — if yes it is L7, not L4 (e.g. lock-order inversion between goroutines is L7 even though it involves mutation).
- **Time/locale paths (L9):** naive/aware datetime, DST, locale-sensitive parse/sort/format, implicit encoding.

Discard a candidate only after stating why it is unreachable or irrelevant. Deep-trace the normal path and the highest-risk reachable candidates first.

## Step 4: Deep-Trace Selected Execution Paths

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

Then trace each selected risk path separately:

- Start with concrete input/state values, not abstract phrases like "bad input".
- Follow value origin → branch decision → callee behavior → state mutation/output.
- For loops, trace zero iterations, one iteration, and the iteration where the invariant changes.
- For async/concurrent code, name the exact boundary where another execution context can observe or mutate state.
- Stop at a confirmed safe post-condition if the candidate is not a bug; do not turn safe paths into Suggestions.

## Step 5: Identify Divergences

For each point where a premise is violated, write a finding using the four-field format with the L-code that best describes the cause.

**Severity:**
- 🔴 Critical: causes exception, data corruption, incorrect output, or security-relevant behavior in a reachable path.
- 🟡 Warning: reachable but only under uncommon inputs or a specific sequence of prior operations.
- 🟢 Suggestion: requires unusual/currently-impossible conditions, consequence is minor, or one premise is partial.

For Class A candidates: if the trace does not conclusively confirm consequence (reachability is already self-evident for Class A), downgrade to Suggestion with `manual verification recommended` or omit it. A plausible code smell without a concrete execution path is not a logic-review finding.

**Reachability gate — apply before writing any finding:**

- **Class A:** report at the assigned severity (local code is sufficient evidence).
- **Class B:** run a reachability probe first:
  1. Search for invariant enforcement — constructor, validator, schema definition, or call sites visible in current scope.
  2. Enforcement found and airtight (no code path bypasses it) → **drop the candidate; do not write a finding.** Optionally record in the report Summary: "Invariant enforced at [location] — no current bug; revisit if callers or schema change."
  3. No enforcement found → report at the assigned severity.
  4. Enforcement partial or outside current scope → report at the assigned severity, capped at 🟡 Warning, with `manual verification recommended`.

Record the probe result in the finding's Trace (not Premises) so the reader can verify the class assignment without violating the Premises checklist.

Deduplicate by root cause: if one bad callee contract creates several caller symptoms, report one L6 finding at the callee/caller contract boundary and list representative call sites in the Trace or Remedy.

**No-bug discipline:** When the user's question is framed as "does X cause bug Y?" and the trace conclusively shows Y does NOT apply (e.g., `defer` in Go runs on all exit paths so there is no lock leak), write a finding concluding **NO logic error** for Y with Premises → Trace → Divergence showing why. Do not fabricate unrelated findings to appear thorough — that undermines precision and triggers false positives. However, if the Risk Path Ledger from Step 3 surfaced a separate, concrete, reachable bug with a complete trace, report it as an independent finding; a no-bug verdict on Y does not suppress genuine findings on other risks. If the ledger produced no other findings, stop.

## Step 6: Apply Iron Law

Premises, Trace, and Divergence must all be complete before writing a Remedy.

**Good remedy example:** "On line 42, replace `format(self.data.year, '04d')` with `builtins.format(self.data.year, '04d')` to avoid dispatching to the module-level `format()` that expects a datetime object."

## Step 7: Compute Score and Output

1. Start at 100. Deduct per confirmed finding (Critical −15, Warning −7, Suggestion −2).
2. Fill in the Report Template from `report-template.md`.
3. Summary: most critical finding, recommended next action, whether the logic is safe to ship.
