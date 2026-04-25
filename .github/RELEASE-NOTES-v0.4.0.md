# Logic-Lens v0.4.0 — Architecture Refactor · Language Hardening · SCOPE HARD RULE

## TL;DR

A systems-level refactor of all 6 `logic-*` skills: outputs now strictly follow the user's input language, trigger boundaries are enforced by a SCOPE HARD RULE per skill, and the shared framework has been consolidated to single-source files. `_shared/common.md` becomes a 12-section spec; 6 `SKILL.md` files are tightened; an 18-case evaluation suite now includes Chinese prompts with mandatory language assertions.

## 🎯 Core Improvements

### 1. Language Hard Constraint (HIGHEST PRIORITY)

`common.md` §1 establishes a language-detection rule: if ≥50% of the user message is CJK, respond entirely in Chinese — including every section header, every finding field label (Premises / Trace / Divergence / Remedy → 前提 / 追踪 / 偏差 / 修复), and Summary prose. A full 16-item English↔Chinese header map is embedded. No more mixed-language reports.

### 2. SCOPE HARD RULE — Trigger Precision

Every `SKILL.md` description now embeds a hard routing rule:

| User context | Skill to trigger |
|---|---|
| Single file / single function with suspicion | `logic-review` |
| Directory / module / repo-wide scope | `logic-health` |
| Confirmed failure (stack trace / failing test / wrong value) | `logic-locate` |
| Two versions to compare | `logic-diff` |
| "Why does this code behave this way?" | `logic-explain` |
| Repo-wide autonomous audit-and-fix | `logic-fix-all` |

All six "Use this skill proactively whenever..." phrasings were removed to stop over-eager triggering.

### 3. Architecture Deduplication (Single Source of Truth)

- **Iron Law** consolidated into `common.md` §2; six guides now reference it.
- **Report Template** extracted to `_shared/report-template.md` (English + Chinese layouts + 5 rendering rules); no longer duplicated across `common.md` / `logic-health/SKILL.md` / `logic-fix-all/SKILL.md`.
- **Premises Construction Checklist** extracted to `_shared/semiformal-checklist.md`; `review` / `explain` / `diff` guides reference it instead of re-listing.
- **Confidence Rubric** unified (`common.md` §7): one High/Medium/Low definition shared across skills, with mode-specific header variants in §5.
- **Remedy Discipline** (§10) now enforces paste-ready remedies (diff or code block); no more prose-style "add validation" weak suggestions.

### 4. SKILL.md Tightening

- `description` fields shrunk from ~25 lines to ≤12 lines each.
- A new Process Step 0 — language detection + scope routing — prepends every skill.
- `logic-fix-all/SKILL.md` reduced from 116 to 90 lines; guide details pushed down to phase files.

### 5. Extended Evaluation Suite

- `evals/v2/evals-v2.json`: 18 cases = 6 EN (carry-over) + 6 Chinese (with mandatory language assertions) + 6 DEEP (cross-file, boundary, systemic patterns).
- `evals/v2/trigger-evals-*.json` × 6: 120 cases total (10 positive + 10 near-miss negative per skill) — the surface for description-optimization via `scripts/run-trigger-evals.sh`.

## 📊 Verification Data (iteration-2, 2026-04-25)

| Metric | v0.3.0 | v0.4.0 | Δ |
|---|---|---|---|
| with_skill execution completion | 3/6 | **9/9** | **+50 pp** |
| Assertion pass_rate | 1.00 (n=3) | **1.000 (38/38)** | sample widened |
| Chinese-language assertion | 0/0 (no samples) | **6/6 = 100%** | from nothing to full |

`logic-diff` / `logic-health` / `logic-fix-all` all returned `null` under v0.3.0's iteration-1 baseline (with_skill did not complete). Under v0.4.0 all three produce complete mode-specific reports (Verdict / Module Breakdown / Fix Log before/after) and pass every assertion.

Raw evidence: `skills-workspace/iteration-2/summary.json` + per-case `grading.json` + `skills-workspace/COMPARISON.md`.

## 💥 Breaking Changes

None. All refactors preserve public skill command names (`/logic-review`, etc.) and trigger words. `.logic-lens.yaml` schema is backwards-compatible.

## ⚠️ Known Limitations (deferred to v0.5.0)

- **Phase 4 trigger-description optimization (`scripts/run-trigger-evals.sh`)** — not yet executed. The 6 SKILL.md descriptions are hand-tuned against the SCOPE HARD RULE rubric, not data-optimized via `run_loop.py`. The 120-case trigger eval set is ready (`evals/v2/trigger-evals-*.json`).
- **`pr-review-toolkit:code-reviewer` agent** has not run a full-diff audit; recommend executing before merging to main downstream.
- **6 DEEP cases** not part of this batch — shipped separately in v0.4.1.

## 📦 Upgrade

Claude Code:
```bash
/plugin update logic-lens
```

Manual clone:
```bash
cd /path/to/logic-lens
git pull
bash hooks/session-start  # reinstall command wrappers
```

## 🙏 Credits

Refactor driven end-to-end by Claude Opus 4.7 (1M context) — audit report, architecture proposal, SKILL.md tightening, eval design, CHANGELOG and release notes all machine-generated, human-reviewed.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
