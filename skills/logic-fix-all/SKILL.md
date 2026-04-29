---
name: logic-fix-all
description: >
  Autonomous repository-wide audit-and-fix pipeline: health → review →
  locate/explain → fix → diff-verify → iterate until clean. Starts with a
  mandatory consent prompt (token-intensive); after consent runs hands-free.
  Trigger when the user wants all logic issues resolved across a codebase
  without naming specific files — "fix everything", "clean up all logic
  issues", "audit and fix the whole repo", "fix all bugs automatically",
  or frustration with recurring bugs wanting a one-shot pass.
  SCOPE HARD RULE: repo-wide fixing without a specific target named. If
  the user names one function/file to fix, use logic-review then a direct
  Edit. Analysis-only requests use logic-health or logic-review. Single
  failure uses logic-locate. Two versions uses logic-diff. One path
  explanation uses logic-explain.
  Do NOT trigger for: analysis-only ("show me the bugs"), single-file
  fixes, style/lint/format concerns, or a user who already knows what
  to fix.
---

# Logic-Lens — Logic Fix All

## Setup

Read in this order:
1. `../_shared/common.md` — language rule, Iron Law, Report Template, mode header (§5: before/after Logic Scores + findings-fixed / findings-unresolved), Remedy discipline, `.logic-lens.yaml` matrix.
2. `../_shared/logic-risks.md` — L1–L9 definitions.
3. `../_shared/semiformal-guide.md` — tracing methodology.
4. `../_shared/semiformal-checklist.md` — Premises Construction Checklist.
5. `../_shared/report-template.md` — Report layout (English + Chinese).
6. `logic-fix-all-guide.md` — phased pipeline. That guide is long because the pipeline has nine phases; read it end-to-end before starting.

## Process

**Step 0. Language + scope routing.** Detect language per `common.md` §1. Default scope is the repo root; honor a user-named subpath. Read `.logic-lens.yaml` for `ignore:`, `custom_risks`, `severity:`, `focus:`, and `fix_all.max_iterations`.

**Step 1. Consent + scope enumeration** (guide Phase 0–1) — mandatory consent prompt displaying scope / method / cost / iteration cap; on consent, enumerate runtime-affecting files (source / config / constraint / doc), exclude `.git` and build artifacts, classify by risk tier.

**Step 2. Health pass** (guide Phase 2) — apply logic-health methodology to map per-module Logic Scores and L-code patterns.

**Step 3. Deep review** (guide Phase 3) — apply logic-review per file to collect full Premises → Trace → Divergence findings.

**Step 4. Conditional clarification** (guide Phase 4–5) — apply logic-locate where concrete failures exist; apply logic-explain when a finding's path is unclear (call depth > 3, cross-module, or async).

**Step 5. Fix queue + remedy** (guide Phase 6) — sort by severity; write a paste-ready Remedy per finding; route cross-file contradictions to the correct edit target (code / constraint / config / doc).

**Step 6. Apply + verify** (guide Phase 7) — apply each fix, then apply logic-diff methodology to verify (expect `⚠️ Conditionally Equivalent` matching the original failing scenario). Revert on regression; retry up to 3×.

**Step 7. Iterate + report** (guide Phase 8–9) — re-run health + review on modified files and their consumers; Criticals loop without cap; Warning/Suggestion rounds capped by `fix_all.max_iterations` with user-escalation prompt at the cap. Output the Fix Report.

**Mode line in report:** `Logic Fix All` (Chinese: `逻辑全修`).

**Fix-report additions** (appended after the standard Summary; localize all labels):

```
## Scope

| Role (source/config/constraint/doc) | Files scanned | Tier H/M/L | Truncated? |
|-------------------------------------|---------------|------------|------------|

## Skill Invocations
logic-health: N · logic-review: N · logic-locate: N · logic-explain: N · logic-diff: N

## Iteration History

| Round | Severity class | New findings | Action |

## Fix Log

| # | File | Lines | Finding | Risk | Severity | Fix Applied (one-line edit or diff summary) | Status (resolved/unresolved/reverted) |

## Resolved by Clarification
[Findings the Phase-5 logic-explain pass revealed as false positives. Empty if none.]

## Unresolved Findings
[Include reason per entry: "conflicting constraints", "user stopped iteration at round N",
"hard iteration ceiling reached", "ambiguous spec", "unclear whether spec or consumer is wrong".
Empty if all resolved.]
```

**Report header fields** (replace the standard single-line header per `common.md` §5):

```
**Logic Score (before):** XX/100
**Logic Score (after):**  YY/100
**Findings fixed:** N  (Critical: n1 · Warning: n2 · Suggestion: n3)
**Findings unresolved:** M
```
