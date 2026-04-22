---
name: logic-health
description: >
  Logic health dashboard that sweeps multiple modules or an entire codebase
  with semi-formal tracing to produce a scored overview of logic correctness
  — identifying risk hotspots and systemic patterns across the whole project.
  Use this skill proactively before any release, deploy, or major code review
  milestone: if the user mentions "shipping soon", "about to release",
  "onboarding to this codebase", or "where should I focus testing effort",
  this skill is almost always the right call. Strong trigger phrases: "logic
  health check", "audit the whole codebase", "audit the entire X module",
  "give me a logic overview before we ship", "what are the risk areas in
  this project", "comprehensive logic audit", "sweep the whole backend",
  "assess the logic quality of this repo", "what's the overall correctness
  picture", "I'm onboarding and want to know the risk areas", "full logic
  review of src/". Also trigger when the user mentions auditing multiple
  named modules together, or wants a priority list of where to focus effort.
  The key signal is SCOPE: the user is asking about a codebase, a directory,
  or multiple modules — not a single function or file. Do NOT trigger for:
  reviewing a single function, file, or specific PR (use logic-review),
  explaining one execution path (use logic-explain), comparing two versions
  (use logic-diff), or locating one specific failing test (use logic-locate).
---

# Logic-Lens — Logic Health

## Setup
1. Read `../_shared/common.md` for the Iron Law, Report Template, and Logic Score.
2. Read `../_shared/logic-risks.md` for all L1–L6 risk definitions.
3. Read `../_shared/semiformal-guide.md` for semi-formal tracing methodology.
4. Read `logic-health-guide.md` in this directory for the aggregation process.

## Process

**Scope:** If no scope is specified, analyze the top-level modules of the repository. Apply the Scope Management prioritization from `common.md`: user-flagged modules first, then external-state surfaces, then recently changed files (`git log --since=30.days --name-only`). State the covered scope at the top of the report.

1. Enumerate the modules/files to cover and plan the sweep (Step 1 of the guide)
2. Run a focused logic-review pass over each module, applying semi-formal tracing to the highest-risk functions (Steps 2–3)
3. Aggregate findings across modules: count by severity and L-code (Step 4)
4. Compute the overall Logic Score and per-module sub-scores (Step 5)
5. Identify systemic patterns: if L1 appears in 4 modules, that is a codebase-wide naming convention problem, not 4 isolated bugs (Step 6)
6. Output using the Health Report Template (Step 7)

**Mode line in report:** `Logic Health`

**Health Report Template additions:**

After the standard Findings section, include:

```
## Module Breakdown

| Module | Score | Critical | Warning | Suggestion | Top Risk |
|--------|-------|----------|---------|------------|----------|
| auth/  | 72    | 1        | 2       | 0          | L6       |
| api/   | 91    | 0        | 1       | 2          | L3       |
...

## Systemic Patterns
[Risk codes that appear in 3+ modules, indicating a codebase-wide habit rather than an isolated bug]

## Recommended Priority Order
1. [Most critical single finding]
2. [Systemic pattern with widest impact]
3. [Quick wins: suggestions that prevent future Criticals]
```
