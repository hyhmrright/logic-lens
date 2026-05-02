---
name: logic-locate
description: >
  Locate the root cause of a CONFIRMED failure via backward-then-forward
  semi-formal tracing. Trigger when the user provides a stack trace,
  failing assertion, error message, or specific wrong-value observation
  — "find the bug", "this test is failing", "track down this crash",
  "why is this test failing", "KeyError at line 89", "expected 70, got
  100", "NoneType has no attribute X", "cart empties when second tab opens".
  SCOPE HARD RULE: requires a concrete failure (exception, failing test,
  or specific wrong output). Vague suspicion without evidence uses
  logic-review; behavior explanation uses logic-explain; refactor
  comparison uses logic-diff; codebase audit uses logic-health.
  Do NOT trigger for: vague "what's wrong" without a concrete symptom,
  style questions, or performance issues.
---

# Logic-Lens — Fault Locate

## Setup

Read in this order:
1. `../_shared/common.md` — language rule, Iron Law, Report Template, Fault Confidence rubric (see §5 and §7), Remedy discipline.
2. `../_shared/logic-risks.md` — L1–L9 definitions (the root fault maps to one).
3. `../_shared/semiformal-guide.md` — tracing methodology and interprocedural reasoning.
4. `../_shared/semiformal-checklist.md` — Premises Construction Checklist.
5. `../_shared/report-template.md` — Report layout (English + Chinese).
6. `logic-locate-guide.md` — fault-localization process.

## Process

**Step 0. Language + scope routing.** Detect language per `common.md` §1. Confirm a concrete failure exists (stack trace, failing assertion, specific wrong value). If only a suspicion, switch to logic-review.

**Step 1. Understand the failure** (guide Step 1) — observed behavior, expected behavior, reproduction path.

**Step 2. Identify the entry point** (guide Step 2) — failing test, outermost application frame, or request handler — whichever is closest to the failure.

**Step 3. Trace backward from the failure point** (guide Step 3) — walk each value and state back to its origin, building premises at every hop.

**Step 4. Trace forward to confirm** (guide Step 4) — from the suspected root, verify the trace reaches the observed symptom.

**Step 5. Interprocedural tracing if a callee is implicated** (guide Step 5) — trace into the callee; check return values under observed conditions, unhandled exceptions, shared-state mutation. Apply the depth limit and Call-Chain Context Label format defined in `semiformal-guide.md` §Call-Chain Context Labels; at the limit, state the remaining callee path as a premise assumption and downgrade to **Medium confidence** (per `common.md` §7).

**Step 6. Identify the root divergence and classify** (guide Step 6) — state the exact line/expression, the violated premise, the actual behavior, the propagation chain to the symptom; pick the L-code.

**Step 7. Output the focused report** (guide Step 7) — Fault Confidence (High/Medium/Low, per `common.md` §7); Primary Fault (single four-field finding); optionally Contributing Factors; a minimal Remedy per `common.md` §10.

**Mode line in report:** `Fault Locate` (Chinese: `故障定位`).

**Output format:** the Findings section has ONE Primary Fault, not a full Critical/Warning/Suggestion split. The Logic Score line is replaced by **Fault Confidence:** High / Medium / Low.
