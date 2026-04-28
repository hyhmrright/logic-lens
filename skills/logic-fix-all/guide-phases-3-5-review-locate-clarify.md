# Logic-Lens — Logic Fix All — Phases 3-5 (Review · Locate · Clarify)

Detailed execution for the clarification phases of the Logic-Fix-All pipeline. Navigation and overview live in sibling file `logic-fix-all-guide.md`.

Scope of this file: **Phase 3** (deep per-file review producing full Premises -> Trace -> Divergence findings), **Phase 4** (conditional fault localization when a concrete failure exists), **Phase 5** (conditional path clarification when a finding's reasoning chain is unclear).

---

## Phase 3 — Deep Review (logic-review)

**Goal:** Produce full Premises → Trace → Divergence entries per file.

3a. Read `logic-review/logic-review-guide.md` and apply its methodology
    to each file in Phase 1 priority order.

3b. Adapt the method to the file's role:
    - **Source code:** standard Premises → Trace → Divergence.
    - **Runtime config:** premises = the config's claimed shape and
      value constraints; trace how the code reads each key and what it
      does with the value; divergence = a key the code reads that's
      missing or typed wrong in the config, or a config value that
      violates a constraint the code assumes.
    - **Constraint files** (CLAUDE.md, .logic-lens.yaml, AGENTS.md):
      premises = stated invariants and rules; trace the code paths those
      rules govern; divergence = code that violates the stated
      invariant.
    - **Behavioral docs:** premises = documented behavior; trace the
      actual implementation; divergence = implementation contradicts
      the documented behavior.

3c. Tag each finding with:
    - File path and line number range
    - File role (source / config / constraint / doc)
    - Risk code (L1–L9 or custom Cx)
    - Severity (Critical / Warning / Suggestion) — assigned per finding
      based on the impact recorded in the Divergence field, not by
      L-code range
    - The full Premises → Trace → Divergence triple
    - One **origin tag** from the canonical set:
      - `"confirmed by trace"` (default — this phase produced the trace)
      - `"unconfirmed — manual check recommended"` (divergence suspected
        but not confirmed by trace; excluded from the fix queue per the
        Iron Law)
      - `"confirmed by test/error"` (written by Phase 4b when a
        logic-locate finding overlaps)
      - `"discovered during verification"` (written by Phase 7c when
        logic-diff surfaces a pre-existing bug unrelated to the fix
        being verified; carried into the next iteration's queue)

3d. Deduplicate: if the same root cause appears in multiple files (e.g.
    a shared utility bug called from five places), record one finding
    for the root cause and list all call sites.

---

## Phase 4 — Fault Location (logic-locate, conditional)

**Goal:** For concrete failures, trace backwards to the exact responsible
line so it won't get lost among Phase 3 findings.

Run this phase only if any of the following is true:
- The user provided a stack trace or error message
- There are failing tests in the repo (detect via `package.json` test
  script, `pytest.ini`, `go.mod` test targets, `Cargo.toml`
  `[[test]]`, etc.)
- The user described a specific wrong behavior

4a. Read `logic-locate/logic-locate-guide.md` and apply its methodology
    to each concrete failure.

4b. For each locate finding, check Phase 3 results:
    - Already present → mark "confirmed by test/error" (affects Phase 6
      sort order only — fix methodology is unchanged)
    - Not present → record using Phase 3c format, mark "confirmed by
      test/error"

---

## Phase 5 — Path Clarification (logic-explain, conditional)

**Goal:** For findings where the execution path is genuinely unclear,
trace step-by-step before writing a remedy. Prevents fixes driven by
misunderstood flow.

Invoke logic-explain only when a Phase 3/4 finding matches any of:
- Call depth > 3 (interprocedural chain spanning more than 3 frames)
- Cross-module (trace crosses a module/package boundary)
- Agent marked the Premises as "partial — path unclear"
- Async / concurrent / callback flow that is hard to linearize

Running logic-explain on every finding would multiply cost 2–3× without
proportional benefit; use it surgically.

5a. Read `logic-explain/logic-explain-guide.md` and apply its methodology
    to each flagged finding.

5b. Update the finding's Premises → Trace → Divergence based on the
    explain output. If the explain pass shows the original divergence
    was a misunderstanding (actual trace does not diverge), remove the
    finding from the queue and note the false positive in Phase 9's
    report under "Resolved by clarification".

---

