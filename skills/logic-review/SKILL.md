---
name: logic-review
description: >
  Code logic review using semi-formal execution tracing — finds behavioral
  bugs, semantic errors, and runtime failures that linters and syntax
  checkers miss. Use this skill proactively whenever code is shared alongside
  any question about correctness, unexpected behavior, or debugging — even
  if the user doesn't say "review" explicitly. The user sharing code and
  asking "does this look right?", "what do you think?", or just describing
  a symptom is enough. Strong trigger phrases: "review this before I
  merge/ship", "can you check this function", "audit this code", "something
  is wrong but I can't find it", "tests pass but prod fails", "code looks
  fine but the test is failing", "can you look at the logic", "check for
  logic errors", "correctness review", "review this PR for bugs". Also
  trigger when the user describes a behavioral symptom and shares code
  with no explicit request — e.g. "this returns wrong values for negative
  inputs", "users randomly get logged out", "this sometimes gives the wrong
  result". Key disambiguation: use logic-review when there is NO confirmed
  failure yet (the user suspects something is wrong); use logic-locate when
  there IS a concrete failure (stack trace, failing test, specific wrong
  value). Do NOT trigger for: pure style/formatting requests ("reformat to
  PEP 8"), security scanning ("is this vulnerable to CSRF"), performance
  optimization ("this query is slow"), test generation, documentation, or
  architecture/design questions.
---

# Logic-Lens — Logic Review

## Setup
**Shared context (standard for all skills that produce findings):**
1. Read `../_shared/common.md` for the Iron Law, Report Template, and Logic Score.
2. Read `../_shared/logic-risks.md` for L1–L6 risk definitions and detection patterns.
3. Read `../_shared/semiformal-guide.md` for semi-formal reasoning methodology and language-specific notes.

**Skill-specific:**
4. Read `logic-review-guide.md` in this directory for the step-by-step review process.

## Process

**Scope detection:** If the user has not specified which code to review, check for a git diff (`git diff HEAD` or `git diff main`). If no diff is available, ask for a file path or code snippet. If the code exceeds ~150 lines or 5 non-trivial functions, apply the Scope Management prioritization from `common.md` and state the covered scope at the top of the report.

1. Establish the claimed behavior of the code under review (Step 1 of the guide)
2. Build premises for each function/block: name resolution, type contracts, state preconditions (Step 2)
3. Trace execution paths for the normal case, then for each edge case (Steps 3–4)
4. Identify divergences; classify each by risk code L1–L6 (Step 5)
5. Apply Iron Law: every finding must have Premises → Trace → Divergence before Remedy is written (Step 6)
6. Compute Logic Score and output using Report Template (Step 7)

**Mode line in report:** `Logic Review`
