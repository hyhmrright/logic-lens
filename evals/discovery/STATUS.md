# Experiment status — 2026-10-28

**Decision: portable execution works; both completed comparisons fail to establish
candidate detection superiority.**

The [final revision-2 comparison](../../benchmarks/reports/codex-discovery-v2-final-2026-10-28/REPORT.md)
completed 72/72 reviews on four new historical dateutil/node-semver defects after
freezing candidate 32151b0. Plain, previous skill and revised skill each detected
9/12 targets. The long-build-identifier target was missed in every arm and repeat.
The revised skill's 0 versus plain's 15 unsupported assertions suggests more careful
contract handling under author adjudication, without increased target discovery.
Accepted output was 1.76 times plain; observed median duration was 1.51 times plain,
with changed concurrency and service conditions precluding a controlled speed claim.
All 14 failed attempts are preserved; 59 deliveries succeeded first try and 13 after
retry. Dollar cost and part of failed-call usage remain unknown. No missing reports
remain. The automatic recovery task is finished; no candidate promotion follows.

Revision 3 is an unqualified compact candidate, with an
[offline audit](../../docs/experiments/discovery-v3-development-audit.md) and an
[approval-gated preregistration draft](../../docs/experiments/discovery-v3-preregistration.md).
No new model experiment is authorized or executed. Development behavior checks and
fresh-case comparisons each require a new user approval; no automatic recovery is active.

The following earlier pilot remains development evidence:

Codex completed the 72-review, four-case paired pilot (three arms, both source
variants, three repetitions). Exact known-regression confirmations: plain 7/12,
prior skill 6/12, candidate 7/12. Additional validated behavior classes: 16 / 15 / 16.
Accepted-run median seconds: 107 / 168 / 171. The candidate ties the plain-model
primary result with higher observed resource use. This is not a general gain claim.

See [the full report](../../benchmarks/reports/codex-discovery-2026-10-28/REPORT.md)
and [frozen per-run evidence](../../benchmarks/runs/codex-discovery-2026-10-28.json).
All 72 reports and exact instruction snapshots are committed. Adjudication was by
the implementing Codex assistant, unblinded; independent human validation remains
outstanding. The strict wrapper-specific target and exploratory related-family
interpretation are both disclosed. Unestablished contracts are kept separate from
confirmed and disproved claims. The 23 additional evaluator checks and all 72
prepared source hashes were rechecked; no model responses were promoted solely
because they contained labels or keywords.

The original 20-pair corpus remains available: 19 target pairs locally verified,
one Windows-only pair blocked. The model pilot used four cases, not all 20. These
public development cases are not a prospective holdout. Three initial instrumentation
calls and four recovered-stream archival failures were excluded; accepted replacements
and overhead are documented. The corrected parser accepts a successful terminal turn
following transient errors and preserves source-integrity evidence before parsing.

The two-case Codex content smoke completed using the unchanged grader: logic 33.3%,
overall 50%, contract 100%. That is not a complete content-suite result or a prior-skill
comparison. Eval-1's unspecified suffix contract is documented in ORACLE_DISPUTES.md;
its original failing score was preserved rather than fixing the oracle to lift it.

Maintained execution now uses Codex or a generic command adapter. No Claude account,
CLI or plugin cache is required. All six skills export as a portable Markdown pack;
other coding tools' native execution is not claimed without host-specific validation.
See [tool compatibility](../../docs/TOOL_COMPATIBILITY.md).

No release/version bump or candidate promotion follows from this pilot. Next gates:
prospective unseen repositories/defect families, independent adjudication, a separate
execution-capable protocol, and broader unchanged content regression checks. Focus a
future ablation on boundary-contract consequences and wrapper/interface probes;
keep this measured candidate frozen rather than tuning it against the same reports.
