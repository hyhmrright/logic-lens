---
name: logic-diff
description: >
  Compare two code versions for semantic equivalence via semi-formal tracing
  of both versions side-by-side. Trigger when the user shares a refactor,
  rewrite, migration, or A/B implementation and wants to confirm behavior
  is unchanged — "did I break anything", "is this equivalent",
  "are these equivalent", "semantically equivalent", "are these two
  implementations semantically equivalent", "check my refactor",
  "same behavior after the change?", "does my rewrite produce
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

Use lazy loading per `../_shared/common.md` §13:
1. Read `../_shared/common.md` only for language, Iron Law, Verdict header, scope routing, Remedy discipline, config fields, and loading budget.
2. Read only the relevant step in `logic-diff-guide.md` as you reach it.
3. Load `../_shared/logic-risks.md`, `../_shared/semiformal-guide.md`, `../_shared/semiformal-checklist.md`, and `../_shared/report-template.md` on demand when the current step needs them.

## Process

**Step 0. Language + scope routing.** Detect language per `common.md` §1. Confirm two versions are provided. If only one version, switch to logic-review.

**Step 1. Identify the shared specification** (guide Step 1) — what inputs should both versions handle; what outputs/side effects are expected. If the user states the refactor intentionally changed behavior in a specific area (e.g., "I changed the error path to raise instead of returning None"), record that as a **declared spec change** and treat divergences within that area as expected. Flag only divergences outside the declared change as findings.

**Step 2. Build independent premises for each version** (guide Step 2) — apply the Premises Construction Checklist to Version A and Version B separately.

**Step 3. Trace both versions for the common case** (guide Step 3) — parallel trace, same input, note the first divergence if any.

**Step 4. Trace boundary cases** (guide Step 4) — empty/null/zero, max/min, error inputs, first/last of collections. Start with at most three highest-risk boundary scenarios unless the user asks for exhaustive equivalence or the shared specification requires more.

**Step 5. Identify and classify semantic divergences** (guide Step 5) — each divergence is a finding with Premises → Trace → Divergence → Trigger → Remedy and an L-code.

**Step 6. Equivalence verdict** (guide Step 6) — one of: `✅ Semantically Equivalent`, `⚠️ Conditionally Equivalent` (state the condition precisely), `❌ Semantically Divergent`.

**Step 7. Output** (guide Step 7) — Report Template with the Verdict header per `common.md` §5; localize headers if the user wrote in Chinese. **Format is mandatory even for trivially short snippets: every divergence finding MUST use the five labeled fields (Premises / Trace / Divergence / Trigger / Remedy); never substitute with a plain paragraph or table.**

**Mode line in report:** `Semantic Diff` (Chinese: `语义对比`).
