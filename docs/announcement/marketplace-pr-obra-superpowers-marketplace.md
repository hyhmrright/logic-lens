# PR Draft: obra/superpowers-marketplace

## Status

CONFIRMED EXISTS (substituted for non-existent davila7/claude-code-plugin-marketplace).
879 stars, updated 2026-04-25. Accepts PRs — all 10 open PRs follow a consistent format.

## File to Modify

`.claude-plugin/marketplace.json` — append a new entry to the `"plugins"` array.

---

## Exact JSON to Add

Append after the last entry in the `"plugins"` array (before the closing `]`):

```json
    {
      "name": "logic-lens",
      "source": {
        "source": "url",
        "url": "https://github.com/hyhmrright/logic-lens.git"
      },
      "description": "Logic-first code review using semi-formal execution tracing. Surfaces behavioral bugs, type contract breaches, boundary blindspots, and interprocedural semantic mismatches — the logic errors that cause production incidents in syntax-clean code. Six skills: /logic-review, /logic-explain, /logic-diff, /logic-locate, /logic-health, /logic-fix-all.",
      "version": "0.5.0",
      "strict": true
    }
```

Current last entry is `"double-shot-latte"`. Add a comma after its closing `}` and paste the block above.

---

## PR Title

```
feat: add logic-lens plugin — logic-first code review via semi-formal execution tracing
```

---

## PR Body

```markdown
## Summary

- Adds [logic-lens](https://github.com/hyhmrright/logic-lens) (v0.5.0) to the marketplace
- Logic-Lens is a logic-first code review plugin that surfaces behavioral bugs linters and type checkers miss by tracing execution paths semi-formally

## Plugin details

- **Name:** `logic-lens`
- **Source:** https://github.com/hyhmrright/logic-lens
- **Version:** 0.5.0
- **Description:** Logic-first code review using semi-formal execution tracing. Surfaces behavioral bugs, type contract breaches, boundary blindspots, and interprocedural semantic mismatches — the logic errors that cause production incidents in syntax-clean code. Six skills: /logic-review, /logic-explain, /logic-diff, /logic-locate, /logic-health, /logic-fix-all.

## Key features

- Six slash-commands covering review, explanation, diff analysis, bug location, codebase health, and autonomous repo-wide fix
- Structured L1–L6 risk taxonomy (Shadow Override, Type Contract Breach, Boundary Blindspot, State Mutation Hazard, Control Flow Escape, Callee Contract Mismatch) with optional project-specific custom codes
- Semi-formal execution tracing methodology (not AST linting — behavioral path analysis)
- Compatible with Claude Code, Codex CLI, and Gemini CLI
- 58/58 eval assertions passing on Opus 4.7 + Sonnet 4.6 — v0.5.0 release: https://github.com/hyhmrright/logic-lens/releases/tag/v0.5.0
- MIT licensed, no telemetry, no network calls except to Anthropic API
```

---

## Prerequisites / Gotchas

- **No CONTRIBUTING.md found** in the repo; infer format from open PRs (all follow `feat: add <name> plugin` title + Summary/Plugin-details body).
- **`"strict": true`** is set on every existing entry — include it.
- **Version must match `.claude-plugin/plugin.json`**: Logic-Lens has 0.5.0 in all metadata files — consistent.
- **The marketplace owner (Jesse Vincent / obra) has not merged any PRs yet** — all 10 visible PRs are open. This is the biggest risk: the marketplace may be semi-abandoned for third-party plugins, or Jesse may be reviewing slowly. Check PR age before deciding priority.
- The `"source"` field uses `{"source": "url", "url": "...git"}` format — match exactly.

---

## Maintainer Responsiveness Signal

- 10 open PRs, 0 merged community PRs visible in the API
- Owner's own commits keep the repo updated (last push 2026-04-25)
- This is a curated personal marketplace — third-party plugins may require direct outreach to obra
- Recommended: open the PR AND ping Jesse via a GitHub issue or the Superpowers Discussions tab
