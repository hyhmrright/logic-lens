# Execution Explain — Step-by-Step Guide

## Step 1: Establish Entry Point and Scenario

Before tracing, confirm with the user (or infer from context):
- Which function, method, or code block is the entry point?
- Which input scenario should be traced? (e.g., "a logged-in user posting a comment", "an empty list passed to sort", "the happy path vs. the error path")
- What is the user trying to understand? (surprising behavior, a performance question, how data transforms through the system, or general comprehension)

State these explicitly at the start of the explanation:
"Tracing `process_payment(order, card)` for the scenario where the card is declined."

## Step 2: Build Premises

Apply the **Premises Construction Checklist** at `../_shared/semiformal-checklist.md` — Name Resolution, Type Contracts, State Preconditions, Control Flow Assumptions. Do it explicitly even for an explanation: premises prevent the trace from making unsubstantiated claims.

Key emphasis for explanations:
- Resolve every non-obvious name. If the user is asking how something works, they probably don't know which `format` or which `sort` is being called.
- State the type of every significant variable at entry. This anchors the trace for the reader.
- Note any global or module-level state that the function reads or modifies.

## Step 3: Produce the Step-by-Step Trace

Write the trace as a numbered sequence. The goal is that a reader who has never seen this code can follow exactly what happens.

**Formatting guidance:**
- Use short, active sentences: "`items.sort()` calls the list's `sort` method with no key, sorting in ascending order using `__lt__`."
- When crossing a function boundary: "Entering `validate_card()` at `payments.py:88`."
- When a conditional determines execution: "`if card.status == 'active'` evaluates to `False` because `card.status` is `'declined'` (set in the fixture at line 12). Taking the else branch."
- When state changes: "`order.status` is mutated from `'pending'` to `'failed'` at line 134."

**Depth calibration:**
- For understanding a high-level flow: trace at the function-call level, summarize internals unless they're relevant.
- For understanding surprising behavior: go deep into the surprising part, even into library code if necessary.
- For a debugging explanation: trace until the point where the unexpected behavior occurs, then explain exactly why it occurs.

## Step 4: Highlight Non-Obvious Behavior

After the trace, explicitly call out anything a reader might not expect:

- Names that resolve differently than they look (L1 patterns)
- Implicit type coercions that change behavior
- Side effects that are not obvious from the function signature
- Conditions under which this execution path is NOT taken
- Any assumption the code makes that may not hold in all environments

Format: "Worth noting: `format()` on line 42 is NOT Python's builtin — it resolves to the module-level `format()` defined at line 8 of this file, which expects a datetime object."

## Step 5: Summarize Actual vs. Assumed Behavior

Close with two statements:

**What the code actually does:**
A one- or two-sentence factual description of the behavior revealed by the trace.

**What a casual reader might assume:**
The plausible misreading that the trace contradicts. This is the most valuable part of the explanation — it directly addresses the gap that caused the user's confusion.

**Example:**
"What the code actually does: `save_record()` commits the database transaction and then logs the record ID, but if the commit fails, the log statement is still executed with a stale record ID.
What a casual reader might assume: logging happens after commit succeeds, so the logged ID is always valid."

## Step 6: Map output to the report template

logic-explain uses the standard report template from `report-template.md` with these adaptations:

- **Header:** Mode = `Execution Explain` / `执行解释`; the mode-specific score line is omitted (see `common.md` §5).
- **Findings section:** Always omit. logic-explain is descriptive — it produces no L-code findings and no Remedy. If the trace reveals what looks like a bug, note it in Step 4 (Non-Obvious Behavior) and recommend the user re-run with logic-review for a confirmed finding.
- **Summary:** Place the Step-by-Step Trace (Step 3), Non-Obvious Behavior callouts (Step 4), and the Actual vs. Assumed Behavior pair (Step 5) here. Structure them as labeled sub-sections within Summary rather than as Findings entries — they are explanatory prose, not bug reports.
