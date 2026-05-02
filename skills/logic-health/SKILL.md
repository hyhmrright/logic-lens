---
name: logic-health
description: >
  Sweep a directory, module, or full codebase for logic correctness and
  produce a scored health dashboard with systemic patterns. Trigger when
  the user requests a health view — "audit the whole codebase",
  "health check", "health overview", "logic health overview",
  "audit src/", "audit auth and payments modules",
  "where should I focus testing", "onboarding review",
  "logic overview before we ship", "give me a health overview of this module".
  SCOPE RULE: prefer multi-file; also trigger for a single module when
  the user explicitly uses "health check", "health overview", or
  "logic health" — a concrete failure uses logic-locate; two versions
  uses logic-diff; explaining a path uses logic-explain; "fix
  everything" uses logic-fix-all.
  Do NOT trigger for: style/architecture-only audits, security-only
  scans, performance-only audits.
---

# Logic-Lens — Logic Health

## Setup

Read in this order:
1. `../_shared/common.md` — language rule, Iron Law, Report Template, Logic Score (weighted-average variant in §6), Remedy discipline.
2. `../_shared/logic-risks.md` — L1–L9 definitions.
3. `../_shared/semiformal-guide.md` — tracing methodology.
4. `../_shared/semiformal-checklist.md` — Premises Construction Checklist.
5. `../_shared/report-template.md` — Report layout (English + Chinese).
6. `logic-health-guide.md` — aggregation process.

## Process

**Step 0. Language + scope routing.** Detect language per `common.md` §1. Proceed for multi-file scopes and for single-module scopes when the user explicitly uses "health check", "health overview", or "logic health". If scope is one file and none of those health phrases appear, switch to logic-review.

**Step 1. Enumerate modules and plan the sweep** (guide Step 1) — prioritize public API surfaces, recently changed files, and user-flagged modules. Read `.logic-lens.yaml` for `ignore:` globs.

**Step 2. Run focused logic-review per module** (guide Step 2) — apply Premises → Trace → Divergence on public-facing functions; skip internal helpers unless a trace leads into them. Apply the per-module function budget from guide Step 2 (small/medium/large line-count tiers) — do not trace all functions in large modules.

**Step 3. Record findings per module** (guide Step 3) — tag module, L-code, severity.

**Step 4. Aggregate findings** (guide Step 4) — counts by severity and by L-code; cross-reference modules.

**Step 5. Compute scores** (guide Step 5) — per-module Logic Score via the standard formula; overall score is the line-weighted average (per `common.md` §6).

**Step 6. Identify systemic patterns** (guide Step 6) — L-codes appearing in **≥ 3 modules or ≥ 30% of scanned modules (whichever threshold is lower)** indicate codebase-wide habits; architectural enablers (heavy global state → L7; deep callee chains → L6) get explicit mention.

**Step 7. Output the Health Report** (guide Step 7) — standard header; Findings; Summary; then Module Breakdown, Systemic Patterns, and Recommended Priority Order (top 3–5) appended after Summary. Localize all headers if the user wrote in Chinese.

**Mode line in report:** `Logic Health` (Chinese: `逻辑体检`).

**Health-specific additions** (append after the standard Summary):

```
## Module Breakdown

| Module | Score | Critical | Warning | Suggestion | Top Risk |
|--------|-------|----------|---------|------------|----------|

## Systemic Patterns
[Risk codes appearing in ≥ 3 modules or ≥ 30% of scanned modules — codebase-wide habit rather than isolated bugs]

## Recommended Priority Order
1. [Most critical single finding]
2. [Systemic pattern with widest impact]
3. [Quick wins: suggestions that prevent future Criticals]
```

Localize column and section headers when the user wrote in Chinese (e.g., `模块分布`, `系统性模式`, `优先级建议`).
