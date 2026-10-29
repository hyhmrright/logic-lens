# Logic-Lens — Developer Guide (Codex CLI)

This file contains instructions for Codex CLI agents working on the Logic-Lens repository.

## Invoking Skills

In Codex CLI, invoke skills with the `$` prefix:

```
$logic-review    — logic bug review
$logic-explain   — execution path explanation
$logic-diff      — semantic equivalence check
$logic-locate    — fault localization
$logic-health    — aggregate logic health dashboard
$logic-fix-all   — autonomous audit-and-fix pipeline
```

## Project Layout

See `DEVELOPMENT.md` for the tool-neutral layout and development workflow. The core content lives in `skills/` as platform-agnostic Markdown. Codex-specific metadata is in `.codex-plugin/plugin.json`.

## Key Conventions

- `skills/_shared/` is the shared framework. Do not duplicate its content in individual skill guides.
- Every finding in a review output must use the Premises → Trace → Divergence → Trigger → Remedy format (Iron Law).
- Risk codes L1–L9 are defined in `skills/_shared/logic-risks.md`. Do not invent new codes without updating that file.
- Version number in `package.json` is the source of truth — keep all metadata files in sync.

## No Hooks

The session-start hook in `hooks/` is Claude Code only. Codex CLI discovers skills via `.codex-plugin/plugin.json` and does not use the hook system.

## Portable execution

Use `python3 scripts/logic_lens.py` for reviews, portable bundles and evaluations.
Codex is the default tested CLI; `--provider command` accepts other coding tools.
Compiled snapshots replace plugin-cache synchronization. No Claude runtime or
authentication is required. Never infer native activation from report field labels.

Do not introduce Claude-only prerequisites or cache gates into the maintained workflow.
Keep optional host distribution metadata separate from the provider-neutral core.
