# Logic-Fix-All — Autonomous Audit-and-Fix Guide (Navigation)

This guide drives a full-repository, logic-level, semi-formal tracing pipeline. It orchestrates the other five Logic-Lens skills — **logic-health, logic-review, logic-locate, logic-explain, logic-diff** — and iterates until the codebase is clean.

The only hard interaction point is **Phase 0 (Pre-flight consent)**. After the user approves, the pipeline runs hands-free unless Phase 8 hits the iteration cap and escalates.

This is a **logic** review, not a syntax/style/lint pass. If the user wants formatting or convention fixes, point them at a linter instead.

---

## Pipeline at a glance

```
  Phase 0 — Pre-flight notice & consent gate        ← hard stop, wait for user
     │
  Phase 1 — Scope enumeration (role + risk tier)    ┐
     │                                              │ clarification
  Phase 2 — Health pass (module Logic Score map)    ┘
     │
  Phase 3 — Deep review (per-file semi-formal)      ┐
     │                                              │
  Phase 4 — Fault location (conditional)            │ detail
     │                                              │
  Phase 5 — Path clarification (conditional)        ┘
     │
  Phase 6 — Fix queue assembly (sorted, remedied)   ┐
     │                                              │
  Phase 7 — Apply + verify (logic-diff)             │ action
     │                                              │
  Phase 8 — Iteration loop (until clean or capped)  │
     │                                              │
  Phase 9 — Final Fix Report                        ┘
```

## Where to find each phase

Detailed execution for every phase is split into three sibling files so that a reader can jump to the relevant stage without loading the whole 600-line guide.

| Phases | File | Scope |
|--------|------|-------|
| **0, 1, 2** | [`guide-phases-0-2-consent-scope-health.md`](./guide-phases-0-2-consent-scope-health.md) | Pre-flight notice + user consent; full-repo file walk classified by role (source / config / constraint / doc) and risk tier (High / Medium / Low); module-level Logic Score map before any deep review. |
| **3, 4, 5** | [`guide-phases-3-5-review-locate-clarify.md`](./guide-phases-3-5-review-locate-clarify.md) | Per-file deep review producing full Premises → Trace → Divergence findings (Phase 3); conditional fault localization when a concrete failure exists (Phase 4); conditional path clarification when a finding's reasoning chain is unclear (Phase 5). |
| **6, 7, 8, 9** | [`guide-phases-6-9-fix-iterate-report.md`](./guide-phases-6-9-fix-iterate-report.md) | Fix queue assembly sorted by severity with Minimal/Targeted/Justified remedies (Phase 6); apply + verify each fix via logic-diff, revert on regression, retry up to 3× (Phase 7); iteration loop — re-run health + review on modified files and their consumers, Critical loops without cap, Warning/Suggestion capped by `fix_all.max_iterations` (Phase 8); Final Fix Report with per-role findings, skill invocation counts, iteration history (Phase 9). |

## Shared context (read first)

Before following any phase file:
1. `../_shared/common.md` — language hard constraint (§1), Iron Law (§2), Report Template pointer (§4), Mode-specific header variants (§5), Logic Score (§6), Confidence Rubric (§7), Scope Management (§9), Remedy Discipline (§10), Fallback Behavior (§11), `.logic-lens.yaml` config matrix (§12).
2. `../_shared/logic-risks.md` — L1–L6 definitions and detection patterns.
3. `../_shared/semiformal-guide.md` + `../_shared/semiformal-checklist.md` — reasoning methodology + Premises Construction Checklist.
4. `../_shared/report-template.md` — Report Template single source with English and Chinese layouts + the "no bugs found" rules.

## Running this skill in a non-git or offline repo

Phase 1 uses `git ls-files` as the default enumerator for speed. If `.git` is absent, fall back to a recursive file walk over the project root with the same ignore patterns (`.logic-lens.yaml` `ignore:` + the built-in build-artifact list). Report the fallback in the Scope table of the Final Report so the user knows the enumeration method.

## When to hand control back to the user

Three points in the pipeline require user interaction:
1. **Phase 0** — always. No scanning or editing before explicit consent.
2. **Phase 8 iteration cap** — when `fix_all.max_iterations` Warning/Suggestion rounds have run and non-Critical findings remain, ask whether to continue or stop. Three consecutive "continue"s hit a hard ceiling and the pipeline stops with the unresolved findings recorded.
3. **Phase 6 constraint-vs-code tie** — when a finding could be fixed by editing either the code or a behavioral doc/config and neither side is clearly authoritative, ask which to treat as the spec.

All other decision points are internal to the pipeline and do not interrupt the user.

## Output format

The Fix Report layout is defined in `SKILL.md`: header fields, then the standard Findings + Summary, then the fix-all extensions (Scope / Skill Invocations / Iteration History / Fix Log / Resolved by Clarification / Unresolved Findings) appended after Summary per report-template.md Rule 4. Render it according to the language rule in `common.md` §1.
