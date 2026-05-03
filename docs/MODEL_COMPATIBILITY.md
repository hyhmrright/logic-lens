# Model Compatibility

Logic-Lens depends on the host model invoking the Skill tool. Trigger reliability — *not* skill content — dominates real-world output quality. This page records what we have measured.

## TL;DR

| Model | Mode | Recommended? | Notes |
|-------|------|:---:|-------|
| Sonnet 4.6 | Claude Code (interactive) | ✅ | Default. Triggers reliably; full template compliance. |
| Opus 4.7  | Claude Code (interactive) | ✅ | Highest quality; ~5× cost of Sonnet. |
| Haiku 4.5 | Claude Code (interactive) | ⚠️ | Triggers, but format-compliance rate lower than Sonnet. |
| Haiku 4.5 | `claude -p` (one-shot, stdin) | ❌ | **Trigger rate ≈ 0%** — answers directly without invoking the skill. Use only for cost experiments, not real workflows. |
| Sonnet 4.6 | `claude -p` (one-shot, stdin) | ✅ | Trigger rate high; this is the default model used by `scripts/run-content-evals.sh`. |

## Evidence

Full benchmark on `evals/v2/evals-v2.json` (79 cases) using `claude-haiku-4-5-20251001` via `claude -p`:

- Overall pass rate: **38.7%**
- Skill trigger rate (output contains a `Premises:` / `前提：` label): **4/79 ≈ 5%**
- Per-mode pass: logic-explain 61.7% · logic-health 40.3% · logic-locate 38.3% · logic-diff 38.1% · logic-review 34.4% · logic-fix-all 26.4%

The same `logic-fix-all` case (`auth/session.py` snippet, eval ID 9) graded under three configurations:

| Configuration | Pass | Trigger? |
|---------------|:---:|:---:|
| Haiku, `claude -p`, default skills (baseline) | 2/4 (50%) | ✗ |
| Haiku, `claude -p`, after SKILL.md rewrite experiment (reverted) | 1/4 (25%) | ✗ |
| Sonnet, in-session `Skill` tool invocation | **4/4 (100%)** | ✓ |

The skill design is sound; the gap is whether the host model decides to invoke it. The reverted experiment row also illustrates that adding more text to SKILL.md can make Haiku output *worse*, not better — the model is not reading the file in this mode.

## Why `claude -p` + Haiku scores low

In `claude -p` one-shot mode the model receives one user message and produces one response. Haiku consistently classifies short "review this code" prompts as ordinary code-Q&A and answers directly, bypassing the `Skill` tool. SKILL.md content (description, body, `_shared/` files) is therefore never loaded. Output reverts to free-form markdown without the `Premises / Trace / Divergence / Remedy` labels and skill-specific headers (`Logic Score`, `Verdict`, `Fault Confidence`, `Fix Log`) that the grader checks for.

This is a property of the model + host combination, not a deficiency of the skill text. Description rewrites that we attempted (broader trigger keywords, imperative wording, inline output schema, body-top cheatsheet — `+205` lines across all six SKILL.md files) produced **−1.05% pass rate** and **trigger 4/79 → 3/79** on a re-run of the full 79-case (v0.6.3 baseline; v0.6.4 expands the suite to 104 cases — re-run pending) benchmark, and were reverted.

## Recommendations

1. **Author SKILL.md for Sonnet/Opus.** They read the description, invoke the skill, and execute the body faithfully.
2. **Run benchmarks on Sonnet** for representative quality numbers (the `MODEL` env var in `scripts/run-content-evals.sh` defaults to `claude-sonnet-4-6` for this reason).
3. **Use Haiku only for cost-bounded smoke tests** (`SMOKE=1 MODEL=claude-haiku-4-5-20251001 …`). Treat its pass-rate numbers as a cost-vs-quality trade-off baseline, not as a target to optimize against by editing SKILL.md.
4. **If you need Haiku to perform better in `claude -p`**, the leverage point is *outside* the skill files: a session-start hook injecting the schema into the system prompt, or a `commands/` wrapper that pre-loads the skill body. Editing description / body alone will not move the needle.

## Reproducing

```bash
# Sonnet baseline (default model, ~$1–2 per full run)
bash scripts/run-content-evals.sh

# Haiku cost experiment (~$0.30–0.50 per full run)
MODEL=claude-haiku-4-5-20251001 bash scripts/run-content-evals.sh

# One-case smoke (~$0.10)
SMOKE=1 bash scripts/run-content-evals.sh
```

Per-iteration outputs land under `skills-workspace/iteration-<TAG>/`; `summary.json` aggregates pass rate by mode.
