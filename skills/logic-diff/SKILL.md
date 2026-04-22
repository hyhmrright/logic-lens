---
name: logic-diff
description: >
  Semantic equivalence analysis that determines whether two code versions,
  patches, or implementations produce identical behavior — using semi-formal
  execution tracing rather than textual diff. Use this skill proactively
  whenever a refactor, rewrite, or migration is shared: users almost always
  want implicit confirmation that nothing broke, even if they only ask "does
  this look right?" or share a PR without an explicit equivalence question.
  Strong trigger phrases: "did I break anything in this refactor", "is this
  semantically equivalent", "are these two implementations equivalent", "does
  my rewrite produce the same output", "verify this migration is a drop-in
  replacement", "check my refactor", "same behavior after the change?",
  "compare these two versions for correctness", "did this change alter any
  behavior". Also trigger when the user migrates between libraries or
  languages ("I switched from lodash to native JS — same results?"), or when
  they want to confirm a bug fix doesn't regress non-buggy inputs. Do NOT
  trigger for: reviewing a single version for bugs (use logic-review),
  explaining what one piece of code does (use logic-explain), locating a
  failing test root cause (use logic-locate), or questions about which
  version is better-designed or faster.
---

# Logic-Lens — Semantic Diff

## Setup
1. Read `../_shared/common.md` for the Iron Law and Report Template.
2. Read `../_shared/logic-risks.md` for risk codes relevant to semantic divergences.
3. Read `../_shared/semiformal-guide.md` for semi-formal tracing methodology.
4. Read `logic-diff-guide.md` in this directory for the comparison process.

## Process

**Scope:** The user must provide two code versions (A and B). Ask if not provided. Clarify which test cases or scenarios to compare across (or derive from the code if obvious).

1. Identify the scope: what is the shared specification both versions are supposed to implement? (Step 1 of the guide)
2. Build premises for Version A and Version B independently (Step 2)
3. Trace both versions for each relevant scenario: common case, boundary cases, error cases (Steps 3–4)
4. Identify semantic divergences: points where A and B produce different behavior for the same input (Step 5)
5. Classify each divergence: is it a bug in one version, or an intentional behavioral change? (Step 6)
6. Output using Report Template with equivalence verdict (Step 7)

**Mode line in report:** `Semantic Diff`

**Verdict options:**
- ✅ Semantically Equivalent — no behavioral divergence found under traced scenarios
- ⚠️ Conditionally Equivalent — equivalent for common cases; diverges under [specific condition]
- ❌ Semantically Divergent — confirmed behavioral difference at [location]
