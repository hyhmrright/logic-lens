# Logic-Lens v0.4.2 — Cost-Conscious Default + Release Notes i18n

## TL;DR

A small housekeeping patch. Two user-facing changes:

1. **`scripts/run-trigger-evals.sh` now defaults to `claude-sonnet-4-6`** instead of `claude-opus-4-7`. Sonnet 4.6 handles the run_loop description-optimization workflow at roughly 5× lower cost; upgrade to opus only if you observe the proposals failing to improve test scores.
2. **`.github/RELEASE-NOTES-v0.4.x.md` rewritten in English** (v0.4.0 and v0.4.1 included). GitHub Release bodies and titles updated too. Makes the project more accessible to an international audience.

No code, SKILL.md, guide, or evaluation logic changes.

## 🎯 Changes

### Default model for trigger optimization

`scripts/run-trigger-evals.sh`:

```bash
# Before (v0.4.1):
MODEL="${MODEL:-claude-opus-4-7}"

# After (v0.4.2):
MODEL="${MODEL:-claude-sonnet-4-6}"
```

Reasoning: `run_loop.py` uses one model for two distinct jobs — bulk per-query evaluation (cheap, many calls) and the extended-thinking description-proposal step (fewer calls, more demanding). Since it's a single `--model` flag, the practical default should minimize cost. Sonnet 4.6 has produced usable proposals in our POC runs; opus remains available via `MODEL=claude-opus-4-7 bash scripts/run-trigger-evals.sh` for cases where proposal quality matters more than spend.

`scripts/README.md` updated with the new default + override guidance.

### Release notes internationalization

- `.github/RELEASE-NOTES-v0.4.0.md` — rewritten end-to-end in English while preserving all section structure, tables, and the English/Chinese header-map example (the one place Chinese is **meaningful content**, not just prose style).
- `.github/RELEASE-NOTES-v0.4.1.md` — same treatment.
- GitHub Release titles and bodies updated via `gh release edit` to match.
- `CHANGELOG.md` remains bilingual (internal-facing); only the release-facing notes moved to English.

## 💥 Breaking Changes

None.

## 📦 Upgrade

```bash
/plugin update logic-lens
# or:
cd /path/to/logic-lens && git pull && bash hooks/session-start
```

🤖 Generated with [Claude Code](https://claude.com/claude-code)
