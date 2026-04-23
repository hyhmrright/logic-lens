---
name: logic-fix-all
description: >
  Fully autonomous repository-wide logic audit-and-fix pipeline. Scans
  the ENTIRE repo (source code, runtime config, constraint files,
  behavioral docs — not just recent commits or staged changes), finds
  every logic bug at every severity using semi-formal execution tracing,
  applies fixes, iterates until clean. Starts with a mandatory pre-flight
  consent prompt because it is token-intensive; after consent, runs
  hands-free. Use this when the user wants all logic issues resolved
  across a codebase without naming specific files: "fix everything",
  "clean up all logic issues", "run a full fix", "audit and fix the whole
  repo", "fix all bugs automatically", or expresses frustration with
  recurring bugs and wants a one-shot resolution. Do NOT trigger for:
  analysis-only requests ("what are the issues?", "show me the bugs" —
  use logic-health or logic-review); single-function explanations (use
  logic-explain); comparing two versions (use logic-diff); locating one
  specific failure (use logic-locate); single-file or single-function
  fixes where the user has already named the specific target (use
  logic-review then direct Edit — the full pipeline is disproportionate
  for a named, scoped fix); syntax/style/linting concerns (use a linter
  — this skill reviews logic only). Key signal: the user wants FIXES
  applied across a codebase without specifying where.
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

**Scope:** Always the entire repository. If the user names a subpath, honor it, but default is the repo root. `.logic-lens.yaml` is read in Phase 1 for `ignore:` patterns, `custom_risks`, `severity:` overrides, and `fix_all.max_iterations`.

1. **Mandatory Consent + Scope Enumeration** — the pipeline's *only* mandatory user interaction: display scope/method/cost/iteration notice and wait for explicit user consent before any scanning or editing. On consent, enumerate every runtime-affecting file (source / config / constraint / doc), auto-exclude `.git` and project-specific build artifacts, classify by risk tier (Phases 0–1)
2. **Health Pass** — apply `logic-health` methodology to map per-module Logic Scores and systemic L-code patterns (Phase 2)
3. **Deep Review** — apply `logic-review` methodology per file to collect full Premises → Trace → Divergence findings (Phase 3)
4. **Conditional Clarification** — apply `logic-locate` when concrete failures exist; apply `logic-explain` when a finding's path is unclear (call depth > 3, cross-module, async) (Phases 4–5)
5. **Fix Queue + Remedy** — sort by severity, write a Minimal/Targeted/Justified remedy per finding, route cross-file contradictions to the correct edit target (code vs constraint vs config) (Phase 6)
6. **Apply + Verify** — apply each fix, then apply `logic-diff` methodology to verify: expect "Conditionally Equivalent" with the condition matching the original failing scenario. Revert on regression, retry up to 3× (Phase 7)
7. **Iterate + Report** — re-run health + review on modified files and their consumers. Critical findings loop without cap; Warning/Suggestion rounds capped by `fix_all.max_iterations` with a user escalation prompt at the cap. Output the Fix Report with per-role findings, skill invocation counts, iteration history (Phases 8–9)

**Mode line in report:** `Logic Fix All`

**Fix Report additions** (append after the standard Findings section from `common.md`):

```
## Scope

| Role       | Files scanned | Tier H/M/L | Truncated? |
|------------|---------------|------------|------------|
| source     | 42            | 12/20/10   | no         |
| config     | 7             | 2/5/0      | no         |
| constraint | 3             | 1/2/0      | no         |
| doc        | 5             | 0/3/2      | no         |

## Skill Invocations

logic-health: N · logic-review: N · logic-locate: N · logic-explain: N · logic-diff: N

## Iteration History

| Round | Severity class | New findings | Action |
|-------|----------------|--------------|--------|
| 1 | mixed | 12 | fixed, iterated |
| 2 | warning/suggestion | 3 | fixed, iterated |
| 3 | suggestion | 1 | cap reached, user: continue |
| 4 | — | 0 | clean |

## Fix Log

(Role is derivable from File path — see Scope table above for the role breakdown. "Status" is one of: verified / unverified / reverted-regression.)

| # | File | Lines | Finding | Risk | Severity | Fix Applied | Status |
|---|------|-------|---------|------|----------|-------------|--------|
| 1 | auth/token.py | 42–55 | Null deref on missing claim | L1 | Critical | Added guard before claim access | verified |
| 2 | api/router.ts | 108 | Off-by-one on page index | L2 | Warning | Changed `<` to `<=` | verified |
| 3 | config/app.yaml | 12 | `timeout_ms: "30s"` (string, code expects int) | L2 | Critical | Changed value to `30000` | verified |
| 4 | CLAUDE.md | 88 | Doc claims API returns `User \| null`, code returns `User \| undefined` | L6 | Warning | Updated consumer code to handle both | verified |
| 5 | db/query.py | 201 | External state, complex trace | L3 | Warning | Added null check | unverified |

## Resolved by Clarification

[Findings that Phase 5's logic-explain pass revealed as false positives
after step-by-step tracing. Empty if none. Visibility matters — shows
the pipeline self-corrected rather than silently dropping findings.]

## Unresolved Findings

[Findings that could not be fixed, with reason. Include:
- "conflicting constraints" (Phase 7d: 3 retries exhausted)
- "user stopped iteration at round N" (Phase 8d: user declined to continue)
- "hard iteration ceiling reached" (Phase 8e: 3 user-continue's in a row)
- "ambiguous spec" (Phase 6d doc-vs-doc conflict)
- "unclear whether spec or consumer is wrong" (Phase 6d code-vs-config tie when both sides look plausible)
Empty if all resolved.]

## Summary

[2–3 sentences: overall improvement, most impactful fix, any items
requiring follow-up runtime testing or human judgment.]
```

**Report header fields** (replace the standard header fields from `common.md`):
```
**Logic Score (before):** XX/100
**Logic Score (after):**  YY/100
**Findings fixed:** N  (Critical: n1 · Warning: n2 · Suggestion: n3)
**Findings unresolved:** M
```
