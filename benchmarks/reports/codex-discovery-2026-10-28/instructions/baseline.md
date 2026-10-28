
--- RESOURCE skills/logic-review/SKILL.md ---
---
name: logic-review
description: >
  Find logic bugs in a single file or function via semi-formal execution
  tracing (Premises → Trace → Divergence → Trigger → Remedy). Trigger when a user
  shares code and suspects something is wrong without naming a concrete
  failure — phrases like "review this", "does this look right", "check
  this function", "audit this code", "tests pass but prod fails".
  SCOPE HARD RULE: one file or one function only. For a directory or
  whole module use logic-health; for a confirmed failure (stack trace,
  failing test, specific wrong value) use logic-locate; for two versions
  use logic-diff; for repo-wide autonomous fixing use logic-fix-all.
  Do NOT trigger for: style/formatting, security scanning, performance,
  test generation, architecture or design questions.
---

# Logic-Lens — Logic Review

## Output Skeleton Contract

The downstream grader (`scripts/grade-iteration.py`) and other Logic-Lens skills consume this report by substring-matching literal tokens defined in `../_shared/common.md` §1 (header map), §2 (mandatory field labels + Logic Score), and `../_shared/report-template.md` (skeleton). Paraphrasing those tokens — even with a synonym that reads fine to a human — breaks the contract regardless of analysis quality.

**Language selects the token set, not the structure.** The two templates below are the same contract in two languages. Emitting English labels into a Chinese report is as much a contract breach as paraphrasing them — it violates `common.md` §1 (HIGHEST PRIORITY) and fails grading identically. Detect the user's language first, then fill the skeleton with that language's column from the §1 header map.

**Three failure modes observed in benchmark that deserve specific callout** beyond the general rule:

- **Synonym substitution for field labels whose substituted form omits the required substring** — replacing `Premises` / `前提` with `前置条件构建` / `前置条件` (eval-201), or `Divergence` / `偏差` with `根因` / `核心缺陷` / `结论` (eval-252). Each substitution reads fine to a human and may even appear as a section heading or table column, but the substituted word does NOT contain the required substring, so grader and cross-skill consumers see the document as missing the field entirely. Use the literal token from `common.md` §1; you can still add a descriptive subtitle alongside it.
- **Demoting a confirmed L-code finding** to `### 附加观察（非 Finding）` / `### Additional observation` — if Premises→Trace→Divergence holds, the finding belongs inside `## Findings` (中文 `## 发现`) with the five literal fields, even at Suggestion severity. This was a recurring cause of eval-279 (quicksort L4) failing on Sonnet runs.
- **Omitting `Divergence:` / `偏差：` field entirely** — the single most frequent failure mode. Many outputs correctly analyze the bug but write the divergence as prose, in a table cell, or under headings like `根因`, `故障点`, `核心问题`, `缺陷`. The `Divergence:` field is the specific label for "the point where actual behavior diverges from the premise." It is NOT optional and has no acceptable synonym. For no-bug findings use `Divergence: None — [why the premise holds]` (中文 `偏差：无——[原因]`).

**Correctly formatted finding — use as template:**

```
### 🔴 Critical
**[L4] — Mutation during iteration skips elements**
Premises: `users` is `list[User]` passed by reference; `list.remove()` shifts subsequent elements left; the `for` iterator advances by index.
Trace: [1] index=0, user is inactive → `remove()` shifts list. [2] Iterator advances to index 1, which now holds the element originally at index 2 — the original index-1 element is skipped. Rebuttal check: PASSED — no defense found.
Divergence: `remove_inactive([inactive₁, inactive₂, active])` returns `[inactive₂, active]` (2 elements) instead of `[active]` (1 element) — the second inactive user is never visited.
Trigger: `remove_inactive([User(False), User(False), User(True)])` → expected 1, actual 2.
Remedy: Replace loop body with `return [u for u in users if u.is_active]`. Dry-run: ✅ divergence eliminated.
```

Each finding block MUST contain all five literal labels (`Premises:` / `Trace:` / `Divergence:` / `Trigger:` / `Remedy:` or `前提：` / `追踪：` / `偏差：` / `触发：` / `修复：`) as line-starting prefixes. Section headers (`### Premises`, `## Execution Trace`) do NOT satisfy this requirement — the labels must appear inside the finding block.

**No-bug case**: emit `## Findings` (中文 `## 发现`) with a finding block that uses all five field labels, with `Divergence: None — [why the premise holds]`. This format is REQUIRED — it satisfies both grading and auditing.

The example below is deliberately shown **in Chinese** to make the localized token set concrete — it is the exact same skeleton as the English template above. For an English-language review, use the English labels; the structure does not change.

```
### ✅ 无 Bug
**[无 Bug] — defer 保证所有退出路径都会解锁**
前提：`mu.Lock()` 在第 12 行获取；`defer mu.Unlock()` 位于第 13 行（在任何条件分支或提前返回之前）。
追踪：[1] `defer` 在 `Lock()` 之后立即注册。[2] Go 规范保证 deferred 调用在所有函数退出路径上执行（return、panic、提前返回）。[3] Lock 与 defer 注册之间无条件分支。
偏差：无——`defer mu.Unlock()` 无条件置于加锁之后，保证每条退出路径都会释放，不存在锁泄漏。
触发：N/A（无 bug 可复现）。
修复：N/A（代码本身正确）。
```

## Setup

Use lazy loading per `../_shared/common.md` §13:
1. Read `../_shared/common.md` only for language, Iron Law, Logic Score, scope management, Remedy discipline, config fields, and loading budget.
2. Read only the relevant step in `logic-review-guide.md` as you reach it.
3. Load `../_shared/logic-risks.md`, `../_shared/semiformal-guide.md`, `../_shared/semiformal-checklist.md`, and `../_shared/report-template.md` on demand when the current step needs them.

## Process

**Step 0. Language + scope routing.** Detect the user's language per `common.md` §1; every label and header below must be in that language. Confirm scope is one file or one function — if the user points at a directory, switch to logic-health; if they describe a confirmed failure, switch to logic-locate; if two versions, logic-diff.

**Step 1. Establish claimed behavior + review entry points** (guide Step 1) — write one sentence describing what the code is supposed to do, then select the concrete entry function(s) that will be traced. If a file exceeds `common.md` §9 limits, state the selected subset and why.

**Step 2. Build premises** (guide Step 2) — per the Premises Construction Checklist in `semiformal-checklist.md`; include caller/callee contracts when the reviewed function depends on another local function.

**Step 3. Build the risk path ledger** (guide Step 3) — enumerate candidate bug paths across L1–L9 before writing findings. Tag each retained path as Class A (self-evident) or Class B (invariant-dependent). Do not stop after the happy path. Read `logic-risks.md` Quick Disambiguation Table before assigning any L-code — common misclassifications are catalogued there. **L4 priority check:** does any function mutate its input AND return the same object? **L7 priority check:** is shared state accessed across `await`/yield/thread boundaries without explicit synchronization? **L4 vs L7 disambiguation:** any state access involving more than one execution context (thread / goroutine / `await` / yield) is **L7**, never L4 — including single-threaded asyncio where coroutines interleave at `await`. L4 is for single-context aliasing only (mutable defaults, in-place mutation footgun, mutation-during-iteration). L4 requires an actual **mutation of shared/aliased state** as the root cause — variable scoping issues (const/let visibility, constructor scope) are L1, and query-pattern inefficiencies (N+1) are L3.

**L1 vs L6 disambiguation:** if the root cause is a name/identifier resolving to a different definition than the developer expected (import shadowing, module constant lookup, prototype chain, constructor-scoped `const`/`let` not visible to methods), it is **L1** even when the symptom is a missing-method error or wrong return value — L6 applies only when the name resolves correctly but the callee's behavior differs from what the caller assumed.

**L2 vs L6 disambiguation:** if the root cause is an implicit type coercion at the **operator level** (`+`/`-`/`*`/`==` triggering string↔number conversion, or `as`/cast bypassing runtime type checks), it is **L2** — L6 requires calling a specific callee whose behavior differs from the caller's assumption. Operators are not callees.

**L5 vs L7 disambiguation:** if an error code, exit status, or exception is suppressed by a **single-context construct** (`|| true`, empty `catch`, missing `set -e`, bare `except`), it is **L5** (control flow escape) — L7 requires multiple execution contexts. Error propagation failure within one sequential script/function is L5.

**L9 check:** if the bug's root cause is timezone/locale/encoding information **lost at the data-type level** (e.g., `TIMESTAMP` vs `TIMESTAMPTZ`, naive vs aware datetime, locale-dependent string sort), it is **L9** — not L6 even if it looks like "callee behavior differs from expectation", not L2, not L8.

**Step 4. Deep-trace selected paths** (guide Step 4) — trace the normal path plus the highest-risk edge paths; resolve every name, state every type, cross callee boundaries, and stop each trace at either a confirmed divergence or a confirmed safe post-condition. **Java/C++ DCL rule:** for double-checked locking patterns, MUST trace both faces: (a) missing `volatile` / memory barrier (visibility hazard) AND (b) `instance = new X(); instance.init();` as two non-atomic statements — lock-free readers can see non-null `instance` before `init()` completes (publish-before-init hazard). Report both; omitting either is an incomplete analysis.

**Step 5. Identify divergences** (guide Step 5) — classify each by L1–L9; assign severity; apply the reachability gate (Class A reports directly; Class B requires a probe — enforcement found → drop candidate, not found → assigned severity, partial → cap at Warning with `manual verification recommended`). Apply the correctness parity principle for no-bug scenarios. **No-bug output discipline:** when zero divergences remain, still emit the full template skeleton — Mode line, Scope, `**Logic Score:** 100/100`, `## Findings` (中文 `## 发现`) followed by a finding block that uses `Divergence: None — [why the premise holds]` (中文 `偏差：无——[原因]`) with all five field labels present. This makes the reasoning auditable and satisfies the format contract. If analysis actively disproves a suspected bug, explain the defense in the `Trace:` field (e.g., "Go `defer mu.Unlock()` guarantees release on all exit paths including early return"). Do not collapse the verdict into free-form prose or omit the structured fields; downstream grading requires the five-field format even for no-bug conclusions.

**Step 5.5. Adversarial Red Team** (guide Step 5.5) — for each candidate finding, attempt to disprove it by answering three rebuttal questions (premise rebuttal, path rebuttal, consequence rebuttal). Withdraw findings with confirmed defenses; downgrade findings with partial defenses to Suggestion. **Design-intent gate:** before reporting an L3 Boundary Blindspot, ask "Does the code explicitly return an error / rejection at this boundary rather than attempting to continue past it?" If yes (e.g., `errors.New("cache full")` at `maxSize`, `429 Too Many Requests`, buffer-full rejection), withdraw — these are correct boundary enforcement, not blindspots. L3 applies only when code *attempts* to operate past the boundary and silently fails (wrong result, crash, infinite loop). Note: a `panic` at a boundary is a crash, not a designed error return, and remains a potential L3.

**Step 6. Apply Iron Law — Five-Field Discipline** (guide Step 6) — confirm all findings have Premises → Trace → Divergence complete; then write Trigger (concrete reproducing input, required for Critical/Warning) and Remedy (paste-ready per `common.md` §10). **Each finding MUST use these literal field labels** — English `Premises:` / `Trace:` / `Divergence:` / `Trigger:` / `Remedy:`, or Chinese `前提：` / `追踪：` / `偏差：` / `触发：` / `修复：`. Do not paraphrase. Headers like `Execution Path`, `Issue Found`, `Core Defect`, `执行路径`, `发现的逻辑隐患`, `核心缺陷` are unacceptable substitutes — they fail downstream grading and break the report contract that other Logic-Lens skills consume. **Multi-finding discipline:** When there are multiple findings, each finding block inside `## Findings` (中文 `## 发现`) must include all five literal field labels — `Premises:` / `Trace:` / `Divergence:` / `Trigger:` / `Remedy:` (or their Chinese equivalents) — with content specific to that finding. Any shared background context may appear as a preamble section, but it does NOT substitute for the per-finding fields. A finding that omits `Divergence:` (or any other required field) breaks the contract even if `Premises:` or `Trace:` appear elsewhere in the report.

**Step 6.5. Remedy Dry-Run** (guide Step 6.5) — mentally re-trace the Trigger input through the fixed code to confirm: divergence eliminated, no regression introduced, happy path preserved.

**Step 7. Score and output** (guide Step 7) — **run Step 8 first whenever a runtime is available**; it withdraws false positives and so changes the score. Compute Logic Score per `common.md` §6 over the findings that survive verification, and emit it as the literal line `**Logic Score:** XX/100` (中文 `**逻辑评分：** XX/100`) directly under the Scope line (`**Scope:**` / 中文 `**范围：**`) — this exact token (not "Score: XX", not "Quality: XX") is required for both grader recognition and cross-skill consumption. Then render the rest of the Report Template with localized headers.

**Step 8. Execution Verification Gate** (guide Step 8) — **required for every Critical and Warning finding whenever a runtime for the target language is available**; it is the only step that can contradict the analysis, so a confident trace is never a reason to skip it. Generate a minimal reproducer from the Trigger field, execute it against the original code, then apply the Remedy and re-execute. Withdraw findings whose reproducer passes on the original code — they are false positives. Mark survivors `✅ Execution-verified`; when no runtime exists mark `⚠️ Unverified — no runtime available` (中文 `⚠️ 未验证——无可用运行时`).

**Mode line in report:** `Logic Review` (Chinese: `逻辑审查`).

--- RESOURCE skills/logic-review/logic-review-guide.md ---
# Logic Review — Step-by-Step Guide

## Step 1: Establish Claimed Behavior

Read any comments, docstrings, test names, or commit message. Write one sentence:
"This code is supposed to [verb] [what], given [inputs], producing [output/side effect]."

This sentence is the reference point: anything the trace contradicts is a candidate finding. If no documentation exists, infer intent from the function signature, caller usage, tests, and names. Do not emit a documentation-gap finding unless the missing contract directly prevents a logic conclusion.

Select the review entry point before tracing:
- Single function input: trace that function and any local callees reached from it.
- Single file input: identify public/exported functions, functions changed recently, and functions touching external state. If the file exceeds `common.md` §9 limits, choose at most 3 high-risk functions and state the uncovered functions in Scope.
- Pasted snippet without line numbers: anchor trace steps to function names and expressions; do not invent line numbers.

## Step 2: Build Premises

Run through every applicable item in **`../_shared/semiformal-checklist.md`** — Name Resolution, Type Contracts, State Preconditions, Control Flow Assumptions. Read its "What is NOT a Premise" section before writing.

Write premises **before** starting the trace.

**Good premise example:** "`users` is a `list[User]` passed by reference; `users.remove(x)` mutates the list in place; the `for user in users` iterator does not re-index after a mutation, so removing element at position `i` causes element at original position `i+1` to be skipped."

For logic-review, premises must cover both sides of each important boundary:
- **Caller contract:** What values can enter this function from real call sites? If call sites are unavailable, mark this premise as partial.
- **Callee contract:** What can each local callee return, raise, mutate, or skip? Trace into local callees when the finding depends on their behavior.
- **State lifetime:** Which state survives across calls, iterations, awaits, callbacks, or retries?
- **Observable consequence:** What output, mutation, exception, persisted value, or externally visible side effect would make the bug real?

## Step 3: Build the Risk Path Ledger

Before writing any finding, enumerate candidate paths. This prevents the review from anchoring on the happy path.

Create a short internal ledger with one row per path:

```
[risk code] [entry point] [input/state condition] [branch/callee/resource involved] [why this path is reachable or not] [Class A | Class B]
```

Tag each **retained** candidate with a **Reachability Class** (discarded candidates need no tag):
- **Class A (Self-evident):** triggering condition is visible in local code — e.g., dereference after explicit nil check, index beyond bounds, unchecked type assertion, resource with no release on a visible exit path.
- **Class B (Invariant-dependent):** triggering condition requires an implicit external assumption to be false — e.g., "all groups always contain at least one alias" or "callers never pass nil here." Requires a reachability probe in Step 5 before reporting.

Example ledger rows:
```
L3  parseCSV  empty input  len(rows)==0 guard absent      always reachable from callers  Class A
L5  filterPkgVulns  all groups ignored  len(newGroups)==0 guard  depends on "vuln always in ≥1 group" invariant  Class B
```

Minimum ledger coverage:
- **Normal path:** the common valid input path.
- **Boundary paths (L3):** empty/null/zero, single item, first/last item, max/min, divide/slice/index boundaries.
- **Type/name paths (L1/L2):** shadowed identifiers, dynamic dispatch, coercions, nullable values, deserialized input.
- **Callee paths (L6):** local callees returning null/None/undefined, raising, mutating arguments, or returning a different shape.
- **Control/resource paths (L5/L8):** every early return, throw/raise, catch/except, break/continue after acquisition or required post-condition. **L5 exhaustive enumeration:** when a required side-effect (audit log, metric, notification, state update) must run on every exit, verify EVERY exit path independently — `return`, explicit `raise`/`throw`, implicit raises from callees, `break`, `continue`. Name each skipped path separately in the finding; a finding that identifies only the first skipped path is incomplete. Example: "Two paths skip `audit_log.record`: (1) `return _unauthorized()` at line 3, (2) `raise BadRequest` at line 5." Note: if the skipped operation is a resource release or rollback, reclassify as L8 and apply the same exhaustive path logic there.
- **State/concurrency paths (L4/L7):** mutation during iteration, shared mutable defaults, aliases, closures, await/callback/task boundaries. For L4 also check: does the function mutate its argument AND return it (aliased-return dual contract)? For L7: does the hazard require two concurrent execution contexts — if yes it is L7, not L4 (e.g. lock-order inversion between goroutines is L7 even though it involves mutation).
  - **L4 aliased-return trap (high priority):** When a function BOTH mutates its input in-place AND returns the same object, this is an L4 finding — not a style issue. The caller may write `result = func(original)` and assume `original` is unchanged. Trace: (a) confirm mutation is in-place (e.g., `list.sort()`, `del arr[i]`, `arr[i], arr[j] = arr[j], arr[i]`); (b) confirm the function returns the SAME object (not a copy); (c) construct a Trigger showing `original` is unexpectedly modified. This is L4, not L3 or L7.
  - **L7 async interleaving (critical for asyncio/coroutines):** When shared mutable state is accessed across `await`/`yield` boundaries, the bug is L7 even if no threads are involved — asyncio coroutines interleave on a single thread via the event loop. Key indicator: a check-then-act pattern with an `await` between the check and the act. Do NOT classify asyncio interleaving as L4.
  - **L7 memory model hazards (Java/C++/Go):** For double-checked locking, volatile/atomic, happens-before: always check BOTH (a) the visibility hazard (missing volatile/atomic) AND (b) the initialization-before-publish ordering (is the object fully constructed before other threads can see it?). Two-step trace: step 1 = reordering/visibility, step 2 = consequence of observing partially-constructed object.
- **Time/locale paths (L9):** naive/aware datetime, DST, locale-sensitive parse/sort/format, implicit encoding.

Discard a candidate only after stating why it is unreachable or irrelevant. Deep-trace the normal path and the highest-risk reachable candidates first.

## Step 4: Deep-Trace Selected Execution Paths

Trace the most common execution path step by step:

```
1. [line N] [expression evaluated] → [result]
2. `name` resolves to [full qualified definition] at [file:line]
3. Arguments passed: arg1 = [value/type], arg2 = [value/type]
4. Inside [callee] at [line]: [key operation] → [result]
5. Returns [value/type] to caller at [line]
6. [line N+k] Result used as [role]
```

**Minimum thresholds** (per `../_shared/semiformal-guide.md`): ≥ 3 substantive steps and ≥ 2 location anchors. Below either threshold, downgrade the finding to Suggestion with `manual verification recommended`.

**Good trace example:**
```
1. [service.py:6] `result = charge(order)` — `charge` resolves to `payments.gateway.charge` (imported at line 1).
2. [gateway.py:3] Inside `charge`: condition `order.amount == 0` evaluates to True for this input.
3. [gateway.py:4] Returns `None` (early return; no dict constructed).
4. [service.py:7] `result['transaction_id']` evaluates `None['transaction_id']` → raises `TypeError`.
```

Then trace each selected risk path separately:

- Start with concrete input/state values, not abstract phrases like "bad input".
- Follow value origin → branch decision → callee behavior → state mutation/output.
- For loops, trace zero iterations, one iteration, and the iteration where the invariant changes.
- For async/concurrent code, name the exact boundary where another execution context can observe or mutate state.
- For **L4 aliased-return mutation**: trace what happens when the caller holds a reference to the input BEFORE the call, calls the function, then uses the original reference. Show that the original was mutated. Example trace:
  ```
  1. caller: original = [3, 1, 2]
  2. caller: result = quicksort(original)
  3. inside quicksort: arr is the SAME object as original (passed by reference)
  4. quicksort mutates arr in-place via swaps
  5. quicksort returns arr — same object
  6. caller: original is now [1, 2, 3] — mutated without caller's knowledge
  7. caller: result is original — they are the same object (result is original == True)
  ```
- For **L7 memory model**: trace two threads/goroutines/coroutines with numbered interleaving steps:
  ```
  T1-step1: thread A checks instance == null → true
  T1-step2: thread A enters synchronized, creates object
  T1-step3: JIT reorders: reference published BEFORE constructor completes
  T2-step1: thread B checks instance == null → false (sees non-null)
  T2-step2: thread B returns instance — but object.data is still null
  ```
- Stop at a confirmed safe post-condition if the candidate is not a bug; do not turn safe paths into Suggestions.

## Step 5: Identify Divergences

For each point where a premise is violated, write a finding using the five-field format (Premises → Trace → Divergence → Trigger → Remedy) with the L-code that best describes the cause.

**Severity:**
- 🔴 Critical: causes exception, data corruption, incorrect output, or security-relevant behavior in a reachable path.
- 🟡 Warning: reachable but only under uncommon inputs or a specific sequence of prior operations.
- 🟢 Suggestion: requires unusual/currently-impossible conditions, consequence is minor, or one premise is partial.

For Class A candidates: if the trace does not conclusively confirm consequence (reachability is already self-evident for Class A), downgrade to Suggestion with `manual verification recommended` or omit it. A plausible code smell without a concrete execution path is not a logic-review finding.

**Reachability gate — apply before writing any finding:**

- **Class A:** report at the assigned severity (local code is sufficient evidence).
- **Class B:** run a reachability probe first:
  1. Search for invariant enforcement — constructor, validator, schema definition, or call sites visible in current scope.
  2. Enforcement found and airtight (no code path bypasses it) → **drop the candidate; do not write a finding.** Optionally record in the report Summary: "Invariant enforced at [location] — no current bug; revisit if callers or schema change."
  3. No enforcement found → report at the assigned severity.
  4. Enforcement partial or outside current scope → report at the assigned severity, capped at 🟡 Warning, with `manual verification recommended`.

Record the probe result in the finding's Trace (not Premises) so the reader can verify the class assignment without violating the Premises checklist.

Deduplicate by root cause: if one bad callee contract creates several caller symptoms, report one L6 finding at the callee/caller contract boundary and list representative call sites in the Trace or Remedy.

**No-bug discipline:** When the user's question is framed as "does X cause bug Y?" and the trace conclusively shows Y does NOT apply (e.g., `defer` in Go runs on all exit paths so there is no lock leak), write a finding concluding **NO logic error** for Y with Premises → Trace → Divergence showing why. Do not fabricate unrelated findings to appear thorough — that undermines precision and triggers false positives. However, if the Risk Path Ledger from Step 3 surfaced a separate, concrete, reachable bug with a complete trace, report it as an independent finding; a no-bug verdict on Y does not suppress genuine findings on other risks. If the ledger produced no other findings, stop.

**Correctness parity principle:** Correctly concluding "no bug" is equally valuable as correctly finding a bug. A Logic Score 100 report with "no confirmed logic errors" is a professional, high-value output — not a failure. Do not lower evidence standards to produce findings. If every path in the Risk Path Ledger terminates at a confirmed safe post-condition, output Score 100 immediately. Record each path's safe-termination reason (≥1 sentence) but do NOT wrap safe paths as Suggestion findings.

## Step 5.5: Adversarial Red Team

For each candidate finding that survived Step 5, attempt to **disprove it** from the defender's perspective before writing the Remedy. This step reduces false positives by forcing an adversarial check.

**Three Rebuttal Questions** (answer each explicitly — do not skip):

1. **Premise rebuttal:** Does any of my premises rest on an unverified assumption? Could callers guarantee the premise through schema validation, type checking, wrapper functions, middleware, or a constructor that enforces the invariant? Search the current scope for evidence.

2. **Path rebuttal:** Is the trigger path truly reachable in production? Could an upstream guard, configuration flag, middleware filter, type system constraint, or framework convention prevent the input from ever reaching this code path?

3. **Consequence rebuttal:** Even if the divergence exists, is the consequence truly harmful? Could a downstream defense (catch/except, fallback value, retry logic, idempotency guard) neutralize the impact?

**Ruling:**
- Any question finds **conclusive evidence** (a defense locatable in code) → **withdraw the finding**. Record in Summary: "Candidate [L-code] at [location] withdrawn — defense confirmed at [defense location]."
- Any question finds **partial evidence** (indirect defense, uncertain coverage) → **downgrade to Suggestion** with `manual verification recommended`.
- All three questions find **no rebuttal evidence** → **retain at original severity**.

**Async/concurrency protection clause:** For L7 findings involving async interleaving (asyncio, goroutines, coroutines) or memory model hazards (volatile, happens-before), apply stricter rebuttal thresholds — only withdraw if the defense is an **explicit synchronization primitive** (lock, semaphore, atomic, channel, volatile). Do NOT treat the GIL, event loop single-threading, or "unlikely timing" as a defense. The GIL does not prevent asyncio interleaving; single-threaded event loops DO interleave at await points.

**Recording:** Append the rebuttal conclusion to the Trace field:
- `Rebuttal check: PASSED — no defense mechanism found in scope.`
- `Rebuttal check: DOWNGRADED — partial defense found at [location].`
- `Rebuttal check: WITHDRAWN — confirmed defense at [location].`

(Chinese: `反驳检查：已通过——范围内未发现防御机制。` / `反驳检查：已降级——在 [位置] 发现部分防御。` / `反驳检查：已撤回——在 [位置] 确认防御。`)

## Step 6: Apply Iron Law (Five-Field Discipline)

Premises, Trace, and Divergence must all be complete before writing a **Trigger** or **Remedy**.

Every finding follows five fields in order: **Premises → Trace → Divergence → Trigger → Remedy**.

### Trigger field (required for Critical and Warning; optional for Suggestion)

Provide a **concrete input or state** that triggers the bug. The trigger must be specific enough that a developer can paste it into a REPL or test to reproduce.

**Good trigger example:**
```
Trigger: remove_inactive([User(active=False), User(active=False), User(active=True)])
  Expected: returns [User(active=True)]  (1 element)
  Actual:   returns [User(active=False), User(active=True)]  (2 elements — second inactive user skipped)
```

**Bad trigger (unacceptable):**
```
Trigger: "when passing a list with inactive users"  ← too vague, cannot reproduce
```

**When a concrete trigger is difficult to construct:**
- Bug depends on external state (DB, network): describe the minimal triggering condition + mark `manual verification recommended`.
- Bug involves concurrency/timing: describe the specific thread/coroutine interleaving sequence with numbered steps.
- Completely unable to construct a trigger: **automatically downgrade to Suggestion**.

### Remedy field

**Good remedy example:** "On line 42, replace `format(self.data.year, '04d')` with `builtins.format(self.data.year, '04d')` to avoid dispatching to the module-level `format()` that expects a datetime object."

## Step 6.5: Remedy Dry-Run Verification

After writing the Remedy, mentally re-execute the Trigger input against the **fixed** code to confirm correctness. This prevents remedies that are ineffective or introduce regressions.

**Procedure (3-step minimum):**

1. **Mentally apply** the Remedy to the original code.
2. **Re-trace** the Trigger input through the fixed code (≥3 steps).
3. **Confirm** all three conditions:
   - (a) The original Divergence no longer occurs.
   - (b) No new Divergence is introduced by the fix (check boundary conditions of the fix itself).
   - (c) The happy-path behavior is preserved (the fix does not change correct behavior).

**Outcomes:**
- (a) fails → Remedy is ineffective. Rewrite before emitting.
- (b) fails → Remedy introduces a regression. Record the new risk, narrow the fix scope, and rewrite.
- (c) fails → Remedy is over-scoped. Reduce the fix to the minimal change.

**Recording:** Append to the Remedy field:
```
Dry-run: ✅ Trigger input re-traced through fix — divergence eliminated, no regression, happy path preserved.
```
(Chinese: `预演：✅ 触发输入已在修复代码中重新追踪——偏差已消除，无回归，正常路径行为保持不变。`)

If dry-run reveals a problem, record the issue and the corrected remedy:
```
Dry-run: ⚠️ Initial remedy [description] failed check (b) — [new issue]. Revised remedy applied.
```

## Step 7: Compute Score and Output

**Ordering:** when a runtime is available, complete Step 8 before rendering output — verification withdraws false positives and therefore changes both the finding set and the score. Produce one final report, never a draft that Step 8 then edits.

1. Start at 100. Deduct per confirmed finding (Critical −15, Warning −7, Suggestion −2). Count only findings that survived Step 5.5 and, where it ran, Step 8.
2. Fill in the Report Template from `report-template.md`.
3. Summary: most critical finding, recommended next action, whether the logic is safe to ship.

## Step 8: Execution Verification Gate (Required when a runtime is available)

Apply this step to every **Critical** and **Warning** finding. It is not optional: Steps 1–6 are all reasoning, and reasoning cannot falsify itself — a wrong trace and a right trace feel identical from the inside. Executing a reproducer is the only step in this skill that can return an answer the analysis did not already believe.

**Prerequisite check:** Detect whether the target language runtime is available (e.g., `python3 --version`, `node --version`, `go version`). Only if it is unavailable, skip the step, mark each affected finding `⚠️ Unverified — no runtime available` (中文 `⚠️ 未验证——无可用运行时`), and proceed to output. A confident trace is not a substitute for a runtime and is never a reason to skip.

### 8a. Generate Minimal Reproducer Script

For each finding, generate a self-contained script based on the Trigger field:
- Include the reviewed function (or a minimal standalone version).
- Include the concrete trigger input from the Trigger field.
- Include an assertion: expected behavior vs. actual behavior.
- The script must **FAIL** (assertion error or exception) when the bug is present.

**Safety constraints:**
- The script must contain only pure computation — NO network requests, file writes, database operations, or other side effects.
- If the function depends on external state, create in-memory mocks/stubs.
- Execution timeout: 10 seconds maximum.

### 8b. Run Original Code (Confirm Bug Exists)

Execute the reproducer script against the original code.
- **Script FAILS (assertion error or expected exception):** Bug confirmed. Proceed to 8c.
- **Script PASSES:** Finding is a **false positive**. Withdraw it, remove from report, and adjust Logic Score.
- **Script errors unexpectedly (syntax error, import failure):** Script needs fixing. Retry once with corrected script. If still broken, mark `unverified — reproducer generation failed`.

### 8c. Apply Remedy and Re-run (Confirm Fix Works)

Apply the Remedy to the code in the reproducer script, then re-execute.
- **Script PASSES:** Fix verified. Mark finding as `✅ Execution-verified`.
- **Script still FAILS:** Remedy is ineffective. Revise and retry (up to 3 attempts). After 3 failures, mark `unverified — remedy needs manual review`.
- **Script throws NEW exception:** Remedy introduces regression. Revert, mark `⚠️ Remedy caused regression — manual fix recommended`.

### 8d. Update Report

Add verification status to each finding:

```
Verification: ✅ Execution-verified — reproducer FAIL → applied fix → PASS
Verification: ⚠️ Unverified — [reason]
```

(Chinese: `验证：✅ 已执行验证——复现脚本 FAIL → 应用修复 → PASS` / `验证：⚠️ 未验证——[原因]`)

Findings withdrawn by 8b are removed from `## Findings` (中文 `## 发现`) entirely, so they carry no Verification field. Record them once in Summary instead, matching the Step 5.5 withdrawal convention: "Candidate [L-code] at [location] withdrawn — reproducer passed on original code." (中文 `候选 [L-code]（位于 [位置]）已撤回——复现脚本在原始代码上通过。`)

**Example reproducer (Python, L4 mutation-during-iteration):**

```python
# 最小可复现脚本 — L4: 迭代中修改列表
class User:
    def __init__(self, active):
        self.is_active = active

def remove_inactive(users):
    for user in users:
        if not user.is_active:
            users.remove(user)
    return users

# 触发输入：两个连续的失效用户
users = [User(False), User(False), User(True)]
result = remove_inactive(users)
assert len(result) == 1, f"Expected 1 active user, got {len(result)}"
# 预期：AssertionError（bug 存在）
```

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

Low-confidence findings in logic-review / logic-health are automatically downgraded to Suggestion severity.

---

## 8. When No Bugs Are Found

Report Logic Score 100 (or the mode-specific equivalent) and state:

> "No confirmed logic bugs found. All traced paths behave as specified."

(Chinese: "未发现已确认的逻辑错误；所追踪的全部路径均符合规范。")

Do not invent speculative findings to fill the Findings section. An empty Findings section with a high score is valid and valuable. Minor observations go under Suggestion with a full five-field entry — never as loose prose.

**Correctness parity principle:** correctly concluding "no bug" has the same professional value as correctly finding a bug. Do not lower evidence standards to produce findings.

---

## 9. Scope Management

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

A trace below either threshold is **incomplete**. For review/diff/health, drop the finding or downgrade to **Suggestion** with `manual verification recommended`; do not promote it to Critical or Warning. For locate, downgrade Fault Confidence to **Low** unless the missing anchor/step is supplied by a concrete stack trace, failing assertion, or observed output.

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

Depth limit: stop tracing into callees beyond **4 hops** from the entry point. Beyond 4 hops the premises required to maintain accuracy compound faster than the trace gains certainty. For review/diff/health findings, downgrade any finding that depends on an inference at hop 5 or deeper to **Suggestion** with `manual verification recommended`; for locate, downgrade Fault Confidence according to `common.md` §7.

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
**Detect:** (1) Identify all mutable state touched: local refs passed by reference, object fields, global state, closure captures. (2) Trace every read and write in execution order. (3) Ask: does any read occur after a write that invalidated its assumption? Do any aliases point to the same mutable object? (4) **Aliased-return check:** does the function mutate its input argument AND also return that same reference? If so, callers who write `result = f(x)` discover `x` was also mutated — neither the pure-function contract (`sorted()` returns a new copy) nor the in-place contract (`list.sort()` returns `None`) is satisfied. This dual-contract footgun is L4. Sort/search routines (quicksort, mergesort, in-place reverse) exhibiting it are confirmed L4 findings — primary classification stays L4 even when a secondary risk like recursion depth coexists on the same function.
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
Verification:  [✅ Execution-verified / ⚠️ Unverified — reason / omitted if Step 8 skipped]

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
6. **Verification status.** Applies only to skills that run an Execution Verification Gate — currently `logic-review` (its Step 8) and `logic-fix-all` (via Phase 3). For those, every Critical and Warning finding carries a Verification field: `✅ Execution-verified` normally, or `⚠️ Unverified — no runtime available` (中文 `⚠️ 未验证——无可用运行时`) when no runtime for the target language exists. Suggestions may omit it. Skills without that gate (`logic-health`, `logic-locate`, `logic-diff`, `logic-explain`) omit the field entirely — never synthesize a verification claim that no execution backs.

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
