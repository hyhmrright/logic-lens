# Model and host compatibility

Logic-Lens's Markdown framework has no model-provider dependency. The maintained
execution default is authenticated Codex CLI, with explicit instruction snapshots.
See [TOOL_COMPATIBILITY.md](TOOL_COMPATIBILITY.md) for generic CLI adapters and
portable editor/assistant use. Claude is not required or used by active eval defaults.

Effectiveness depends on the host/model/tool combination and must be measured under
that combination. Do not extrapolate historical Claude scores to Codex or another
provider. `benchmarks/runs/` preserves original records; those are historical evidence,
not a recommendation to use the corresponding provider.

Three distinct questions must be measured separately:

1. Did the host receive the intended instructions? Save exact snapshots and hashes.
2. Did the host actually use the intended tools and follow the procedure? Inspect events.
3. Did it find a real behavioral defect without unsupported claims? Adjudicate root
   cause, consequence and reachability against source-backed evidence.

A literal report label is not evidence of skill activation. Description routing is
not editor-native activation. CLI process success is not evidence of correct reasoning.
Use same-provider/model paired runs to compare skill changes; cross-model comparisons
are separate studies. Record model, effort, tool policy, versions, usage and limitations.

Measured Codex evidence: [2026-10-28 pilot](../benchmarks/reports/codex-discovery-2026-10-28/REPORT.md),
CLI 0.164.0, gpt-6.1-sol, high effort, four development cases, 72 paired reviews.
Candidate exact-regression confirmations tied plain Codex (7/12); no superiority
claim is supported. This tests explicit delivery, not native activation.
