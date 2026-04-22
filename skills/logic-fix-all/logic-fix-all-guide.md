# Logic-Fix-All — Autonomous Audit-and-Fix Guide

This guide drives the fully autonomous pipeline. The user is not expected to
read code, make decisions, or approve intermediate steps. Every decision point
is resolved by the agent using the criteria defined here.

---

## Step 1 — Scope Sweep (Health Pass)

**Goal:** Produce a prioritized list of files to deep-review, sorted by risk.

1a. Read `.logic-lens.yaml` at the project root (if it exists) to load `ignore`
    patterns and `custom_risks`. Apply ignore patterns immediately — do not
    analyze excluded paths.

1b. Enumerate all source files in the target directory (default: repo root).
    Exclude: test fixtures, vendored code, generated files, lock files, and
    binary assets. When uncertain, err on the side of including the file.

1c. Classify each file by risk tier using the same prioritization defined in
    `logic-health-guide.md` Step 1: public API surfaces and recently changed
    files (`git log --since=30.days`) are High; core business logic without
    test coverage is High; utility modules and newly added code are Medium;
    stable, well-tested code is Low. When a file matches multiple criteria,
    assign it the highest matching tier.

1d. Sort: High first, then Medium, then Low. Within each tier, sort by
    descending line count (larger files = more surface area).

1e. State the final list at the start of the Fix Report (file name + tier).
    If the list exceeds 20 files, note that Low-tier files will be reviewed
    at reduced depth (top 3 non-trivial functions only).

---

## Step 2 — Deep Review Pass (Per File)

**Goal:** Collect every finding across all files, with full Premises → Trace →
Divergence entries. Do not write remedies yet — remedies come in Step 5.

For each file in the prioritized list from Step 1:

2a. Apply semi-formal tracing (per `semiformal-guide.md`) to:
    - All functions flagged as High-tier
    - All functions touching external state in Medium-tier files
    - Top 3 non-trivial functions in Low-tier files

2b. Record every confirmed divergence. Do not record speculative findings
    (per the Iron Law). If a divergence is suspected but not confirmed by
    trace, mark it "unconfirmed — manual check recommended" and exclude it
    from the fix queue.

2c. Tag each finding with:
    - File path and line number range
    - Risk code (L1–L6 or custom Cx)
    - Severity (Critical / Warning / Suggestion)
    - The full Premises → Trace → Divergence triple

2d. After completing all files, deduplicate: if the same root cause appears
    in multiple files (e.g., a shared utility with a bug called from five
    places), record one finding for the root cause and list all call sites.

---

## Step 3 — Failing Test / Error Integration (Conditional)

**Goal:** If concrete failures exist, collect locate findings and flag them for
priority treatment in Step 4.

Run this step only when any of the following is present:
- The user provided a stack trace or error message
- There are failing tests in the repo (`npm test`, `pytest`, `go test ./...`, etc.)
- The user described a specific wrong behavior

3a. For each concrete failure, run logic-locate: trace backwards from the
    failure point to find the exact line and condition that caused it.

3b. For each locate finding, check whether it already appears in the Step 2
    results. If yes, mark it "confirmed by test/error" (this affects priority
    in Step 4, not the fix format). If no, record it using the same tag
    format as Step 2c and mark it "confirmed by test/error".

---

## Step 4 — Fix Queue Assembly

**Goal:** Produce an ordered queue of (finding, remedy) pairs from all sources.

4a. Merge all findings collected in Steps 2 and 3 into a single queue.
    Each entry must have the full Premises → Trace → Divergence triple from
    Step 2c (required before a remedy can be written, per the Iron Law).

4b. Sort using this priority:

    | Priority | Criteria |
    |----------|----------|
    | 1 (highest) | "confirmed by test/error" findings from Step 3 |
    | 2 | 🔴 Critical (L1, L2) findings |
    | 3 | 🟡 Warning (L3, L4) findings |
    | 4 | 🟢 Suggestion (L5, L6) findings |

    Within each priority tier, fix root causes before call sites — fixing the
    root eliminates the symptom at all call sites simultaneously.

4c. For each finding, write the remedy now. The remedy must be:
    - **Minimal**: change only what the trace shows is wrong
    - **Targeted**: do not refactor surrounding code as a side effect
    - **Justified**: one sentence explaining why this fix and not another

---

## Step 5 — Apply Fixes

**Goal:** Edit the source files to resolve every finding in queue order.

5a. Apply fixes one finding at a time. After each fix:
    - Record the file path, line range changed, and a one-line description of
      the change in the Fix Log (appended to the Fix Report)

5b. If two findings in the same file affect overlapping line ranges, fix the
    higher-priority one first, then re-read the file before applying the
    second fix (to avoid stale-offset errors).

5c. Do not fix "confirmed by test/error" findings differently from others —
    the same Iron Law applies. The "confirmed" label only affects ordering,
    not the fix methodology.

5d. If a remedy requires a choice between two equally valid approaches (e.g.,
    "clamp to 0" vs "raise an error"), choose the more defensive option
    (raise / reject / fail fast). Defensive choices produce failures that are
    early, loud, and observable — which means the subsequent logic-diff in
    Step 6 can confirm the fix conclusively via static trace. Silent fallbacks
    (clamp, default, swallow) push failures into runtime state that static
    analysis cannot verify. Apply this default unless the codebase's existing
    conventions clearly prefer the other approach.

---

## Step 6 — Semantic Verification (Per Fix)

**Goal:** Confirm each fix removes the divergence and does not introduce new ones.

When multiple fixes apply to different, independent files, apply them all
before verifying — then run logic-diff on each changed file in parallel.
When fixes apply to the same file or have cross-file dependencies, apply and
verify one at a time (to avoid stale-offset errors, per Step 5b).

For each fix (or batch of independent fixes):

6a. Run logic-diff between the pre-fix and post-fix version of the changed
    function(s). Verify:
    - On the previously-failing path: the divergence is gone
    - On all previously-correct paths: behavior is unchanged

6b. If logic-diff reveals a regression (a previously-correct path now
    diverges), revert the fix, re-examine the trace, write a new remedy, and
    re-apply. After 3 failed attempts on the same finding, stop retrying:
    record it as "Unresolved — conflicting constraints" in the Fix Log and
    continue to the next finding.

6c. If logic-diff cannot confirm equivalence (e.g., the function is too
    complex or involves external state that cannot be traced statically),
    note it in the Fix Log as "unverified — integration test recommended"
    and continue to the next fix. Do not block the pipeline.

---

## Step 7 — Post-Fix Confirmation Sweep

**Goal:** Confirm the codebase is clean after all fixes are applied.

7a. Re-run logic-review on every file that was modified in Step 5. In
    subsequent rounds (if Step 7b triggers additional fixes), re-scan only
    the files modified in that round — do not re-scan already-confirmed files.

7b. For each re-reviewed file:
    - If the original findings are gone and no new findings appear: mark as ✅ Resolved
    - If a new finding appears: add it to a Post-Fix Queue and fix it using
      Steps 5–6 before continuing
    - If an original finding persists: record it as "Unresolved" with the
      reason (e.g., "requires runtime context unavailable statically")

7c. Run at most 2 Post-Fix Queue rounds. If new findings still appear after
    2 rounds, record all remaining findings as "Unresolved — exceeded fix
    iteration limit" and stop. Do not loop further.

---

## Step 8 — Fix Report Output

Use the standard Report Template from `common.md` with the Fix Report additions
defined in `SKILL.md`. Do not output individual per-finding Premises/Trace/
Divergence blocks — those are working notes used during the pipeline. The Fix
Log table is the user-facing record. If the user asks for the full trace of a
specific finding, provide it on request.
