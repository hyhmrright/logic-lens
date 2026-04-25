# Template: submitting Logic-Lens to a third-party Claude plugin marketplace

Use this template when opening a PR to a marketplace repo (e.g. `davila7/claude-code-plugin-marketplace`, `hesreallyhim/awesome-claude-code`, or similar).

## Typical PR title

```
Add Logic-Lens — semi-formal logic bug review (6 skills)
```

## PR body

```
## Adding Logic-Lens

[Logic-Lens](https://github.com/hyhmrright/logic-lens) is a Claude Code plugin that ships six skills for behavioral / logic code review using semi-formal execution tracing (Premises → Trace → Divergence → Remedy). Also installable in Codex CLI and Gemini CLI.

### Skills

| Command | Purpose |
|---|---|
| `/logic-review` | Find logic bugs in a single file or function |
| `/logic-explain` | Step-by-step execution trace when behavior surprises |
| `/logic-diff` | Semantic equivalence check between two code versions |
| `/logic-locate` | Root-cause a failing test / stack trace / wrong output |
| `/logic-health` | Scored logic health dashboard for a module or repo |
| `/logic-fix-all` | Autonomous audit-and-fix pipeline, iterative until clean |

### Verification

v0.4.x: 58/58 assertions pass across 15 cases (EN + 中文 + DEEP / cross-file / async / race). Validated on both Opus 4.7 and Sonnet 4.6. Eval data in `evals/v2/` and grader in `scripts/grade-iteration.py`.

### Metadata for your marketplace.json (adjust to your schema)

\`\`\`json
{
  "name": "logic-lens",
  "version": "0.4.2",
  "description": "Semi-formal logic bug review — 6 skills that find bugs linters (and tests) miss",
  "source": "https://github.com/hyhmrright/logic-lens",
  "license": "MIT",
  "author": "hyhmrright",
  "keywords": ["code-review", "logic", "debugging", "static-analysis", "claude-code", "bug-detection"],
  "category": "code-review"
}
\`\`\`

### Release link

https://github.com/hyhmrright/logic-lens/releases/tag/v0.4.2

Happy to adjust the description or categorization to match your marketplace conventions.
```

## Marketplaces to prioritize (P0 first)

1. **`davila7/claude-code-plugin-marketplace`** — schema-based marketplace.json
2. **`hesreallyhim/awesome-claude-code`** — README table entry
3. **`Pi-Cla/awesome-claude-code-skills`** — README entry
4. Any others found via GitHub search: `claude-code marketplace` / `claude plugin registry`

## After merging

- Add the marketplace to `docs/MARKETING-ROADMAP.md`'s tracking list with status and date.
- Check analytics / stars-over-time to see if referrals from that marketplace drive traffic.
- If no traffic in 4 weeks, deprioritize re-submission to similar marketplaces.
