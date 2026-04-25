---
name: logic-health
description: >
  Sweep a directory, module, or full codebase for logic correctness and
  produce a scored health dashboard with systemic patterns. Trigger when
  the scope is multi-file — "audit the whole codebase", "health check",
  "audit src/", "audit auth and payments modules", "where should I focus
  testing", "onboarding review", "logic overview before we ship".
  SCOPE HARD RULE: multi-file or directory scope. One file or one
  function uses logic-review; a concrete failure uses logic-locate; two
  versions uses logic-diff; explaining a path uses logic-explain; "fix
  everything" (no scope named) uses logic-fix-all.
  Do NOT trigger for: single function/file, style/architecture-only
  audits, security-only scans, performance-only audits.
---

# Logic-Lens — Logic Health

## Setup

Read in this order:
1. `../_shared/common.md` — language rule, Iron Law, Report Template, Logic Score (weighted-average variant in §6), Remedy discipline.
2. `../_shared/logic-risks.md` — L1–L6 definitions.
3. `../_shared/semiformal-guide.md` — tracing methodology and Premises Construction Checklist.
4. `logic-health-guide.md` — aggregation process.

## Process

**Step 0. Language + scope routing.** Detect language per `common.md` §1. Confirm scope is multi-file (directory / module list / repo). If scope is one file or one function, switch to logic-review.

**Step 1. Enumerate modules and plan the sweep** (guide Step 1) — prioritize public API surfaces, recently changed files, and user-flagged modules. Read `.logic-lens.yaml` for `ignore:` globs.

**Step 2. Run focused logic-review per module** (guide Step 2) — apply Premises → Trace → Divergence on public-facing functions; skip internal helpers unless a trace leads into them.

**Step 3. Record findings per module** (guide Step 3) — tag module, L-code, severity.

**Step 4. Aggregate findings** (guide Step 4) — counts by severity and by L-code; cross-reference modules.

**Step 5. Compute scores** (guide Step 5) — per-module Logic Score via the standard formula; overall score is the line-weighted average (per `common.md` §6).

**Step 6. Identify systemic patterns** (guide Step 6) — L-codes appearing in 3+ modules indicate codebase-wide habits; architectural enablers (heavy global state → L4; deep callee chains → L6) get explicit mention.

**Step 7. Output the Health Report** (guide Step 7) — standard header; Module Breakdown table; Findings; Systemic Patterns; Recommended Priority Order (top 3–5). Localize all headers if the user wrote in Chinese.

**Mode line in report:** `Logic Health` (Chinese: `逻辑体检`).

**Health-specific additions** (append after the standard Summary):

```
## Module Breakdown

| Module | Score | Critical | Warning | Suggestion | Top Risk |
|--------|-------|----------|---------|------------|----------|
| auth/  | 72    | 1        | 2       | 0          | L6       |
| api/   | 91    | 0        | 1       | 2          | L3       |

## Systemic Patterns
[Risk codes appearing in 3+ modules — codebase-wide habit rather than isolated bugs]

## Recommended Priority Order
1. [Most critical single finding]
2. [Systemic pattern with widest impact]
3. [Quick wins: suggestions that prevent future Criticals]
```

Localize column and section headers when the user wrote in Chinese (e.g., `模块分布`, `系统性模式`, `优先级建议`).
