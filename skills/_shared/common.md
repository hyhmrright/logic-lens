# Logic-Lens — Shared Framework

## 1. Language Hard Constraint (HIGHEST PRIORITY)

**Rule:** Identify the dominant language of the user's most recent message. Treat a message as Chinese if ≥ 50% of its characters are CJK; otherwise English. All response text MUST use that same language — including:

- Every section header (`# Findings`, `## Summary`, and every header listed in the map below)
- Every finding's four field labels (Premises / Trace / Divergence / Remedy)
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

**Stay in native form regardless of user language:** fenced code blocks, identifier names (`format`, `users.remove(...)`), L-codes (`L1`–`L9`, `C1`, `C2`...), file paths, exception class names, operator symbols.

**Violation check:** if the response is Chinese but a header reads `# Findings`, rewrite before returning.

---

## 2. Iron Law

NEVER emit a Remedy before completing Premises → Trace → Divergence for that finding.
EVERY finding follows these four fields in order: **Premises → Trace → Divergence → Remedy**.

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

Floor: 0. Cap at one deduction per unique L-code per scope (do not stack four L1 findings for the same shadow).

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

Do not invent speculative findings to fill the Findings section. An empty Findings section with a high score is valid and valuable. Minor observations go under Suggestion with a full four-field entry — never as loose prose.

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

If the fix requires a design decision the user must make, say so explicitly and list the options instead of giving vague advice.

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
| `custom_risks` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
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
