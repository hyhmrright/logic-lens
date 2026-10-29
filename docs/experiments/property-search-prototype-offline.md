# Property-search prototype — offline qualification and proposed diagnostic

Date: 2026-10-29. User authorized an optional minimal property → bounded local search
prototype and offline validation only, kept in draft PR #16. No main merge, model
review, retry, new real-case selection or background run is authorized. This document
proposes the next diagnostic; it does not authorize or preregister its execution.

## What was implemented

`python3 scripts/logic_lens.py search` accepts a sourced property, finite parameter
domains, a passing control and a trusted local command adapter. It samples unique
combinations with a fixed seed, invokes the actual subject, preserves a witnessed
difference and performs bounded control-relative coordinate reduction. All invocations,
including reduction, share the same count and wall-time budget. It archives inputs,
results, bounded logs, source integrity digests and spec/adapter/report hashes; the
CLI returns a compact summary instead of every passing example. Large witnesses are
replaced with an evidence reference. See [the runnable protocol](../PROPERTY_SEARCH.md).

The engine never generates a property, decides its semantic truth, confirms a bug,
invokes a model, installs dependencies or modifies the original source. It is not a
sandbox: adapters are trusted executable code, imports/provenance must be inspected,
and copying plus digest checks do not prevent arbitrary external side effects.
No hidden oracle, known reproduction or historical case name is embedded in it.

No review skill or prompt compiler changed. The review snapshot remains SHA256
`d429f5d89726d00cf166644a238849b0fce2e9f1a75197f0d106d5ac5fe6de37`.
The original v2/v3/v4 plans, reports and outcomes remain immutable. The prototype's
command is optional and has not been integrated into model sessions.

## Offline behavioral validation

Sixteen new tests exercise the mechanism using synthetic signed-axis code and small
controlled adapters. These are local program tests, not fresh real historical cases,
model benchmarks or evidence that model-generated properties will be useful.

- Real local implementation passes its stated reversible-displacement relation;
  a signed arithmetic defect yields a witnessed difference, bounded reduction reaches
  a smaller reproducer, and the corrected implementation passes again.
- Sampling is reproducible and nonduplicating, with the control first and sampled
  versus exhausted domains distinguished. Reduction cannot exceed total call budget.
- Invalid inputs, failed controls, process crashes, malformed protocol and missing or
  out-of-scope source provenance are separated from behavioral violations.
- Global remaining time bounds individual execution; excessive output is stopped and
  retained logs capped. CLI summaries do not dump large witnesses into model context.
- Source mutation in the execution copy invalidates observations; original source
  remains intact. Output refuses overwrite and cannot be placed inside the source.
- Source quotations must match; invalid controls and limits fail before execution.
- A Node.js adapter checks an actual JavaScript module using the same JSON protocol;
  this test skips if Node is absent. No claim that every language/runtime is tested.
- Full artifacts match their SHA256 manifest; all six skill exports and the unchanged
  review snapshot are checked separately without a model invocation.

On the local host, all 92 repository tests pass, including all sixteen new tests
(Node available). Repository validation and shell lint pass; `git diff --check` passes.
A first output-cap test exposed process cleanup rejecting an already-exited group on
this host; cleanup now handles that condition and the behavioral test passes. No
source-backed discovery/content/routing evaluation ran. These checks qualify the
mechanism for consideration, not its efficacy as a reviewer.

## Next proposed diagnostic — requires approval and a new freeze

Use **two review sessions on the same existing semver-build snapshot**, one current
v4 control and one optional property-search workflow, one repeat each, serial and
randomized before dispatch. No new cases. Codex gpt-6.1-sol/high, 360 seconds, soft ten
tool calls / 1600 final words. Search invocations count as tool calls; local internal
cases are separately bounded and reported. Keep the full v4 compiled material in both
arms; do not bundle prompt trimming, new scoring or compiler changes into the test.

The old historical protocol is read-only and prohibits writing harness files. Before
this diagnostic can be frozen, provide a separately scoped harness scratch area and
search capability identically to both arms, with monitored immutable source snapshots.
Explicitly record this common protocol change: results are a new experiment, not a
same-plan continuation or a directly pooled historical measurement. Do not silently
relax permissions for one arm. Integration/permission checks must first pass offline.
The prototype alone does not supply that model-session integration.

Candidate instructions would require proposing sourced executable properties rather
than hand-picking every expected failing example. Do not pre-author its property,
parameter domain, adapter, key source location, failure input or anticipated oracle.
Without autonomous property selection, this would only test the local engine using
evaluator knowledge. A bounded proposal is at most two properties, each at most 32
total local evaluations and ten seconds, including control/reduction; all attempts
share the original session time/call budget. Adapter setup is part of the cost.
No added model planner, judge or subagent. No automatic retry; any capacity/network
error stops dispatch. Preserve failures and unknown usage.

Primary diagnostic questions, to lock before calls:

1. Does the candidate independently state a supported useful relationship and encode
   it faithfully against the real implementation? A valid JSON form or matching
   quotation is not semantic success.
2. Does its generated domain actually check the previously unexamined relationship
   with a valid control, and are the local results reproducible? Generic irrelevant
   searches and repeated known examples do not qualify.
3. Does it detect the unchanged original defect, without added unsupported/refuted
   claims? Nearby defects, case counts and successful engine runs cannot substitute.

If it selects no useful property, misses the relationship or produces an invalid
oracle/harness, record the failure rather than repairing its answer behind the scenes
and rescoring. Distinguish setup failure from subject behavior. If it checks the
relationship but still misses the target, that is process evidence only. A single
known development pair cannot establish generalization or superiority over plain
Codex, even if positive. No fresh-case stage follows automatically.

## Preliminary token planning

The last actual full pair used 881,931 cumulative input+output tokens; its v4 arm
used 392,313. Those are the only close observed anchors. No measured usage exists for
this workflow, and adapter construction or failure can increase consumption.

For the proposed two sessions, plan approximately **0.8–1.1 million input+output
tokens**, with **1.2 million planning allowance**, cached input included. This is
an uncertain estimate, not a hard cap or a demonstrated saving. Preserve terminal
usage, reasoning/output and cache/input subsets; unknown failures and dollars remain
unknown. Local non-model cases use runtime, not model tokens; reading their outputs
and producing adapters does use model tokens. Do not equate per-case local execution
with a free overall workflow. Chat/implementation token use is outside evaluation
telemetry. Revisit the estimate after offline integration and final prompt freeze,
then ask for explicit execution approval. No model calls are authorized now.
