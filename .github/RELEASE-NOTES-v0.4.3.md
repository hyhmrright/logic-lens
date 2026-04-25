# Logic-Lens v0.4.3 — Community & Outreach Pack

## TL;DR

No skill / guide / code changes. This release gets the repository ready for public growth:

- **GitHub community health files**: SECURITY policy, Code of Conduct, issue templates (bug + feature), PR template, FUNDING placeholder.
- **Repository hardening**: `main` branch protected (no force-push / no delete / PR required / conversation resolution required), Discussions enabled, 15 SEO topics set.
- **Outreach roadmap + draft posts**: `docs/MARKETING-ROADMAP.md` + ready-to-send drafts for HN Show HN, r/ClaudeAI, Twitter/X thread, and third-party marketplace submission.
- **README upgrade**: added status badges (release, last-commit, issues, PRs, verification-58/58, forks).

One finding from a Phase 4 POC run_loop is recorded in `skills-workspace/phase4-poc/` — it exposes a recall=0% in the current hand-tuned SKILL.md descriptions. That will be addressed in v0.5.0 with data-driven description optimization; v0.4.3 ships the groundwork.

## 🎯 What's New

### GitHub infrastructure

- `SECURITY.md` — private vulnerability reporting (GitHub Security Advisories + email).
- `CODE_OF_CONDUCT.md` — Contributor Covenant v2.1.
- `.github/ISSUE_TEMPLATE/bug_report.yml` — structured bug report with skill picker, version, host-env.
- `.github/ISSUE_TEMPLATE/feature_request.yml` — structured feature request with contribution intent checkboxes.
- `.github/ISSUE_TEMPLATE/config.yml` — blank issues disabled; links to Discussions + Security Advisory.
- `.github/PULL_REQUEST_TEMPLATE.md` — scope checklist + verification requirements + breaking-change gate.
- `.github/FUNDING.yml` — placeholder until a sponsor channel is live.

### Outreach assets

- `docs/MARKETING-ROADMAP.md` — four-layer plan (repo infra → marketplace submissions → technical community → content marketing) with ownership and success criteria per layer.
- `docs/announcement/hn-show-hn.md` — ready-to-paste Show HN draft.
- `docs/announcement/reddit-claudeai.md` — ready-to-paste r/ClaudeAI post.
- `docs/announcement/twitter-thread.md` — 7-tweet thread draft.
- `docs/announcement/marketplace-submission.md` — template PR body for third-party Claude plugin marketplaces.

### README

- New badges row: release tag, last-commit date, issue count, PR count, verification score, forks.
- Existing badges (version, license, Claude Code / Codex / Gemini compat) refreshed to 0.4.3.

### Phase 4 POC (internal note)

`scripts/run-trigger-evals.sh review` ran successfully end-to-end on sonnet-4-6 with 2 iterations, 8-item held-out test:

- starting_score: 4/8
- best_score: 4/8 (no improvement in 2 iterations)
- **diagnosis**: recall = 0% on positive cases — the hand-tuned SCOPE HARD RULE is so tight that genuine review requests (vague suspicion + inline code + Chinese prompts) fail to trigger.

Raw log in `skills-workspace/phase4-poc/`. **This is the target for v0.5.0**: run a full `run_loop.py` × 6 skills and let data drive description revision.

## 💥 Breaking Changes

None.

## 📦 Upgrade

```bash
/plugin update logic-lens
# or:
cd /path/to/logic-lens && git pull && bash hooks/session-start
```

🤖 Generated with [Claude Code](https://claude.com/claude-code)
