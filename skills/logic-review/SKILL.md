---
name: logic-review
description: >
  Find logic bugs in a single file or function via semi-formal execution
  tracing (Premises → Trace → Divergence → Trigger → Remedy). Trigger when a user
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

**Step 3. Build the risk path ledger** (guide Step 3) — enumerate candidate bug paths across L1–L9 before writing findings. Tag each retained path as Class A (self-evident) or Class B (invariant-dependent). Do not stop after the happy path. **L4 priority check:** does any function mutate its input AND return the same object? **L7 priority check:** is shared state accessed across `await`/yield/thread boundaries without explicit synchronization? **L4 vs L7 disambiguation:** any state access involving more than one execution context (thread / goroutine / `await` / yield) is **L7**, never L4 — including single-threaded asyncio where coroutines interleave at `await`. L4 is for single-context aliasing only (mutable defaults, in-place mutation footgun).

**Step 4. Deep-trace selected paths** (guide Step 4) — trace the normal path plus the highest-risk edge paths; resolve every name, state every type, cross callee boundaries, and stop each trace at either a confirmed divergence or a confirmed safe post-condition.

**Step 5. Identify divergences** (guide Step 5) — classify each by L1–L9; assign severity; apply the reachability gate (Class A reports directly; Class B requires a probe — enforcement found → drop candidate, not found → assigned severity, partial → cap at Warning with `manual verification recommended`). Apply the correctness parity principle for no-bug scenarios. **No-bug output discipline:** when zero divergences remain, still emit the full template skeleton — Mode line, Scope, `**Logic Score:** 100/100`, `## Findings` followed by `_No divergence found_` (中文 `_未发现问题_`), and Summary. Do not collapse the verdict into free-form prose; downstream grading requires the structured sections to be present even when empty.

**Step 5.5. Adversarial Red Team** (guide Step 5.5) — for each candidate finding, attempt to disprove it by answering three rebuttal questions (premise rebuttal, path rebuttal, consequence rebuttal). Withdraw findings with confirmed defenses; downgrade findings with partial defenses to Suggestion.

**Step 6. Apply Iron Law — Five-Field Discipline** (guide Step 6) — confirm all findings have Premises → Trace → Divergence complete; then write Trigger (concrete reproducing input, required for Critical/Warning) and Remedy (paste-ready per `common.md` §10). **Each finding MUST use these literal field labels** — English `Premises:` / `Trace:` / `Divergence:` / `Trigger:` / `Remedy:`, or Chinese `前提：` / `追踪：` / `偏差：` / `触发：` / `修复：`. Do not paraphrase. Headers like `Execution Path`, `Issue Found`, `Core Defect`, `执行路径`, `发现的逻辑隐患`, `核心缺陷` are unacceptable substitutes — they fail downstream grading and break the report contract that other Logic-Lens skills consume.

**Step 6.5. Remedy Dry-Run** (guide Step 6.5) — mentally re-trace the Trigger input through the fixed code to confirm: divergence eliminated, no regression introduced, happy path preserved.

**Step 7. Score and output** (guide Step 7) — compute Logic Score per `common.md` §6 and emit it as the literal line `**Logic Score:** XX/100` (中文 `**逻辑评分：** XX/100`) directly under `**Scope:**` — this exact token (not "Score: XX", not "Quality: XX") is required for both grader recognition and cross-skill consumption. Then render the rest of the Report Template with localized headers.

**Step 8. Execution Verification Gate** (guide Step 8, optional) — when a runtime is available, generate a minimal reproducer script for each Critical/Warning finding, execute it to confirm the bug exists, apply the Remedy and re-execute to confirm the fix works. Withdraw false positives; mark verified findings as `✅ Execution-verified`.

**Mode line in report:** `Logic Review` (Chinese: `逻辑审查`).
