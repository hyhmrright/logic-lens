# Logic Health — Step-by-Step Guide

## Step 1: Enumerate Scope and Plan the Sweep

Decide which modules to cover and in what order:

**Priority tiers:**
1. **Highest:** Public API surfaces; files changed in the last 30 days (`git log --since=30.days --name-only --pretty=format: | sort -u`)
2. **High:** Core business logic; functions with no tests
3. **Medium:** Utility modules, helpers, recently added code
4. **Lower:** Stable, well-tested code with no recent changes

For large codebases, state what is and is not covered: "This report covers `auth/`, `payments/`, `api/`. `frontend/` and `tests/` are excluded."

**Sweep budget:**
- Up to 12 modules: inspect every module at the tiered function budget below.
- 13-40 modules: inspect all Highest/High modules plus enough Medium modules to reach 12 modules total.
- More than 40 modules: inspect at most 15 modules in the first pass: all user-flagged modules, all recently changed High modules, then the highest-risk remaining modules by control-flow complexity and external-state access.

If the user explicitly asks for exhaustive coverage, split the report into passes and state the current pass number. Do not silently perform a full shallow scan.

## Step 2: Run Focused Logic Reviews Per Module

For each module, apply the Logic Review process from `../logic-review/logic-review-guide.md` at a higher level of abstraction:
- Focus on public functions and entry-point logic.
- Trace most likely execution paths; skip internal helpers unless a trace leads into them. "Internal" = Python `_`-prefixed, Java/Kotlin `private`, Go unexported, or absent from public API docs.
- Spend more time on modules with complex control flow, many callee dependencies, or recent changes.
- Apply L1–L9 checklist at the module level for systemic patterns.

**Time allocation:**
- Small module (<200 lines): full trace of all public functions, capped at 5 non-trivial functions.
- Medium (200-1000 lines): trace up to 5 functions: public API first, then functions with multiple callers or external-state access.
- Large (>1000 lines): trace up to 3 highest-risk public/entry functions by control-flow complexity, external-state access, or recent change.

When a module exceeds its budget, list the untraced public functions in the module's Scope note. A skipped helper can still be traced if a selected public path calls into it.

## Step 3: Record Findings Per Module

Apply the standard four-field format (Premises→Trace→Divergence→Remedy). Tag each finding with:
- Module path
- Risk code (L1–L9 or Cx)
- Severity (Critical / Warning / Suggestion)

## Step 4: Aggregate Findings

```
Total findings: [N]
  🔴 Critical: [n] in [module list]
  🟡 Warning:  [n] in [module list]
  🟢 Suggestion: [n]

By risk code:
  L1: [n findings, modules affected]
  ...
```

## Step 5: Compute Scores

**Per-module Logic Score:** Apply standard formula (100 − deductions) to each module.

**Overall Logic Score:** Line-weighted average:
`sum(module_score × (module_line_count / total_lines_reviewed))`

A small perfect module must not mask a large Critical-heavy one.

## Step 6: Identify Systemic Patterns

**Repeated L-codes across modules:** L1 in 4 modules = codebase-wide naming convention problem; remedy is a linting rule, not 4 individual fixes.

**Architectural enablers:**
- Heavy global state → enables L7 and L4 across the codebase
- Deep callee chains with no defensive checks → enables L6 propagation
- No type annotations in a dynamic language → makes L2 invisible until runtime

**Risk concentration:** Criticals clustered in one module → prioritized attention or refactoring candidate.

## Step 7: Output the Health Report

Layout (per `../_shared/report-template.md` + logic-health additions in `SKILL.md`):
1. Standard header with overall Logic Score
2. Full Findings section (by severity, then module)
3. Standard Summary (2–3 sentences)
4. Module Breakdown table (after Summary)
5. Systemic Patterns section (after Summary)
6. Recommended Priority Order — top 3–5 actions by impact (after Summary)
