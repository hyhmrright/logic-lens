# Reddit r/ClaudeAI draft

**Suggested title:**
```
I built Logic-Lens — 6 Claude Code skills that find logic bugs your linter (and tests) miss
```

**Body (markdown-flavored):**

```
Hey r/ClaudeAI — wanted to share a project I've been using daily for the past few weeks.

**Logic-Lens** is a Claude Code plugin (also installable in Codex CLI and Gemini CLI) that adds six skills for behavioral / logic code review:

| Command | What it does |
|---|---|
| `/logic-review` | Find logic bugs in a single file or function |
| `/logic-explain` | Trace execution step-by-step when behavior surprises you |
| `/logic-diff` | Verify two code versions are semantically equivalent |
| `/logic-locate` | Root-cause a failing test / stack trace / wrong value |
| `/logic-health` | Scored dashboard of logic correctness across a module/repo |
| `/logic-fix-all` | Autonomous audit-and-fix pipeline — repo-wide, iterative |

## Why semi-formal tracing

Most AI review tools pattern-match. They'll catch `null` dereferences and obvious off-by-ones, but they miss:

- Cross-file callee contract mismatches (L6)
- Nil-interface traps in Go (an interface holding a nil pointer is not nil)
- Shadow-override bugs (your local `format` shadowing the builtin one)
- Race conditions with non-atomic increments
- Mutations during iteration (tests pass if the mutation skips only consecutive elements)

Logic-Lens enforces **Premises → Trace → Divergence → Remedy** on every finding. No finding without an explicit chain. No "add validation" hand-waves — remedies are paste-ready code.

## Verification

15 cases across English / Chinese / DEEP (cross-file, async, race) — 58/58 assertions pass. Tested on both Opus 4.7 and Sonnet 4.6 to confirm the architecture doesn't depend on top-tier reasoning. Eval data + grader script are in the repo (`evals/v2/`, `scripts/grade-iteration.py`).

## What I'd love feedback on

- Does the output format (Premises / Trace / Divergence / Remedy) work for your workflow? Or is it too verbose?
- Are there bug patterns you hit that Logic-Lens misses? (Open an issue with a repro, I'll add it to the eval set.)
- Does `logic-fix-all` feel too aggressive for your repos? It has a mandatory consent gate in Phase 0 but I'm open to more granular safety controls.

Link: https://github.com/hyhmrright/logic-lens

MIT, zero telemetry, works offline once installed. Stars appreciated if it's useful to you.
```

## Posting guidelines

- Avoid reposting the exact same text to multiple subs (auto-mod catches it).
- Respond to comments within the first 6 hours.
- If asked "how is this different from aider/cursor/<other AI coding tool>?", the answer is: those are task-completion assistants; Logic-Lens is a targeted review lens with a specific reasoning discipline.
