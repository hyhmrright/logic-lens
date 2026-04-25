# Logic-Lens — Report Template (Single Source)

This is the **single source of truth** for every Logic-Lens skill's report layout. All skills (review / explain / diff / locate / health / fix-all) render their output by following this template, applying the language rule from `common.md` §1 and the mode-specific header field from `common.md` §5.

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
Premises:   [what the code assumes — one or more explicit statements]
Trace:      [step-by-step execution path, interprocedural where needed]
Divergence: [exact line/expression where the premise breaks; what consequence follows]
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

When the user writes in Chinese (`common.md` §1 detection), use this exact form. Replace headers per the §1 localized header map; the finding body becomes:

```
# Logic-Lens [模式名称]

**模式：** [逻辑审查 / 执行解释 / 语义对比 / 故障定位 / 逻辑健康 / 全量修复]
**范围：** [所分析的文件、函数或 diff]
[<模式特定字段 — 见 common.md §5>]

> [一句话总评：整体逻辑是否健全 / 是否存在重大缺陷。]

---

## 发现

### 🔴 严重
**[L-code] — [简短标题]**
前提：   [代码所做的假设 — 一条或多条显式陈述]
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

## Rules (apply to both English and Chinese output)

1. **Language consistency.** No English headers in a Chinese response, and vice versa. The whole report — header, field labels, narrative prose — uses one language end-to-end.
2. **Four-field discipline.** Every finding must have all four fields (Premises / Trace / Divergence / Remedy). If Trace is incomplete, drop the finding or downgrade to Suggestion with an explicit "manual verification needed" note. **No prose findings** — an observation without all four fields is not a finding.
3. **Severity markers.** Use `🔴` / `🟡` / `🟢`. In plain-terminal / ASCII-only mode (see `common.md` §11) substitute `[CRITICAL]` / `[WARNING]` / `[SUGGESTION]`.
4. **Skill-specific extensions.** Additional sections — `## Module Breakdown` (logic-health), `## Fix Log` / `## Iteration History` (logic-fix-all), Verdict elaboration (logic-diff), `## Resolved by Clarification` / `## Unresolved Findings` (logic-fix-all) — all appear **after** Summary, never between Findings and Summary.
5. **No findings, high score is valid.** When the trace confirms no divergences, output an empty Findings section, set the mode-specific score to its maximum (Logic Score 100, Fault Confidence High with "no fault present", Verdict ✅ Semantically Equivalent), and state plainly in Summary. Do not invent speculative findings to fill space.

---

## Mode-specific header — quick reference

For the full table see `common.md` §5. Inline:

| Skill | Header line directly under `**Scope:**` |
|-------|----------------------------------------|
| logic-review | `**Logic Score:** XX/100` |
| logic-health | `**Logic Score:** XX/100` (weighted) + `## Module Breakdown` |
| logic-explain | _(omitted — descriptive, no score)_ |
| logic-locate | `**Fault Confidence:** High / Medium / Low` |
| logic-diff | `**Verdict:** ✅ / ⚠️ / ❌ <equivalence verdict>` |
| logic-fix-all | `**Logic Score (before):** XX` + `**Logic Score (after):** YY` + `**Findings fixed:** N (Critical: n1 · Warning: n2 · Suggestion: n3)` + `**Findings unresolved:** M` |
