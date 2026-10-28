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

1. **Establish behavior** (guide Step 1). Separate observed code facts, required
   behavior with its source, and unverified assumptions. Read actual callers and
   tests; do not use names or the current implementation as the sole correctness oracle.
2. **Map the dependency slice** (guide Step 2). Follow inputs, transformations,
   state owners, configuration, and consumers across files. Bound cost by questions
   answered, preserving unresolved dependencies when the budget expires.
3. **Generate failure hypotheses** (guide Step 3). Start from violated invariants
   and operation sequences, then use L1–L9 as a backstop. Maintain a compact ledger
   with evidence, missing facts, and the next discriminating check.
4. **Trace and challenge** (guide Step 4). Trace concrete values and observable
   consequences; search for defenses covering that exact path. Keep impact,
   confidence, and investigation status separate. Partial defenses require investigation.
5. **Verify experimentally** (guide Step 5). For Critical/Warning candidates, attempt
   bounded experiments against real code when feasible. An experiment that fails
   to reproduce is inconclusive unless it supplies a valid counterexample to the
   finding. Record runtime, setup, assertion source, and fidelity limitations.
6. **Prepare findings and remedies** (guide Step 6). Deduplicate by root cause,
   assign L-codes and severity to supported defects, and verify the proposed remedy
   without changing the user's files during a read-only review.
7. **Report once** (guide Step 7). Preserve the five literal Iron Law fields and
   localized template. Scope includes traced paths and omissions; append unresolved
   investigations after Summary. A score describes confirmed findings within that
   scope, never probability of correctness or permission to ship.

**Mode line:** `Logic Review` (Chinese: `逻辑审查`). Route whole-directory requests
to logic-health; supporting caller/callee/configuration files remain available to review.
