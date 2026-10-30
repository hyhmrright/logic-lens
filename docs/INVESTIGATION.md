# Experimental offline investigation scheduler

This opt-in prototype remains in draft PR #16. It joins automatic structural relation
discovery, source facts, constraint-domain planning and actual property execution on
**explicitly trusted synthetic Python programs**. No formal skill, model provider,
release default or historical experiment changes. No claim of general bug discovery,
whole-program analysis, calibrated importance ranking or token savings.

```bash
# Discovery/planning only: never imports or executes subject code.
python3 scripts/logic_lens.py investigate \
  --spec examples/investigation/request.json \
  --workspace examples/investigation/workspace --out /tmp/new-investigation-plan

# Only for a user-reviewed trusted synthetic fixture. Executes local Python code.
python3 scripts/logic_lens.py investigate \
  --spec examples/investigation/request.json \
  --workspace examples/investigation/workspace --out /tmp/new-investigation-run \
  --execute-trusted-synthetic
```

The execution flag is required even when the request pins the source hash. Pinning
is an integrity check, not a safety approval. The fixed adapter/search engine is not
an OS sandbox; do not use this execution mode for arbitrary untrusted repositories.

## Inputs and independent oracle

The complete runnable request is in the example. Required top-level fields are
`schema_version:1`, source path, `trusted_source_sha256` and1..8 unique `entries`.
Optional `slots`1..4 (default2), `point_budget`4..64 (default32). Each entry has exactly:

- `name`: manually scoped public entry, not a manually nominated suspicious helper.
- `valid`:1..8 finite integer intervals inside [-10000,10000].
- `expectation`: `returns`, `return_or_value_error` or `unknown`.
- `evidence`: exact `{path,start,end,quote}` supporting the entry obligation.

No suspicious consumer, coefficient, unit, route, expected defect label or failure
sample is accepted in the request schema. Public contract interpretation and entry
selection remain manual. Quote matching does not establish semantic applicability;
contract files must be reviewed independently. The program does not infer a business
contract from a consumer's internal refusal. A permitted ValueError cannot become a
violation just because an internal capacity was exceeded.

## Closed loop

1. Parse the restricted module with existing `python_facts` rules. Enumerate direct
   same-module calls under each entry and candidate consumers with the recognized
   literal `len(parameter)>bound` rejection guard. Uncalled consumers do not enter the
   entry inventory. Record each actual caller/call site; relation IDs are source
   location identities, not semantic root-cause identifiers.
2. Seed a finite input set from contract interval endpoints, valid -1/0/1 anchors and
   simple entry-parameter comparison literals with adjacent values. Internal byte
   thresholds are not copied into input units as seed values. All points stay inside
   the independently declared public domain, regardless of implementation rejection.
3. Interpret those points. For observed affine quantities, invert the consumer boundary
   and add nearby valid integer inputs. Freeze the enlarged set before a second pass.
   Exceeding budget blocks the entry; there is no silent truncation. This is at most
   one refinement round, not a solver for arbitrary hidden branches.
4. Reuse `facts` with explicit point sets. Check model, representation unit, observed
   route and implementation bound; then pass the structural relation through the
   existing constraint planner. Check the planner's resulting declaration back against
   source and ensure every proposed execution input was actually interpreted and is
   contract-valid. Incorrect coefficient/unit/route or unchecked-domain transfers block
   eligibility. These checks reuse the same interpreter; they are consistency gates,
   **not independent proofs**. Business units remain unknown and are not required for
   this representation-only mechanism.
5. Treat an excessive consumer quantity as a lead, not an executable oracle. Only a
   supported must-return entry obligation and a predicted distinguishing outcome qualify
   this narrow selector. Correct alternate handling, allowed refusal, unknown contract,
   unsupported facts and unobserved paths retain explicit deferred reasons.
6. A supported contract-valid rejection before the selected consumer also creates an
   entry-outcome candidate. It does not shrink the public valid domain or attribute
   the failure's cause to that consumer. Entries without any recognized consumer are
   currently unqualified; this is not a general entry audit.
7. Select at most one candidate per entry, then smaller execution domain and stable ID,
   within the slot budget. Related candidates cannot consume both slots when another
   entry qualifies. Entry grouping is a cheap diversity heuristic, not semantic
   independence or severity/expected-bug-yield ranking. Ties can change after renaming
   or moving code; no arbitrary tie preference is presented as a quality improvement.
8. With a predicted normal-return control, compile a finite property spec and run the
   existing search engine. Without a control, perform one direct probe rather than
   forcing an impossible search control. The fixed adapter imports the actual copied
   module and calls the entry. **Its oracle uses only the entry outcome contract**, not
   derived coefficients or thresholds. It observes the original consumer through a
   forwarding wrapper and compares actual quantities/types/outcome with interpreted
   facts. A disagreement is blocked, not a bug; the wrapper is an assumption confined
   to this restricted pure synthetic subset.

No observed consumer on a finite point set means `not observed`, never global
unreachability. Gaps between explicit points are unassessed. The planner sees only
contiguous runs of actually checked reachable points; no new route is assumed when
it generates domains. More than8 such intervals is currently budget-blocked. Multiple
quantity variants or different sites sharing one consumer can conservatively defer
otherwise interesting candidates because the current fact audit aggregates sites.

## Bounds, failure and evidence

Source/interpreter limits are inherited from `facts`:128KiB source,4000 AST nodes,
2000 steps/input, call depth4,8 consumer observations/input and128-bit coefficients.
At most8 entries and16 syntactic consumer sites/entry; point budget is shared by
candidate relations of one entry. Slots and points are fixed prototype limits, not
performance-calibrated settings.

At most4 actual property executions, each at most32 adapter calls and10 seconds,
including bounded reduction; direct mode is one1-second call. There is no overall OS
memory/wall-time quota including parsing/copying/hashing. No background processes,
services, dependencies or models. The first execution block, timeout, integrity error,
control failure or recorded search-setup error stops subsequent dispatch. No retries.
A static unsupported/deferred candidate does not prevent another qualified entry from
being considered. A found counterexample is preserved before moving to another entry.

Output is a new directory outside the source; overwrite is refused. It preserves the
request, sanitized source snapshot, implementation hashes, all relations/deferred
reasons, two-pass facts/bridge checks, property specs/fixed adapters, search cases or
direct observation, summary, missing dispatches and SHA256 manifest. Source integrity
is checked before/after execution. `complete` means the bounded workflow finished,
not all relationships were examined or the code is correct. CLI exit0 only means a
summary was produced; inspect all stage statuses. Request/setup errors can use exit2.
Raw execution artifacts can refer to temporary paths; archived source/adapter/hash
records retain the corresponding provenance. Original and execution-copy integrity
have separate checks; the copy strips native instructions/cache files.

## Remaining boundaries

This first version covers one structural family in one restricted Python module.
Public entries/contracts remain manual. Nonlinear/text/state/concurrency relations,
policy resolution, cross-module imports and automatic relationship significance are
not solved. Entry-only seed guards can miss helper-only interior routes; no observed
model means no inverse-boundary refinement for that route. All-safe predictions can
hide different obligations not represented here. Such omissions stay visible rather
than being treated as coverage.

The offline synthetic tests separately check inventory, fact/transfer gates, domain
refinement, selection and actual outcome execution. Their success does not establish
autonomous real-project discovery, superiority over direct Codex or lower token use.
No paid follow-up or main merge is authorized by an offline pass.
