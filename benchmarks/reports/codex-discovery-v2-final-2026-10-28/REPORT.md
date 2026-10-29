# Codex discovery revision 2 — final result

**No target-detection improvement over direct Codex.** All 72 frozen trials were
successfully delivered and semantically adjudicated. Plain Codex, the previous skill,
and the revised skill each detected 9/12 selected buggy targets. Each arm detected
all three repeats of the inequality, midnight-rollover and release-diff defects;
each missed all three repeats of the long-build-identifier defect. The preregistered
requirement of at least three additional detections across at least two cases fails.
No candidate promotion or version release follows.

| Arm | Delivered | Target hits | Unsupported assertions | Output tokens | Median accepted seconds |
|---|---:|---:|---:|---:|---:|
| Plain Codex | 24/24 | 9/12 | 15 | 102,370 | 149.60 |
| Previous skill | 24/24 | 9/12 | 0 | 177,004 | 223.73 |
| Revised skill | 24/24 | 9/12 | 0 | 180,633 | 225.64 |

All 12 buggy case/repeat units are now fully matched. Repaired variants are not
assumed bug-free; confirmed remaining defects are separately recorded. No assertion
was conclusively refuted under the fixed judgments. The plain arm's 15 assertions
lack an established rejection contract, rather than being conclusively disproved.
Unresolved leads are excluded. These author judgments suggest a contract-discipline
benefit, but do not establish perfect precision or increased bug discovery.

Confirmed additional behavior classes number 18 / 17 / 17. They overlap causes,
are not independent bug counts or exhaustive recall, and cannot replace the target
endpoint. Skill-only classes include compact ordinal dates with spaces and ignored
loose options; plain-only coverage includes other range boundaries. The sets differ:
there is no overall discovery superiority conclusion. See the full per-report
judgments and [adjudication rules](../../../docs/experiments/discovery-v2-adjudication.md).

## Delivery, retries and costs

The 72 deliveries required **86 attempts**, including **14 preserved failures**:
four explicit capacity rejections and ten 360-second timeouts. Reconnect errors
occurred inside one timed-out review. Fifty-nine unique trials delivered on their
first attempt, thirteen after retry; no trial exceeded three attempts. First-attempt
delivery was plain 23/24, previous 17/24, revised 19/24. First-attempt target
deliveries were 9/12, 5/12 and 7/12 respectively; undelivered first attempts are not
capability misses. Every failed attempt remains represented after successful retry.

Two timeouts contain terminal model completion and usage, but the CLI process did
not successfully return within the deadline. Their output was never rescued into
accepted reports. Known failed usage totals 911,091 input tokens including 819,328
cached, and 20,446 output tokens. Twelve failures lack terminal usage. Unknown
failure overhead and all dollar costs remain **unknown**, not zero.

| Arm | Accepted input, including cached | Cached subset | Accepted output |
|---|---:|---:|---:|
| Plain | 4,980,084 | 4,210,432 | 102,370 |
| Previous | 9,923,646 | 8,683,008 | 177,004 |
| Revised | 10,150,615 | 8,886,528 | 180,633 |

Revised accepted output is 1.76 times plain; its observed median accepted duration
is 1.51 times plain. These are descriptive ratios, excluding failed durations.
Concurrency changed from four to three, with availability checks at one; recovery
occurred under changing service conditions. There is no controlled speed claim.
The final check used one capacity-row retry at concurrency one and three batches
of three selected retries. All ten succeeded with unchanged budgets and instructions.

## Integrity and interpretation

Candidate 32151b0 was frozen before inspecting the four validation fixes; previous
skill 83652aa stayed fixed. Every arm used Codex gpt-6.1-sol/high, a 360-second
per-attempt deadline, the same soft 10-call/1600-word budget, source exports and local
probe permission. No Claude runtime was used. Reviewer workspaces excluded history,
fixes, future regression tests and evaluator probes. All execution remained on the
original frozen plan. No matching rules, cases or prompts were tuned during recovery.

The [final record](../../runs/codex-discovery-v2-final-2026-10-28.json) contains all
72 planned rows and reports, source/instruction/report/event/probe hashes, semantic
judgments, all failed attempts, first-attempt delivery and recovery changes. All
three instruction snapshots and evaluator sources are published alongside this report.
The [35-report partial](../codex-discovery-v2-partial-2026-10-28/REPORT.md) and
[62-report checkpoint](../codex-discovery-v2-checkpoint-2026-10-28-62/REPORT.md)
remain unchanged. The final record retains the checkpoint's correction that two
failed attempts have known terminal usage.

Only four public historical cases across two projects were tested, with author
selection and unblinded implementing-assistant adjudication. Public-source training
contamination is possible. Repeats are not independent new defects. The common local
probe protocol differs from the earlier development pilot equally for all arms;
its effects cannot be attributed to the skill. This set is now development material.
A future design needs a new preregistered comparison and unseen cases; tuning here
cannot establish a fresh validation gain. See [failure analysis and proposed next
experiment](../../../docs/experiments/discovery-v2-final-analysis.md).
