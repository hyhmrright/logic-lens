# Revision-3 Gate B execution freeze — 2026-10-29

The user explicitly approved eight existing-case diagnostic reviews, no automatic
retry, no new-case evaluation. This authorizes Gate B only, not Gate C.

- Candidate commit: `f948b796afbbc7aac010906742ec7f88a8e64950`; old candidate: `32151b0f9c10a557d1da81dad0dd1b221522333d`.
- Runner-native candidate instruction SHA256: `9dd5e4c50d47cd71fca3d04abc006690759e8510cdbce705a9853c4a61685e0a`.
- Runner-native old instruction SHA256: `774330a59357599fc2be1f1c93211690202352d84166946ef7f50f20cd4e9c0c`.
- Plan SHA256: `0d531a75ef67b0e4ef93cb72ed08393269d23237a3374e7706aefff04224904a`.
- Scratch plan: `skills-workspace/codex-discovery-v3-gate-b-2026-10-29/plan.json`.
- Eight buggy-only reviews: four existing v2 cases × two arms × one repeat.
- Paired randomized case/arm order, seed 31; one worker; Codex gpt-6.1-sol/high;
  360 seconds each; unchanged soft 10 tool calls / 1600 final words.
- Existing source snapshots copied with exact tree-hash equality; original probe
  permissions and Python/Node runtime protocol retained. No evaluator evidence in reviewer prompts.
- Runner-native resource order is the original discovery runner order, unchanged
  across both arms; its SHA differs from the portable compiler's resource order.
- Planning estimate about 3.5 million cumulative input+output tokens, including
  cached input; 4.5 million allowance is an estimate, not a hard cap. Fees and
  subscription quota consumption are unknown. Failures can consume tokens.
- At most eight dispatches, no retry. Capacity/network failure stops new dispatches;
  review timeouts remain missing and other unattempted trials may proceed.
- No skill/prompt/budget changes after this freeze; publish all attempts and
  source-backed manual behavior judgments, including missingness and limitations.

This records execution authorization, not a claim of diagnostic improvement.
