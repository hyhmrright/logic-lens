---
name: iterate-skill
description: Run the Logic-Lens skill-improvement loop end to end — baseline → diagnose failures → edit → sync cache → re-eval → verify net gain → iterate until clean. Use whenever the goal is to RAISE a skill's eval score or fix a failing eval mode: "improve logic-review", "the format compliance is failing, fix it", "iterate on this skill until the evals pass", "raise the score", "re-run the loop on the latest failures", "run another iteration", "tune the skill description / disambiguation table against the evals". Also use to RESUME a prior loop ("continue improving from where we left off", "do another pass", "iterate further"). Do NOT use for: a one-off question about a skill, shipping a release (use bump-version), or scaffolding a brand-new skill (use new-skill).
disable-model-invocation: true
---

# iterate-skill — the Logic-Lens improvement loop

This is the harness orchestrator. It coordinates three agents and two support skills into one
deterministic loop that raises a skill's eval score without overfitting or grader-gaming.

**Execution mode: sub-agent pipeline (generate → test → verify).** Each step's output is the next
step's input, handed off through the filesystem (`skills-workspace/iteration-<TAG>/`) and agent
return values. There is no peer-to-peer team chatter, so agents are spawned via the `Agent` tool —
**always with `model: "opus"`**, and **`subagent_type` set to the agent's own definition name** (e.g.
`subagent_type: "skill-editor"`), not `"general-purpose"` — passing `general-purpose` would discard
the role/principles in `.claude/agents/<name>.md`, defeating the harness. Agents return results to
this orchestrator, which owns state and the ship/rollback decisions.

**Agents (who) — all in `.claude/agents/`, spawn by these exact `subagent_type` names:**
| `subagent_type` | Role |
|-----------------|------|
| `eval-failure-analyzer` | Read-only: cluster failures, map to eval IDs, propose minimal edits |
| `skill-editor` | Apply one minimal, generalized edit; refuse grader edits |
| `iteration-guard` | Verify net gain vs variance; recommend SHIP / ROLLBACK / RERUN (orchestrator executes any revert) |

**Support skills (how):** `sync-skill-cache` (mandatory pre-eval gate), `run-iteration-eval` (run + grade).

## Phase 0 — context check (initial / resume / partial)

Determine the run mode before doing anything:
- `ls -dt skills-workspace/iteration-*/` — if recent iterations exist and the user asks to "continue"
  or "another pass" → **resume**: use the latest as baseline, skip re-baselining.
- User provides a fresh target skill / new failure → **initial**: establish a baseline first (Phase 1).
- User asks to redo just one mode or one skill → **partial**: scope the eval to the affected case IDs.

Confirm the target skill (which of the six `logic-*`) and the failing mode with the user if ambiguous —
do not guess which skill to mutate.

## Phase 1 — baseline

If no usable baseline exists for the target: run the `run-iteration-eval` skill (sync cache, then a
full or mode-scoped run) to get `summary.json`. This is the number every later iteration is judged
against. Record its TAG.

## Phase 2 — diagnose

Spawn `eval-failure-analyzer` (`Agent`, `model: "opus"`) pointed at the baseline iteration dir. It
returns the prioritized failure modes, the exact failing eval IDs, and concrete edit proposals. Pick
the single highest (failure-count × ease-of-fix) mode for this iteration. **One mode per iteration** —
batching edits makes the verify step unable to attribute a regression.

## Phase 3 — edit

Spawn `skill-editor` (`Agent`, `model: "opus"`) with the chosen proposal. It applies one minimal,
generalized edit and reports what it touched + its risk note. If it refuses (the proposal needs a
grader/assertion change), drop that proposal and pick another mode — never relax the grader.

## Phase 4 — sync cache (gate)

Run `sync-skill-cache`. If it reports DRIFT or a missing cache, **stop the loop** and surface it — an
unsynced eval grades stale content and wastes the run. Do not proceed to Phase 5 until it prints OK.

## Phase 5 — re-eval

Run `run-iteration-eval` scoped to the affected mode's case IDs (cheap) for a fast read; widen to a
full run before a final SHIP decision. New `summary.json`, new TAG.

## Phase 6 — verify

Spawn `iteration-guard` (`Agent`, `model: "opus"`) with the baseline and candidate iteration dirs +
the editor's risk note. Act on its verdict:
- **SHIP** → keep the edit; the candidate becomes the new baseline.
- **ROLLBACK** → revert the edit (it named which one); baseline unchanged.
- **RERUN** → the move is inside variance; rerun the affected cases 2–3× (Phase 5) and re-verify
  before deciding.

## Phase 7 — iterate or report

If SHIP and more modes remain and the score isn't at target → loop back to Phase 2 on the next mode.
Otherwise produce the **迭代报告** (in 简体中文): baseline→final overall + logic/format subscores, the
per-iteration Fix Log (mode, edit, verdict), and any mode left unresolved with why.

After reporting, offer Phase 7 evolution (harness skill): if the same failure mode recurs across loops,
or the editor keeps refusing the same proposal, propose a harness change (a new disambiguation rule in
the editor's principles, a new agent) and log it in CLAUDE.md's 변경 이력.

## Data-passing protocol

- **File-based** (durable handoff): all run artifacts live in `skills-workspace/iteration-<TAG>/`;
  agents read these dirs directly. Never delete a prior iteration dir — it is the rollback reference
  and the audit trail.
- **Return-value based** (control flow): each agent returns its report to this orchestrator, which
  decides the next step. Agents do not call each other.

## Error handling

1-retry then proceed-with-note. Specifically:
- **Cache sync fails** → hard stop (never eval stale content). Report and fix the cache, don't skip.
- **An eval case errors** (claude call fails) → the runner isolates it; re-run just that case once,
  then proceed and note the missing case in the report rather than blocking the whole loop.
- **Guard says RERUN repeatedly** (persistent variance) → report the move as "within noise floor,
  inconclusive" rather than forcing a SHIP/ROLLBACK; widen the case set instead of trusting one run.
- **Conflicting signals** (logic up, format down) → do not average them away; report both subscores
  with their sources and let the user weigh, per the project's "logic = primary / format = gate" split.

## 테스트 시나리오

**정상 흐름:** User: "logic-review 的 format compliance 一直挂，迭代修一下。" → Phase 0 initial → Phase 1
baseline (format subscore low) → analyzer flags the format-label mode + eval IDs → editor sharpens the
literal label in the SKILL.md skeleton → sync OK → re-eval affected cases → guard: format up, logic
flat, no collateral → SHIP → report with before/after subscores.

**에러 흐름:** Editor's proposed fix requires loosening a grader assertion → editor refuses in Phase 3 →
orchestrator drops that proposal, picks the next mode from the analyzer's list, and continues — the
grader is never touched. If instead the cache sync prints DRIFT in Phase 4, the loop halts and reports
the drift before spending any eval tokens.
