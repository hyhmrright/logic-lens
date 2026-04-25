# scripts/ — Logic-Lens dev utilities

Offline-friendly shell scripts used during development and release. All scripts are idempotent and safe to re-run.

## `validate-repo.sh`

Structural + metadata sanity check. Fast and offline — suitable for CI.

```bash
bash scripts/validate-repo.sh
```

Checks: required SKILL.md frontmatter in six skills, shared framework files under `_shared/`, per-skill guide files, `logic-fix-all` phase files, version consistency across `package.json` / `.claude-plugin/plugin.json` / `.claude-plugin/marketplace.json` / `.codex-plugin/plugin.json` / `gemini-extension.json` / README badge.

Exit code 0 = release-ready; non-zero = fix before tagging.

## `run-trigger-evals.sh`

Drives skill-creator's `run_loop.py` against the six per-skill trigger eval sets in `evals/v2/trigger-evals-<skill>.json` to tune each `SKILL.md` description for higher trigger accuracy. Requires:

- `claude` CLI on PATH
- the skill-creator plugin (default path `~/.claude/plugins/marketplaces/anthropic-agent-skills/skills/skill-creator`; override via `SKILL_CREATOR_PATH`)
- network access (each iteration issues real `claude -p` calls and costs tokens)

```bash
# All six skills (5 iterations each, Opus 4.7 default):
bash scripts/run-trigger-evals.sh

# One skill:
bash scripts/run-trigger-evals.sh review

# Shorter loop, different model:
MAX_ITERATIONS=3 MODEL=claude-sonnet-4-6 bash scripts/run-trigger-evals.sh
```

Each run emits a JSON result with `best_description` selected by held-out test score. Copy it into the corresponding `skills/logic-<skill>/SKILL.md` frontmatter `description:` field to apply.

The trigger eval JSON files (20 cases per skill, 10 positive + 10 negative near-miss) live in `evals/v2/trigger-evals-*.json` and were designed to cover scope-routing boundaries (single file → review / directory → health / confirmed failure → locate / two versions → diff / repo-wide → fix-all) and language-specific phrasings.
