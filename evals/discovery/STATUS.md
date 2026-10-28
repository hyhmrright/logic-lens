# Experiment status — 2026-10-28

**Decision: experimental candidate; effectiveness unmeasured. Do not release.**

Implemented a seven-step investigation process in logic-review: sourced behavioral
invariants, dependency slices, sequence-based hypotheses, candidate evidence states,
faithful verification, remedies, and scoped reporting. Shared edits resolve conflicts
with the old depth/confidence/verification rules and correct the universal L4
mutate-and-return assertion. No other skill entry points were rewritten. The legacy
content cases and grader have not been relaxed or modified.

## Evidence collected

- 20 upstream historical source pairs: 10 HTTPX and 10 Requests. Every base/fix
  commit is pinned in `catalog.json`; repair tests and future history are hidden
  from model workspaces. These are development seeds, not a held-out corpus.
- 19 target failures were inspected on the actual original source and passed after
  the implementation-only repair. 18 pairs verified on Python 3.11.18; requests-01
  verified on Python 3.15.2 (the trigger did not reproduce on 3.11). requests-07
  needs Windows and remains blocked. Assertions, environments, limitation notes,
  and failing/passing log hashes are recorded in the catalog. No model was involved.
- Python 3.15 initially blocked eight historical HTTPX cases in an old dependency
  import. These were setup failures, not bug detections; the 3.11 rerun resolved them.
- A two-case, one-repeat smoke matrix prepared 12 opaque workspaces with explicit
  plain/baseline/candidate instructions. The first model call failed authentication:
  `Failed to authenticate: OAuth session expired and could not be refreshed`.
  No model reviews completed, and no recall/precision improvement is claimed.
- Offline validation covers safe snapshots, parent pinning, future-test/history
  exclusion, instruction/source drift, actual tool-event parsing, failed runs,
  source-mutation rejection, and incomplete/human-adjudicated metrics.

The full run artifacts remain in ignored `skills-workspace/`; the catalog retains
portable verification evidence. The model smoke attempt used read-only tools and
no account credentials were stored. The frozen baseline skill is `bcf8dbd3f3a5bf6bb34fb46e0284c78303f9fba2`;
`catalog.json` is authoritative for that revision.

## Remaining release gates

1. Supply valid provider/API credentials to a supported Claude CLI. The bare-mode
   runner does not rely on ambient plugin caches or interactive OAuth login.
2. Re-prepare snapshots after final candidate edits; existing plans deliberately
   retain the exact earlier snapshot and must not be reused for a different candidate.
3. Run plain/baseline/candidate with identical actual read tools, model, effort,
   source pairs and budgets; use at least three paired repeats and human root-cause
   adjudication. Report tool availability, per-project/family results and variance.
4. Predeclared operational gates for this candidate: recall improves over the prior
   skill across paired repeats; false positives per review do not increase; completed
   review cost stays within 2× baseline. Reject unmatched/incomplete comparisons.
   These are operating gates, not a claim of statistical significance.
5. Reserve additional unseen repositories/defect families for prospective held-out
   validation before further tuning. Current two-project seeds cannot establish
   general real-world coverage, and public-history memorization remains possible.
6. Run the unchanged content regression suite after cache synchronization. Record
   existing oracle disputes (including eval-279) separately, never change expected
   answers merely to make the candidate score better.
7. Run an execution-capable protocol in a disposable isolated environment separately
   before claiming improved integration/runtime verification. This first model
   protocol measures targeted, repository-context discovery using read tools.

No version bump, deployment, merge, or published benchmark claim is authorized by
passing the offline structural checks alone.
