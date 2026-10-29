# Offline path exploration — frozen validation rules

2026-10-29. Draft PR #16 only. No formal skills, model calls, real subject execution,
main merge or automatic retries. This plan precedes real-module selection/readout.

Implement static entry/evidence inventory from exports, public definitions and direct
local test calls. Assertions establish only exact concrete examples, never adjacent
valid inputs. Conflicting examples remain conflicts; unresolved fixtures, dynamic
calls and imported ownership remain unknown. Do not infer public validity from guards.

Use the existing bounded affine interpreter to record cross-function comparison
predicates in entry-input coordinates. Invert observed comparison decisions with their
prefix, within a separately supplied finite investigation universe, to generate unseen
paths. Iterate within fixed budgets. This is bounded path exploration, not global
symbolic proof. A route not reached is unknown unless a supported prefix's alternative
is exhaustively empty in this universe. Units remain representation-only.

Alternate verification (exact test obligation) and exploration (new path) queues;
round-robin entries in each queue, deduplicate entry/input tasks. Record overflow,
unsupported and pending tasks; do not qualify unknown-input rejection as a bug.
Reuse facts interpretation for quantity observations. Actual synthetic execution must
agree with predicted path/outcome/value; disagreement blocks, not a finding. Existing
consumer-capacity relations are a supported family, not a universal eligibility gate.

Limits: 8 selected entries, 32 pending path tasks per entry, 32 analyzed points per
entry, 64 total local synthetic execution calls. Investigation universe <=128 integers
inside [-10000,10000]. No retries. Static real checks never enable execution.

Synthetic qualification families (before implementation outcomes): hidden helper-only
branch; affine cross-call transform; repeated consumer sites; correct alternative;
allowed refusal; contradictory exact test obligations; infeasible path; unsupported
dynamic dispatch. Include renaming, helper splitting and equivalent arithmetic.
Independent exhaustive actual execution over a small finite domain is evaluator-only;
it must not feed planner inputs. Compare same-budget seed-only, auto-evidence seeds,
and full path exploration. Report case-specific path/outcome coverage, not bug yield.

Real-module selection rule, fixed before inspecting module outcomes: use this tool's
Python standard-library directory, top-level .py files in filename order, exclude
underscore names, size <=128KiB, literal list/tuple __all__, and at least3 public
top-level functions. Take the first2 eligible files. Read AST/text only, no target
import, test execution, dependencies or subprocess invocation. Inventory exact direct
test evidence only if a sibling test/test_<module>.py exists; absence is reported.
Do not replace an unsupported selection. No historical bug benchmark is consulted.
Audit a fixed sample of first/last public definitions, first eligible/unsupported root,
and first unresolved call when present, including unselected records. This is an
integration check, not a real bug evaluation. Source paths and hashes pin observations.
