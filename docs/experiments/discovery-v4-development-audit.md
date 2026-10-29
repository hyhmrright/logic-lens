# Discovery revision 4 — offline selection-policy audit

Date: 2026-10-29. Status: **unqualified experimental candidate** in draft PR #16.
The user authorized implementing the preceding offline design proposal, with no
further model evaluation. No new model calls, retries, fresh-case selection or
background continuation are authorized. Version stays 0.6.10; no release promotion.

## Evidence and limits

The [revision-3 continuation](../../benchmarks/reports/codex-discovery-v3-gate-b-continuation-2026-10-29/REPORT.md)
delivered only two candidate reports. One baseline timed out; another was rejected
for capacity; four trials remain unattempted. Neither candidate report executes a
modified implementation, but the common-miss transformation limit was not checked.
Gate B did not pass. No matched baseline pair exists, so neither selection-policy
causality nor improvement over direct Codex is established.

In the candidate build trace, item_2 reads the removal operation and safeRe alias;
item_4 returns references to MAX_SAFE_BUILD_LENGTH and BUILD definitions. No command
reads the bound's constant definition or the complete regex-generation logic. The
reviewer instead selects Comparator construction, OR simplification and intersection,
then runs 325 fixture assertions in item_9. It ends after eight calls at about 268
seconds, below the soft ten-call / 360-second limits. This is evidence of the chosen
path, not access failure or proof that extra time would have found the target.

The first four commands return 64,185 characters in the retained events. Output
volume is descriptive; it does not prove attention loss or establish a causal token
threshold. The candidate diff trace does check a numeric representation boundary,
showing that boundary reasoning is possible when that relationship is selected.

## Intervention

Only `skills/logic-review/SKILL.md` and its guide change in this revision. Shared
contracts, classifications, report/remedy requirements, compiler, tool rights and
runner remain unchanged. The previous frozen plan, prompts, judgments, oracles,
sources and all published artifacts remain immutable.

The new guide changes selection before detailed tracing:

- Orient on main behavioral routes before selecting a narrow deep trace. The map
  is not a comprehensive function inventory or a requirement to probe every path.
- Resolve hidden conditions of consequential operations and their consumers before
  requiring a complete hypothesis. Bound dependency exploration to that relationship.
- Prioritize supported consequences, producer/consumer mismatches, uncertainty and
  check cost; do not select solely by familiar patterns or available fixtures.
- After sufficient confirmation, compare another example of the known defect with
  a different unresolved relationship. Continue proving the current defect if needed.
- Before stopping, revisit consequential operations already seen but not understood;
  report material omissions and reasons. Finding several bugs or finishing the first
  worklist is not itself a coverage criterion.

Implementation conditions generate hypotheses, not expected-behavior oracles. Keep
contract evidence, reachable execution, exact-path defenses, counterevidence and real
implementation probes. Unsupported candidates remain unresolved; no demand to find a
bug, increase finding count, exhaust all budgets or audit every dependency is added.

## Offline replay of available mechanisms

This is a source-informed design walkthrough, not an independent forward test or
new observed model behavior. Known answers can bias it. Expected next decisions:

| Mechanism | Decision supported by the revised rule | Retained constraint |
|---|---|---|
| Bounded normalization feeding parsing (existing common miss) | Resolve effective helper constraints and downstream interpretation before dropping the route from the worklist | Valid supported input and preservation oracle; no sample constants or reproductions in the skill |
| Early return bypassing classification (existing diff target) | Compare branch conditions with the consumer's required classification before deepening another route | Existing special cases remain contract evidence, not automatically bugs |
| Rich comparison dispatch (existing inequality target) | Follow protocol return values to the language operator's observable result | Real dispatch and foreign-operand behavior, not a mocked operator |
| Normalization losing date rollover (existing midnight target) | Trace changed state to the consuming date operation | Distinguish time-only and combined date/time obligations |
| State update with conditional persistence (hypothetical structural walkthrough) | Compare the update path and skipped persistence with the promised observable state | First establish whether durability is promised; no unconditional persistence requirement |
| Acquisition with alternate exit (hypothetical structural walkthrough) | Resolve ownership and cleanup responsibility on the actual exit route | Caller ownership or an existing cleanup defense may refute the hypothesis |

The last two rows are generic thought exercises, not new real cases, benchmark
results or validated defects. No candidate prompts name historical projects, cases,
evaluator reproductions or numeric sample limits. The existing generic probe timeout
is unchanged. A producer/consumer relationship can involve values, state, ordering or
effects; the rule does not privilege long strings or parsing.

## Tradeoffs and deferred changes

The entry plus guide grows from 1,335 to 1,588 whitespace-delimited words. The full
compiled review snapshot grows from 8,770 to 9,023 words, and 62,235 to 63,894 UTF-8
bytes. These are text measurements, not token or price estimates. Compared with v2's
2,397-word entry plus guide, it is still smaller; brevity is not the success metric.
Full current review snapshot SHA256:
`d429f5d89726d00cf166644a238849b0fce2e9f1a75197f0d106d5ac5fe6de37`.
The commit containing this audit identifies the candidate source.

Mapping itself can become overhead or yield shallow coverage. The guide limits it
to orientation and consequential relationships, allows one route for small targets,
and preserves deep verification. Ranking remains judgment-based; new wording cannot
guarantee an unfamiliar relationship is selected. No fixed exploration percentage,
mandatory unrelated probe, finding quota or exhaustive boundary catalog is added.

The compiled runner still injects all shared resources despite lazy-loading guidance.
Actual deferred loading, report simplification, automatic extraction, probe generation
and executor orchestration are deferred interventions. Mixing them into this change
would obscure what was tested and add cost. No new tests merely match guide wording.

## Offline validation and next decision

Repository validation passed, all 76 existing tests passed, shell lint passed for
nine scripts, and all six portable skill exports matched their compiled snapshots.
The review compiler matches the discovery snapshot. `git diff --check` passed.
These checks used no model invocation. The skill-creator quick validator is
blocked by missing PyYAML in the default Python; no dependency was installed. Its
frontmatter and references are inspected directly, which is not a successful run of
that validator. None of these checks measures bug-discovery effectiveness.

The v3 Gate B plan remains stopped and refers to its original candidate. Do not run
this revision under that plan or replace any frozen prompt. Before any behavioral
validation, present a separate frozen candidate, exact scope/count, same-provider
comparison protocol, process observations, token estimate and failure policy for user
approval. Keep target detection and unsupported assertions primary; maps or process
compliance cannot substitute for findings. Existing cases remain development evidence;
any claim of superiority needs separately authorized fresh real-case comparisons.
This task neither amends the old outcome nor authorizes that next experiment.
