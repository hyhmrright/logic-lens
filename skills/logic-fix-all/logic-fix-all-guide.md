# Logic-Fix-All — Autonomous Audit-and-Fix Guide

This guide drives a full-repository, logic-level, semi-formal tracing
pipeline. It orchestrates the other five Logic-Lens skills — **logic-health,
logic-review, logic-locate, logic-explain, logic-diff** — and iterates
until the codebase is clean.

The only hard interaction point is **Phase 0 (Pre-flight consent)**. After
the user approves, the pipeline runs hands-free unless Phase 8 hits the
iteration cap and escalates.

This is a **logic** review, not a syntax/style/lint pass. If the user wants
formatting or convention fixes, point them at a linter instead.

---

## Phase 0 — Pre-flight Notice & Consent Gate

**Goal:** Tell the user exactly what's about to happen and get explicit
consent before any scanning or editing. This is the one interaction the
pipeline always performs.

0a. Estimate file count using the best available source:
    - In a git repo: `git ls-files | wc -l` (respects `.gitignore`).
    - Not in a git repo: detect the project marker (per Phase 1b) and
      run `find . -type f` with the relevant exclusions applied up
      front — e.g.
      `find . -type f -not -path '*/.git/*' -not -path '*/node_modules/*' -not -path '*/target/*' -not -path '*/.venv/*' -not -path '*/build/*' -not -path '*/dist/*' -not -path '*/vendor/*' | wc -l`.
      Order-of-magnitude is enough — the user only needs it for the
      cost notice, not for exact scope.

    Then display the notice below verbatim with the estimate filled in.
    Do not skip or paraphrase — the user is agreeing to this exact
    scope and cost profile.

    ```
    ⚠️  /logic-fix-all — Full Repository Logic Audit & Fix

    Scope:    ENTIRE repository, not just recent commits or staged changes.
              Includes runtime-affecting files: source code, runtime
              config (.json/.yaml/.toml/.ini), constraint files
              (CLAUDE.md, .logic-lens.yaml, AGENTS.md, etc.), and
              behavioral documentation (README, ARCHITECTURE, ADRs).
              Auto-excludes .git, build artifacts, dependency caches,
              binary assets; respects .gitignore and .logic-lens.yaml
              `ignore:` patterns.
    Estimated files to scan: ~N

    Method:   Semi-formal execution tracing — Premises → Trace →
              Divergence → Remedy. This is a LOGIC review, not a
              syntax/style/lint pass.

    Skills:   logic-health → logic-review → logic-locate → logic-explain
              → logic-diff, iterated until clean.

    Token cost: HIGH. Budget roughly 5k–15k tokens per file for a full
    trace (more for deeply interprocedural code, less for stateless
    utilities), times ~1.3 for iteration rounds.
    Your estimate: N files × ~10k tokens × 1.3 ≈ (compute and show
    here, e.g. "~1M tokens").
    Larger repos or high finding density push this higher.

    Git impact: The pipeline edits source files. It does NOT commit,
    push, or amend. If you have uncommitted work, commit or stash first
    so you can revert if needed.

    Iteration: Critical findings loop until resolved (no cap). Warnings
    and Suggestions default to 3 rounds, configurable via
    `.logic-lens.yaml` `fix_all.max_iterations:`. When the cap is hit
    with non-critical findings remaining, you will be asked whether to
    continue another batch of rounds.

    Proceed with full autonomous run? [Y/n]
    ```

0b. Parse the user's reply. The agent maintains two independent
    phase-local counters (neither resets the other; both reset when
    Phase 0 exits):
    - `consecutive_pauses` — rule 2 bumps this each soft-pause reply.
    - `consecutive_questions` — rule 4 bumps this each question reply.

    Signal sets:
    - **Consent signals** (reply contains any, case-insensitive): `Y`,
      `yes`, `ok`, `sure`, `proceed`, `go`, `continue`, `继续`, `好`,
      `好的`, `行`, `可以`.
    - **Hard negation signals**: `no`, `n`, `abort`, `cancel`, `取消`,
      `don't`, `不要`.
    - **Soft-pause signals**: `wait`, `hold on`, `not yet`, `一下`,
      `先别`, `等一下`, `等我`, `let me`.

    Decision (evaluate in this order — first match wins):
    1. Hard negation present (with or without consent) → abort with
       "Aborted by user before scan — no files modified".
    2. Consent present AND soft-pause present (e.g. "yes, let me stash
       first", "好，等我 push 一下") → treat as consent-with-pause.
       Increment `consecutive_pauses`. Acknowledge in one line
       ("Understood, waiting for your go-ahead after the pause."),
       then wait for the user's next message and re-run rule matching
       on it. If `consecutive_pauses` would reach 3 on this increment,
       re-show the Phase 0 notice in full (scope/method/cost/iteration)
       and reset `consecutive_pauses` to 0 — long pauses may have
       changed the user's context, so re-confirm before proceeding.
    3. Consent present AND no negation → proceed. If the reply also
       carries specific instructions (e.g. "skip frontend/", "output
       the report in Chinese"), acknowledge them in one line and honor
       them in later phases (respect scope narrowing, language
       preference).
    4. Reply is a question → increment `consecutive_questions`, answer
       the question, then re-prompt once. If `consecutive_questions`
       would reach 2 on this increment, answer the question and fall
       through to rule 5 immediately (no further Q&A — re-show the
       notice once).
    5. Reply is wholly unrelated (none of the above matched, or falling
       through from rule 4) → re-show the notice once; if the next
       reply still matches none of rules 1–4, treat as abort.

0c. After consent, do not ask further questions until Phase 8 cap
    escalation — unless the user's consent reply included specific
    instructions that require a one-line confirmation before Phase 1.

---

## Phase 1 — Scope Enumeration

**Goal:** Build the complete file list the pipeline will review. Whole-repo
coverage is the contract — recency is a prioritization signal, not a scope
filter.

1a. Read `.logic-lens.yaml` at the project root (if present) to load
    `ignore` patterns, `custom_risks`, `severity:` overrides, and
    `fix_all.max_iterations`. Apply `ignore` patterns immediately.

1b. Detect project type from marker files and derive default exclusions.
    The pipeline must not hardcode a single exclusion list — infer from
    the repo structure actually present:
    - `package.json` → exclude `node_modules/`, `dist/`, `build/`,
      `.next/`, `.nuxt/`, `coverage/`
    - `Cargo.toml` → exclude `target/`
    - `go.mod` → exclude `vendor/` unless the vendored tree is
      project-owned (check for a project-local `modules.txt` vs a
      managed one)
    - `pyproject.toml` / `requirements.txt` / `Pipfile` → exclude
      `.venv/`, `venv/`, `__pycache__/`, `*.egg-info/`,
      `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`
    - `Gemfile` → exclude `vendor/bundle/`
    - `pom.xml` (Maven) → exclude `target/`
    - `build.gradle` / `build.gradle.kts` (Gradle) → exclude `build/`,
      `.gradle/`
    - `build.sbt` (Scala/sbt) → exclude `target/`, `project/target/`
    - `mix.exs` (Elixir) → exclude `_build/`, `deps/`
    - `composer.json` (PHP) → exclude `vendor/`
    - `*.csproj` / `*.sln` (.NET) → exclude `bin/`, `obj/`
    - `pubspec.yaml` (Dart/Flutter) → exclude `.dart_tool/`, `build/`
    - Always exclude: `.git/`, `.DS_Store`, lock files (`*.lock`,
      `package-lock.json`, `yarn.lock`, `Pipfile.lock`, `poetry.lock`,
      `Cargo.lock`, `go.sum`), log files, binary extensions
      (`.png/.jpg/.gif/.pdf/.wasm/.zip/.tar/.gz/.woff*/.ttf`)
    - Respect `.gitignore` as a hint, but do not follow it blindly —
      some ignored paths can still be relevant (e.g. a local env
      template that the code reads).

1c. Enumerate files by role. Every non-excluded file falls into exactly
    one bucket:
    - **Source code:** files whose extension matches a language the
      project actually uses, derived from the markers detected in 1b
      (npm → .js/.jsx/.mjs/.cjs/.ts/.tsx; Cargo → .rs; go.mod → .go;
      Python markers → .py; Gemfile → .rb; Maven/Gradle → .java/.kt/.kts;
      sbt → .scala/.sc; mix.exs → .ex/.exs; composer.json → .php;
      .csproj → .cs; pubspec.yaml → .dart; Swift Package → .swift;
      plus .c/.h/.cpp/.hpp, .sh/.bash/.zsh, .lua, .r/.R for projects
      that contain those files regardless of marker). When a file's
      extension is recognized but no marker was detected, include it
      anyway — marker absence just means exclusions can't be inferred,
      not that the code isn't real.
    - **Runtime config:** `.json`, `.yaml/.yml`, `.toml`, `.ini`,
      `.conf`, `*.config.js/ts` — files the code actually reads at
      startup or runtime. Verify by grepping the codebase for the file
      name before classifying; an unreferenced config file is a
      behavioral-doc candidate instead.
    - **Constraint files:** `CLAUDE.md` at every level, `.logic-lens.yaml`,
      `AGENTS.md`, `GEMINI.md`, schema files referenced by code
      (`*.schema.json`, `openapi.yaml`, `*.proto`, `*.graphql`).
    - **Behavioral docs:** `README.md`, `CONTRIBUTING.md`,
      `ARCHITECTURE.md`, `docs/**/*.md` describing runtime behavior,
      and environment-variable templates like `.env.example` (which
      document required env vars even when the code doesn't parse the
      template directly). Skip pure changelogs, licenses, and
      marketing copy. `.editorconfig` is a pure editor convention —
      skip it entirely.

1d. Classify each file by risk tier. Fix-all uses a 3-tier system (High /
    Medium / Low), folding `logic-health-guide.md` Step 1's 4-tier system
    as: its "Highest" + "High" → High; its "Medium" → Medium; its "Lower"
    → Low. Concretely:
    - **High:** public API surfaces; files changed in the last 30 days
      (`git log --since=30.days --name-only --pretty=format: | sort -u`);
      core business logic without test coverage.
    - **Medium:** utility modules, helpers, non-core configs, stable
      constraint files.
    - **Low:** stable well-tested code, stable docs.

    Newly added files are by definition "recently changed" and therefore
    already High — do not also list them as Medium. Constraint files and
    behavioral docs are Medium by default, upgraded to High if referenced
    by recently-changed code. When a file matches multiple criteria,
    assign the highest matching tier.

1e. Sort: High → Medium → Low; within each tier, descending line count.

1f. Apply scope caps to keep the pipeline bounded on large repos:
    - **>20 files:** Low-tier files reviewed at reduced depth (top 3
      non-trivial functions only).
    - **>100 files:** after prioritization, keep only the top 100 entries
      ranked by (tier desc, line-count desc); drop the rest. Note the
      truncation in the Fix Report so the user can re-run on a narrower
      scope. Do not pause to ask — consent was given in Phase 0.

1g. State the final list at the start of the Fix Report: file name +
    tier + role (source/config/constraint/doc).

---

## Phase 2 — Health Pass (logic-health)

**Goal:** Big-picture risk map before drilling into individual files.

2a. Read `logic-health/logic-health-guide.md` and apply its methodology
    to the Phase 1 file list. Output:
    - Per-module Logic Score
    - Aggregated findings by L-code
    - Systemic patterns (repeated L-codes across modules, risk
      concentration, architectural enablers)

2b. Record Phase 2 output for reference. Do NOT write remedies yet — the
    health pass gives shape, not precision. Precise findings come from
    Phase 3.

2c. If the health pass reveals a systemic pattern (same L-code in 4+
    modules), earmark it for **Phase 3 priority review** rather than
    queuing it directly. Pick a representative file exhibiting the
    pattern and pin it to the top of Phase 3's file list. Phase 3 will
    produce the full Premises → Trace → Divergence triple on the
    representative file; only after that triple exists does the
    pattern enter Phase 6 as a root-cause fix candidate. This preserves
    the Iron Law — a systemic observation without a trace cannot
    justify a remedy.

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
    - Risk code (L1–L6 or custom Cx)
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
