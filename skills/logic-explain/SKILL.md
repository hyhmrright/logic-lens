---
name: logic-explain
description: >
  Explain what a specific piece of code actually does for a given input by
  producing a step-by-step execution trace (interprocedural, with name
  resolution and type transitions). Trigger when the user is confused
  about behavior or asks why code produces X instead of Y — "walk me
  through this", "trace through X with input Y", "why does this return
  X", "what does yield-from do here", "explain the execution path".
  SCOPE HARD RULE: a specific function + a specific input scenario. If the
  user wants to find bugs without a scenario in mind, use logic-review;
  two-version comparison uses logic-diff; concrete failures use
  logic-locate; codebase-wide audit uses logic-health.
  Do NOT trigger for: finding bugs without a behavioral question, style
  or design discussion, or concept explanations not tied to specific code.
---

# Logic-Lens — Execution Explain

## Setup

Use lazy loading per `../_shared/common.md` §13:
1. Read `../_shared/common.md` only for language, report header variants, scope routing, and loading budget.
2. Read only the relevant step in `logic-explain-guide.md` as you reach it.
3. Load `../_shared/semiformal-guide.md`, `../_shared/semiformal-checklist.md`, and `../_shared/report-template.md` on demand when the current step needs them.

Note: `logic-risks.md` is intentionally skipped — logic-explain does not produce L-code findings, and Remedy is intentionally out of scope for this mode. If the trace reveals a bug, stop and recommend logic-review or logic-locate. When handing off, do not discard work already done — present the premises established and trace steps completed under a **"Partial trace context (carry into next skill):"** heading so the user can pass them directly to the follow-on skill.

## Process

**Step 0. Language + scope routing.** Detect language per `common.md` §1. Confirm a single function + a single input scenario. If the user wants bug-finding without a scenario, hand off to logic-review.

**Step 1. Entry point and scenario** (guide Step 1) — name the function, the input scenario, and what the user is trying to understand.

**Step 2. Build premises** (guide Step 2) — resolve every non-obvious name, state the types of key variables at entry, note global/module state accessed.

**Step 3. Produce step-by-step trace** (guide Step 3) — numbered, interprocedural, active voice; cross function boundaries whenever relevant to the user's scenario. Keep the trace scenario-bound; do not branch into alternative paths unless they explain the user's confusion.

**Step 4. Highlight non-obvious behavior** (guide Step 4) — name resolutions, implicit coercions, hidden side effects; the "gotchas" the casual reader would miss.

**Step 5. Summarize actual vs. assumed** (guide Step 5) — one sentence each; this is the core value for the user.

**Mode line in report:** `Execution Explain` (Chinese: `执行解释`).

**Note:** Execution Explain is descriptive, not evaluative. Omit the Logic Score / Fault Confidence / Verdict line from the report header.
