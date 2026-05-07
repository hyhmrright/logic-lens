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
Premises:   [what the code assumes]
Trace:      [step-by-step execution path, interprocedural where needed]
Divergence: [exact line/expression where the premise breaks; consequence]
Remedy:     [minimal, paste-ready fix — see common.md §10]

*Cross-file finding (when the fix spans multiple files):*
  Remedy (caller):  <file A> line N — <edit>
  Remedy (callee):  <file B> line M — <edit>

### 🟡 Warning
[same four-field structure]

### 🟢 Suggestion
[same four-field structure]

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
Premises:   [what the failing path assumes]
Trace:      [backward trace from symptom, then forward confirmation]
Divergence: [exact root line/expression where the premise breaks; propagation to symptom]
Remedy:     [minimal, paste-ready fix — see common.md §10]

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
前提：   [代码所做的假设]
追踪：   [逐步执行路径；涉及跨函数调用时跟进被调方]
偏差：   [前提被破坏的确切位置（行号/表达式）及后果]
修复：   [最小、可直接粘贴的修复 — 见 common.md §10]

*跨文件发现（修复涉及多个文件时）：*
  修复（调用方）：<文件 A> 第 N 行 — <改动>
  修复（被调方）：<文件 B> 第 M 行 — <改动>

### 🟡 警告
[同样的四字段结构]

### 🟢 建议
[同样的四字段结构]

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
前提：   [失败路径所做的假设]
追踪：   [从症状反向追踪，再正向确认]
偏差：   [前提被破坏的根因位置（行号/表达式）及其如何传导到症状]
修复：   [最小、可直接粘贴的修复 — 见 common.md §10]

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
2. **Four-field discipline.** Every evaluative finding must have all four fields (Premises/Trace/Divergence/Remedy). `logic-explain` produces no evaluative findings. If Trace is incomplete, drop or downgrade to Suggestion with "manual verification needed". No prose findings.
3. **Severity markers.** Use `🔴`/`🟡`/`🟢`. In plain-terminal mode substitute `[CRITICAL]`/`[WARNING]`/`[SUGGESTION]`.
4. **Skill-specific extensions** (Module Breakdown, Fix Log, Iteration History, etc.) appear **after** Summary, never between Findings and Summary.
5. **No findings = valid.** Empty Findings + max score is correct. Do not invent speculative findings.

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
