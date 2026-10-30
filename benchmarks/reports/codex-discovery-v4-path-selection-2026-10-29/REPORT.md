# Revision-4 paired path-selection diagnostic

Date: 2026-10-29. **The diagnostic fails: no demonstrated improvement in selecting
and checking the key relationship.** Both frozen arms delivered on their only
attempt. Neither tested the effective long-metadata boundary or detected the
original target defect. Some investigation actions differ, but those differences
must not be promoted into success on the preregistered diagnostic.

| Observation | Baseline v3 | Candidate v4 |
|---|---|---|
| Accepted reports | 1/1 | 1/1 |
| Effective bound's constant definition read | no | yes |
| Key constraint/consumer relationship resolved in evidence | no | no |
| Contract-supported family at that boundary executed | no | no |
| Original target detected | no | no |
| Confirmed additional behavior classes | 5 | 7 |
| Unsupported / refuted finding assertions | 0 / 0 | 0 / 0 |
| Executed modified implementation | no | no |
| Existing fixture sweep | 271 cases | none |
| Tool calls | 8 | 6 |

The two additional candidate classes are padded caret normalization and null-set
intersection. They were already established in prior v2 work. Counts overlap causes,
are not independent root causes or exhaustive recall, and do not replace the target
endpoint. Both reports also leave explicit unresolved leads. Zero unsupported claims
under this limited author judgment does not establish perfect precision.

## Frozen conditions and delivery

See [execution freeze](execution-freeze.md) and `plan.json`. Baseline is v3
`f948b796afbbc7aac010906742ec7f88a8e64950`; candidate is v4
`9f3b0cd72c67aaf000da3e8e88332efb2f3556b6`. Both reuse the identical historical buggy
semver-build source, same generic review request, isolated sessions and tool rights,
`codex/gpt-6.1-sol/high`, 360 seconds and original soft ten calls / 1600 final words.
Only instruction snapshots differ. Seed 31 fixed candidate-first/baseline-second
order before calls. Serial execution, no fresh cases, failures, retries or extra
model calls. Both reports are within the soft word/call budgets.

Plan SHA256:
`63ebf5ed617552b4c5e4fab758c25bcbd1916c31dfd8de53aba545d9a73ce408`.
Instruction SHA256 values are in the plan and manifest. The common USER REQUEST
portion was verified byte-identical. Neither reviewer received evaluator probes,
known failing input, expected next check or earlier reports. Both original and
executed source digests were reverified unchanged. No old plan or historical artifact
was overwritten. No dynamic skill revision occurred during execution.

## Manual process adjudication

The implementing assistant reviewed raw events, reports, actual sources and existing
contract/oracle decisions, unblinded to case and arm. This is not an independent or
keyword-based evaluation. `judgments.json` identifies event items and records all
finding classifications; existing evaluator-only real-source probe code and outputs
are retained separately. These probes are not model calls. Assertion failure is
interpreted alongside its contract evidence, not used as an oracle by itself.

### Candidate v4

`item_2` reads the target. `item_3` reads constants, full relevant regex generation,
Comparator/SemVer implementations, contracts and fixtures. Unlike the previous v3
candidate trace, it receives the actual constant definition. It then explicitly
selects OR simplification, intersection and Comparator construction. This establishes
broader dependency reading, not reasoning about the effective bound.

`item_6` checks OR and constructor routes plus intersection witnesses/controls.
`item_7` expands to padded caret normalization and ordinary hyphen metadata, with
canonical/endpoint controls. The final report explains how a generated prerelease
marker is removed along with ordinary metadata. That is a valid separate defect,
not the selected partial-removal/residual-digit mechanism. There is no concrete
hypothesis or distinguishing check at the effective long-identifier bound. Reading
its definition does not meet the preregistered relationship/check criterion.

Five report findings cover seven established behavior classes, independently
reproduced. The report leaves option-specific tilde/x-range equivalence unresolved;
that lead is not scored as an extra defect or an unsupported assertion. Remedies
are mentally checked only. No broad fixture sweep or modified implementation runs.
The report is 1,065 whitespace-delimited words, with six command calls.

### Baseline v3

`item_2` reads the target; `item_3/item_4` read contracts, Comparator and regex-generation
code. The bound is present symbolically, but the constant definition is not read.
It selects OR simplification, Comparator initialization and intersection.

`item_6` checks those paths. `item_8` tests ordinary hyphen metadata and intersection
controls and runs 271 existing fixture cases. `item_10` repeats established defect
assertions. Neither the key bound nor its residual effect on downstream parsing is
investigated. Four final findings cover five established behavior classes, all
independently reproduced. General prerelease interval intersections remain explicitly
unresolved. Remedies are reasoned only, with no modified implementation execution.
The report is 986 whitespace-delimited words, with eight command calls.

### Interpretation

V4 reads more relevant definitions, avoids a fixture sweep and explores two additional
established behavior classes in this one pair. These are narrow descriptive changes.
It still does not convert the hidden implementation constraint into a testable
producer/consumer question. The bottleneck remains hypothesis formation/selection
after source acquisition; merely acquiring the definition did not resolve it here.
This observation does not isolate the causal contribution of any individual clause.

By the frozen first rule, failure to resolve/check the key relationship means the
diagnostic fails. Both target outcomes are misses, not a positive process-only result.
The single known development case and one repeat do not estimate reliability,
generalization or superiority over direct Codex. No plain arm was run. Do not change
the endpoint to helper reading or additional-finding counts after seeing results.

## Actual reported token usage

| Arm | Input including cache | Cached subset | Output | Input + output |
|---|---:|---:|---:|---:|
| Baseline v3 | 480,809 | 398,592 | 8,809 | 489,618 |
| Candidate v4 | 380,819 | 331,008 | 11,494 | 392,313 |
| **Total** | **861,628** | **729,600** | **20,303** | **881,931** |

Both attempts contain one terminal usage event and successful process delivery;
there is no missing failure usage in this diagnostic. Reasoning output totals 10,252
and is included in output, not added again. Cached input is included in input and
not counted twice or treated as free. The total is the cumulative evaluation usage,
not a unique-context count or this chat/adjudication's consumption. Dollar cost and
subscription quota share remain unknown.

Total is about 0.882 million tokens, versus the planning estimate of about 0.84
million and allowance of 1.2 million. The allowance was never a hard cap. Candidate
reported less input but more output and took 323.40 seconds versus baseline 265.13.
One serial pair under changing service conditions does not establish token efficiency
or controlled speed improvement.

## Evidence and stopping

The corresponding run JSON holds the complete two-row plan, results, judgments,
usage and SHA256 manifest of instructions, raw requests/events/reports/results/
integrity files, evaluator probes/outputs, catalog and this report. Source provenance
is pinned through the existing catalog and workspace digest. All probes and original
oracles stay outside reviewer workspaces. Historical v2/v3 checkpoints are preserved.

This approved batch is complete. No automatic tuning/retry, additional model judge,
new-case evaluation, background continuation, main merge or release follows. Keep
v4 experimental in draft PR #16. Any further experiment requires separate user
approval and a new frozen plan; never reuse this plan with a modified candidate.
