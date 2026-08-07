# Template: submitting Logic-Lens to a third-party Claude plugin marketplace

Generic template for opening a PR to a marketplace repo. For the three verified targets there
are tailored drafts — use those instead: `marketplace-pr-hesreallyhim-awesome-claude-code.md`,
`marketplace-pr-obra-superpowers-marketplace.md`,
`marketplace-pr-helloianneo-awesome-claude-code-skills.md`.

**Update the version, release link, and verification numbers before pasting** — they are filled
in below with concrete values that go stale on every release.

## Typical PR title

```
Add Logic-Lens — semi-formal logic bug review (6 skills)
```

## PR body

```
## Adding Logic-Lens

[Logic-Lens](https://github.com/hyhmrright/logic-lens) is a Claude Code plugin that ships six skills for behavioral / logic code review using semi-formal execution tracing (Premises → Trace → Divergence → Trigger → Remedy). Also installable in Codex CLI and Gemini CLI.

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

Benchmarked against a 104-case eval suite across 12+ languages, graded offline by a rule-based
grader (no LLM judge). Published `logic-review` runs on Sonnet 4.6: 53.9% (v0.6.5) → 78.3%
(v0.6.9). Every frozen run summary is in the repo under `benchmarks/runs/`, cataloged by
`benchmarks/index.json`. Eval data: `evals/content/v2/evals-v2.json`; grader:
`scripts/grade-iteration.py`.

### Metadata for your marketplace.json (adjust to your schema)

\`\`\`json
{
  "name": "logic-lens",
  "version": "0.6.10",
  "description": "Semi-formal logic bug review — 6 skills that find bugs linters (and tests) miss",
  "source": "https://github.com/hyhmrright/logic-lens",
  "license": "MIT",
  "author": "hyhmrright",
  "keywords": ["code-review", "logic", "debugging", "static-analysis", "claude-code", "bug-detection"],
  "category": "code-review"
}
\`\`\`

### Release link

https://github.com/hyhmrright/logic-lens/releases/latest

Happy to adjust the description or categorization to match your marketplace conventions.
```

## Marketplaces to prioritize (P0 first)

1. **`hesreallyhim/awesome-claude-code`** — browser issue form only; `gh` CLI submissions are banned
2. **`obra/superpowers-marketplace`** — PR adding a JSON entry to `.claude-plugin/marketplace.json`
3. **`helloianneo/awesome-claude-code-skills`** — README table row
4. Any others found via GitHub search: `claude-code marketplace` / `claude plugin registry`

See `marketplace-research-summary.md` for the verification behind this ordering.

## After merging

- Add the marketplace to `docs/MARKETING-ROADMAP.md`'s tracking list with status and date.
- Check analytics / stars-over-time to see if referrals from that marketplace drive traffic.
- If no traffic in 4 weeks, deprioritize re-submission to similar marketplaces.
