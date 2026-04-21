# Logic-Lens — Developer Guide (Claude Code)

This file contains instructions for Claude when working on the Logic-Lens repository itself.

## Project Layout

```
logic-lens/
├── skills/
│   ├── _shared/         ← Framework shared by all skills (Iron Law, risks, methodology)
│   └── logic-{review,explain,diff,locate,health}/
│       ├── SKILL.md     ← Frontmatter + process skeleton (triggers the skill)
│       └── *-guide.md   ← Detailed step-by-step instructions (loaded on demand)
├── .claude-plugin/      ← Claude Code plugin metadata
├── .codex-plugin/       ← Codex CLI plugin metadata
├── gemini-extension.json← Gemini CLI extension metadata
├── commands/            ← Short command wrappers installed by session-start hook
├── hooks/               ← Claude Code session-start hook
└── evals/evals.json     ← Benchmark test cases
```

## Conventions

### SKILL.md Structure
- YAML frontmatter: `name` and `description` are required.
- `description` must include a "Do NOT trigger for:" clause.
- `description` should be explicit about trigger phrases — err on the side of triggering.
- Process section: 5–7 numbered items; each item cites a step in the guide file.
- Setup section: explicit `Read` instructions for each shared file and the guide.

### Guide Files
- Numbered steps (Step 1, Step 2, ...).
- Each step explains the *why*, not just the *what*.
- Sub-steps use letters (Step 2a, 2b).
- Concrete examples preferred over abstract descriptions.

### Risk Codes
- Built-in: L1–L6 (defined in `skills/_shared/logic-risks.md`)
- Custom project-specific: C1, C2, ... (defined in `.logic-lens.yaml`)
- Every finding must be tagged with a risk code.

### Version Sync
`package.json` is the source of truth for the version number. When bumping version, update:
1. `package.json` → `version`
2. `.claude-plugin/plugin.json` → `version`
3. `.claude-plugin/marketplace.json` → `version`
4. `.codex-plugin/plugin.json` → `version`
5. `gemini-extension.json` → `version`
6. `README.md` → version badge

### Iron Law
Never add a Remedy to a finding before Premises, Trace, and Divergence are written. This is the core discipline of the project. Do not weaken it.

## Commands in This Repo

Claude Code users invoke skills as `/logic-review`, `/logic-explain`, etc.
The session-start hook copies these from `commands/` to `~/.claude/commands/` automatically.

## Adding a New Skill
1. Create `skills/logic-newskill/SKILL.md` following the existing SKILL.md pattern.
2. Create `skills/logic-newskill/logic-newskill-guide.md`.
3. Add a command wrapper to `commands/logic-newskill.md`.
4. Register in `gemini-extension.json` contribution.skills and contribution.commands.
5. Add 3–5 eval cases to `evals/evals.json`.
