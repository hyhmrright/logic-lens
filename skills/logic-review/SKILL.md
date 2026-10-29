---
name: logic-review
description: >
  Find behavioral bugs in a file or function by investigating its contracts,
  callers, dependencies, and execution paths. Trigger for "review this",
  "check this function", "find bugs", or "tests pass but production fails"
  without an already confirmed failure. A file is the review target, not a
  boundary on supporting evidence. For directory-wide surveys use logic-health;
  for a confirmed failure use logic-locate; for two versions use logic-diff.
  Do NOT trigger for: style/formatting, standalone security or performance audits,
  test authoring without a review request, or architecture-only questions.
---

# Logic-Lens — Logic Review

Find observable violations of supported behavior. Investigate before rendering a
report: a familiar pattern, missing guard, or uncertain contract is a lead, not a bug.

## Setup

Use lazy loading from `../_shared/common.md` §13. Read its language, Iron Law,
headers/score, scope, confidence, remedy, and project-config rules; read the active
step of `logic-review-guide.md` as needed. Load `semiformal-checklist.md` when building
premises, `semiformal-guide.md` for trace mechanics, `logic-risks.md` when classifying
confirmed causes, and `report-template.md` only when rendering output.

## Process

1. **Establish an obligation** (guide Step 1). Separate facts, sourced requirements
   and unknowns. Orient on the main input/state routes and supported outcomes.
2. **Map and select paths** (guide Step 2). Identify consequential operations and
   their consumers; resolve hidden conditions before ranking a small worklist.
3. **Run distinguishing checks** (guide Step 3). Test supported relationships using
   effective implementation conditions and controls. Reconsider remaining paths
   after confirmation and before ending discovery.
4. **Challenge the violation** (guide Step 4). Establish reachability, exact-path
   defenses and the smallest observable consequence; preserve unresolved leads.
5. **Preserve probe evidence** (guide Step 5). Probe real code during discovery when
   feasible. Record oracle, runtime, result and limitations. Defer implementation
   and broad remedy regression to a separately requested fix task.
6. **Prepare findings** (guide Step 6). Deduplicate causes, classify confirmed defects
   and give a minimal concrete remedy with its verification limits.
7. **Report once** (guide Step 7). Use shared localized Iron Law fields and scope/score
   rules. Expose uncovered obligations without treating them as confirmed defects.

**Mode line:** `Logic Review` (Chinese: `逻辑审查`). Route whole-directory requests
to logic-health; supporting caller/callee/configuration files remain available to review.
