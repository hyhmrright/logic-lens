# Discovery revision 2: preregistration

Status: candidate design fixed before held-out case curation; results pending.

## Observed mechanisms

The previous 72 reviews did not establish a detection gain over plain Codex.
Inspection of the missed Requests stream case shows relevant producer, dispatch,
and consumer code was read, but the candidate did not test the distinction between
a supported interface and its recognition predicate. Additional broad reading did
not resolve that distinction. In the HTTPX timeout miss, a missing default reached
the consumer, but uncertainty about an eventual unbounded wait caused the smaller
contract claim to be withheld. Conflicting send documentation also needs genuine
resolution; reducing evidence requirements would create false positives.

The changes therefore operationalize boundary comparisons, early distinguishing
experiments, and reporting the smallest evidenced violation. They do not include
sample names, patches, special classes, HTTP rules, or case-specific triggers.
The shared finding format and precision requirements are unchanged.

## Separation and comparisons

Development material: the previous HTTPX/Requests pilot and Click history (including
parameter-source visibility and competing default arbitration). Neither counts as
new validation. Freeze the candidate Git revision before inspecting held-out fixes.
New validation uses at least four historical defects from at least two previously
unused projects. Reject cases only for unavailable execution, non-behavioral changes,
unisolatable patches, or absence of a supported requirement. Record all exclusions.
Do not change the candidate after inspecting held-out cases or results.

Arms: plain Codex; previous candidate at 83652aa; frozen revised candidate. Use
Codex gpt-6.1-sol/high, explicit instruction snapshots, identical source variants,
10 shell/tool calls, 1600 final words, 360-second timeout, three independent repeats,
randomized order, four concurrent processes. Buggy and repaired versions share base
docs/tests; only implementation fixes are overlaid. No history, oracle, fix diff,
case description, new regression tests, or host instructions reach the reviewers.

The common protocol explicitly permits local in-memory probes and disables bytecode
writes. It excludes services, dependency installation and integration testing.
This clarification applies equally to all arms and is a protocol change from the
previous pilot: do not attribute cross-pilot changes to the skill.

## Judgment and success

Before review execution, record each target's supported obligation, reachable
trigger family, root cause, observable consequence, and real-code failing/passing
probe. Match semantic cause and consequence, not exact wording, L-code or input
class. Broader findings count only if their claim entails the target mechanism.
A remaining real defect in the repaired variant is not a false positive. Separately
count refuted assertions, unsupported assertions, and additional confirmed defects.
Unresolved leads do not count as detections or false assertions.

Primary endpoint: paired target detections on buggy variants. A practical improvement
requires at least three more detections than plain Codex and improvement on at least
two distinct cases, with no increase in false or unsupported assertions and no more
than twice plain Codex's total output tokens and median time. Report the old-skill
comparison too. Publish all repeats, denominators, per-case results, costs where
reported, failures, and limitations even if this criterion fails. Four public cases
cannot establish superiority over arbitrary projects; no universal claim or release
promotion follows from this experiment alone. Training contamination remains possible.

Adjudication is by the implementing assistant, unblinded; disclose this limitation.
The frozen set becomes development material after analysis. A failed experiment
must not be rescued by tuning against it and calling it held-out again.
