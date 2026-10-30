# Revision-3 Gate B — stopped on capacity rejection

Date: 2026-10-29. Status: **incomplete; no behavioral conclusion**.

The user approved eight existing-case diagnostic reviews, with no automatic retry
and no fresh-case evaluation. The first frozen trial was rejected by the service:
`Selected model is at capacity. Please try a different model.`
The model was not changed. Further dispatch stopped under the preregistered rule.

| Case | Arm | State |
|---|---|---|
| semver-build | baseline | service_capacity_rejected |
| semver-build | candidate | not_attempted |
| semver-diff | candidate | not_attempted |
| semver-diff | baseline | not_attempted |
| dateutil-midnight | candidate | not_attempted |
| dateutil-midnight | baseline | not_attempted |
| dateutil-inequality | candidate | not_attempted |
| dateutil-inequality | baseline | not_attempted |

Here baseline means frozen v2 candidate 32151b0, not the older skill 83652aa.
Candidate source is f948b796afbbc7aac010906742ec7f88a8e64950.
See the frozen plan for exact instruction and source hashes.

## Delivery and usage

- Planned 8; dispatched 1; delivered 0; service rejection 1; unattempted 7; retries 0.
- First attempt elapsed 10.64 seconds. This is not a review timeout or a semantic miss.
- No terminal usage event was returned. Actual input/cached/output/reasoning token
  consumption and dollar cost are **unknown**, not zero. No valid report can be scored.
- No model judge, content/trigger evaluation, new cases or further model calls ran.
- Source integrity digest was unchanged. Raw request, events, stderr, failure and
  integrity evidence are preserved byte-for-byte with SHA256 manifest in the run JSON.

## Interpretation and continuation

There is no report to inspect for sourced obligations, boundary checks, repair
diversion, unsupported assertions or target detection. Gate B remains unassessed;
this does not demonstrate improvement or regression. Existing static audit results
remain static evidence only. No promotion to main or Gate C follows.

The seven unattempted trials remain in the frozen plan. The failed trial will not
be retried automatically. No background retry or heartbeat was created. Any later
resumption/retry requires an explicit user instruction and bounded budget; preserve
this checkpoint and failure evidence rather than overwrite them.
