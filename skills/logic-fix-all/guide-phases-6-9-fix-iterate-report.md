# Logic-Lens — Logic Fix All — Phases 6-9 (Fix · Verify · Iterate · Report)

Detailed execution for the fix application and reporting phases of the Logic-Fix-All pipeline. Navigation and overview live in sibling file `logic-fix-all-guide.md`.

Scope of this file: **Phase 6** (fix queue assembly — sort by severity, write Minimal/Targeted/Justified remedies), **Phase 7** (apply + verify each fix using logic-diff methodology; revert on regression, retry up to 3x), **Phase 8** (iteration loop — re-run health + review on modified files and consumers), **Phase 9** (Final Fix Report with per-role findings, skill invocation counts, iteration history).

---

## Phase 6 — Fix Queue Assembly

**Goal:** Ordered queue of (finding, remedy) pairs from all sources.

6a. Merge all findings from Phases 2–4, after Phase 5 clarification.
    Each entry must have the full Premises → Trace → Divergence triple
    (required before a remedy can be written, per the Iron Law).

6b. Sort by severity (Critical / Warning / Suggestion) tagged in
    Phase 3c. Severity is per-finding, based on impact — not a fixed
    mapping from L-code. Two L3 findings can land at different
    severities if one breaks a payment path and the other breaks a log
    format. The default severity per L-code can be overridden globally
    via `.logic-lens.yaml` `severity:` config (repo-wide, not
    per-module). Custom risk codes (Cx) use the severity declared in
    their `custom_risks` entry.

    | Priority | Criteria |
    |----------|----------|
    | 1 (highest) | 🔴 Critical findings |
    | 2 | 🟡 Warning findings |
    | 3 | 🟢 Suggestion findings |

    Within each severity tier, apply secondary sort keys in order:
    1. "confirmed by test/error" findings from Phase 4 first (a failing
       test gives a ready-made verification signal).
    2. Systemic-pattern roots from Phase 2c before their downstream
       symptoms.
    3. Root causes before call sites — fixing the root eliminates the
       symptom at all call sites simultaneously.

6c. For each finding, write the remedy. The remedy must be:
    - **Minimal:** change only what the trace shows is wrong.
    - **Targeted:** do not refactor surrounding code as a side effect.
    - **Justified:** one sentence explaining why this fix and not
      another.

6d. Remedy target rules for cross-file contradictions:
    - **Code vs constraint file** (CLAUDE.md / AGENTS.md / GEMINI.md /
      behavioral README): default → edit the CODE. Constraint files
      are the spec; code that diverges is the bug. Exception: if the
      constraint text is obviously stale (e.g. references a removed
      function / renamed module) and the code is internally coherent,
      edit the CONSTRAINT FILE instead and note the spec drift in the
      Fix Log.
    - **Code vs runtime config** (`.logic-lens.yaml`,
      `*.json/.yaml/.toml` loaded at startup): default → edit the
      CONFIG. But first check reasonability: if the config value is
      internally coherent for its key (timeout in its stated unit, URL
      well-formed, path exists) AND the code's handling of it looks
      typo'd, edit the CODE instead. When both sides look plausible,
      record as "Unresolved — unclear whether spec or consumer is wrong"
      and surface it in Phase 9's summary for human judgment.
    - **Doc vs doc** (e.g. CLAUDE.md says X, README says not-X): decide
      by this mechanical ranking:
      1. More recent git mtime wins (if both are tracked).
      2. If mtimes tie or one is untracked: doc in the deeper path
         beats a root-level doc (e.g. `docs/api.md` > `README.md`).
      3. Still tied → "Unresolved — ambiguous spec" with both
         citations.
    - **Config is internally inconsistent** (two keys contradict each
      other): edit the CONFIG at the less-referenced key.

---

## Phase 7 — Apply + Verify (logic-diff)

**Goal:** Apply each fix and confirm it removes the divergence without
introducing a regression.

7a. Apply fixes one finding at a time. After each fix:
    - Record file path, line range changed, one-line description → Fix
      Log row.
    - If two findings in the same file affect overlapping line ranges,
      fix the higher-priority one first, then re-read the file before
      applying the second fix (avoid stale-offset errors).

7b. When a remedy requires a choice between two approaches (e.g. "clamp
    to 0" vs "raise an error"), first look for the surrounding code's
    existing convention: read the nearest callers and peer functions in
    the same module and match what they do on invalid input (raise /
    return sentinel / clamp / silently skip). Minimum-change behavior —
    don't invent a new failure mode if one already exists. Only when no
    convention is discoverable, default to the more defensive option
    (raise / reject / fail fast): defensive choices produce early, loud,
    observable failures, which means logic-diff verification below can
    confirm the fix conclusively via static trace.

7c. Read `logic-diff/logic-diff-guide.md` and apply its methodology
    between the pre-fix and post-fix versions of the changed function(s).
    When multiple fixes apply to independent files, apply them all then
    verify each changed file in parallel. For same-file or
    cross-dependent fixes, verify one at a time.

    logic-diff produces a single verdict per comparison — one of
    **Semantically Equivalent**, **Conditionally Equivalent**, or
    **Semantically Divergent**. Interpret as follows (note: the bug's
    "Divergence" in the Premises→Trace→Divergence triple from Phase 3c
    is a separate concept from logic-diff's "divergent" verdict — do
    not conflate):

    | logic-diff verdict | Accompanying condition | Meaning | Action |
    |---|---|---|---|
    | Conditionally Equivalent | condition covers exactly the scenario in the finding's Divergence field | fix removes the bug without touching correct paths | **pass** — go 7a for next finding |
    | Conditionally Equivalent | condition is narrower or broader than the failing scenario | partial / over-scoped fix | go 7d (regression) |
    | Conditionally Equivalent | condition is orthogonal / unrelated to the failing scenario (and the original Divergence no longer triggers post-fix) | fix succeeded; the new condition is a pre-existing separate bug that logic-diff surfaced | **pass** — go 7a, AND record the new condition as a separate finding in Phase 3c format, tagged "discovered during verification", for the next iteration round |
    | Semantically Equivalent | — | fix changed nothing observable | go 7d (ineffective fix) |
    | Semantically Divergent | — | fix altered behavior on previously-correct paths too | go 7d (regression) |

    Additionally, regardless of verdict, the specific condition recorded
    in the finding's Divergence field must no longer trigger on the
    post-fix trace. Check this manually as a sanity step.

7d. On regression: revert the fix, re-examine the trace, write a new
    remedy, re-apply. After 3 failed attempts on the same finding, stop
    retrying: record as "Unresolved — conflicting constraints" in the
    Fix Log and continue to the next finding.

7e. If logic-diff cannot confirm equivalence (function too complex, or
    involves external state not statically traceable), note as
    "unverified — integration test recommended" and continue. Do not
    block the pipeline.

---

## Phase 8 — Iteration Loop

**Goal:** Repeat the review→fix cycle until the codebase is clean, with
explicit state tracking to prevent (a) infinite loops on Critical
findings that Phase 7d already gave up on, and (b) runaway iteration on
non-critical findings.

### 8a. Persistent state across rounds

The pipeline maintains three pieces of state spanning all Phase 8
rounds:

- **`unresolvable_findings`** (set): every finding that Phase 7d retired
  with "Unresolved — conflicting constraints" (3 retries failed). Each
  entry is a tuple `(file_path, line_range, L_code,
  divergence_signature)` where `divergence_signature` is a short hash
  of the Divergence-field text. Phase 3 re-emits these findings each
  round because the code still diverges; this set lets the pipeline
  recognize them and **not re-queue them**. They carry their existing
  Unresolved tag forward.

  Matching priority: match primarily on `(file_path, line_range, L_code)`
  — these three are stable across rounds. `divergence_signature` is a
  tie-breaker for the rare case of two distinct bugs at the same
  location with the same L-code, not the primary key. This matters
  because LLM-generated Divergence text can drift in wording between
  rounds; a hash-first match would miss the same bug on re-scan.
- **`non_critical_round_counter`** (int, starts at 0): number of rounds
  since the last user-facing prompt that produced at least one Warning
  or Suggestion. Incremented in 8d, reset to 0 only on a user
  "continue" response in 8e.
- **`consecutive_continues`** (int, starts at 0): number of times the
  user has answered "continue" at the escalation prompt during the
  current pipeline run. Incremented in 8e, never reset by any other
  step — it only resets when the pipeline exits. The hard cap is 3,
  independent of `fix_all.max_iterations` — if the user wants to run
  many rounds, the right lever is raising `fix_all.max_iterations`
  (cap per user prompt), not answering "continue" repeatedly. Phase 8e
  surfaces this tradeoff to the user when the counter is non-zero.

### 8b. Re-scan scope

After Phase 7 completes, re-run Phase 2 (logic-health) and Phase 3
(logic-review) on:

- All files modified in Phase 7.
- All files in the same module as any modified file (side-effect
  radius).
- All files that statically import from a modified file (consumer
  impact).

Do not re-scan files whose dependencies were not touched.

**Known limitation — static-graph boundary:** reflection-based calls,
string-dispatch, shared global state, test fixtures invoked via
framework magic, and similar dynamic wiring can carry regressions into
files this scan does not reach. This is an intrinsic limit of static
tracing, not a pipeline bug. If the repo has a test suite, Phase 9's
summary should recommend running it once as an additional runtime
verification — but the pipeline does not execute tests itself and does
not block on missing runtime evidence.

### 8c. Classify each new finding

For each finding Phase 3 re-emits in this round:

- If it matches an entry in `unresolvable_findings` → skip (already
  accounted for).
- Else if 🔴 **Critical** → add to Post-Fix Queue; Critical findings
  iterate until resolved OR until Phase 7d retires them (at which
  point they enter `unresolvable_findings` and stop being re-queued).
- Else 🟡 Warning / 🟢 Suggestion → add to Post-Fix Queue.

Run Phases 6–7 on the Post-Fix Queue.

### 8d. Round accounting

After Phases 6–7 complete for the current round, classify the round:

- **Clean round** (no new findings of any severity, outside
  `unresolvable_findings`): pipeline is done → proceed to Phase 9.
- **Critical-only round** (only Critical findings this round, no
  Warnings or Suggestions): do NOT increment
  `non_critical_round_counter`. Return to 8b for another round.
- **Mixed or non-critical round** (produced any Warning or Suggestion):
  increment `non_critical_round_counter` by 1. If it is now less than
  the cap, return to 8b. If it has reached the cap (default 3, or
  `.logic-lens.yaml` `fix_all.max_iterations`), go to 8e.

### 8e. User escalation

When `non_critical_round_counter` reaches the cap, show the escalation
prompt:

    ```
    Logic-Fix-All iteration cap reached.

    After {cap} non-critical rounds, N Warning and M Suggestion
    findings remain. No outstanding Critical findings
    (unresolvable Criticals, if any, are listed in the Fix Log).

    Continue for another {cap} rounds?  [Y/n]
    ```

    When `consecutive_continues` is 1 or 2 (user has continued before
    in this run), append a second line to the prompt:

    ```
    (You have continued {consecutive_continues} time(s) so far — hard
    cap is 3 continues per run. To run more rounds without repeated
    prompts, raise `fix_all.max_iterations` in `.logic-lens.yaml`
    instead.)
    ```

    Omit that line entirely on the first escalation (when
    `consecutive_continues` is still 0) — the user hasn't continued yet,
    so the count-based hint is noise.

Parse the reply using the same consent/negation rules as Phase 0b.

- **Consent:** increment `consecutive_continues` by 1. **Immediately**
  after the increment, check: if `consecutive_continues` is now ≥ 3,
  hard stop — do not start a new round. Record remaining findings as
  "Unresolved — hard iteration ceiling reached (user continued 3×)"
  and proceed to Phase 9. Otherwise reset `non_critical_round_counter`
  to 0 and return to 8b.
- **Negation (or any non-consent):** record remaining findings as
  "Unresolved — user stopped iteration at round N" and proceed to
  Phase 9.

The `consecutive_continues` check runs **at increment time**, not at
the next escalation entry, so the pipeline does not waste another full
cap of rounds before honoring the hard limit.

---

## Phase 9 — Final Report

Use the standard Report Template from `common.md` with the Fix Report
additions defined in `SKILL.md`. Additional sections to include in this
phase specifically:

- **Scope summary:** file count by role (source / config / constraint /
  doc); Phase 1f truncation notice if applied.
- **Skill invocation count:** how many times each sibling skill was run
  (health: N, review: N, locate: N, explain: N, diff: N).
- **Iteration history:** round count by severity class; each cap
  escalation and the user's response.
- **Findings by role:** separate sub-tables for source, config,
  constraint, and doc findings. A constraint-file finding is a spec
  violation, not a code bug, and should be visible as such.
- **Resolved by clarification:** any findings Phase 5 downgraded as
  false positives (visibility matters — it tells the user the pipeline
  self-corrected).

Do not output individual per-finding Premises/Trace/Divergence blocks
in the final report — those are working notes used during the pipeline.
The Fix Log table is the user-facing record. If the user asks for the
full trace of a specific finding, provide it on request.

### Logic Score computation

Compute both Logic Scores using the deduction table and the per-L-code
cap defined in `common.md` — do not reinvent the scoring rules here:

- **Logic Score (before):** start at 100 and deduct for every finding
  collected in Phases 2–4 (before any fixes).
- **Logic Score (after):** start at 100 and deduct only for findings
  still marked Unresolved after Phase 8 — resolved findings do not
  contribute.

A practical consequence of the cap: before and after can be numerically
equal even when several findings were fixed (e.g. 3 L1 findings collapse
to a single −15 in "before", and if the one remaining Unresolved in
"after" is also L1, its −15 matches). When this happens, the "Findings
fixed" count in the report header is the authoritative improvement
signal, not the score delta.
