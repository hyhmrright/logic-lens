---
name: logic-fix-all
description: >
  Fully autonomous logic audit-and-fix pipeline — scans the target scope,
  finds every logic bug at every severity level, fixes each one without
  requiring user involvement, verifies each fix with semantic diff, then
  re-confirms the codebase is clean. Use this when the user wants all logic
  issues resolved hands-free: "fix everything", "clean up all logic issues",
  "I don't want to look at the code", "just fix it all", "run a full fix",
  "audit and fix", "fix all bugs automatically". Also trigger when the user
  expresses frustration with recurring bugs and wants a one-shot resolution.
  Do NOT trigger for: analysis-only requests ("what are the issues?", "show me
  the bugs" — use logic-health or logic-review instead), single-function
  explanations (use logic-explain), comparing two versions (use logic-diff),
  locating one specific failure (use logic-locate), single-file or
  single-function fixes where the user has already named the specific target
  (use logic-review then direct Edit instead — the full 8-step pipeline is
  disproportionate for a named, scoped fix). The key signal is that the
  user wants FIXES applied without specifying where, not just findings reported.
---

# Logic-Lens — Logic Fix All

## Setup
**Shared context (standard for all skills that produce findings):**
1. Read `../_shared/common.md` for the Iron Law, Report Template, and Logic Score.
2. Read `../_shared/logic-risks.md` for L1–L6 risk definitions and detection patterns.
3. Read `../_shared/semiformal-guide.md` for semi-formal reasoning methodology.

**Skill-specific:**
4. Read `logic-fix-all-guide.md` in this directory for the full autonomous fix pipeline.

## Process

**Scope detection:** If the user has not specified a target, default to the repository root. Check for `.logic-lens.yaml` — ignore patterns and custom risk codes are read in Step 1 of the guide.

1. Enumerate and classify files by risk tier using the logic-health prioritization criteria (Step 1)
2. Run a full semi-formal review pass per file and collect all findings (Step 2)
3. If concrete failures exist, run logic-locate and merge findings into the collected set (Step 3)
4. Assemble the fix queue, sort by severity, and write a remedy for each finding applying the Iron Law (Step 4)
5. Apply fixes in queue order (Step 5)
6. Verify each fix with logic-diff — confirm the divergence is removed and correct paths are unchanged (Step 6)
7. Re-run logic-review on modified files to confirm clean; output the Fix Report (Steps 7–8)

**Mode line in report:** `Logic Fix All`

**Fix Report additions** (append after the standard Findings section from `common.md`):

```
## Fix Log

| # | File | Lines | Finding | Risk | Fix Applied | Status |
|---|------|-------|---------|------|-------------|--------|
| 1 | auth/token.py | 42–55 | Null deref on missing claim | L1 | Added guard before claim access | verified |
| 2 | api/router.ts | 108 | Off-by-one on page index | L2 | Changed `<` to `<=` | verified |
| 3 | db/query.py | 201 | External state, complex trace | L3 | Added null check | unverified |

## Unresolved Findings

[List any findings that could not be fixed, with reason. Empty if all resolved.]

## Summary

[2–3 sentences: overall improvement, most impactful fix, any items requiring
follow-up runtime testing.]
```

**Report header fields** (replace the standard header fields from `common.md`):
```
**Logic Score (before):** XX/100
**Logic Score (after):**  YY/100
**Findings fixed:** N  (Critical: n1 · Warning: n2 · Suggestion: n3)
**Findings unresolved:** M
```
