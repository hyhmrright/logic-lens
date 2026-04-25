# Hacker News — Show HN draft

**Suggested title:**
```
Show HN: Logic-Lens – Find logic bugs linters miss via semi-formal execution tracing
```

**URL field:** `https://github.com/hyhmrright/logic-lens`

**Text (optional, can leave empty to link-only):**

```
Logic-Lens is a Claude Code plugin (also works with Codex CLI and Gemini CLI)
that ships six skills for behavioral/logic code review — the kind of bugs
that pass lint, pass type-check, pass your unit tests, but still blow up
at the first unexpected input.

Instead of pattern-matching like most AI review tools do, it runs a
semi-formal execution trace: Premises → Trace → Divergence → Remedy.
Every finding has an explicit chain from "what the code assumed" to
"where reality broke the assumption" to a paste-ready fix.

Skills:
- /logic-review   — find logic bugs in one file / function
- /logic-explain  — step-by-step execution trace when behavior surprises you
- /logic-diff     — semantic equivalence check after a refactor
- /logic-locate   — root-cause a failing test / stack trace / wrong value
- /logic-health   — repo- or module-level scored dashboard
- /logic-fix-all  — autonomous audit-and-fix pipeline, iterative until clean

v0.4.x verification data: 58/58 assertions passed across 15 cases covering
English, Chinese, and cross-file/async/race-condition scenarios. Validated
on both Opus 4.7 and Sonnet 4.6 (so architecture doesn't depend on the
top-tier model's reasoning ceiling).

Background: the L1–L6 risk taxonomy and tracing methodology are derived
from Ugare & Chandra's *Agentic Code Reasoning* (arXiv:2603.01896), which
showed semi-formal tracing beats unstructured chain-of-thought by ~10
accuracy points on code-semantics tasks.

MIT licensed, zero telemetry, no external API keys required if you're
already using Claude Code / Codex / Gemini CLI.

Happy to answer questions on the reasoning model, the eval harness
(evals/v2/), or the architecture choices.
```

## Posting guidelines

- Submit Tuesday or Wednesday 8–10 AM US Pacific.
- Stay in the thread for at least 4 hours to respond to questions.
- If asked "how is this different from SonarQube / Semgrep / <other static analyzer>?", the answer is: those do syntactic pattern-matching and miss interprocedural / type-contract bugs that show up only at runtime. Logic-Lens forces explicit premise construction so the model cannot silently assume correctness.
- Do not argue or downvote detractors. Address the technical substance.
