# Discovery revision 3 — approval-gated preregistration draft

Status: design draft, not an executed or fully frozen experiment. No model calls are
authorized by this document. The user requires an explicit scope/budget proposal and
approval before the next experiment, including development-set behavioral checks.
No automatic recovery schedule is active. No new validation fixes have been selected
or inspected for this revision. Do not reuse the v2 plan or overwrite its artifacts.

## Hypothesis and intervention

Revision 2 ties direct Codex at 9/12 selected target detections with higher resource
use. Revision 3 tests whether compact transformation/invariant checks and deferring
repair execution improve discovery allocation. It retains contract evidence,
reachability, counterevidence, real-code probes and the shared Iron Law. The skill
contains no historical project names, reproduction inputs or numeric sample limits.
This bundles workflow and brevity changes; a positive result would not isolate the
causal contribution of each. It is not a release qualification by itself.

Candidate source is `skills/logic-review/` plus the existing shared framework. The
shared fallback now agrees with the review guide: names alone do not establish a
contract. No compiler/resource omission or provider protocol change is bundled in
this candidate. Record the eventual candidate commit and complete compiled prompt
SHA before any model diagnostic. Record revisions after diagnostics, then freeze a
new commit before selecting or inspecting fresh cases. Never call a moving branch
name a frozen candidate. Keep every failed candidate and diagnostic result visible.

## Gate A — offline structural review (no model calls)

Compare old/new compiled prompts, links, retained evidence requirements and conflicts.
Replay existing traces conceptually against all four v2 target mechanisms, including
the common miss, and record where instructions would ask for a different next check.
This establishes instruction consistency and a testable mechanism, not execution
compliance or increased recall. Offline checks cannot pass Gate B by themselves.
See [the recorded audit](discovery-v3-development-audit.md).

## Gate B — development behavior diagnostic (separate approval required)

Proposed first request: eight runs, four existing v2 buggy targets × two arms
(frozen v2 candidate 32151b0 and new candidate), one repeat. Reuse the original source
snapshots, runtimes, oracle definitions and common local-probe protocol; prepare a
fresh isolated plan only after approval. No repaired-side or new-case runs in this
stage. Randomize paired order with seed 31, one worker, same gpt-6.1-sol/high,
360 seconds, soft ten tool calls / 1600 final words. These are not hard token caps.
At most eight dispatches; failures remain missing, with no automatic retry. Present
available token usage and unknown costs. Existing reports are context, not matched
new control executions. Do not claim held-out improvement on this development set.

Annotate event evidence manually for: first sourced obligation; first distinguishing
check and control; actual transformation boundary exercised; original-defect
verification; any repair/regression work before remaining obligations; unresolved
work and terminal delivery. Cite commands/source locations. Do not infer compliance
from report vocabulary or score it by keyword matching.

Proceed to proposing Gate C only if the new candidate delivers all four runs,
retains the three previously found targets, exercises a contract-supported check of
the transformation limit on the common-miss case, and does not divert tool calls to
repair execution before the selected obligations are resolved or explicitly blocked.
Any new unsupported/refuted assertion blocks the gate pending analysis. Publish
both arms even on failure. These are engineering diagnostic thresholds, not a
statistical finding. A failed gate leads to documented analysis, not an automatic
paid tuning loop. User approval is required again for another diagnostic batch.

## Gate C — fresh real-case comparison (new approval required)

After Gate B, present the frozen candidate, exact run count, budget settings and
known/unknown cost estimate to the user. Passing Gate B does not authorize Gate C.

Proposed screen: eight distinct real historical behavioral defects across at least
four projects unused in previous discovery experiments. All old pilot/v2 cases and
projects are development material. Seek multiple families (normalization/conversion,
state transitions, routing/matching, collections/arithmetic) rather than selecting
only variants of the observed long-input miss. Select two defects per new project,
with no more than two sharing the same mechanism family. Keep a chronological
selection/exclusion log. Public historical data may still be in model training.

Before execution, lock eight cases, source commits and hashes, runtime/dependency
versions, independent contract evidence and evaluator-only real-code failing/passing
probes. Exclusions are limited to unavailable execution, non-behavioral or unisolatable
patches, or an unresolved oracle. Publish every exclusion. Do not inspect model
results while replacing cases; no replacement after plan freeze. If fewer than eight
qualified cases are available, stop and propose a protocol amendment before calls.

Arms: direct Codex, frozen v2 candidate 32151b0, frozen new candidate. Eight cases ×
buggy/repaired × three arms × one repeat = 48 planned reviews. One worker,
randomized paired order with seed 31, same model/effort, 360-second deadline, soft
10 calls / 1600 final words and identical probe rights. Keep all tool/runtime
capabilities common; disclose actual soft-budget compliance. Opaque source exports
exclude history, fixes, evaluator probes, future tests and native host instructions.
Use separate instruction/source/report/event hashes and fresh artifact directory.
No model switch, deadline increase, result rescue or prompt change after freeze.

Primary endpoint: paired target detections on eight buggy variants. Semantic matches
require the same supported cause and consequence, not exact wording or reproduction.
Per-case gains/losses are primary; no treating repeats as independent defects.
A screening success requires at least two net additional target detections over
plain, improvements on at least two distinct cases, no increase in unsupported or
refuted assertions, and first-attempt delivery no worse than plain. Additionally,
accepted output tokens must be at most 1.25× plain. Publish the v2-arm comparison
without claiming mechanism isolation. These practical thresholds are fixed before
selection and are not significance tests. Report all cases, losses and denominators.

Repaired variants are not clean negatives. Classify target recurrence, additional
confirmed defects, unsupported assertions, refuted claims and unresolved leads
separately. Deduplicate additional behavior classes, disclose overlapping causes;
do not substitute their totals for the failed primary endpoint. Mask arm labels and
randomize report IDs during semantic judgment. Record who adjudicated and whether
they knew the cases/results. If no independent adjudicator is available, disclose
implementer bias and keep the conclusion provisional; masking alone is not independence.

## Delivery, cost and stopping

Capacity/network errors stop new dispatches. Review timeouts are separately recorded.
No automatic retries in either proposed stage; preserve failures and request a bounded
retry budget separately if needed. Missing delivery is not a semantic miss. Report
first-delivery and paired-complete capability results side by side. Missing primary
pairs prevent a success declaration; do not silently use smaller denominators.
Retain terminal usage even in failed attempts, all unknown usage and unknown dollar
costs. Do not count cached input as free. Duration is descriptive without controlled
service conditions. No heartbeat, CI model eval or paid validation without approval.

A Gate C success warrants a separately approved confirmation on another frozen unseen
set, with repeated measurements. A tie, failed cost/precision/delivery gate or loss
means no superiority claim or release promotion. Preserve the full record and decide
whether to narrow the product claim to evidence discipline rather than bug discovery.
