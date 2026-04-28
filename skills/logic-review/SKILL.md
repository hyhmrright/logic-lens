---
name: logic-review
description: >
  Find logic bugs in a single file or function via semi-formal execution
  tracing (Premises → Trace → Divergence → Remedy). Trigger when a user
  shares code and suspects something is wrong without naming a concrete
  failure — phrases like "review this", "does this look right", "check
  this function", "audit this code", "tests pass but prod fails".
  SCOPE HARD RULE: one file or one function only. For a directory or
  whole module use logic-health; for a confirmed failure (stack trace,
  failing test, specific wrong value) use logic-locate; for two versions
  use logic-diff; for repo-wide autonomous fixing use logic-fix-all.
  Do NOT trigger for: style/formatting, security scanning, performance,
  test generation, architecture or design questions.
---

# Logic-Lens — Logic Review

## Setup

Read in this order:
1. `../_shared/common.md` — language rule, Iron Law, Report Template, Logic Score, Remedy discipline.
2. `../_shared/logic-risks.md` — L1–L9 definitions.
3. `../_shared/semiformal-guide.md` — tracing methodology and Premises Construction Checklist.
4. `logic-review-guide.md` — step-by-step review process.

## Process

**Step 0. Language + scope routing.** Detect the user's language per `common.md` §1; every label and header below must be in that language. Confirm scope is one file or one function — if the user points at a directory, switch to logic-health; if they describe a confirmed failure, switch to logic-locate; if two versions, logic-diff.

**Step 1. Establish claimed behavior** (guide Step 1) — write one sentence describing what the code is supposed to do.

**Step 2. Build premises** (guide Step 2) — name resolution, type contracts, state preconditions, control-flow assumptions, per the Premises Construction Checklist in `semiformal-guide.md`.

**Step 3. Trace normal path** (guide Step 3) — sequential, interprocedural trace; resolve every name; state every type.

**Step 4. Trace edge cases** (guide Step 4) — empty/null/zero, max/min, else/catch branches, concurrent calls.

**Step 5. Identify divergences** (guide Step 5) — classify each by L1–L9; assign severity; downgrade to Suggestion when trace is unverified.

**Step 6. Apply Iron Law** (guide Step 6) — confirm all findings have Premises → Trace → Divergence complete before Remedy is written; Remedy must be paste-ready per `common.md` §10.

**Step 7. Score and output** (guide Step 7) — compute Logic Score per `common.md` §6; render Report Template with localized headers.

**Mode line in report:** `Logic Review` (Chinese: `逻辑审查`).
