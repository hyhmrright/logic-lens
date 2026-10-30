# Experimental property → bounded local search

This optional prototype lives in draft PR #16. It is not the default review method,
release-qualified, or evidence of better bug discovery. It uses Python's standard
library and trusted local command adapters; it never calls a coding model or service.
No dependency installation, solver, fuzzing framework or project-specific bug catalog
is required. Current review skills, prompt compilation and frozen experiments are
unchanged.

## Run the synthetic example

From the repository root, choose a new output directory:

```bash
python3 scripts/logic_lens.py search \
  --spec examples/property-search/property.json \
  --workspace examples/property-search/workspace \
  --out /tmp/logic-lens-property-example
```

The example contract promises that a signed displacement and its inverse restore
position. The adapter imports the real `axis.py` from the copied workspace and checks
that relation. It is a synthetic program, not a newly selected real benchmark case.
The correct implementation exhausts ten combinations. Offline tests introduce an
absolute-value defect, obtain and reduce a counterexample, then restore the correct
implementation and observe the violation disappear. No model generates an answer.

## Property specification and adapter protocol

The example JSON is the complete runnable schema. Required descriptions:

- `claim`: the relation being tested, without asserting a defect exists.
- `domain`: valid input/state conditions and any limits of the relation.
- `observation`: the observable result or effect to compare.
- `violation`: what would contradict the claim.
- `contract`: nonempty `{path, start, end, quote}` references to workspace text.
  Lines are one-based and inclusive; quotations must match exactly. Matching text
  checks provenance, not whether the text establishes the proposed property.

`domains` maps one to eight parameter names to finite arrays of 1..64 JSON values;
the product is capped at one million combinations. Parameters can describe lengths,
values or an entire operation sequence. The trusted adapter constructs real inputs
from them. The engine does not infer valid inputs, invent transformations or assume
round trips, idempotence or ordering invariance. `control` names one member of every
domain and must pass before exploratory results are interpreted.

`adapter.files` lists local files relative to the spec's directory, archived with
the specification. `adapter.argv` is a literal argument array, never a shell string.
`{python}` expands to the current interpreter; `{adapter_dir}` expands to the archived
adapter directory. Other local runtimes can be invoked explicitly. The working
directory is a temporary source copy, with Python paths pointing to that copy.
Adapters receive one stdin JSON object, `{"case": {...}}`, and emit exactly one JSON
object on stdout:

```json
{"status":"pass","observation":{"expected":0,"actual":0},"sources":["axis.py"]}
```

Statuses are `pass`, `violation`, `invalid` or `blocked`. The first two require an
observation and nonempty source path list; paths must refer to files within the
executed copy and are hashed. Invalid/blocked cases need a nonempty reason. An
adapter crash, malformed output, missing source provenance or timeout is blocked,
not a bug. Catch a subject exception in the adapter if a sourced contract makes
that exception an observable violation; do not equate arbitrary process errors with
subject defects. Each case runs in a fresh process; stateful sequences belong inside
one case rather than rely on state across cases.

Adapters are executable trusted code. The tool copies source and checks original
and executed tree digests, but it is **not an OS sandbox** and does not prevent an
adapter from accessing external resources. Adapters must avoid services and external
state. The source list is adapter-reported provenance, not proof of what was imported;
inspect the adapter, validate actual module paths and review its oracle. The example
includes a runtime module-path assertion. Dependency files outside the archived list
and native runtimes need separate provenance if used. This prototype does not claim
hermetic, cross-platform execution equivalence.

## Bounded search and evidence

Defaults (all configurable within small prototype caps):

| Limit | Default | Allowed |
|---|---:|---:|
| Total adapter invocations, including control and shrinking | 32 | 1..128 |
| Search deadline in seconds | 10 | 1..60 |
| Individual invocation seconds, also limited by remaining deadline | 1 | 1..10 |
| Retained stdout/stderr bytes per invocation, each | 4,096 | 256..65,536 |
| Shrinking invocations, within total invocation budget | 8 | 0..32 |

The control runs first. A seeded sample without replacement chooses other finite
combinations; the entire product is covered only if it fits the budget and execution
finishes. On the first violation, bounded coordinate reduction tries earlier domain
members, preferring the control. It preserves observed violating results and never
claims a globally minimal witness. Domain ordering is the declared reduction order,
not a universal notion of smallest input. Blocking during shrinking stops reduction;
the original witnessed difference remains evidence requiring review.

Timeout or adapter/protocol blocking stops further exploration. Invalid cases are
counted separately and do not pass. Search stops after one counterexample; it does
not enumerate all defects. The timed search includes source copying and invocations; initial validation,
archiving and source hashing precede it, and final hashing/cleanup add overhead. Output sizes are polled, excessive output triggers
termination and retained logs are truncated; this is not a hard filesystem quota.
The process group is terminated where supported. Do not use daemonizing adapters.

CLI output contains aggregate counts and the witness, with large witnesses replaced
by an artifact reference. It does not emit every passing case or source code. Full
`observations.json`, per-case inputs/logs, `summary.json`, archived spec/adapter and
`sha256.json` retain the audit trail. Output must be outside the workspace and cannot
be overwritten. Relevant status meanings:

| Status | Meaning |
|---|---|
| `counterexample` | Adapter witnessed a difference; review oracle, harness and reachability before calling it a bug |
| `exhausted` | Finite declared combinations completed, some may be invalid; no general correctness claim |
| `sampled` | Only a bounded subset completed; no absence-of-bugs claim |
| `control_failed` | Baseline check was not a valid passing control; search did not start |
| `blocked` / `incomplete` | Execution failure or deadline/budget prevented further exploration |
| `integrity_failure` | Original/copy source digest changed; observations cannot qualify a defect |

Exit code 0 means the experiment produced a counterexample or finished its finite
search, not that the subject is correct. Execution/spec errors use code 2. No retry,
model invocation, report grading or automatic repair is part of this command.

## Intended next integration

A reviewer would propose a few sourced properties and small adapters, run local search,
then investigate returned differences. It need not guess each concrete failing input
before execution. Schema completion alone cannot establish a valid property, and the
model may still select unhelpful relations. This is a finite search mechanism, not
an automatic semantic property generator or a proof system.

The prototype currently requires a separately authored spec/adapter. It is not yet
wired into model sessions or the read-only historical discovery protocol. That protocol
forbids writing harness files; any future integration must explicitly allow a separate
scratch area to both comparison arms, while preserving source snapshots. Never silently
add this tool to one arm's permissions or reuse old frozen plans with a new protocol.
Before a model test, freeze that integration, common permissions, prompts, cases,
budgets and judgment criteria and obtain user approval. Offline mechanism tests alone
cannot establish better investigation selection or bug discovery.
