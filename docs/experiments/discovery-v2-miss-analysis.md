# Why the previous candidate missed bugs

This analysis concerns investigation behavior, not the number of risk-code rules.
The [previous report](../../benchmarks/reports/codex-discovery-2026-10-28/REPORT.md)
records 7/12 target confirmations for both plain Codex and the candidate. The result
cannot support a claim that the old candidate improved discovery.

## Premises

The previous protocol supplied the entire target repository without history and
allowed supporting reads. Candidate reports and command logs show access to stream
recognition, body preparation, size helpers, redirect replay and public documentation.
The timeout reports reached request defaults, client construction, direct sending,
and transport forwarding. Missing files were not the primary obstacle in these runs.

## Trace

1. In Requests, successful investigation of ordinary readable streams produced a
   valid replay finding, but did not distinguish an interface supported by forwarding
   from the nominal predicate selecting body preparation. Reading more stream code
   did not create that missing hypothesis. See the
   [related finding](../../benchmarks/reports/codex-discovery-2026-10-28/reviews/requests-02-buggy-candidate-1.md).
2. In HTTPX, the candidate sometimes observed the missing timeout extension but
   deferred the finding alongside the unproved indefinite wait. There is a legitimate
   conflict between “as-is” sending and a client-wide default promise, so simply
   forcing confirmation would be wrong. The investigation needs to separate the
   smaller boundary obligation from downstream escalation and resolve that contract.
   See the [unresolved account](../../benchmarks/reports/codex-discovery-2026-10-28/reviews/httpx-03-buggy-candidate-2.md)
   and [confirmed account](../../benchmarks/reports/codex-discovery-2026-10-28/reviews/httpx-03-buggy-candidate-0.md).
3. Several reports treated “integration tests excluded” as a reason to execute no
   code at all. Pure local probes could distinguish return values and metadata
   propagation without a server. This is partly a protocol problem and must be
   corrected equally for all arms, not credited to the revised skill.
4. The formal trace/report/remedy obligations consumed substantial output and time:
   the candidate had roughly 1.8 times plain Codex's output tokens. These mechanisms
   help communicate and reject weak claims, but are not discovery mechanisms.

## Divergence

The instructions described what a defensible final finding looks like more concretely
than how to select the next counterexample. Their generic lists of unusual inputs
and operations did not reliably produce comparisons across supported routes or
representations. Long context and additional risk rules did not fix this search gap.
The observed misses do not show that every unsupported claim should be promoted.

## Trigger

These mechanisms matter when a contract spans multiple representations or entry
points, a predicate approximates a supported capability, or a real local violation
is bundled with an unproved severe outcome. They also matter under a bounded review
budget: repeated evidence gathering can crowd out exploration of a second hypothesis.

## Remedy and falsification

The revised review skill explicitly maps obligations through producers, representations
and consumers, selects paired counterexamples grounded in actual contracts, probes
before finishing a proof, and reports the smallest supported observable violation.
It retains counterevidence checks and unresolved status when requirements conflict.
It defers report/remedy polishing until discovery has covered important obligations.

The [preregistration](discovery-v2-preregistration.md) fixes the comparisons and success
criterion. The revised instructions contain no sample names, upstream patches or
case-specific inputs. Candidate 32151b0 was committed and pushed before dateutil and
node-semver fixes were inspected. Click history and the previous pilot are development
material; dateutil and node-semver are new validation material for this frozen
candidate. Public-history contamination and author adjudication remain limitations.
A failure to improve on this set must be published rather than converted into a
success by changing the matching rules or tuning against these same answers.
