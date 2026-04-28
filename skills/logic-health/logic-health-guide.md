# Logic Health — Step-by-Step Guide

## Step 1: Enumerate Scope and Plan the Sweep

For a full health check, decide which modules to cover and in what order:

**Priority tiers:**
1. **Highest:** Public API surfaces (functions called by external code or exposed via HTTP/RPC); code changed in the last 30 days (`git log --since=30.days --name-only --pretty=format: | sort -u`)
2. **High:** Core business logic; functions with no tests or low test coverage
3. **Medium:** Utility modules, helpers; recently added code
4. **Lower:** Stable, well-tested code with no recent changes

For large codebases, be explicit about what is and is not covered. "This health report covers the `auth/`, `payments/`, and `api/` modules. `frontend/` and `tests/` are excluded."

## Step 2: Run Focused Logic Reviews Per Module

For each module in the priority list, apply the Logic Review process from `logic-review-guide.md`, but at a higher level of abstraction:

- Focus on public functions and their entry-point logic.
- Trace the most likely execution paths; skip internal helpers unless a trace leads into them. "Internal helper" means not reachable from outside the module: Python `_`-prefixed names, Java/Kotlin `private`, Go unexported (lowercase) identifiers, and any function absent from the module's public API documentation. When a language has no visibility modifier, treat any function not documented in public-facing docs as internal.
- Apply the L1–L9 checklist at the module level: are there patterns that suggest systemic risk?
- Spend more time on modules with complex control flow, many callee dependencies, or recent changes.

Time allocation guidance (adjust to codebase size):
- Small module (<200 lines): full trace of all public functions
- Medium module (200–1000 lines): trace public API + any function with multiple callers
- Large module (>1000 lines): trace public API + top 3 highest-risk functions by control flow complexity

## Step 3: Record Findings Per Module

For each finding, apply the standard four-field format (Premises → Trace → Divergence → Remedy). Tag each finding with:
- The module it belongs to
- Its risk code (L1–L9 or Cx)
- Its severity (Critical / Warning / Suggestion)

Keep a running count as you go — you'll use this in Step 4.

## Step 4: Aggregate Findings

After sweeping all modules, compile the aggregate data:

```
Total findings: [N]
  🔴 Critical: [n] in [module list]
  🟡 Warning:  [n] in [module list]
  🟢 Suggestion: [n]

By risk code:
  L1: [n findings, modules affected]
  L2: [n findings, modules affected]
  ...
```

## Step 5: Compute Scores

**Per-module Logic Score:** Apply the standard scoring formula (100 − deductions) to each module's findings.

**Overall Logic Score:** Average of per-module scores, weighted by line count. Do not simply average the scores — a small module with a perfect score should not mask a large module with a Critical.

Weighted formula: `sum(module_score * module_weight)`
where `module_weight = line_count / total_lines_reviewed`.

## Step 6: Identify Systemic Patterns

This is the unique value of a health check over individual reviews. Look for:

**Repeated L-codes across modules:** If L1 (Shadow Override) appears in 4 modules, that is a codebase-wide naming convention problem. The remedy is a linting rule or a naming convention document, not 4 individual fixes.

**Architectural patterns enabling risks:**
- Heavy use of global state → enables L7 (concurrent races) and L4 (single-context aliasing) across the codebase
- Deep callee chains with no defensive checks → enables L6 propagation
- No type annotations in a dynamic language → makes L2 invisible until runtime

**Risk concentration:** Are Criticals clustered in one module? That module needs prioritized attention — it may be a good refactoring candidate or a coverage gap.

## Step 7: Output the Health Report

Use the Report Template single source at `../_shared/report-template.md` plus the Logic-Health additions defined in `logic-health/SKILL.md` (mode line, Module Breakdown, Systemic Patterns sections). The base layout is:
1. Standard header with overall Logic Score
2. Full Findings section (organized by severity, then module)
3. Standard Summary (2–3 sentences)
4. Module Breakdown table (appended after Summary, per report-template.md Rule 4)
5. Systemic Patterns section (also after Summary)
6. Recommended Priority Order (top 3–5 actions, ordered by impact; also after Summary)
