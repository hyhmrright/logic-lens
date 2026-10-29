# Codex discovery pilot — 2026-10-28

**This pilot does not establish that the candidate finds more bugs than plain Codex.**
It confirmed one more known regression than the prior skill in 12 buggy-source
trials, tied plain Codex, and took longer than plain Codex. The sample contains only
four public development cases, and adjudication was performed by the implementing
Codex assistant with access to answers. These are observations, not independent
validation or a statistically established gain.

## Matched comparison

All arms used Codex CLI 0.164.0, `gpt-6.1-sol`, high effort, the same read-only shell
policy, source snapshots, prompts, a 360-second timeout, and a soft 10-tool-call /
1600-word limit. Every accepted report used at most nine shell calls. Two source
variants × four cases × three arms × three repetitions produced **72 completed,
source-adjudicated reviews**, 24 per arm. Each arm had 12 buggy-source trials.

| Method | Exact known-regression confirmations | Additional validated behavior classes | Unestablished assertions | Median accepted-run seconds |
|---|---:|---:|---:|---:|
| Plain Codex | 7/12 (58.3%) | 16 | 2 | 107 |
| Prior skill | 6/12 (50.0%) | 15 | 1 | 168 |
| Candidate skill | 7/12 (58.3%) | 16 | 0 | 171 |

“Additional” means outside the specific regression used to select that file; these
are deduplicated behavior classes, not an exhaustive count of independent bugs.
Some share a cause family with a target. Assertions whose contracts could not be
established are not counted as confirmed or disproved. No asserted defect was
conclusively disproved, but this does **not** establish 100% precision: the selected
files contain many real defects even after repairing the target, and three assertions
remain unresolved. The metrics must be read together with these denominators.

### Per-target confirmations (three buggy-source trials per cell)

| Target | Plain | Prior | Candidate |
|---|---:|---:|---:|
| httpx-03: explicit Request misses client timeout | 1/3 | 1/3 | 1/3 |
| httpx-10: repeated headers lost during update | 3/3 | 2/3 | 3/3 |
| requests-02: attribute-proxy stream preparation | 0/3 | 0/3 | 0/3 |
| requests-06: JSON exception pickle reconstruction | 3/3 | 3/3 | 3/3 |

The strict requests-02 annotation requires diagnosing the forwarding-wrapper
regression, rather than any upload/replay issue. Several reports instead identified
a broader non-iterable readable-body replay defect that remains after the targeted
repair. Those are valid related discoveries, not false positives. If these related
family findings are included in an **exploratory** family-level total, the totals
become plain 8/12, prior 7/12, candidate 9/12. The table keeps the stricter annotation and discloses both interpretations;
annotation was not preregistered by an independent evaluator. This sensitivity is another reason not to
claim a general improvement from this pilot.

## Evidence beyond the selected targets

Across the three arms, **23 other behavior classes** were checked on actual pinned
historical source using evaluator-only probes. For example:

- ASGI application dispatch loses to environment proxy routing.
- Authentication challenges consume redirect allowance; auth retries drop earlier history.
- Blank query values disappear; equal query objects hash differently.
- Internationalized host updates fail, and credential slashes change the parsed authority.
- Response text remains stale after encoding changes; repaired header update code caches an incompatible encoding.
- Line iteration adds CRLF-boundary records; stream/body byte counts and framing disagree.
- Ignored JSON can abort multipart preparation, and response serialization omits required state.

All probe failures were inspected at the predicted invariant/consequence; import
errors were not counted. The frozen record includes the probe source hash, failure
tails and log hashes. The final checker was rerun with bytecode writes disabled;
all 72 prepared source hashes still matched their frozen plan. Probes run in a
recorded Python 3.11 environment and use in-process transports / temporary environment
changes. They do not prove wire behavior, fix correctness, or absence of other bugs.

Two assertions about an empty proxy mapping's contract (one plain, one prior) and
one assertion about preserving an explicitly falsey custom request remain
unestablished. They are visible in the per-run judgments instead of being forced
into either “true bug” or “false positive”. Explicit open leads are excluded.

## Resource observations

| Method | Input tokens including cached | Cached input | Output tokens |
|---|---:|---:|---:|
| Plain | 5,506,475 | 4,542,720 | 71,270 |
| Prior | 9,760,991 | 8,396,544 | 131,846 |
| Candidate | 10,134,322 | 8,640,256 | 126,657 |

These are cumulative CLI terminal usage counters for the 72 accepted calls. Cached
input is a subset of input, not extra input. Dollar cost was not reported and remains
null; token ratios are not monetary estimates. Medians include CLI/provider latency
under concurrency and are not isolated latency benchmarks.

Three initial instrumentation calls completed model responses but failed driver
archival; they were excluded. Four later calls recovered from transient connection
errors and completed, but an overly strict event parser rejected the interim error
messages before the integrity guard. All four were preserved as excluded attempts
and rerun after terminal-state parsing was corrected. No failed response was counted
as a miss, and no replacement was selected based on its bug outcome. The two-case
content smoke is separate. These seven excluded calls and the smoke overhead are
not included in the accepted-run token totals and may also consume quota.

## Interpretation and next work

The candidate's known-regression difference from the prior skill is one additional
header-update success. Both trail the ideal coverage substantially, and the candidate
has not improved this primary metric over the plain-model control. Its fewer
unestablished assertions and different extra discoveries may be useful, but the
sample does not qualify it as a superior default bug detector.

The timeout misses reveal a concrete investigation problem: some reports establish
missing option propagation but withhold the issue because they cannot establish a
stronger claim such as an unbounded wait. A future revision should distinguish a
confirmed boundary-contract violation from an unverified escalation of its harm.
The wrapper-stream misses motivate concrete interface/representation probes rather
than another formatting rule. Keep the current candidate frozen; evaluate those
changes in a separate ablation and on prospective unseen projects/families.

This protocol measures targeted discovery with explicitly delivered instructions,
not host-native skill activation, production integrations, security of arbitrary
repositories, cross-language/business-domain coverage, or every coding assistant.
The portable runner is usable independently of whether the candidate is promoted.

## Inspectable artifacts

- [Frozen run, per-review judgments, commands and probe evidence](../../runs/codex-discovery-2026-10-28.json)
- [Exact prior instructions](instructions/baseline.md) and [candidate instructions](instructions/candidate.md)
- All 72 model reports are under `reviews/`; only temporary source links were normalized.
- [Corpus/protocol](../../../evals/discovery/README.md) and [content-oracle disputes](../../../evals/discovery/ORACLE_DISPUTES.md)

The implementing assistant's judgments are unblinded and require independent review.
Do not use this development pilot as a release claim or reinterpret legacy Claude
benchmark percentages as a direct Codex comparison.
