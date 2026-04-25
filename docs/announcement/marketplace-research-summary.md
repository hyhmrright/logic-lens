# Marketplace Research Summary — Logic-Lens v0.5.0

Research date: 2026-04-25

## Results Table

| Marketplace | Exists? | Substituted from | Stars | Submission Format | Merged-PR Cadence | Priority | Exact Next Step |
|---|---|---|---|---|---|---|---|
| `hesreallyhim/awesome-claude-code` | Yes | (original target) | ~high | GitHub **Web UI issue form only** — no PRs, no `gh` CLI | Multiple merges/week (bot-automated) | **P0** | Open https://github.com/hesreallyhim/awesome-claude-code/issues/new?template=recommend-resource.yml in browser; fill all fields per draft |
| `obra/superpowers-marketplace` | Yes | davila7/claude-code-plugin-marketplace | 879 | PR adding JSON entry to `.claude-plugin/marketplace.json` `"plugins"` array | 0 community PRs merged (10 open) — owner merges own commits only | **P1** | Fork repo, append JSON block to `.claude-plugin/marketplace.json`, open PR with title `feat: add logic-lens plugin — ...` |
| `helloianneo/awesome-claude-code-skills` | Yes | Pi-Cla/awesome-claude-code-skills | 91 | PR adding one table row to `README.md` `## 代码质量` section | No visible merged PRs — solo-maintained, last push 2026-04-23 | **P2** | Fork repo, add table row per draft, open PR with title `feat: 添加 Logic-Lens` |

## Priority Rationale

**P0 — hesreallyhim/awesome-claude-code**: Highest reach by far, bot-automated pipeline means fast turnaround once the maintainer approves. The issue-only process is more friction but the payoff is proportional. Caveat: maintainer is selective; strong validation evidence required.

**P1 — obra/superpowers-marketplace**: The marketplace format (JSON entry + `/plugin install` command) is a direct install path for users — high conversion. Risk: no community PRs have been merged yet; may need a direct ping to Jesse Vincent.

**P2 — helloianneo/awesome-claude-code-skills**: Chinese-language audience, lower stars, but actively maintained. Simple table-row PR — lowest effort. Good for visibility in the Chinese Claude Code community.

## Biggest Gotcha

`hesreallyhim/awesome-claude-code` **blocks all `gh` CLI submissions** — the form must be filled in the browser by a human, and the bot permanently bans programmatic bypasses. Do not attempt to automate it.

## Draft File Locations

- `docs/announcement/marketplace-pr-hesreallyhim-awesome-claude-code.md`
- `docs/announcement/marketplace-pr-obra-superpowers-marketplace.md`
- `docs/announcement/marketplace-pr-helloianneo-awesome-claude-code-skills.md`
