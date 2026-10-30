# Revision-4 paired path-selection diagnostic freeze

Date: 2026-10-29. User authorized **two existing-case reviews only**, no automatic
retry, no fresh cases. Capacity/network errors stop further dispatch. One worker,
same Codex gpt-6.1-sol/high, 360-second deadline and original soft ten calls / 1600
final words. Local real-code probes and runtime protocol are unchanged. A review
timeout stays missing, with no retry; the other unattempted row may run once.

- Baseline v3: `f948b796afbbc7aac010906742ec7f88a8e64950`; instruction SHA256 `9dd5e4c50d47cd71fca3d04abc006690759e8510cdbce705a9853c4a61685e0a`.
- Candidate v4: `9f3b0cd72c67aaf000da3e8e88332efb2f3556b6`; instruction SHA256 `d429f5d89726d00cf166644a238849b0fce2e9f1a75197f0d106d5ac5fe6de37`.
- Source is the original existing semver-build buggy snapshot, SHA256 `e4b0a736dd370fd4079c00c50164a2b87aefbd1ff5bb4b03c44d0acebe90eb7b`.
- Independent isolated sessions; order randomized with seed 31 before any calls.
- Plan: `skills-workspace/codex-discovery-v4-path-selection-2026-10-29/plan.json`; SHA256 `63ebf5ed617552b4c5e4fab758c25bcbd1916c31dfd8de53aba545d9a73ce408`.
- Order: candidate 135ac75f92cc40b880c091c410ad025e, baseline 6739ba7ad215404a8ec4dc8f44450c3b.
- Estimated cumulative input+output ~840,000 tokens; planning allowance 1,200,000
  is not a hard cap. Cached input is included. Failure overhead, dollar cost and
  subscription quota use may be unknown. No cost reduction is assumed from caching.

Use the original generic review request verbatim. Do not disclose the known miss,
helper, boundary, expected next action, evaluator probe or earlier reports to reviewers.
Only their skill snapshots differ. No prompt/protocol/source/criterion changes after
freeze. Preserve all raw failures and hashes. No model judge or background retry.

## Predetermined judgment

Manually inspect real-source evidence and event order: whether the review independently
resolves the consequential operation's effective constraints and downstream use,
whether it actually tests a contract-supported distinguishing family with a control,
and whether it identifies the original defect. A path map, reading a line, keyword
mention, nearby metadata defect or counting findings is insufficient. Review all
accepted findings for unsupported/refuted claims; keep unresolved leads separate.

- Candidate does not resolve/check the key relationship: diagnostic fails; no paid
  tuning loop follows.
- Candidate checks it but misses the defect: positive process signal only, without
  demonstrated bug-discovery improvement.
- Candidate checks and detects it, baseline does not: one supporting development-set
  observation, not stable improvement, causality proof or superiority to plain Codex.
- Both do it or reports are missing: no attribution of improvement to new rules.

Use existing fixed target oracle; real implementation probes validate additional
behavior claims. Do not redefine the target to reward a neighboring defect. Adjudicator
is the implementing assistant and knows case/arm; disclose that bias. One repeat and
one known development case cannot establish generalization. Missing reports are not
semantic misses. Record known terminal usage in successful and failed attempts;
unknown failure usage remains unknown, never zero. Keep input/cache and output/reasoning
subsets distinct. No model-backed follow-up or new cases are authorized by a positive
result. The stopped v3 plan and all historical checkpoints remain unchanged.
