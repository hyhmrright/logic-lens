# scripts/ — Logic-Lens dev utilities

Offline-friendly shell scripts used during development and release. All scripts are idempotent and safe to re-run.

## `validate-repo.sh`

Structural + metadata sanity check. Fast and offline — suitable for CI.

```bash
bash scripts/validate-repo.sh
```

Checks: required SKILL.md frontmatter in six skills, shared framework files under `_shared/`, per-skill guide files, `logic-fix-all` phase files, version consistency across `package.json` / `.claude-plugin/plugin.json` / `.claude-plugin/marketplace.json` / `.codex-plugin/plugin.json` / `gemini-extension.json` / README badge.

Exit code 0 = release-ready; non-zero = fix before tagging.

## `run-content-evals.sh` + `grade-iteration.py`

End-to-end content-eval pipeline: drives every case in `evals/v2/evals-v2.json` through `claude -p`, then grades each output against the assertion rules in `grade-iteration.py` and writes a per-case + overall pass-rate `summary.json`.

The split is intentional:
- `run-content-evals.sh` is the **runner** — calls Claude, costs tokens, needs the `claude` CLI on PATH.
- `grade-iteration.py` is the **grader** — pure Python, regex-based, costs nothing. Can be re-run on existing outputs without re-spending tokens.

```bash
# Run all 24 cases against Sonnet 4.6 (default), tag from current git SHA:
npm run content-evals       # or: bash scripts/run-content-evals.sh

# Re-run with a custom tag:
TAG=v0.6.0-baseline bash scripts/run-content-evals.sh

# Run only the new L7/L8/L9 cases (cheap subset, 6 calls):
CASES="200 201 202 203 204 205" bash scripts/run-content-evals.sh

# Run with Opus (5x cost — only when comparing models):
MODEL=claude-opus-4-7 bash scripts/run-content-evals.sh

# Run-only, grade later (e.g. CI uploads outputs as artifacts, grades elsewhere):
SKIP_GRADE=1 bash scripts/run-content-evals.sh
python3 scripts/grade-iteration.py skills-workspace/iteration-<TAG>
```

Outputs land in `skills-workspace/iteration-<TAG>/`:
- `eval-<id>/prompt.md` — exact prompt sent to the model (reproducibility)
- `eval-<id>/output.md` — model response
- `eval-<id>/grading.json` — per-case rule pass/fail
- `summary.json` — overall + per-mode + per-language pass rates

The runner is idempotent — if `output.md` already exists for a case, it skips that case. Delete the file (or the whole `eval-<id>/` dir) to force a re-run.

`skills-workspace/` is gitignored; don't commit run outputs.

## `run-trigger-evals.sh`

Drives skill-creator's `run_loop.py` against the six per-skill trigger eval sets in `evals/v2/trigger-evals-<skill>.json` to tune each `SKILL.md` description for higher trigger accuracy. Requires:

- `claude` CLI on PATH
- the skill-creator plugin (default path `~/.claude/plugins/marketplaces/anthropic-agent-skills/skills/skill-creator`; override via `SKILL_CREATOR_PATH`)
- network access (each iteration issues real `claude -p` calls and costs tokens)

```bash
# All six skills (5 iterations each, Sonnet 4.6 default — cost-conscious):
bash scripts/run-trigger-evals.sh

# One skill:
bash scripts/run-trigger-evals.sh review

# Shorter loop, upgrade to Opus only if Sonnet proposals look weak:
MAX_ITERATIONS=3 MODEL=claude-opus-4-7 bash scripts/run-trigger-evals.sh review
```

Default model is **`claude-sonnet-4-6`** — the run_loop uses the same model for both bulk evaluation (cheap) and the smarter description-proposal step, so one-model choice trades off cost vs proposal quality. Sonnet 4.6 handles both well at ~5× lower cost than opus; only switch to opus if you see the proposal descriptions fail to improve test scores across iterations.

Each run emits a JSON result with `best_description` selected by held-out test score. Copy it into the corresponding `skills/logic-<skill>/SKILL.md` frontmatter `description:` field to apply.

The trigger eval JSON files (20 cases per skill, 10 positive + 10 negative near-miss) live in `evals/v2/trigger-evals-*.json` and were designed to cover scope-routing boundaries (single file → review / directory → health / confirmed failure → locate / two versions → diff / repo-wide → fix-all) and language-specific phrasings.
