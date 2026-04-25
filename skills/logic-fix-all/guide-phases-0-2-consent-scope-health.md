# Logic-Lens — Logic Fix All — Phases 0-2 (Consent · Scope · Health)

Detailed execution for the first three phases of the Logic-Fix-All pipeline. Navigation and overview live in sibling file `logic-fix-all-guide.md`.

Scope of this file: **Phase 0** (pre-flight notice + consent gate), **Phase 1** (scope enumeration — walk the entire repo, classify files by role and risk tier), **Phase 2** (health pass — module-level Logic Score map before any deep review).

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

