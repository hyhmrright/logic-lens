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
```

## Project Layout

See `CLAUDE.md` for the full layout. The core content lives in `skills/` as platform-agnostic Markdown. Codex-specific metadata is in `.codex-plugin/plugin.json`.

## Key Conventions

- `skills/_shared/` is the shared framework. Do not duplicate its content in individual skill guides.
- Every finding in a review output must use the Premises → Trace → Divergence → Remedy format (Iron Law).
- Risk codes L1–L6 are defined in `skills/_shared/logic-risks.md`. Do not invent new codes without updating that file.
- Version number in `package.json` is the source of truth — keep all metadata files in sync.

## No Hooks

The session-start hook in `hooks/` is Claude Code only. Codex CLI discovers skills via `.codex-plugin/plugin.json` and does not use the hook system.
