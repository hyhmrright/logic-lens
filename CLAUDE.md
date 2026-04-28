# Logic-Lens — Developer Guide (Claude Code)

This file contains instructions for Claude when working on the Logic-Lens repository itself.

## Project Layout

```
logic-lens/
├── skills/
│   ├── _shared/
│   │   ├── common.md              ← Language rule, Iron Law, Logic Score, yaml schema
│   │   ├── logic-risks.md         ← L1–L9 risk taxonomy definitions
│   │   ├── semiformal-guide.md    ← Execution tracing methodology + min thresholds
│   │   ├── semiformal-checklist.md ← Premises Construction Checklist (single source)
│   │   └── report-template.md     ← Report Template (English + Chinese, single source)
│   ├── logic-{review,explain,diff,locate,health}/
│   │   ├── SKILL.md               ← Frontmatter + process skeleton (triggers the skill)
│   │   └── *-guide.md             ← Detailed step-by-step instructions (loaded on demand)
│   └── logic-fix-all/             ← Skill 6: orchestrates the other five into one pipeline
│       ├── SKILL.md
│       ├── logic-fix-all-guide.md ← Navigation + shared context
│       ├── guide-phases-0-2-consent-scope-health.md
│       ├── guide-phases-3-5-review-locate-clarify.md
│       └── guide-phases-6-9-fix-iterate-report.md
├── .claude-plugin/                ← Claude Code plugin metadata
├── .codex-plugin/                 ← Codex CLI plugin metadata
├── gemini-extension.json          ← Gemini CLI extension metadata
├── commands/                      ← Short command wrappers installed by session-start hook
├── hooks/
│   ├── hooks.json                 ← Claude Code hook registration (uses ${CLAUDE_PLUGIN_ROOT} — portable across platforms)
│   └── session-start              ← Copies commands/ to ~/.claude/commands/ on session start
├── evals/v2/evals-v2.json         ← Benchmark test cases (current)
├── evals/v1/                      ← Legacy v1 cases (archived for reference)
├── CONTRIBUTING.md                ← Contribution ground rules and versioning policy
└── AGENTS.md / GEMINI.md          ← Companion guides for Codex and Gemini CLI users
```

## Conventions

### SKILL.md Structure
- YAML frontmatter: `name` and `description` are required.
- `description` must include a "Do NOT trigger for:" clause.
- `description` should be explicit about trigger phrases — err on the side of triggering.
- Process section: 5–7 numbered items; each item cites a step in the guide file.
- Setup section: two fixed parts — (1) read shared files (`common.md`, `logic-risks.md` if the skill produces L-code findings, `semiformal-guide.md` + `semiformal-checklist.md`, and `report-template.md` for skills that emit reports); (2) read the skill's own `*-guide.md`. Do not reorder or omit unless there is a documented reason (e.g., `logic-explain` omits `logic-risks.md` because it produces no L-code findings).

### Guide Files
- Numbered steps (Step 1, Step 2, ...).
- Each step explains the *why*, not just the *what*.
- Sub-steps use letters (Step 2a, 2b).
- Concrete examples preferred over abstract descriptions.

### Risk Codes
- Built-in: L1–L9 (defined in `skills/_shared/logic-risks.md`)
- Custom project-specific: C1, C2, ... (defined in `.logic-lens.yaml` at the repo root — optional file, omit if no custom codes needed)
- Every finding must be tagged with a risk code.

`.logic-lens.yaml` schema: see `skills/_shared/common.md` — `custom_risks` is a list of records with `code`, `name`, `description`, and `severity` fields.

### Version Sync
`package.json` is the source of truth for the version number. When bumping version, update:
1. `package.json` → `version`
2. `.claude-plugin/plugin.json` → `version`
3. `.claude-plugin/marketplace.json` → `version`
4. `.codex-plugin/plugin.json` → `version`
5. `gemini-extension.json` → `version`
6. `README.md` → version badge

### Iron Law
See `skills/_shared/common.md` — Iron Law section. That is the canonical definition; do not duplicate or paraphrase it here.

## Companion Docs by AI Tool

| File | Read by | Purpose |
|------|---------|---------|
| `AGENTS.md` | OpenAI Codex / Agents SDK | Task instructions for agent-based runners |
| `GEMINI.md` | Gemini CLI | Extension setup and skill invocation for Gemini |
| `CONTRIBUTING.md` | Human contributors | Ground rules, versioning policy, PR requirements |

## Development Commands

```bash
npm run validate       # Validate repo structure and metadata consistency (scripts/validate-repo.sh)
npm run trigger-evals  # Run trigger-eval suites under evals/v2/ (scripts/run-trigger-evals.sh)
npm run content-evals  # Run evals-v2.json end-to-end through claude -p + grade (scripts/run-content-evals.sh) — costs API tokens
```

Manual one-liners that don't require the scripts:

```bash
# Verify SKILL.md frontmatter exists in all six skills
grep -l "^name:" skills/*/SKILL.md

# Verify all guide files are present
ls skills/*/logic-*-guide.md

# Verify version is consistent across all metadata files
grep '"version"' package.json .claude-plugin/plugin.json .claude-plugin/marketplace.json .codex-plugin/plugin.json gemini-extension.json
```

## First Clone Setup

`hooks/hooks.json` uses the `${CLAUDE_PLUGIN_ROOT}` placeholder, so no path edit is needed regardless of where the repo lives.

**1. Run the session-start hook once manually** to install short-form command wrappers (the hook fires automatically on every session start once Claude Code picks the plugin up, but the first install needs a one-shot kick):

```bash
# Run from the repo root (macOS / Linux / WSL / Git Bash on Windows):
bash hooks/session-start
```

**2. Verify commands are installed:**

```bash
ls ~/.claude/commands/logic-*.md
# Expected: logic-diff.md  logic-explain.md  logic-fix-all.md  logic-health.md  logic-locate.md  logic-review.md
```

**Platform note:** the hook requires `bash`. On macOS and Linux it is preinstalled. On Windows, Claude Code itself runs under WSL or Git Bash, both of which provide `bash` — no extra install needed. For users installing through the marketplace (`/plugin install`), Claude Code auto-discovers `hooks/hooks.json` and runs the hook on every session — this manual step is only for clone-based development of the plugin itself.

## Commands in This Repo

Claude Code users invoke skills as `/logic-review`, `/logic-explain`, etc.
The session-start hook copies these from `commands/` to `~/.claude/commands/` automatically.

## Adding a New Skill
1. Create `skills/logic-newskill/SKILL.md` following the existing SKILL.md pattern.
2. Create `skills/logic-newskill/logic-newskill-guide.md`.
3. Add a command wrapper to `commands/logic-newskill.md`.
4. Register in `gemini-extension.json` contribution.skills and contribution.commands.
5. No change needed in `.codex-plugin/plugin.json` — it points at `skills/` directory and auto-discovers subfolders.
6. Add the skill name to the `for skill in ...` loop in `hooks/session-start` (search for `for skill in` to find the line).
7. Add 3–5 eval cases to `evals/v2/evals-v2.json` (or to the appropriate `evals/v2/trigger-evals-*.json` file if the new skill needs trigger evals).
