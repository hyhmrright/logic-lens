
--- RESOURCE skills/logic-review/SKILL.md ---
---
name: logic-review
description: >
  Find behavioral bugs in a file or function by investigating its contracts,
  callers, dependencies, and execution paths. Trigger for "review this",
  "check this function", "find bugs", or "tests pass but production fails"
  without an already confirmed failure. A file is the review target, not a
  boundary on supporting evidence. For directory-wide surveys use logic-health;
  for a confirmed failure use logic-locate; for two versions use logic-diff.
  Do NOT trigger for: style/formatting, standalone security or performance audits,
  test authoring without a review request, or architecture-only questions.
---

# Logic-Lens — Logic Review

Find observable violations of supported behavior. Investigate before rendering a
report: a familiar pattern, missing guard, or uncertain contract is a lead, not a bug.

## Setup

Use lazy loading from `../_shared/common.md` §13. Read its language, Iron Law,
headers/score, scope, confidence, remedy, and project-config rules; read the active
step of `logic-review-guide.md` as needed. Load `semiformal-checklist.md` when building
premises, `semiformal-guide.md` for trace mechanics, `logic-risks.md` when classifying
confirmed causes, and `report-template.md` only when rendering output.

## Process

1. **Establish behavior** (guide Step 1). Separate observed code facts, required
   behavior with its source, and unverified assumptions. Read actual callers and
   tests; do not use names or the current implementation as the sole correctness oracle.
2. **Map behavior boundaries** (guide Step 2). Connect each important promise to
   its producer, representations, alternate supported entries, and first consumer.
   Follow dependencies to answer specific questions; preserve uncovered routes.
3. **Search for distinguishing counterexamples** (guide Step 3). Compare supported
   representations, routes, and operation sequences against the same obligation.
   Choose a small experiment or read whose outcomes separate competing explanations.
   Keep a hypothesis ledger; use L1–L9 as a backstop.
4. **Trace and challenge** (guide Step 4). Trace concrete values and observable
   consequences; search for defenses covering that exact path. Keep impact,
   confidence, and investigation status separate. Partial defenses require investigation.
5. **Probe early and verify** (guide Step 5). Use bounded real-code experiments
   during discovery when they resolve uncertainty; do not wait for a finished proof.
   For Critical/Warning candidates, attempt verification when feasible. A failure
   to reproduce is inconclusive unless it supplies a valid counterexample to the
   finding. Record runtime, setup, assertion source, and fidelity limitations.
6. **Prepare findings and remedies** (guide Step 6). Deduplicate by root cause,
   assign L-codes and severity to supported defects, and verify the proposed remedy
   without changing the user's files during a read-only review.
7. **Report once** (guide Step 7). Preserve the five literal Iron Law fields and
   localized template. Scope includes traced paths and omissions; append unresolved
   investigations after Summary. A score describes confirmed findings within that
   scope, never probability of correctness or permission to ship.

**Mode line:** `Logic Review` (Chinese: `逻辑审查`). Route whole-directory requests
to logic-health; supporting caller/callee/configuration files remain available to review.

--- RESOURCE skills/logic-review/logic-review-guide.md ---
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

--- RESOURCE skills/_shared/common.md ---
# Logic-Lens — Shared Framework

## 1. Language Hard Constraint (HIGHEST PRIORITY)

**Rule:** Identify the dominant language of the user's most recent message. Treat as Chinese if ≥ 50% of characters are Chinese Han (not Japanese kana or Korean Hangul — respond in those languages for those scripts). Default to English if ambiguous. All response text MUST use the detected language — including:

- Every section header (`# Findings`, `## Summary`, and every header listed in the map below)
- Every finding's field labels (Premises / Trace / Divergence / Trigger / Remedy / Verification)
- The narrative one-liner under the header, the Summary prose, and any text between findings

**Localized header map (use these exact strings when the user writes in Chinese):**

| English | 中文 |
|---------|------|
| Findings | 发现 |
| Summary | 总结 |
| Premises | 前提 |
| Trace | 追踪 |
| Divergence | 偏差 |
| Remedy | 修复 |
| Mode | 模式 |
| Scope | 范围 |
| Logic Score | 逻辑评分 |
| Fault Confidence | 故障置信度 |
| Verdict | 判定 |
| Module Breakdown | 模块分布 |
| Systemic Patterns | 系统性模式 |
| Recommended Priority Order | 优先级建议 |
| Fix Log | 修复记录 |
| Iteration History | 迭代历史 |
| Skill Invocations | 技能调用次数 |
| Critical / Warning / Suggestion | 严重 / 警告 / 建议 |
| Semantically Equivalent | 语义等价 |
| Conditionally Equivalent | 条件等价 |
| Semantically Divergent | 语义分歧 |
| Trigger | 触发 |
| Verification | 验证 |
| Rebuttal check | 反驳检查 |
| Dry-run | 预演 |

*Note: `Rebuttal check` and `Dry-run` are sub-annotations appended within the Trace and Remedy fields respectively — they are not top-level finding fields.*

**Stay in native form regardless of user language:** fenced code blocks, identifier names (`format`, `users.remove(...)`), L-codes (`L1`–`L9`, `C1`, `C2`...), file paths, exception class names, operator symbols.

**Violation check:** if the response is Chinese but a header reads `# Findings`, rewrite before returning.

---

## 2. Iron Law

NEVER emit a Trigger or Remedy before completing Premises → Trace → Divergence for that finding.
EVERY finding follows these fields in order: **Premises → Trace → Divergence → Trigger → Remedy**.
The **Trigger** field (concrete reproducing input) is required for Critical and Warning findings; optional for Suggestions.

**Mandatory field labels:** Each finding MUST use the exact field labels as literal prefixes — `Premises:`, `Trace:`, `Divergence:`, `Trigger:`, `Remedy:` (or their Chinese equivalents `前提：`, `追踪：`, `偏差：`, `触发：`, `修复：`). Free-form prose without these labels is NOT a valid finding. A response that identifies the bug correctly but omits these labels has failed the Iron Law.

**Mandatory L-code:** Every finding title MUST include the L-code (e.g., `**[L4] — ...`). Every finding's Divergence field must name the L-code. An analysis without L-code classification is incomplete.

**Mandatory Logic Score:** Every logic-review output MUST include a `Logic Score: XX/100` line (or `逻辑评分：XX/100`). This is part of the report header, not optional.

Reasoning without an execution trace is guessing. Semi-formal tracing is the evidence.

---

## 3. Semi-Formal Reasoning

Three-step tracing: **Premises → Trace → Divergence**. Full methodology, language-specific tracing notes, and interprocedural reasoning guidance live in `skills/_shared/semiformal-guide.md`. The premises construction checklist is defined once in `skills/_shared/semiformal-checklist.md` — guides cite it by reference rather than duplicating it.

---

## 4. Report Template

The full English + Chinese templates and all rendering rules live in **`report-template.md`** (single source). Every skill renders its output by following that file, applying the language rule from §1 and the mode-specific header field from §5.

---

## 5. Mode-Specific Header Variants

The header field directly under `**Scope:**` differs by skill:

| Skill | Header field | Values |
|-------|--------------|--------|
| logic-review | **Logic Score:** | `XX/100` (see §6) |
| logic-health | **Logic Score:** | `XX/100` (weighted average of per-module scores, §6) |
| logic-explain | _(omitted)_ | Execution Explain is descriptive, not evaluative |
| logic-locate | **Fault Confidence:** | `High` / `Medium` / `Low` (see §7) |
| logic-diff | **Verdict:** | `✅ Semantically Equivalent` / `⚠️ Conditionally Equivalent` / `❌ Semantically Divergent` |
| logic-fix-all | **Logic Score (before)** / **(after)** | two lines + findings-fixed / findings-unresolved counts |

---

## 6. Logic Score (logic-review & logic-health)

Start at 100. Deduct only per **confirmed** finding (Trace supports the finding — speculative divergences stay at Suggestion severity but do not deduct):

| Severity | Deduction |
|----------|-----------|
| Critical | −15 |
| Warning | −7 |
| Suggestion | −2 |

Floor: 0. Cap at one deduction per unique L-code per **module** (do not stack multiple L1 findings for the same shadow). In logic-health this cap applies per-module, not repo-wide — five modules each with an L3 each lose 7 points independently.

logic-health weights per-module scores by `line_count / total_lines_reviewed` — a tiny perfect module must not mask a large Critical-heavy one.

---

## 7. Confidence Rubric (unified across skills)

| Level | Trace requirement | Primary use |
|-------|-------------------|-------------|
| **High** | Premises → Trace → Divergence form a complete, verifiable chain | logic-locate Fault Confidence; "confirmed" findings |
| **Medium** | Chain is strong but one step rests on an unverified assumption (library behavior, external config) | logic-locate Fault Confidence; findings needing manual check |
| **Low** | Plausible fault; alternative causes cannot be ruled out without executing the code | logic-locate Fault Confidence; must carry "manual verification recommended" |

Low-confidence findings in logic-health are downgraded to Suggestion severity. In logic-review, keep impact, confidence, and investigation status separate per its guide: incomplete candidates remain unresolved investigations, not confirmed findings or automatic fix candidates.

---

## 8. When No Bugs Are Found

Report Logic Score 100 (or the mode-specific equivalent) and state the scoped conclusion below. For logic-review, also disclose unresolved investigations and clarify that the score measures confirmed findings in inspected paths, not probability of correctness:

> "No confirmed logic bugs found in the inspected paths."

(Chinese: "所检查的路径中未发现已确认的逻辑错误。")

Do not invent speculative findings to fill the Findings section. An empty Findings section with a high score is valid and valuable. Minor observations go under Suggestion with a full five-field entry — never as loose prose.

**Correctness parity principle:** correctly concluding "no bug" has the same professional value as correctly finding a bug. Do not lower evidence standards to produce findings.

---

## 9. Scope Management

The target bounds what is reviewed, not which supporting caller/callee/configuration files may be read. For logic-review use its dependency-slice guide: the following size limits are an initial worklist budget, not a hard stop on evidence gathering.

If the target exceeds ~150 lines or 5 non-trivial functions, do not scan shallowly. A deep trace of 3 functions beats pattern-matching across 30. Priority:

1. Functions the user flagged as suspicious or recently broken.
2. Functions touching external state, APIs, or user-controlled input.
3. Functions changed in the last commit (`git log --oneline -5 --name-only`).

State the covered scope at the top of the report. If partial, say so.

**Scope-to-skill cheat sheet** (used by every SKILL.md's Step 0 routing):

| Signal | Correct skill |
|--------|---------------|
| One file or one function, no confirmed failure | logic-review |
| Directory, module, or "the codebase" | logic-health |
| Stack trace / failing test / specific wrong output | logic-locate |
| Two code versions (before/after refactor, A/B implementations) | logic-diff |
| "Why does this do X?" / "trace through Y" | logic-explain |
| "Fix everything across the repo" (no target named) | logic-fix-all |

---

## 10. Remedy Discipline

A Remedy MUST be a **minimal, concrete, paste-ready fix**. Acceptable:

- A diff or code block containing the exact replacement text
- A one-line edit instruction naming file, line range, and the new expression
- For config/docs: the exact new value or the exact replacement sentence

Unacceptable: "add validation", "be careful with", "consider refactoring", "add more tests".

If the fix requires a design decision the user must make, say so explicitly using this block format:

```
[DESIGN DECISION REQUIRED]
Options:
  A. <option> — <trade-off>
  B. <option> — <trade-off>
Recommendation: <which option and why, or "no recommendation — depends on X">
```

When responding in Chinese, translate all user-visible text in the block: use `[需要设计决策]` as the block label; `选项：` for "Options:"; `推荐：` for "Recommendation:"; `无推荐——取决于 X` for "no recommendation — depends on X". Keep `<option>` and `<trade-off>` placeholders and A./B. option letters in their original form.

---

## 11. Fallback Behavior

- **Git unavailable:** skip git-based scope detection, ask the user for the target, proceed.
- **Emoji disabled / plain terminal:** replace severity emojis with text markers — `[CRITICAL]`, `[WARNING]`, `[SUGGESTION]`. Keep L-codes as-is.
- **No tests / no docs:** state the absence in premises, infer intent from function/variable names, flag the doc gap as a Suggestion.

---

## 12. `.logic-lens.yaml` — Optional Project Config

Lives at repo root. Each skill reads only the fields it needs.

```yaml
disable: []           # risk codes to skip
severity: {}          # severity overrides, e.g. {L3: critical}
ignore: []            # glob paths to skip
focus: []             # risk codes to prioritize
custom_risks: []      # project-specific Cx codes (schema below)
trace:
  min_steps: 3        # if a trace has fewer steps, the reviewer must downgrade the finding to Suggestion (no automated checker — see semiformal-guide.md "Minimum thresholds")
  require_anchors: 2  # minimum line/file/boundary anchors across the trace; same downgrade rule applies
fix_all:
  max_iterations: 3   # Warning/Suggestion iteration cap (Criticals loop without cap)
```

**Field-by-skill matrix:**

| Field | review | explain | diff | locate | health | fix-all |
|-------|:------:|:-------:|:----:|:------:|:------:|:-------:|
| `disable` | ✓ | — | ✓ | ✓ | ✓ | ✓ |
| `severity` | ✓ | — | ✓ | ✓ | ✓ | ✓ |
| `ignore` | — | — | — | — | ✓ | ✓ |
| `focus` | ✓ | — | ✓ | ✓ | ✓ | ✓ |
| `custom_risks` | ✓ | — | ✓ | ✓ | ✓ | ✓ |
| `trace.*` | ✓ | — | ✓ | ✓ | ✓ | ✓ |
| `fix_all.*` | — | — | — | — | — | ✓ |

`custom_risks` schema:

```yaml
custom_risks:
  - code: C1
    name: "Protocol Version Mismatch"
    description: "Messages encoded with one protocol version are decoded with another"
    severity: critical   # one of: critical | warning | suggestion
```

---

## 13. Loading and Scan Budget

Do not bulk-load the whole framework unless the current step needs it.

**Required upfront for every skill:**
- `common.md` sections relevant to routing, language, output header, confidence/score, scope, and remedy.
- The skill's own `SKILL.md`.

**Load on demand:**
- `logic-risks.md` only when selecting, classifying, or explaining an L-code.
- `semiformal-guide.md` only for trace mechanics, thresholds, call-chain labels, or interprocedural depth questions.
- `semiformal-checklist.md` only while constructing premises.
- `report-template.md` only immediately before rendering the final report.
- The skill guide section for the active step; avoid reading later guide sections until that step starts.

**Scan budget rule:** prefer complete traces over broad shallow scans. If scope is large, first build a ranked worklist, then trace only the highest-risk slice and state the uncovered remainder in `Scope`. Expand only when the user asks for exhaustive coverage or the current trace requires it.

--- RESOURCE skills/_shared/semiformal-guide.md ---
# Logic-Lens — Semi-Formal Reasoning Guide

Semi-formal means: more structured than prose, less formal than a proof system. The goal is a **certificate** — a trace any reader can follow step by step to verify the conclusion.

---

## Premises Construction

Before tracing, enumerate premises explicitly using the four-section checklist in **`semiformal-checklist.md`**: Name Resolution, Type Contracts, State Preconditions, Control Flow Assumptions. That file is the single source — all skill guides reference it rather than re-listing.

A trace without explicit premises is not valid: skip the checklist and you forfeit the certificate property.

---

## Execution Trace Discipline

A valid trace is sequential and interprocedural:

```
1. [line N] Expression E is evaluated.
2. Name `f` resolves to [actual definition, with module/class path].
3. Arguments: arg1 has type T1 (traced from line M), arg2 has value V.
4. Inside `f` at line P: condition C evaluates to [True/False] because [reason].
5. [line Q] Side effect: variable X is mutated to Y.
6. `f` returns Z (type: T).
7. [line R] The returned Z is used as [role]; assumption was [expected value/type].
```

Rules:
- **Do not summarize.** "The function processes the input" is not a trace step.
- **Resolve every name.** Never write "calls `format()`" — write "calls the module-level `format()` defined at `dateformat.py:12`, which expects a datetime object."
- **State types explicitly.** "Passes `self.data.year`" → "passes `self.data.year`, type `int`."
- **Cross function boundaries.** If the bug is in a callee, trace into the callee.
- **Stop at the divergence.** The trace ends when you've identified the exact step where the premise breaks.

### Minimum thresholds

For logic-review, these are certificate targets: a shorter direct proof need not be padded, and missing evidence stays an unresolved investigation per its guide, without changing impact. For other modes, a trace below either threshold is **incomplete**. For diff/health, drop the finding or downgrade to **Suggestion** with `manual verification recommended`; do not promote it to Critical or Warning. For locate, downgrade Fault Confidence to **Low** unless the missing anchor/step is supplied by a concrete stack trace, failing assertion, or observed output.

- **≥ 3 substantive steps.** Each step is a distinct evaluation, name resolution, type transition, mutation, branch decision, or callee return.
- **≥ 2 location anchors.** `[line N]`, `[file.py:N]`, a function-boundary marker (`→ enter callee X`), or for non-line code a section/key reference.

Optional config: `.logic-lens.yaml` can override via `trace.min_steps` and `trace.require_anchors` (see `common.md` §12).

---

## Divergence Identification

A divergence names: location (line/expression), violated premise, actual behavior, and observable consequence:

```
Divergence: Line 42 — `format(self.data.year, "04d")` calls the module-level
`format(obj, format_string)` (resolved in Premises), passing an `int` where
a datetime is expected. This raises `AttributeError: 'int' object has no
attribute 'strftime'` at runtime.
```

---

## Language-Specific Tracing Notes

### Python
- `from module import name` — does `module` redefine a builtin called `name`? (L1)
- Mutable default arguments: `def f(x=[])` shares the list across calls (L4)
- `None` returns from methods that sometimes don't return explicitly (L2, L6)
- `for i, x in enumerate(lst)` modifying `lst` inside loop (L4)
- `except Exception` swallowing the real error (L5)

### JavaScript / TypeScript
- `var` hoisting and closure capture of loop variable — L4 if handlers fire sequentially; L7 if concurrent listeners
- Implicit coercion: `"5" + 3 === "53"`, `"5" - 3 === 2` (L2)
- `undefined` vs `null` — methods exist on one but not the other (L2, L3)
- Promise rejection not caught in `async` function (L5)
- Prototype chain method lookup (L1)

### Java / Kotlin
- `equals()` vs `==` for object comparison (L2)
- Integer overflow without explicit widening cast (L2, L3)
- Checked exception caught at wrong level, returning null (L5, L6)
- Subclass method hiding a parent method (L1)

### Go
- Named return values and `defer` — deferred call arguments are evaluated immediately, while deferred closures read captured variables when the closure runs (L4)
- Nil interface vs nil pointer — an interface holding a nil pointer is not nil (L2)
- Goroutine closure capturing loop variable — L4 if sequential; L7 if concurrent
- Error ignored with `_` (L6)

### Rust
- `unwrap()` / `expect()` — trace whether the None/Err case can actually occur (L3)
- Interior mutability (`RefCell`, `Mutex`) — runtime borrow, potential panic (L4)
- Iterator adapters are lazy — missing `.collect()` means no work happens (L6)

### SQL (embedded)
- `NULL` propagation: any arithmetic with `NULL` produces `NULL` (L3)
- `NOT IN` with a subquery that can return `NULL` — entire expression evaluates to unknown (L3)
- Implicit type coercion in `WHERE` disabling index (L2)
- `TIMESTAMP` vs `TIMESTAMP WITH TIME ZONE` mismatch (L9)
- Transaction left open on early-return path (L8)

### Concurrency / async (cross-language, L7)
- Read of shared state across `await`/`yield`/channel boundary without re-checking
- Non-reentrant lock acquired twice by same context; lock released on path that did not acquire it
- Cancellable task mutating shared state mid-operation, leaving partial updates
- Producer writes to channel/queue after consumer was cancelled

### Resource lifecycle (cross-language, L8)
- Resource acquired but released only on success path (try without finally/with/defer)
- Resource released twice on overlapping cleanup paths
- Ownership returned to caller without updating caller's release plan
- Long-lived subscription whose unsubscribe captures a stale handle

### Time / locale (cross-language, L9)
- Naive datetime compared with timezone-aware datetime
- Wall-clock arithmetic across a DST boundary
- `toLowerCase`/`sort` whose result depends on active locale
- Date parsed without explicit zone — defaults differ across runtimes
- Numeric parse/format that assumes `.` decimal separator under a locale that uses `,`

---

## Interprocedural Reasoning

When `f` calls `g(x)`, do not assume `g` behaves as its name implies. Instead:

1. Find `g`'s actual definition (check imports, monkey-patching, dependency injection).
2. Read `g`'s implementation for the specific argument `x`.
3. Note any conditions under which `g` behaves differently from the caller's assumption.
4. Return to `f`'s trace with the actual behavior of `g` substituted.

The bug is most often in the interaction between two functions, not in the function being looked at in isolation.

### Call-Chain Context Labels

When a trace crosses more than one function boundary, prefix each step with a call-chain label so the reader never loses their place in the stack:

```
[entry → parse_config:12] cfg_path = args[0]  — type: str
[entry → parse_config → read_file:34] fd = open(cfg_path)  — may raise FileNotFoundError
[entry → parse_config → read_file:41] content = fd.read()  — fd is open here
[entry → parse_config → read_file:47] ← early return on empty content; fd NOT closed  [L8]
```

Format: `[caller → callee → …:line]`. Omit intermediate frames only if they add no observable state change. The label makes cross-file findings unambiguous and allows a reader to reconstruct the exact call stack without re-reading source.

For logic-review, use its dependency-slice budget: depth alone does not determine confidence; resolve intermediate contracts and record missing evidence. For other modes, stop tracing into callees beyond **4 hops** from the entry point. Beyond 4 hops the premises required to maintain accuracy compound faster than the trace gains certainty. For diff/health findings, downgrade any finding that depends on an inference at hop 5 or deeper to **Suggestion** with `manual verification recommended`; for locate, downgrade Fault Confidence according to `common.md` §7.

---

## Backward Reasoning

Use when forward tracing loses the bug path — for example: too many branches make it unclear which path leads to the failure, or a loop invariant is too complex to track forward from initialization.

**Procedure:**

1. **State the failure precisely.** Name the location (file, line or expression), the incorrect value or behavior, and the condition that makes it wrong: `"At line 78, result is -1 but the contract requires ≥ 0."`
2. **Ask: what must be true one step earlier for this failure to occur?** Work backward through the most recent assignment, return, or branch that produced the failing value.
3. **Continue backward** through assignments, function returns, and conditional branches. At each step ask: *which predecessor state is necessary for this state to hold?*
4. **Stop at the broken premise.** When you reach a step where the necessary predecessor state contradicts a premise you established in Premises Construction, you have the root cause. Write the Divergence there — not at the symptom site.

**When to use:**
- The symptom is at a late stage (e.g., wrong output, assertion failure at return site) but the root cause is at an early input-processing step.
- Forward tracing reaches a branch with ≥ 3 paths and you cannot determine which path was taken without executing the code.
- L7/OV findings where you know B produced a wrong result but need to trace back to find which earlier operation A was supposed to precede B.

**Do not use backward reasoning alone.** It establishes a necessary condition at the root site, not a sufficient one. After identifying the root candidate, confirm with a short forward trace (even 2–3 steps) that the root condition actually leads to the symptom — this completes the certificate.

--- RESOURCE skills/_shared/semiformal-checklist.md ---
# Logic-Lens — Premises Construction Checklist (Single Source)

This is the **single source of truth** for the Premises step. Skill guides cite this file — directly in review/explain/diff, indirectly in locate/health/fix-all. Run every applicable bullet before producing a Trace.

When the user writes in Chinese (per `common.md` §1), produce the trace in Chinese; this checklist is language-neutral.

---

## 1. Name Resolution

For every non-trivial identifier in a function call, attribute access, or expression:

- **Full qualified name.** What does the identifier resolve to? Local → enclosing scope → module → builtins/global. State the exact definition site (`module.py:12`, `class Foo.method`).
- **Shadowing check.** Is there a local definition, import, class attribute, or enclosing-scope name that hides a builtin or expected name? (`from module import name` / `import module as alias` / subclass attribute hiding parent method)
- **Method dispatch.** For `receiver.method(...)`, what is the **runtime type** of the receiver? Which class's `method` dispatches?

---

## 2. Type Contracts

- **Expected type** at declaration/call site (annotations, docstrings, usage patterns).
- **Actual type** at each call: trace from origin — declaration, return of another function, parsed input, deserialized data — noting every transformation.
- **Implicit coercion/widening.** Does any operator or method call along the path implicitly convert types?
- **Nullable.** Can the value be `None`/`null`/`undefined`/`nil`? Under which branch?

---

## 3. State Preconditions

- What state must be initialized/non-null/non-empty before this code runs?
- Is that initialization guaranteed? By whom? Under what conditions might it be absent?
- For mutable state: what was the prior value, and does this code depend on a specific prior state?
- For external state (DB, file, network, lock, transaction): is it acquired and in the assumed state?
- For resource ownership: who must release/rollback/close/unsubscribe, and does ownership transfer to another caller or object?

---

## 4. Control Flow Assumptions

- **Conditional branches.** For each `if`/`switch`/pattern match: which branch executes for the relevant inputs? Is it provably reachable?
- **Loops.** How many iterations? What terminates it? Can it run zero times? Unboundedly?
- **Early exits.** Are there `return`/`raise`/`throw`/`break`/`continue`/unhandled-exception escapes the caller might not anticipate? Do they skip non-lifecycle post-conditions (L5) or resource lifecycle obligations (L8)?
- **Async ordering.** For async/concurrent code: which `await`/`yield`/channel-send/callback/task-spawn is the happens-before boundary the rest of the trace depends on?

---

## What is NOT a Premise (anti-patterns)

Rewrite before continuing if the Premises field contains any of:

- **Goal restatement.** "The function is supposed to remove all inactive users" — this is intent, not an assumption the code makes.
- **Test-suite expectations.** "The test asserts the result equals 42" — this is what the trace must explain, not a premise.
- **Author intent from naming.** "The author probably meant X because the function is named `remove_all`" — state what the *code* assumes.
- **Unverified library behavior.** "`requests.get` raises on 5xx" without checking — mark as "unverified" and downgrade confidence.
- **The fix as a premise.** "Premises: the list should not be mutated during iteration" — this is the remedy in disguise.
- **Vacuous restatement.** "Premises: the function takes a list and a boolean" with no claim about contents, nullability, or origin.

A premise is valid when it is **falsifiable by the trace**: the trace can either confirm or contradict it.

--- RESOURCE skills/_shared/logic-risks.md ---
# Logic-Lens — Logic Risk Taxonomy (L1–L9)

## L1 — Shadow Override
An identifier resolves to a different entity than assumed — local/import/class binding silently overrides a builtin or expected name.
**Detect:** (1) Walk scope chain for every call/access: local→enclosing→module→builtins. (2) Check `from X import Y` / `import X as Y` for builtin shadowing. (3) Check subclass attributes hiding parent methods. If a name cannot be uniquely resolved, that itself is a finding.
**Symptom:** `f(x)` calls project-local `f` not builtin `f`; tests pass because they mock the same wrong name.
**Common in:** Python (import shadowing), JavaScript (prototype chain), Ruby (method aliasing), Lua (global mutation).

---

## L2 — Type Contract Breach
A function/operator receives a value of a type it cannot correctly process; the mismatch may be implicit or conditional.
**Detect:** (1) State the expected type for each parameter (hints/docs/usage). (2) Trace actual argument type from origin through every transformation to call site. (3) Check for implicit coercions or interface widening along the path. (4) Note nullable paths: when can the value be `None`/`null`/`undefined`?
**Symptom:** Value enters as type A, is treated as type B by an operator/intermediary, and arrives at a call expecting type C.
**Common in:** Python (`None` where `str` expected), JavaScript (numeric/string coercion), Go (nil interface vs nil pointer), Java (unchecked cast).

---

## L3 — Boundary Blindspot
Logic is correct for typical inputs but does not handle boundary conditions: empty collections, zero/negative numbers, null/None, single-element sequences, first/last loop iterations.
**Detect:** (1) For each collection/numeric/optional: trace the empty/zero/null path explicitly — do not assume happy-path trace covers it. (2) Check loop indices, slice ranges, division operations for off-by-one and divide-by-zero. (3) Check first/last element of sequences separately.
**Symptom:** `items[0]` or `total / count` without a guard for `len(items) == 0` or `count == 0`.
**Not L3 — designed capacity limits:** If code explicitly returns an error or rejection at a designed boundary (e.g., `return errors.New("cache full")` when `len >= maxSize`, HTTP 429, buffer-full rejection), that is correct boundary enforcement, not a blindspot. L3 applies only when code *attempts* to operate past the boundary and silently fails (crash, wrong result, infinite loop) — not when it explicitly gates the operation with an error return. Apply adversarial red-team: "Does the code explicitly return an error / rejection at this boundary rather than attempting to continue past it?" If yes, withdraw the L3 candidate. Note: a `panic` at a boundary is NOT a designed error return — it is a crash and remains a potential L3.
**Common in:** All languages. Especially array indexing, pagination, aggregation, date arithmetic.

---

## L4 — State Mutation Hazard
Shared mutable state is read or written in a **single execution context** in an order producing incorrect results. Includes mutations affecting ongoing iterations, aliased references causing unexpected sharing, read-after-side-effect ordering. For multi-context hazards, see L7.
**Detect:** (1) Identify mutable state, aliases, and state surviving across calls. (2) Trace reads and writes in order. (3) Establish an actual invariant or caller expectation violated by a mutation. Mutating an argument and returning the same reference is legal: report L4 only when documented non-mutation, independent-copy semantics, or a real caller's reliance on prior state is contradicted. An API convention alone is not evidence of a behavioral defect.
**Symptom:** Collection modified during iteration; variable read after being reset by side effect; alias mutated through one name and observed through another; function sorts/modifies in-place AND returns the same object.
**Common in:** Python (mutable default args, list mutation during `for` loop, in-place-sort returning self), JavaScript (closure over `var` loop variable), Go (slice aliasing across `append`), Java (mutating `Collection` while iterating).

---

## L5 — Control Flow Escape
An early exit (`return`, `raise`/`throw`, `break`, `continue`, unhandled exception) skips a required non-lifecycle operation: state update, validation, commit marker, audit event, notification, or invariant restoration. For acquire/use/release imbalance, use L8.
**Detect:** (1) List all required post-conditions for the function/block: state updated, invariant restored, commit marker written, notification emitted. (2) Enumerate every exit point including implicit raises from callees. (3) Verify each exit path meets all non-lifecycle post-conditions. (4) If the skipped operation is a resource release/rollback/unsubscribe/close, classify as L8 instead. **Exhaustive path rule:** report EACH exit path that skips the post-condition as a named path in the finding — do not stop after the first skipped path. A finding that names only one path is incomplete if others also skip the required operation.
**Symptom:** Status flag updated only on the happy path; audit event skipped on exception; validation bypassed by an early `return`; `continue` skips a required accumulator update.
**Common in:** All languages. Especially code refactored to add early returns, or exception handlers that don't mirror the acquisition path.

---

## L6 — Callee Contract Mismatch
Calling code assumes behavioral guarantees (return value semantics, exception behavior, idempotency, side-effect ordering) that the callee does not actually provide.
**Detect:** (1) For each local or external call, state what the caller assumes: return value, exceptions, idempotency, side effects, ordering. (2) Trace into the callee's implementation when local, or docs when external, and verify each assumption. (3) Flag: `None`/`null` returns the caller doesn't check; exceptions the caller doesn't catch; side effects the caller relies on but aren't guaranteed.
**Symptom:** `result = get_user(id)` then `result.name` without checking if `get_user` can return `None`; retry calling a non-idempotent function; assuming sort is stable when it isn't.
**Common in:** All languages. Especially at API boundaries, ORM interactions, third-party integrations.

---

## L7 — Concurrency / Async Hazard
Code under concurrency (threads, goroutines, async tasks, event loops) violates a single-thread assumption: atomicity of read-modify-write, happens-before across `await`/yield/channel boundaries, message ordering, cancellable operation progress. Distinct from L4 — L7 requires **more than one execution context**.
**Detect:** (1) Enumerate every concurrency boundary: `await`, `yield`, channel send/receive, lock acquire/release, callback, `Promise.then`, goroutine/task spawn. (2) For each boundary: which shared state is observable on both sides? Can another context mutate it between read and use? (3) For locks: trace acquire→use→release on every exit path. (4) For ordering: identify the synchronization enforcing it — "usually happens first" is not enforcement. (5) For cancellable tasks: trace partial-update state.
**Subtype — AV (Atomicity Violation):** A code region implicitly assumed to execute atomically is interleaved by another context (Detect step 2). Pattern: thread A performs read₁ … write₁ on variable V; thread B can execute between read₁ and write₁ and mutate V, making write₁ operate on a stale read. Check: (a) find every multi-step read-modify-write on shared state; (b) confirm another context can observe the variable between those steps; (c) verify a lock or atomic primitive protects the entire sequence, not just individual operations.
**Subtype — OV (Order Violation):** Code assumes operation A always completes before operation B, but no explicit synchronization enforces that order (Detect step 4). Pattern: initialization flag set by goroutine A is read by goroutine B before A has run. Check: (a) for every "A must happen before B" assumption, name the concrete synchronization primitive (mutex, channel, WaitGroup, Promise chain); (b) if none exists, the ordering is accidental — classify as L7/OV.
**Split-state flag race (L7/AV):** When one logical state is encoded as two independent non-atomic flags updated by different code paths (e.g., `mode_flag` set synchronously by one thread; `hardware_ready_flag` cleared asynchronously by a callback), reads of the pair in another thread are not atomic — any combination of values can be observed. The fix is always a single atomic state variable (e.g., an enum `ELECTRON | XRAY_RETRACTING | XRAY_READY`) so state transitions are indivisible. Recommend collapsing dual flags into one atomic state machine. **No-bug variant:** if both flags are updated atomically under the same lock (or a single atomic CAS) with no other code path mutating either flag outside that lock, the pair is effectively a single state variable — confirm by tracing all mutation sites before reporting.
**Async interleaving is L7, not L4:** Even though Python asyncio runs on a single OS thread, coroutines interleave at `await` boundaries. A check-then-act pattern with an `await` between the check and the act is an L7 atomicity violation (the event loop can schedule other coroutines that mutate shared state between the check and the act). Do NOT classify this as L4 — L4 is for single-context mutation hazards (iteration aliasing, mutable defaults). Similarly, JavaScript Promise races and Go goroutine interleaving are L7.
**Memory model hazards (Java/C++/Go):** For double-checked locking or publication patterns, always trace TWO aspects: (a) **visibility** — can another thread see a non-null reference before the object's fields are initialized? (missing `volatile`, missing `atomic`, no happens-before); (b) **initialization ordering** — is `loadFromDisk()` / constructor work guaranteed to complete before the reference is published? If `new Foo()` is followed by `this.data = loadFromDisk()` inside the constructor, the fields may be visible in an intermediate state. **Post-constructor initialization hazard (distinct pattern):** if initialization runs OUTSIDE the constructor — e.g., `instance = new ConfigCache(); instance.loadFromDisk();` — threads that read `instance` without holding the lock (e.g., the outer null-check in double-checked locking) can observe a non-null `instance` with `this.data == null`, because the write to `instance` can be visible to lock-free readers before `loadFromDisk()` completes. Report BOTH (a) the missing-`volatile` hazard AND (b) the publish-before-init-complete hazard; these are two faces of the same L7 finding. **Code-structure parsing rule:** When you see `instance = new ConfigCache(); instance.loadFromDisk();` as two separate statements, these are NOT atomic — the write to `instance` can be visible to lock-free readers (e.g., the outer null-check in DCL) after the first line, before `loadFromDisk()` runs on the second line. Report this as the publish-before-init-complete hazard in addition to the missing-`volatile` hazard.
**Symptom:** Counter incremented as `x = x + 1` from multiple coroutines loses updates; value read before `await` used as if unchanged after; producer sends after consumer cancelled; init function assumed complete before first use without a barrier.
**Common in:** JavaScript (Promise races, missing `await`), Python (asyncio task interleaving), Go (concurrent map access, goroutine leaks), Java (visibility without `volatile`/synchronized), Rust (`unsafe` blocks, `Mutex` poisoning).

---

## L8 — Resource Lifecycle Hazard
A resource (file handle, DB connection, lock, transaction, subscription, buffer, process, listener) has a broken acquire/use/release lifecycle: missing release, double release, wrong-order release, or ownership transferred without updating the release plan. Distinct from L5 — L8 covers the full pairing discipline including double-release and ownership transfer.
**Detect:** (1) List every resource the code acquires. (2) Identify the matching release and when it must run (always / on success only / exactly once). (3) Trace every exit path; verify release runs the correct number of times. (4) Check ownership transfer: if resource is returned/stored/passed elsewhere, verify the new owner releases it.
**Symptom:** Connection released only on success path; transaction neither committed nor rolled back on exception; subscription registered in mount but unsubscribe references stale handle.
**Exception-path disambiguation (L8 vs L6):** If a callee throws mid-processing and the exception bypasses resource cleanup (`fclose`, socket close, DB connection return), the primary finding is **L8** — the issue is the broken acquire/release pairing. Classify as **L6** only when the callee's exception behavior differs from what the caller assumed (the caller's contract assumption is wrong). Both can coexist; if so, lead with L8.
**Go `defer` guarantee (no-bug pattern):** `defer mu.Unlock()` (or `defer f.Close()`) placed immediately after the acquire — not inside any conditional branch and not after any early return — guarantees release on ALL function exit paths. Do NOT flag this as L8. L8 applies only when the release is absent entirely, or `defer` is placed inside a conditional branch that may not execute.
**Common in:** All languages. Python (`with` not used), JavaScript (listeners on long-lived DOM), Java (try-with-resources omitted in chain), Go (no `defer` for release, or `defer` placed inside a conditional branch that may not execute), C/C++ (`free`/`delete` across function boundaries).

---

## L9 — Time / Locale Hazard
Code makes implicit assumptions about time zones, calendars, locale-dependent ordering, character encodings, or numeric locale conventions that hold on the developer's machine but break elsewhere.
**Detect:** (1) Every datetime: trace naive vs timezone-aware at every hop — naive↔aware comparison/arithmetic is L9. (2) Datetime arithmetic: can a DST transition fall inside the interval? Wall vs monotonic clock? (3) String comparison/ordering: locale-dependent? (4) Encoding conversion: explicit or guessed? Round-trip preserving? (5) Numeric parse/format: `.` vs `,` decimal separator?
**Symptom:** `new Date('2025-03-09T02:30:00')` in `America/Los_Angeles` lands in a non-existent hour; `datetime.now()` (naive) compared with timezone-aware DB value raises `TypeError`; `"i".upper() == "I"` fails in Turkish locale.
**Common in:** Python (`datetime` naive vs aware), JavaScript (`Date` always wall-time), Java (`java.util.Date` vs `java.time`), Go (`time.Time` Location), SQL (`TIMESTAMP` vs `TIMESTAMP WITH TIME ZONE`).

---

## Custom Risk Codes (Cx)
Projects define custom codes in `.logic-lens.yaml` using `C1`, `C2`, etc. Treat with the same Premises→Trace→Divergence→Trigger→Remedy discipline as built-ins. Appear in findings as `[C1]`, `[C2]`, etc.

---

## Quick Disambiguation Table

| If the bug involves | Use | Common mistake to avoid |
|---------------------|-----|------------------------|
| more than one execution context to manifest | **L7** | ❌ L4 (L4 is single-context only) |
| lock-acquisition order differs between two functions, deadlock requires concurrent goroutines/threads | **L7** | ❌ L4, ❌ L6 |
| resource lifecycle imbalance (missing/double release, ownership transfer) | **L8** | ❌ L5, ❌ L6 |
| control-flow exit skipping required non-lifecycle code in a single sequential path (audit log, metric, notification) | **L5** | ❌ L2 (skipping a side-effect is a control-flow escape, not a type issue) |
| modifying a collection during `for`-loop iteration (elements skipped or crash) | **L4** | ❌ L3 (this is a mutation hazard, not a boundary blindspot) |
| aliased references causing unexpected sharing in single-context code | **L4** | ❌ L7 (no concurrent context needed) |
| function mutates its argument AND returns the same reference (dual-contract footgun) | **L4** | ❌ L3 |
| TypeScript `as` / Java unchecked cast bypassing runtime type safety | **L2** | ❌ L4 (no mutation involved — the issue is a type-system gap) |
| implicit type coercion at operator level (`+`/`-`/`*`/`==` string↔number) | **L2** | ❌ L6 (operators are not callees — the issue is a type contract gap at the language level) |
| `.get()` / `.value()` on Optional/Maybe without presence check → throws | **L6** | ❌ L1 (no name shadowing — the issue is a callee-contract violation) |
| timezone, DST, locale-dependent parsing/sorting, or encoding to trigger | **L9** | ❌ L6, ❌ L2, ❌ L3 |
| data type lacking tz/locale metadata (`TIMESTAMP` vs `TIMESTAMPTZ`, naive datetime) | **L9** | ❌ L6 (the root cause is information lost at data-type choice, not callee behavior) |
| name resolution to a different definition than expected (constant lookup, module shadowing, import aliasing) | **L1** | ❌ L3 (shadowing is about names, not boundaries) |
| variable scoping: `const`/`let` in constructor not visible to methods, block-scoped variable hiding outer | **L1** | ❌ L4 (no mutable state mutation — the issue is name/scope resolution) |
| callee behavior under specific inputs not matching caller's assumption | **L6** | |
| file/connection/handle not released on exception path | **L8** | ❌ L6 (the issue is a broken acquire/release lifecycle) |
| error code / exit status suppressed (shell or-true, empty `catch`, bare `except`, missing `set -e`) | **L5** | ❌ L7 (single-context error suppression is control flow escape, not concurrency) |
| lock/mutex acquire-release imbalance under concurrency | **L7 + L8** jointly | |
| Go `defer release` placed before any conditional — guarantees all paths covered | **no-bug** | |
| two independent non-atomic flags jointly encoding one logical state, read across threads | **L7** (split-state flag race) | ❌ L3 |
| post-constructor initialization called on published reference before completion | **L7** (publish-before-init) | |

--- RESOURCE skills/_shared/report-template.md ---
# Logic-Lens — Report Template (Single Source)

All skills render output by following this template, applying the language rule from `common.md` §1 and the mode-specific header from `common.md` §5.

---

## English template

```
# Logic-Lens [Mode Name]

**Mode:** [Logic Review / Execution Explain / Semantic Diff / Fault Locate / Logic Health / Logic Fix All]
**Scope:** [files, functions, or diff under analysis]
[<mode-specific header field — see common.md §5>]

> [One-sentence verdict on overall logic.]

---

## Findings

### 🔴 Critical
**[L-code] — [Short descriptive title]**
Premises:      [what the code assumes]
Trace:         [step-by-step execution path, interprocedural where needed; ends with rebuttal check result]
Divergence:    [exact line/expression where the premise breaks; consequence]
Trigger:       [concrete input/state that reproduces the bug — see common.md §2]
Remedy:        [minimal, paste-ready fix — see common.md §10; ends with dry-run result]
Verification:  [✅ Execution-verified — scope / ⚠️ Unverified — reason and limitations]

*Cross-file finding (when the fix spans multiple files):*
  Remedy (caller):  <file A> line N — <edit>
  Remedy (callee):  <file B> line M — <edit>

### 🟡 Warning
[same five-field structure + Trigger required]

### 🟢 Suggestion
[same five-field structure; Trigger optional]

---

## Summary

[2–3 sentences: most important finding, recommended next action, overall trend if reviewing a codebase.]
```

### logic-locate body override

`logic-locate` uses the same header and Summary placement, but its Findings body is focused on one root cause rather than grouped by severity:

```
## Findings

### Primary Fault
**[L-code] — [Short descriptive title]**
Premises:      [what the failing path assumes]
Trace:         [backward trace from symptom, then forward confirmation]
Divergence:    [exact root line/expression where the premise breaks; propagation to symptom]
Trigger:       [concrete failing input/state]
Remedy:        [minimal, paste-ready fix — see common.md §10]

### Contributing Factors
[Optional short bullets. Omit if none.]
```

Do not add Critical / Warning / Suggestion subsections in `logic-locate`; confidence is expressed only by the `Fault Confidence` header field.

### logic-explain body override

`logic-explain` is descriptive, not evaluative. It omits the mode-specific score line and the Findings section:

```
## Summary

### Step-by-Step Trace
[numbered execution trace]

### Non-Obvious Behavior
[name resolution, coercions, side effects, branch exclusions]

### Actual vs. Assumed
What the code actually does: [fact revealed by trace]
What a casual reader might assume: [plausible misreading]
```

If the trace reveals a likely bug, do not create an L-code finding or Remedy in `logic-explain`; provide the partial trace handoff block defined in `logic-explain-guide.md`.

---

## Chinese template (中文版)

When the user writes in Chinese (`common.md` §1 detection):

```
# Logic-Lens [模式名称]

**模式：** [逻辑审查 / 执行解释 / 语义对比 / 故障定位 / 逻辑体检 / 逻辑全修]
**范围：** [所分析的文件、函数或 diff]
[<模式特定字段 — 见 common.md §5>]

> [一句话总评：整体逻辑是否健全 / 是否存在重大缺陷。]

---

## 发现

### 🔴 严重
**[L-code] — [简短标题]**
前提：      [代码所做的假设]
追踪：      [逐步执行路径；涉及跨函数调用时跟进被调方；末尾附反驳检查结果]
偏差：      [前提被破坏的确切位置（行号/表达式）及后果]
触发：      [能复现 bug 的具体输入/状态 — 见 common.md §2]
修复：      [最小、可直接粘贴的修复 — 见 common.md §10；末尾附预演结果]
验证：      [✅ 已执行验证 / ⚠️ 未验证——原因 / 省略（若跳过 Step 8）]

*跨文件发现（修复涉及多个文件时）：*
  修复（调用方）：<文件 A> 第 N 行 — <改动>
  修复（被调方）：<文件 B> 第 M 行 — <改动>

### 🟡 警告
[同样的五字段结构 + 触发必填]

### 🟢 建议
[同样的五字段结构；触发可选]

---

## 总结

[2-3 句：最关键发现、推荐的下一步、若是代码库审阅则给出整体趋势。]
```

### logic-locate 正文覆盖

`logic-locate` 使用同样的头部和总结位置，但“发现”正文只聚焦一个根因，不按严重级别分组：

```
## 发现

### 主要故障
**[L-code] — [简短标题]**
前提：      [失败路径所做的假设]
追踪：      [从症状反向追踪，再正向确认]
偏差：      [前提被破坏的根因位置（行号/表达式）及其如何传导到症状]
触发：      [具体失败输入/状态]
修复：      [最小、可直接粘贴的修复 — 见 common.md §10]

### 促成因素
[可选短列表；没有则省略。]
```

`logic-locate` 不要添加“严重 / 警告 / 建议”小节；置信度只由头部的 `故障置信度` 字段表达。

### logic-explain 正文覆盖

`logic-explain` 是描述性模式，不做评价。它省略模式特定评分行，也省略“发现”小节：

```
## 总结

### 逐步追踪
[编号执行追踪]

### 非显然行为
[名称解析、隐式转换、副作用、未进入的分支]

### 实际行为 vs. 常见误解
代码实际执行的是：[追踪揭示的事实]
一般读者可能误以为：[可能的误读]
```

如果追踪揭示了疑似 bug，不要在 `logic-explain` 中创建 L-code 发现或修复；按 `logic-explain-guide.md` 定义的部分追踪移交块输出。

---

## Rules

1. **Language consistency.** All headers, field labels, and narrative use one language end-to-end per `common.md` §1. Never use English headers (`# Findings`) in a Chinese response.
2. **Five-field discipline.** Every evaluative finding must have all five fields (Premises/Trace/Divergence/Trigger/Remedy). Trigger is required for Critical and Warning; optional for Suggestion. `logic-explain` produces no evaluative findings. If Trace is incomplete, drop or downgrade to Suggestion with "manual verification needed". No prose findings.
3. **Severity markers.** Use `🔴`/`🟡`/`🟢`. In plain-terminal mode substitute `[CRITICAL]`/`[WARNING]`/`[SUGGESTION]`.
4. **Skill-specific extensions** (Module Breakdown, Fix Log, Iteration History, etc.) appear **after** Summary, never between Findings and Summary.
5. **No findings = valid.** Empty Findings + max score is correct. Do not invent speculative findings.
6. **Verification status.** Applies only to skills that run an Execution Verification Gate — currently `logic-review` (its Step 5) and `logic-fix-all` (via Phase 3). For those, every Critical and Warning finding carries a Verification field: `✅ Execution-verified` only for faithful executed reproduction, or `⚠️ Unverified — reason` (中文 `⚠️ 未验证——原因`) when execution is blocked, inconclusive, or unsupported by the environment. A non-reproducing experiment alone is not disproof. Suggestions may omit it. Skills without that gate (`logic-health`, `logic-locate`, `logic-diff`, `logic-explain`) omit the field entirely — never synthesize a verification claim that no execution backs.

---

## Mode-specific header — quick reference

| Skill | Header line directly under `**Scope:**` |
|-------|----------------------------------------|
| logic-review | `**Logic Score:** XX/100` |
| logic-health | `**Logic Score:** XX/100` (weighted) + `## Module Breakdown` |
| logic-explain | _(omitted — descriptive, no score)_ |
| logic-locate | `**Fault Confidence:** High / Medium / Low` |
| logic-diff | `**Verdict:** ✅ / ⚠️ / ❌ <equivalence verdict>` |
| logic-fix-all | `**Logic Score (before):** XX/100` + `**Logic Score (after):** YY/100` + `**Findings fixed:** N` + `**Findings unresolved:** M` |
