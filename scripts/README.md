# scripts/ — Logic-Lens dev utilities

Offline-friendly shell scripts used during development and release. All scripts are idempotent and safe to re-run.

## `validate-repo.sh`

Structural + metadata sanity check. Fast and offline — suitable for CI.

```bash
bash scripts/validate-repo.sh
```

Checks: required SKILL.md frontmatter in six skills, shared framework files under `_shared/`, per-skill guide files, `logic-fix-all` phase files, that every tracked `*.json` file parses, version consistency across `package.json` / `.claude-plugin/plugin.json` / `.claude-plugin/marketplace.json` / `.codex-plugin/plugin.json` / `gemini-extension.json` / README badge.

Exit code 0 = release-ready; non-zero = fix before tagging.

## `lint-shell.sh`

Runs shellcheck over every tracked shell script. Probe fixtures under
`evals/real-world/probes/` are excluded — they are deliberately buggy test data.

```bash
npm run lint-shell                  # or: bash scripts/lint-shell.sh
```

Fails if the script list comes back empty (not a git checkout, or a broken pathspec),
so a silently-skipped lint cannot pass as green. Prints the shellcheck version it used:
GitHub's ubuntu runner ships 0.9.0 while Homebrew is newer, so a local/CI divergence is
expected to be explained by that line.

## `bump-version.py`

Rewrites the version number in all six places at once (`package.json`, the four plugin manifests, and the `README.md` badge), preserving each file's formatting, then runs `validate-repo.sh` to confirm. Replaces the manual six-file edit documented in CLAUDE.md → Version Sync.

```bash
npm run bump-version -- 0.7.0       # or: python3 scripts/bump-version.py 0.7.0
```

Exits with `validate-repo.sh`'s code (0 = consistent). Does **not** touch `CHANGELOG.md` — add the release entry by hand.

## `run-content-evals.sh`

End-to-end content-eval pipeline. Pairs with `grade-iteration.py` (the rule-based grader): the runner calls Claude and writes outputs; the grader scores them offline against the assertion rules.

The split is intentional — `run-content-evals.sh` is the **runner** (calls Claude, costs tokens, needs the `claude` CLI on PATH); `grade-iteration.py` is the **grader** (pure Python, regex-based, free, can be re-run on existing outputs without re-spending tokens).

```bash
# Run all content eval cases against Sonnet 4.6 (default), tag from current git SHA:
npm run content-evals       # or: bash scripts/run-content-evals.sh

# Re-run with a custom tag:
TAG=v0.6.0-baseline bash scripts/run-content-evals.sh

# Run only the L7/L8/L9 coverage (concurrency / lifecycle / locale, 7 calls):
CASES="107 200 201 202 203 204 205" bash scripts/run-content-evals.sh

# Run only the L2/L5 coverage (type contract / control-flow escape, 4 calls):
CASES="206 207 208 209" bash scripts/run-content-evals.sh

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

## `grade-iteration.py`

The offline grader. Pure Python, regex-based, free — it re-scores an existing iteration directory
without spending a token, so you can iterate on assertion rules against outputs you already paid for.

```bash
python3 scripts/grade-iteration.py skills-workspace/iteration-<TAG>
```

One positional argument: the iteration directory. It reads every `eval-<id>/output.md`, writes an
`eval-<id>/grading.json` per case, and aggregates `summary.json`.

Each case is scored on two orthogonal axes:

- **logic** — did the skill find the bug, classify the L-code, and propose a fix? This is the
  headline metric for skill effectiveness.
- **contract** — does the report carry the literal Iron Law field labels and the correct output
  language? A binary, high-variance compliance gate. (The JSON keys are still named `format_*`
  for backward compatibility.)

`overall_pass_rate` mixes both. See `benchmarks/README.md` → "Metric Hierarchy" before drawing
conclusions from it.

**The grader is ground truth.** Never relax a rule to make a run pass — that destroys the only
signal you have.

## `_defaults.sh`

Sourced by both eval runners. Holds the two-tier model default: `claude-haiku-4-5` for
trigger-evals (cheap yes/no classification), `claude-sonnet-4-6` for content-evals (which
pre-sets `MODEL` before sourcing, because semi-formal format compliance requires it). Override
either with `MODEL=<id>`.

## `run-trigger-evals.sh`

Drives skill-creator's `run_loop.py` against the six per-skill trigger eval sets in `evals/trigger/v2/trigger-evals-<skill>.json` to tune each `SKILL.md` description for higher trigger accuracy. Requires:

- `claude` CLI on PATH
- the skill-creator plugin (default path `~/.claude/plugins/marketplaces/anthropic-agent-skills/skills/skill-creator`; override via `SKILL_CREATOR_PATH`)
- network access (each iteration issues real `claude -p` calls and costs tokens)

```bash
# All six skills (5 iterations each, Haiku 4.5 default — cost-conscious):
bash scripts/run-trigger-evals.sh

# One skill:
bash scripts/run-trigger-evals.sh review

# Shorter loop, upgrade to Opus only if Sonnet proposals look weak:
MAX_ITERATIONS=3 MODEL=claude-opus-4-7 bash scripts/run-trigger-evals.sh review

# Write and open an HTML report instead of the default headless JSON-only run:
REPORT=auto bash scripts/run-trigger-evals.sh review
```

Default model is **`claude-sonnet-4-6`** for content-evals (semi-formal format compliance requires it; haiku skips structured output and fails ~60% of rules) and **`claude-haiku-4-5`** for trigger-evals (simple classification, lower-cost). Override either with `MODEL=<id>`.

Each run emits a JSON result with `best_description` selected by held-out test score. Copy it into the corresponding `skills/logic-<skill>/SKILL.md` frontmatter `description:` field to apply. `MAX_ITERATIONS` must be a positive integer. `REPORT` defaults to `none` so the script works in headless CI and Codex sessions; set `REPORT=auto` to use skill-creator's live browser report.

The trigger eval JSON files (20 cases per skill, 10 positive + 10 negative near-miss) live in `evals/trigger/v2/trigger-evals-*.json` and were designed to cover scope-routing boundaries (single file → review / directory → health / confirmed failure → locate / two versions → diff / repo-wide → fix-all) and language-specific phrasings.
