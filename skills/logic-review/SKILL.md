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

Use lazy loading per `../_shared/common.md` §13:
1. Read `../_shared/common.md` only for language, Iron Law, Logic Score, scope management, Remedy discipline, config fields, and loading budget.
2. Read only the relevant step in `logic-review-guide.md` as you reach it.
3. Load `../_shared/logic-risks.md`, `../_shared/semiformal-guide.md`, `../_shared/semiformal-checklist.md`, and `../_shared/report-template.md` on demand when the current step needs them.

## Process

**Step 0. Language + scope routing.** Detect the user's language per `common.md` §1; every label and header below must be in that language. Confirm scope is one file or one function — if the user points at a directory, switch to logic-health; if they describe a confirmed failure, switch to logic-locate; if two versions, logic-diff.

**Step 1. Establish claimed behavior + review entry points** (guide Step 1) — write one sentence describing what the code is supposed to do, then select the concrete entry function(s) that will be traced. If a file exceeds `common.md` §9 limits, state the selected subset and why.

**Step 2. Build premises** (guide Step 2) — per the Premises Construction Checklist in `semiformal-checklist.md`; include caller/callee contracts when the reviewed function depends on another local function.

**Step 3. Build the risk path ledger** (guide Step 3) — enumerate candidate bug paths across L1–L9 before writing findings. Tag each retained path as Class A (self-evident) or Class B (invariant-dependent). Do not stop after the happy path.

**Step 4. Deep-trace selected paths** (guide Step 4) — trace the normal path plus the highest-risk edge paths; resolve every name, state every type, cross callee boundaries, and stop each trace at either a confirmed divergence or a confirmed safe post-condition.

**Step 5. Identify divergences** (guide Step 5) — classify each by L1–L9; assign severity; apply the reachability gate (Class A reports directly; Class B requires a probe — enforcement found → drop candidate, not found → assigned severity, partial → cap at Warning with `manual verification recommended`).

**Step 6. Apply Iron Law** (guide Step 6) — confirm all findings have Premises → Trace → Divergence complete before Remedy is written; Remedy must be paste-ready per `common.md` §10.

**Step 7. Score and output** (guide Step 7) — compute Logic Score per `common.md` §6; render Report Template with localized headers.

**Mode line in report:** `Logic Review` (Chinese: `逻辑审查`).
