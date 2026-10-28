# Logic Review — Investigation Guide

## Step 1: Establish Behavior and Its Evidence

Read the target and the contracts needed to judge it: public documentation, real
callers, tests, schema, configuration, and relevant pre-existing history. Use the
premises checklist in `../_shared/semiformal-checklist.md` for code assumptions.
Keep three kinds of information distinct:

- **Observed facts:** what this version actually evaluates, returns, mutates, or persists.
- **Required behavior:** a supported invariant, with source location and conditions.
- **Unknown assumptions:** facts still needed to decide whether behavior is wrong.

Tests and documentation are evidence of requirements, not infallible specifications.
When they disagree, investigate caller reliance and provenance; do not resolve the
conflict by assuming the current implementation is correct. Names alone cannot
establish requirements. If no authoritative contract is available, mark the question
unresolved rather than inventing intent or reporting a generic documentation gap.

For business/stateful code, extract applicable invariants such as conservation of
amounts, unique effects, valid state transitions, ownership, ordering, isolation,
and eventual visibility. Specify the observable violation, not just "this looks risky".
An in-place API returning its input is legal unless an actual contract or caller
requires independent state; mutation alone is not an L4 finding.

## Step 2: Map Behavior Boundaries

The named file/function is the target; evidence may live elsewhere. Start from an
entry point and follow both directions:

- Where inputs originate and which validators every relevant entry traverses.
- Which implementations are actually selected by imports, injection, configuration,
  runtime/library versions, callbacks, or dispatch.
- Where state is owned, persisted, invalidated, cached, retried, and consumed.
- Which callers depend on return values, exceptions, mutations, or ordering.

Before deep investigation, sketch the important obligations in the target:

```
promise/source | producer → representation → consumer | alternate route/state | observable mismatch
```

This is a discovery map, not an output table requirement. Look for the same promise
implemented in different entries or stages: where is a default attached, a value
normalized, a capability recognized, or state made visible? A shared helper protects
only routes that actually traverse it. Follow information lost or reinterpreted at
each boundary, including wrappers, callbacks, metadata, units, and retained state.
Do not equate different routes unless the contract requires their equivalence.

Prioritize paths by impact and unresolved contract boundaries, including internal
helpers when they own those boundaries. Do not automatically downgrade a finding
because a path crosses files or exceeds four calls: resolve intermediate contracts
or use an experiment. Stop expanding when the question has an evidenced answer.

For a large target, build a ranked worklist and choose a bounded first pass. Treat
`common.md` §9's three-function budget as a starting worklist for this skill, not a
limit on reading the dependencies necessary to decide a candidate. State the budget
and uncovered work. If exhausted, retain the missing dependency and next check;
never translate "not inspected" into "safe". Respect explicit user scope/access limits.

## Step 3: Generate Failure Hypotheses and a Ledger

For each important invariant, ask what combination of valid inputs, prior state,
and operations could violate it. Explore both ordinary and exceptional paths:

- Empty/single/maximal inputs, equal keys, numeric precision and representation changes.
- Repeated operations, retry after partial success, duplicates, and out-of-order delivery.
- Cancel/delete/update followed by stale callbacks, reads, or cached results.
- Failures before and after an external effect; cleanup and compensation across exits.
- Concurrent interleavings, ownership transfer, restart/reload, and serialization round trips.

Turn a promising boundary into a **paired counterexample**: hold the required
behavior constant and vary one supported representation, entry point, partition,
or prior state. Compare a direct value with an adapter; one batch with equivalent
chunks; a fresh object with a reused one; or a value before and after a supported
round trip. Select pairs from the actual API contract, not assumed universal laws.
Use valid but unusual implementations of a documented interface: does dispatch
check the capability the consumer needs, or a narrower proxy for it?

Predict both outcomes before the next tool call. If two plausible explanations
remain, test the smallest input or sequence that separates them. Import real code
for cheap local probes when permitted; otherwise trace both routes to their first
observable difference. A failed import is setup evidence, not a behavior result.
Do not keep rereading already established facts: identify the specific unknown
that another read would answer, or switch hypothesis. Reserve budget for exploring
uncovered obligations before polishing findings or remedies.

Choose relevant scenarios; do not mechanically expand every combination. Use L1–L9
from `logic-risks.md` as a coverage backstop after generating hypotheses, and defer
fine classification until the root cause is understood. Trace normal behavior as a
control, but do not spend the entire budget certifying the happy path.

Maintain a compact internal ledger:

```
ID | invariant/source | triggering sequence | supporting locations |
unknown fact | next check | impact | confidence | status
```

Statuses: **open**, **confirmed**, **disproved**, **blocked**. Keep rejected leads with
their actual counterevidence; open/blocked leads are not reportable defects. Rank
next checks by how much uncertainty they resolve and potential impact. Where two
hypotheses remain, prefer a check whose outcomes distinguish them.

## Step 4: Trace, Resolve Reachability, and Challenge

For promising hypotheses build Premises → Trace → Divergence before writing the
finding's Trigger or Remedy. Internal experiments may use tentative inputs earlier;
the Iron Law governs the order of the final finding, not the order of investigation.
Use concrete values, source anchors, actual name resolution, and callee contracts.
Trace through the observable consequence and downstream handling: catching an
exception may still leave a committed effect, stale state, or incorrect response.

Use `semiformal-guide.md` for trace mechanics. Three substantive steps and two anchors
are the normal certificate minimum; do not pad a short direct proof. If evidence is
incomplete, keep an open/blocked ledger entry instead of manufacturing certainty.

Challenge each hypothesis:
1. Is the required behavior supported, or merely assumed?
2. Can the input/sequence reach this code through real callers and configuration?
3. Does a defense cover this exact path AND preserve the required outcome?

A defense closes a candidate only when its coverage and consequence are evidenced.
A validator on one entry is insufficient for another; a retry is insufficient if
an earlier attempt committed a non-idempotent effect. No defense found is not proof
of reachability: obtain a caller path, supported public input, or faithful experiment.
An intentional rejection is safe only if rejection is permitted by the contract.

For concurrency, reason about explicit ordering, scheduling, ownership and memory
visibility. Single-threaded execution alone does not prevent interleaving at await;
confinement or immutability may be valid defenses without a lock. Attempt a specified
schedule rather than treating a lucky stress-test pass as disproof.

Report the **smallest supported violation**. If A → B is established but B → C
is uncertain, evaluate B against its own contract. A wrong returned value, missing
required metadata, or callback observing invalid state can be a complete defect
without proving a later crash, hang, or data loss. State only the established
consequence and keep the escalation conditional. Conversely, an internal difference
without an evidenced observable obligation is still a lead. Conflicting contract
sources require resolution; paired outputs alone do not prove which is correct.

Keep **impact**, **confidence**, and **status** independent. Missing context does not
make data loss minor. Partial defenses create further checks, not automatic severity
demotion. Only confirmed defects enter Findings; incomplete high-impact leads stay
visible as unresolved investigations, with the missing evidence named.

## Step 5: Verify with Faithful, Bounded Experiments

Experiments can generate hypotheses as well as verify them. Prefer an early
cheap probe over more reading when its result would change the next investigation
step. Avoid running a checklist of probes unrelated to the target obligations.

For every Critical/Warning candidate, attempt an appropriate experiment if the
runtime, dependencies, and permitted isolated environment are available. A runtime
binary alone does not mean the application can run. If blocked, explain what is
missing and retain a supported static finding as unverified.

Prefer importing the real implementation and existing test fixtures. Use isolated
temporary files, disposable local databases, controlled clocks, and deterministic
schedules where needed. No production data/services, external writes, destructive
operations, or dependency installation without task authorization. Default to a
10-second probe timeout; choose and record a bounded longer timeout for a necessary
integration test. Run risky/hanging probes in a terminable subprocess.

For each experiment record:
- The requirement source used as the assertion oracle.
- Actual entry, input/prior state, dependencies, versions and schedule exercised.
- How mocks/simplifications differ from the real path. Never mock the behavior in dispute.
- Command, timeout, result, and what that result establishes.

Interpret outcomes carefully:
- **Reproduced:** the intended behavior assertion fails at the predicted divergence
  on real code (not setup/import failure). This supports the defect.
- **Not reproduced:** a passing run, simplified harness, or unscheduled concurrent
  attempt is inconclusive. Recheck fidelity and the trigger before making a judgment.
- **Disproved:** concrete counterevidence shows the proposed trigger cannot violate
  the requirement, and covers the claim's conditions. Close this hypothesis only.
- **Blocked:** dependencies, access, runtime or setup prevent a meaningful experiment.
  Keep the limitation; a broken harness does not refute the code analysis.

After reproducing, test a minimal remedy in an isolated copy, preserving the same
oracle and trigger. FAIL → PASS verifies that scenario only, not absence of regressions.
Check the normal path and nearby boundaries affected by the remedy. Stop after three
unsuccessful remedy attempts and report that the fix needs review; inability to fix
an evidenced defect does not erase the finding. A copied/minimized implementation
can support a mechanism but must be labeled separately from execution of actual code.

## Step 6: Prepare Findings and Remedies

Apply L1–L9 classification from `logic-risks.md` to the established cause; do not
suppress a defect merely because two classifications seem plausible. Deduplicate
by cause and list affected callers. Use existing severity overrides where configured.
Severity describes supported impact/conditions; confidence describes evidence strength.
Do not promote speculative risks to confirmed bugs or demote serious impact because
an isolated environment cannot reproduce it.

Each finding follows `common.md` §2 and §10: Premises → Trace → Divergence → Trigger →
Remedy, with literal localized field labels. Critical/Warning triggers include
concrete inputs or a precise prior-state/operation/interleaving sequence plus expected
and actual behavior. A remedy is minimal and paste-ready, or uses the existing design
decision block if the required contract is genuinely disputed.

Dry-run the proposed remedy against the trigger and normal/neighboring paths. Distinguish
mental checks from executed tests. Do not claim "no regression" from a mental trace or
a single passing test. Do not modify the reviewed checkout in a read-only review.

## Step 7: Report Scope, Findings, and Remaining Work

Render once using `report-template.md` and `common.md` language/header/score rules.
Keep the existing score for compatibility, computed only over confirmed findings;
state that it describes the inspected slice, not whole-project health or shipping safety.
Scope names targets, supporting files, traced sequences, omissions and budget limits.

Each Critical/Warning finding includes localized **Verification**: reproduced on
actual code, static evidence only, not reproduced, or blocked, with reason and any
harness limitations. Report remedy verification separately; no "Execution-verified"
label for an unexecuted claim or a failure unrelated to the alleged divergence.

When no defect is confirmed, say "No confirmed logic bugs found in the inspected
paths" and qualify unresolved work. Keep the no-bug five-field block for existing
consumers, explaining actual checked defenses; Trigger/Remedy are N/A. Never imply
that all possible paths are correct because the ledger or budget is exhausted.

After Summary, append **Unresolved Investigations** (中文 **待完成调查**) when needed:
ID, suspected impact, evidence so far, missing fact, and next check. These are leads,
not Findings, must not reduce the score, and must not enter an automatic fix queue.
