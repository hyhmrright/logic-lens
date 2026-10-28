# Codex discovery revision 2 — 62-report checkpoint

**The frozen candidate cannot meet this experiment's preregistered target-gain
threshold.** The matrix remains incomplete: 62/72 reviews were delivered and
adjudicated, and all 72 unique trials have been attempted. Plain Codex has completed
all 12 buggy trials and detected 9 targets. The revised candidate has 8 detections
in 10 completed buggy trials. Even if both missing buggy trials detect their targets,
its maximum is 10/12: only one more than plain, below the required three. This bound
does not count failed delivery as a missed bug. It rules out the specified practical
improvement, not every possible precision benefit or future skill design.

The original [35-report publication](../codex-discovery-v2-partial-2026-10-28/REPORT.md)
is preserved. This checkpoint adds 27 accepted reports, including four from the
first recovery check and 23 from the following check. Continue the same frozen plan
to resolve missing reports; do not tune the candidate or change matching criteria.

## Coverage and matching

| Arm | Delivered / planned | Buggy targets detected / delivered | Buggy trials missing |
|---|---:|---:|---:|
| Plain Codex | 23/24 | 9/12 | 0 |
| Previous candidate | 18/24 | 5/7 | 5 |
| Revised candidate | 21/24 | 8/10 | 2 |

These completed-only fractions have different case compositions and are not fair
recall comparisons. Sixteen source-variant/repeat units have all three arms; seven
are buggy, with **5/7 target detections for each arm**. All completed buggy reviews
in every arm still miss the selected long-build-identifier tail becoming a release
digit. Other metadata failures do not count as that target.

A newly verified additional behavior class is compact ordinal-date dispatch with
whitespace: `2017123 1230` returns December 3 at 23:00 instead of May 3 at 12:30.
Both previous and revised skill reports discovered this class; no completed plain
report did. Existing ordinal fixtures and the documented arbitrary separator supply
the oracle. Evaluator-only probes reproduce it in both source variants. It is not
an extra target hit and does not rescue the preregistered endpoint.

The plain arm contains 15 assertions whose rejection oracle remains unestablished;
the other completed arms contain none under the fixed adjudication rules. These
are not conclusively refuted findings. Unblinded contract interpretation and unequal
coverage prevent a clean overall precision comparison. Explicit unresolved leads
are excluded. Additional classes overlap implementation causes and are not counts
of independent bugs. See [adjudication notes](../../../docs/experiments/discovery-v2-adjudication.md).

## Execution and failures

There have been **76 calls: 62 accepted reports and 14 failed attempts**. Fifty-nine
trials delivered on their first attempt, three delivered after archived failures,
and ten remain undelivered. There are no unattempted trials. Failures comprise four
explicit capacity rejections and ten 360-second timeouts. Request reconnect failures
also appear in a recent timed-out review; the timeout is not reclassified as a
completed capability miss. Two failed attempts for the same candidate range trial
contain `turn.completed` events but did not return successfully before the process
deadline. Their reports remain unaccepted; terminal model completion and delivery
are different events.

Recovery used one availability trial at concurrency one, then concurrency three.
Dispatch stopped on a timeout; pending rows were resumed twice without changing
model, instructions, hashes or budgets. The final batch contained a request reconnect
timeout, after which no further calls were dispatched in this check. Concurrency
and provider conditions differ from preregistration, so elapsed times do not support
a controlled speed claim. Every current failure and archived attempt is retained.

Accepted-call token usage:

| Arm | Input including cached | Cached subset | Output |
|---|---:|---:|---:|
| Plain | 4,747,647 | 4,005,504 | 97,534 |
| Previous | 7,766,230 | 6,786,304 | 132,026 |
| Revised | 8,908,928 | 7,795,456 | 158,117 |

Correction to the initial partial report: failed-call terminal usage is not wholly
unavailable. Two preserved failed attempts contain usage totaling 911,091 input
(including 819,328 cached) and 20,446 output tokens. These are additional to the
accepted-call table. The other twelve failures lack terminal usage; complete failed
costs and all dollar costs remain unknown. The machine-readable checkpoint preserves
available per-attempt usage instead of assuming zero overhead.

## Frozen design and continuation

Candidate 32151b0 and previous candidate 83652aa remain unchanged. All calls use
Codex `gpt-6.1-sol`, high effort, the same 360-second deadline, frozen explicit
instructions, source snapshots, and common local-probe protocol. No Claude runtime
is used. The held-out fixes, evaluator probes, history and future tests remain
outside review contexts. Common-protocol changes from the previous pilot apply to
all arms and cannot be credited to the skill.

The [record](../../runs/codex-discovery-v2-checkpoint-2026-10-28-62.json) includes all
72 planned rows, 62 reports and judgments, instruction/source/report/probe hashes,
14 failures, first-attempt deliveries, recovery notes and target bounds. Evaluator
sources are snapshotted here independently of later probe extensions. The original
partial artifact is not overwritten. Resume
`skills-workspace/codex-discovery-v2/plan.json`, retry capacity-rejected rows first,
and keep retries bounded without extending the per-call deadline. Remaining review
timeouts must stay visible even if later delivery succeeds.

This is four public historical cases in two projects with author selection and
unblinded assistant adjudication. It cannot establish universal performance, and
training contamination remains possible. The finding is narrower and already
conclusive: this candidate fails the preregistered +3 target-gain threshold even
under its best remaining outcome. No release promotion is justified.
