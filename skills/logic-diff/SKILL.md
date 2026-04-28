---
name: logic-diff
description: >
  Compare two code versions for semantic equivalence via semi-formal tracing
  of both versions side-by-side. Trigger when the user shares a refactor,
  rewrite, migration, or A/B implementation and wants to confirm behavior
  is unchanged — "did I break anything", "is this equivalent", "check my
  refactor", "same behavior after the change?", "does my rewrite produce
  the same output", "switched from X to Y — same results?".
  SCOPE HARD RULE: requires two code versions (A and B). A single version
  for bug-finding uses logic-review; one version + a failing test uses
  logic-locate; explaining what one piece of code does uses logic-explain;
  codebase audit uses logic-health.
  Do NOT trigger for: single-version review, performance comparison,
  design-quality comparison, or "which is better-written" questions.
---

# Logic-Lens — Semantic Diff

## Setup

Read in this order:
1. `../_shared/common.md` — language rule, Iron Law, Report Template, Verdict header (see §5), Remedy discipline.
2. `../_shared/logic-risks.md` — L1–L9 definitions (used to classify divergences).
3. `../_shared/semiformal-guide.md` — tracing methodology and Premises Construction Checklist.
4. `logic-diff-guide.md` — comparison process.

## Process

**Step 0. Language + scope routing.** Detect language per `common.md` §1. Confirm two versions are provided. If only one version, switch to logic-review.

**Step 1. Identify the shared specification** (guide Step 1) — what inputs should both versions handle; what outputs/side effects are expected.

**Step 2. Build independent premises for each version** (guide Step 2) — apply the Premises Construction Checklist to Version A and Version B separately.

**Step 3. Trace both versions for the common case** (guide Step 3) — parallel trace, same input, note the first divergence if any.

**Step 4. Trace boundary cases** (guide Step 4) — empty/null/zero, max/min, error inputs, first/last of collections.

**Step 5. Identify and classify semantic divergences** (guide Step 5) — each divergence is a finding with Premises → Trace → Divergence → Remedy and an L-code.

**Step 6. Equivalence verdict** (guide Step 6) — one of: `✅ Semantically Equivalent`, `⚠️ Conditionally Equivalent` (state the condition precisely), `❌ Semantically Divergent`.

**Step 7. Output** (guide Step 7) — Report Template with the Verdict header per `common.md` §5; localize headers if the user wrote in Chinese.

**Mode line in report:** `Semantic Diff` (Chinese: `语义对比`).
