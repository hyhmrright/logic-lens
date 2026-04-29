# Logic-Lens — Logic Fix All — Guide (Navigation)

This guide drives a full-repository logic-level semi-formal tracing pipeline, orchestrating **logic-health → logic-review → logic-locate → logic-explain → logic-diff** until the codebase is clean.

The only hard interaction point is **Phase 0 (consent gate)**. After approval, the pipeline runs hands-free unless Phase 8 hits the iteration cap.

This is a **logic** review, not a syntax/style/lint pass.

---

## Pipeline at a glance

```
  Phase 0 — Pre-flight notice & consent gate        ← hard stop, wait for user
  Phase 1 — Scope enumeration (role + risk tier)
  Phase 2 — Health pass (module Logic Score map)
  Phase 3 — Deep review (per-file semi-formal)
  Phase 4 — Fault location (conditional)
  Phase 5 — Path clarification (conditional)
  Phase 6 — Fix queue assembly (sorted, remedied)
  Phase 7 — Apply + verify (logic-diff)
  Phase 8 — Iteration loop (until clean or capped)
  Phase 9 — Final Fix Report
```

## Where to find each phase

| Phases | File |
|--------|------|
| **0, 1, 2** | `guide-phases-0-2-consent-scope-health.md` — Pre-flight consent; full-repo file walk by role and risk tier; module Logic Score map. |
| **3, 4, 5** | `guide-phases-3-5-review-locate-clarify.md` — Per-file Premises→Trace→Divergence (Phase 3); conditional fault localization (Phase 4); conditional path clarification (Phase 5). |
| **6, 7, 8, 9** | `guide-phases-6-9-fix-iterate-report.md` — Fix queue sorted by severity (Phase 6); apply + verify via logic-diff, revert on regression, retry ≤3× (Phase 7); iteration loop with state tracking (Phase 8); Final Fix Report (Phase 9). |

## Required reading before Phase 0

Read end-to-end before starting. Later phases reference fields defined in earlier phases (Phase 6 reads severity tags from Phase 3; Phase 8 reads the unresolved-finding signature from Phase 7d).

**Stage A — shared framework (in order):**
1. `../_shared/common.md`
2. `../_shared/logic-risks.md`
3. `../_shared/semiformal-guide.md` + `../_shared/semiformal-checklist.md`
4. `../_shared/report-template.md`

**Stage B — all three phase files end-to-end (BEFORE Phase 0, not just-in-time):**
- `guide-phases-0-2-consent-scope-health.md`
- `guide-phases-3-5-review-locate-clarify.md`
- `guide-phases-6-9-fix-iterate-report.md`

## Running without git

Phase 1 uses `git ls-files` as the default enumerator. If `.git` is absent, fall back to a recursive file walk with the same ignore patterns. Report the fallback in the Scope table.

## When to hand control back to the user

1. **Phase 0** — always, before any scanning or editing.
2. **Phase 8 iteration cap** — when `fix_all.max_iterations` Warning/Suggestion rounds have run with remaining non-Critical findings. Three consecutive "continue"s hit a hard ceiling.
3. **Phase 6 constraint-vs-code tie** — when a finding could be fixed by editing either the code or a behavioral doc/config and neither side is clearly authoritative.

## Output format

Fix Report layout: header fields → Findings + Summary → fix-all extensions (Scope / Skill Invocations / Iteration History / Fix Log / Resolved by Clarification / Unresolved Findings) after Summary. Render per `common.md` §1 language rule.
