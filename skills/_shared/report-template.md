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

### 🟡 Warning
[same four-field structure]

### 🟢 Suggestion
[same four-field structure]

---

## Summary

[2–3 sentences: most important finding, recommended next action, overall trend if reviewing a codebase.]
```

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

### 🟡 警告
[同样的四字段结构]

### 🟢 建议
[同样的四字段结构]

---

## 总结

[2-3 句：最关键发现、推荐的下一步、若是代码库审阅则给出整体趋势。]
```

---

## Rules

1. **Language consistency.** All headers, field labels, and narrative use one language end-to-end per `common.md` §1. Never use English headers (`# Findings`) in a Chinese response.
2. **Four-field discipline.** Every finding must have all four fields (Premises/Trace/Divergence/Remedy). If Trace is incomplete, drop or downgrade to Suggestion with "manual verification needed". No prose findings.
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
| logic-fix-all | `**Logic Score (before):** XX` + `**Logic Score (after):** YY` + `**Findings fixed:** N` + `**Findings unresolved:** M` |
