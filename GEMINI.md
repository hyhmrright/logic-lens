# Logic-Lens — Developer Guide (Gemini CLI)

This file contains instructions for Gemini CLI agents working on the Logic-Lens repository.

## Invoking Skills

In Gemini CLI, invoke skills with the `/` prefix:

```
/logic-review    — logic bug review
/logic-explain   — execution path explanation
/logic-diff      — semantic equivalence check
/logic-locate    — fault localization
/logic-health    — aggregate logic health dashboard
```

## Installation

Install via Gemini CLI extension system using `gemini-extension.json` at the repository root.

## Project Layout

See `CLAUDE.md` for the full layout. The core content lives in `skills/` as platform-agnostic Markdown. Gemini-specific metadata is in `gemini-extension.json`.

## Key Conventions

- `skills/_shared/` is the shared framework. All skills load it on demand.
- Every finding must follow Premises → Trace → Divergence → Remedy (Iron Law).
- Risk codes L1–L9 are defined in `skills/_shared/logic-risks.md`.
- Version in `package.json` is the source of truth.

## No Hooks

The session-start hook is Claude Code only. Gemini CLI discovers skills via `gemini-extension.json` and does not use hooks.
