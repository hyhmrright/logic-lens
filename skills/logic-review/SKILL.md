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
2. **Map behavior boundaries** (guide Step 2). Connect each important promise to
   its producer, representations, alternate supported entries, and first consumer.
   Follow dependencies to answer specific questions; preserve uncovered routes.
3. **Search for distinguishing counterexamples** (guide Step 3). Compare supported
   representations, routes, and operation sequences against the same obligation.
   Choose a small experiment or read whose outcomes separate competing explanations.
   Keep a hypothesis ledger; use L1–L9 as a backstop.
4. **Trace and challenge** (guide Step 4). Trace concrete values and observable
   consequences; search for defenses covering that exact path. Keep impact,
   confidence, and investigation status separate. Partial defenses require investigation.
5. **Probe early and verify** (guide Step 5). Use bounded real-code experiments
   during discovery when they resolve uncertainty; do not wait for a finished proof.
   For Critical/Warning candidates, attempt verification when feasible. A failure
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
