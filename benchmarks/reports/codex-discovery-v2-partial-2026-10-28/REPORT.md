# Codex discovery revision 2 — incomplete, 2026-10-28

**The revised skill has not demonstrated superiority over plain Codex.** The
comparison is incomplete: 35 of 72 planned reviews completed and were adjudicated.
Four provider-capacity failures and four timeouts interrupted execution. Do not
compare completed-only recall rates across arms with different case composition.
The user chose to retain the same model and resume when capacity returns.

## Design and isolation

[Miss analysis](../../../docs/experiments/discovery-v2-miss-analysis.md) identifies
counterexample selection, conflating local violations with downstream escalation,
and verification/report overhead as investigation obstacles. Candidate **32151b0**
adds obligation-boundary maps, paired counterexamples, early distinguishing probes,
and the smallest supported observable consequence. It contains no case-specific
fixes or triggers. The prior-skill control is **83652aa**, the previous pilot's
candidate, not that pilot's older baseline.

The candidate was committed and pushed before the dateutil/node-semver fixes were
inspected. The [preregistration](../../../docs/experiments/discovery-v2-preregistration.md)
sets the endpoint and threshold before model execution. Four fresh real defects
span Python and JavaScript: rich comparison fallback, dated-midnight rollover,
release-component classification, and build-metadata normalization. All four
real-source probes failed before their upstream fix and passed after it. One other
candidate was excluded before reviews because its intended rejection conflicted
with the parent grammar. See the [catalog](../../../evals/discovery/catalog-v2.json).

All arms use Codex CLI 0.164.0, `gpt-6.1-sol`, high effort, frozen explicit instruction
snapshots, identical source variants, a soft 10-tool-call / 1600-word limit, and a
360-second hard timeout. No Claude dependency or account is used. History, future
tests, evaluator probes, fix descriptions and host instructions are withheld.

The common prompt now permits pure local probes equally for every arm. This protocol
change cannot be credited to the new skill or compared directly against the previous
pilot. Runtime: Node.js v26.12.1 and Python 3.11.18 with six 1.17.0. The recorded Python
environment and evaluator sources are archived under `evaluator/` in this report.

## What completed

| Arm | Planned | Completed and adjudicated | Still missing |
|---|---:|---:|---:|
| Plain Codex | 24 | 14 | 10 |
| Previous candidate | 24 | 10 | 14 |
| Revised candidate | 24 | 11 | 13 |

Only four source-variant/repeat units have all three arms completed. Two are buggy
units: rich comparison repeat 0 was found by all three; build metadata repeat 2 was
missed by all three. That is **1/2 for each arm on this tiny matched buggy subset**,
not an overall recall estimate. Across the six completed buggy build-metadata reports,
no arm diagnosed the selected long-identifier tail becoming a release digit.

Additional verified behavior includes equal weekday objects missing dictionary
lookups, incorrect leap-year ordinal dates, numeric identifier precision loss,
loose options being discarded, prerelease OR simplification, and range intersections
contradicting a concrete common witness. The upstream date-rollover repair introduces
a separate time-only midnight failure, correctly discovered on repaired source.
Repaired snapshots therefore cannot be assumed to contain no other bugs.

Additional counts in the machine-readable record are **behavior classes**, with
several overlapping intersection causes. They are not independent root-cause counts
or a replacement for the preregistered target endpoint. Explicit open leads are
excluded. [Adjudication notes](../../../docs/experiments/discovery-v2-adjudication.md)
explain unresolved strictness and prerelease-promotion oracles. An observed output
alone does not establish the required behavior; unsupported assertions are separate
from refuted assertions. No claim of perfect precision follows from this partial set.

## Failures and protocol deviations

There were **43 calls: 35 completed reports and 8 failed attempts**. Thirty-nine
unique planned trials were attempted: 32 succeeded on their first attempt, three
succeeded after a preserved failure, and four remain failed. Thirty-three trials
were not yet attempted. The selected-model capacity error occurred both before and
during review; it is not an authentication error.

The four timeout attempts reached the uniform 360-second limit. Some coincide with
model-refresh failures and a capacity window; model/infrastructure contributions
cannot be reliably separated. A candidate range review timed out twice and remains
unfilled. None is silently counted as a completed miss or discarded as an irrelevant
infrastructure event. The record retains first-attempt delivery and every failure.

After 34 completions, concurrency was reduced from four to three to recover from
capacity errors; capacity rejection continued. This deviates from preregistration,
and pooled elapsed times are not a controlled speed benchmark. The model, effort,
instructions, source hashes, review request and per-call timeout did not change.
Dispatch stopped on failure instead of continually launching paid retries.

Accepted-call usage, with unequal completion counts:

| Arm | Input including cached | Cached subset | Output |
|---|---:|---:|---:|
| Plain | 3,037,001 | 2,557,568 | 61,205 |
| Previous | 4,303,844 | 3,744,384 | 76,483 |
| Revised | 4,646,026 | 4,045,056 | 83,251 |

Failed-call terminal usage and dollar cost are unavailable. These totals exclude
that overhead and must not be used to claim an efficiency gain.

## Interpretation and continuation

The mechanisms now make counterexample search explicit, but completed reports still
miss the hard representation-boundary target. Large skill reviews spend calls and
output on proposed fixes and their verification; plain reviews often describe more
issues within the same report budget. This is an observed investigation pattern,
not yet a causal estimate or evidence that a new revision would win.

The [machine-readable record](../../runs/codex-discovery-v2-partial-2026-10-28.json)
preserves the full 72-row plan, 35 reports and judgments, instruction/report/probe
hashes, target failures and repairs, failed attempts, recovery policy, and missingness.
The operational plan remains at `skills-workspace/codex-discovery-v2/plan.json`.
Resume that exact plan with the same model and instruction snapshots; do not tune the
candidate against these answers. Failed retries are automatically archived, and
`--run-id` permits a bounded availability check without changing the plan. Retain
this partial publication when later publishing complete results.

Adjudication was by the implementing assistant with access to answers, not an
independent human. Four public historical cases cannot establish broad superiority;
training contamination, author case selection, incomplete coverage and provider
failures remain limitations. The preregistered success criterion is **not evaluated**
until a sufficient matched comparison is complete. No release promotion is justified.
