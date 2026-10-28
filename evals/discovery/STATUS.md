# Experiment status — 2026-10-28

**Decision: candidate remains experimental; Codex comparison in progress.**

The maintained workflow now runs through Codex or a generic command adapter. Claude
is not required. An offline Markdown pack exports all six skills for other hosts;
see `docs/TOOL_COMPATIBILITY.md` for tested execution versus portable packaging.

The corpus contains 20 pinned historical source pairs. Nineteen target failures
were inspected on actual source and passed after the implementation-only repair;
one Windows-only pair is blocked. Runtime/version details remain in `catalog.json`.
These are public development cases, not an independent holdout.

The formal Codex pilot uses four cases (httpx-03/httpx-10/requests-02/requests-06),
both variants, three arms and three repetitions: 72 reviews, gpt-6.1-sol, high effort,
read-only shell, no web, isolated home/source, 360-second per-call timeout. All arms
receive the same 10-tool-call/1600-word soft budget. Dollar cost is unknown; actual
CLI token usage is retained. The prior skill is frozen at the catalog's baseline SHA.

An initial three-call instrumentation trial completed model responses but hit a
runner reload/import error before post-run integrity checks. Those raw outputs
are retained for debugging and excluded from the formal pilot. They are not misses
or success evidence. The formal runner no longer reloads the driver from disk.

Additional discoveries are being adjudicated against real historical source rather
than treating the repaired target files as completely bug-free. Evaluator-only
`discovered_checks.py` provides separate checks for selected additional behaviors;
it is never supplied to the reviewing model. A failed behavior assertion still needs
a supported requirement and a traceback at the predicted consequence.

No effectiveness claim follows from an in-progress run. Final root-cause judgments,
per-case repeated metrics, tool/token/resource data and limitations will be frozen
when this matrix completes. Adjudication by the implementing assistant must be
labeled as such, not presented as independent human validation.

Remaining release gates include prospective unseen projects/families, independent
adjudication, untouched content-regression checks, and a separate execution-capable
integration protocol. This four-case development pilot cannot establish universal
bug recall or native activation reliability across coding tools.
