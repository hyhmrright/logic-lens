# Revision-3 Gate B — authorized continuation stopped on capacity

Date: 2026-10-29. **Gate B not passed; no superiority conclusion.** The user
explicitly authorized a same-model, same-budget retry of the previous rejection,
then completion of unattempted rows if capacity recovered. No automatic retries or
fresh-case evaluation were authorized. The retry entered review but timed out at
360 seconds. Two subsequent candidate reports delivered; the next baseline request
received `Selected model is at capacity. Please try a different model.` Dispatch
stopped immediately. No background continuation was created.

| Case | Arm | Latest state | Target detected |
|---|---|---|---|
| semver-build | baseline | 360-second timeout | unknown |
| semver-build | candidate | delivered | no |
| semver-diff | candidate | delivered | yes |
| semver-diff | baseline | capacity rejection | unknown |
| dateutil-midnight | candidate | not attempted | unknown |
| dateutil-midnight | baseline | not attempted | unknown |
| dateutil-inequality | candidate | not attempted | unknown |
| dateutil-inequality | baseline | not attempted | unknown |

Baseline is the frozen v2 candidate `32151b0`; candidate is `f948b79`. Model remains
`codex/gpt-6.1-sol/high`, deadline 360 seconds, one worker, original soft ten calls
and 1600 final words, identical local-probe rights. Plan, instruction and source
hashes are unchanged. This continuation dispatched four requests, with no automatic
retry. Including the original preserved capacity rejection, there have been five
attempts on four unique trials, two accepted reports and three failed attempts.
The [original checkpoint](../codex-discovery-v3-gate-b-capacity-2026-10-29/REPORT.md)
remains immutable. Its failure is also preserved under `failed-attempts/`.

## What the process evidence establishes

Judgments are manual, source-backed assessments by the implementing assistant,
unblinded to case and arm. They are not independent or keyword scoring. The exact
commands/results are retained in each attempt's events; `judgments.json` references
item IDs. Evaluator-only probes and their outputs are separately archived, never
supplied to reviewers. Probe failures reproduce supported defects; a failing
assertion alone does not establish its expected-behavior contract.

- **Candidate semver-build:** `item_3/item_4` read documented union and prerelease
  contracts and Comparator fixtures. `item_6` exercises the actual implementation
  with equivalent construction, stable, option and intersection controls. Four
  findings cover five established behavior classes: Comparator options, OR
  prereleases, intersection witness, empty sentinel and stable release gap. All
  were independently reproduced using existing evaluator probes. None is the
  selected long-build-metadata target. No probe exercises its bounded stripping
  transformation. `item_9` spends a call on 325 existing fixture assertions while
  parser boundaries remain unresolved. Eight command calls, including a blocked
  heredoc, remain within the soft call budget.
- **Candidate semver-diff:** `item_2/item_3` read the public diff contract and
  existing graduation/string-preservation fixtures. `item_6` exercises release
  changes with stable and reversed-argument controls, and the safe-integer
  boundary with a neighboring control. It detects the selected early-return defect
  and the additional numeric identifier comparison defect, both independently
  reproduced. It does not assert the unsettled minor-graduation oracle. `item_8`
  runs 29 existing fixtures in both directions. Six command calls including a
  blocked heredoc remain within the soft call budget.
- **Repair allocation:** neither delivered candidate executes a modified
  implementation; remedies are only reasoned through in its reports. The timed-out
  baseline build trace contains repeated in-memory modified-implementation probes
  (`item_7`, `item_9`, `item_11`). This is a limited descriptive signal consistent
  with deferring repair. The baseline is undelivered and no pair is complete, so
  this cannot establish a controlled improvement or estimate its frequency.
- **Uncertainty:** no new unsupported or refuted finding was established in the
  two accepted reports. Six additional behavior classes across them are distinct
  established classes already seen in v2, not six new independent root causes or
  evidence of superiority. Baseline timeout content is not rescued as a report.

The candidate's explicit transformation-limit criterion already fails on the common
miss. It also has not delivered all four candidate runs or demonstrated retention of
all three previously found targets. Missingness is not scored as a semantic miss.
There is a narrow repair-allocation signal, but **no evidence that discovery has
improved**. Gate C is not authorized or justified by this diagnostic. Do not change
prompts, budgets, cases or hit criteria to turn this partial result into a pass.

## Actual reported usage and limitations

| Delivered report | Input including cache | Cached subset | Output | Input + output |
|---|---:|---:|---:|---:|
| Candidate semver-build | 409,662 | 360,320 | 8,022 | 417,684 |
| Candidate semver-diff | 266,025 | 226,688 | 5,354 | 271,379 |
| **Known subtotal** | **675,687** | **587,008** | **13,376** | **689,063** |

The 5,041 reasoning-output tokens are included in output, not added again. Cached
input is included in input and is not free or counted twice. The timeout and both
capacity failures have no terminal usage event. Thus actual cumulative consumption
is **unknown beyond the known subtotal of 689,063 tokens**; it is not zero for
failures and not a complete actual-total estimate. Dollar cost and subscription
quota consumption remain unknown. The subtotal concerns these evaluation attempts,
not this chat's token consumption. Accepted durations are descriptive, not controlled
speed evidence. No model calls were made for grading, new cases or validation.

## Evidence and next action

`plan.json`, both instruction snapshots, all accepted reports, request/event/result/
failure/integrity files, the historical rejection, source-backed judgments and
probe evidence are archived with SHA256 manifest in the corresponding run JSON.
All eight source workspace digests were reverified unchanged. The original plan
hash remains `0d531a75ef67b0e4ef93cb72ed08393269d23237a3374e7706aefff04224904a`.

Stop here under the user's capacity rule. No automatic retry or new-case evaluation.
Any later model dispatch requires explicit renewed authorization. Keep experimental
skills in draft PR #16 and out of main. Further design discussion should address why
the selected bound was not prioritized, rather than claim this brevity change fixed
hypothesis generation. No skill modification follows from this execution task.
