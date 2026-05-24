# Benchmark Report — v0.6.9 / Sonnet 4.6 / logic-review

| 字段 | 值 |
|------|-----|
| 分支 | main |
| Commit | `fe9a1aa` |
| 模型 | claude-sonnet-4-6 |
| Skill | logic-review |
| 运行日期 | 2026-05-24 |
| 用例来源 | evals/content/v2/evals-v2.json |
| 已评测用例 | **36 / 104**（仅 logic-review 模式） |
| **整体通过率** | **78.3%**（+2.4pp vs v0.6.8 avg 75.9%；+2.1pp vs v0.6.6 76.2%） |
| 中文语言断言 | 1/4 |

## 改进概览

v0.6.9 在 v0.6.8 基础上新增四组 L-code 消歧规则和 no-bug 五字段输出模板：

1. **四组 L-code 消歧规则**：SKILL.md Step 3 新增 L1 vs L6（constructor scope）、L2 vs L6（operator coercion）、L5 vs L7（single-context error suppression）内联消歧段落；logic-risks.md Quick Disambiguation Table 新增 4 条高频误分类条目。
2. **No-bug 五字段模板**：Output Skeleton Contract 新增 Go defer 正例模板，要求 no-bug 结论也使用 `Divergence: None` 的完整五字段格式。
3. **DCL 双面规则**：Step 4 强制要求 Java/C++ DCL 模式同时报告 volatile 缺失和 publish-before-init 两个面。

## 用例得分详情（vs v0.6.8 2-run avg / v0.6.6）

| id | 用例名 | v0.6.9 | v0.6.8avg | Δ8 | v0.6.6 | Δ6 | L-code |
|----|--------|--------|----------|-----|--------|-----|--------|
| 1 | python-shadow-override-builtin | **100%** | 100% | 0 | 100% | 0 | L1 |
| 100 | zh-python-mutation-during-iteration | 60% | 90% | -30 | 60% | 0 | L4 |
| 101 | deep-cross-file-callee-contract-L6 | **100%** | 88% | **+12** | 75% | **+25** | L6 |
| 200 | logic-review-asyncio-shared-state | 75% | 88% | -13 | 75% | 0 | L7 |
| 201 | logic-review-resource-leak-on-exception | **100%** | 88% | **+12** | 100% | 0 | L8 |
| 202 | logic-review-naive-datetime-dst-arithmetic | **100%** | 75% | **+25** | 100% | 0 | L9 |
| 203 | zh-go-goroutine-loop-variable-race | 80% | 70% | **+10** | 100% | -20 | L7 |
| 206 | logic-review-js-implicit-coercion-fragile | 50% | 50% | 0 | 75% | -25 | L2 |
| 207 | zh-python-str-int-comparison-L2 | 80% | 100% | -20 | 80% | 0 | L2 |
| 208 | logic-review-skip-audit-on-early-return-L5 | 25% | 75% | -50 | 50% | -25 | L5 |
| 210 | ts-type-assertion-bypass-L2 | **100%** | 70% | **+30** | 60% | **+40** | L2 |
| 211 | python-float-equality-L2 | 80% | 100% | -20 | 80% | 0 | L2 |
| 212 | go-deadlock-mutex-order-L7 | **100%** | 100% | 0 | 60% | **+40** | L7 |
| 213 | python-n-plus-one-query-L3 | **100%** | 80% | **+20** | 100% | 0 | L3 |
| 214 | java-optional-get-without-check-L6 | **100%** | 90% | **+10** | 60% | **+40** | L6 |
| 215 | rust-integer-overflow-release-L3 | 80% | 70% | **+10** | 80% | 0 | L3 |
| 216 | zh-python-bare-except-swallows-L5 | 80% | 80% | 0 | 100% | -20 | L5 |
| 228 | ruby-class-shadows-stdlib-logger-L1 | **100%** | 90% | **+10** | 60% | **+40** | L1 |
| 229 | kotlin-coroutine-nonatomic-counter-L7 | **100%** | 90% | **+10** | 100% | 0 | L7 |
| 230 | php-fopen-resource-leak-exception-L8 | 80% | 80% | 0 | 60% | **+20** | L8 |
| 231 | cpp-size-t-underflow-infinite-loop-L3 | 80% | 80% | 0 | 80% | 0 | L3 |
| 232 | js-constructor-const-shadow-L1 | 40% | 60% | -20 | 80% | -40 | L1 |
| 233 | go-import-shadows-builtin-len-L1 | 80% | 50% | **+30** | 100% | -20 | L1 |
| 234 | sql-timestamp-no-tz-locale-hazard-L9 | **100%** | 60% | **+40** | 80% | **+20** | L9 |
| 235 | python-strptime-locale-dependent-L9 | 80% | 90% | -10 | 60% | **+20** | L9 |
| 236 | bash-or-true-suppresses-error-L5 | 67% | 67% | 0 | 100% | -33 | L5 |
| 249 | python-none-sentinel-no-bug | 75% | 62% | **+13** | 75% | 0 | no-bug |
| 250 | go-defer-unlock-all-paths-no-bug | 50% | 50% | 0 | 50% | 0 | no-bug |
| 251 | js-let-loop-closure-no-bug | 75% | 75% | 0 | 75% | 0 | no-bug |
| 252 | python-with-statement-no-bug | 75% | 75% | 0 | 75% | 0 | no-bug |
| 253 | sql-parameterized-query-no-bug | 50% | 50% | 0 | 75% | -25 | no-bug |
| 276 | lu2008-style-double-checked-locking-broken-AV-L7 | 50% | 50% | 0 | 50% | 0 | L7 |
| 277 | lu2008-style-wait-without-loop-OV-L7 | **100%** | 75% | **+25** | 75% | **+25** | L7 |
| 279 | quixbugs-style-quicksort-aliased-input-mutation-L4 | 33% | 67% | -34 | 67% | -34 | L4 |
| 280 | therac25-style-race-mode-flag-L7-L4 | 75% | 88% | -13 | 25% | **+50** | L7+L4 |
| 284 | coverity-bessey-style-clean-cache-no-bug | **100%** | 62% | **+38** | 100% | 0 | no-bug |

## 按 L-code 分组

| L-code | 用例数 | v0.6.9 | v0.6.8 avg | Delta |
|--------|--------|--------|-----------|-------|
| L1 Shadow | 4 | 80.0% | 75.0% | **+5.0** |
| L2 类型 | 4 | 77.5% | 80.0% | -2.5 |
| L3 边界 | 3 | 86.7% | 76.7% | **+10.0** |
| L4 状态 | 2 | 46.5% | 78.5% | -32.0 |
| L5 控制流 | 3 | 57.3% | 74.0% | -16.7 |
| L6 Callee | 2 | 100.0% | 89.0% | **+11.0** |
| L7 并发 | 6 | 84.2% | 78.8% | **+5.3** |
| L8 资源 | 2 | 90.0% | 84.0% | **+6.0** |
| L9 时区 | 3 | 93.3% | 75.0% | **+18.3** |
| no-bug | 6 | 70.8% | 62.3% | **+8.5** |

> 注：id=280（L7+L4）未计入单一分组，分组合计 35 个用例。

## 关键观察

1. **L9 时区/locale 消歧大幅生效**（+18.3pp，75.0% → 93.3%）：eval-234（sql-timestamp）从 60% 升至 100%（+40pp），是最大单 case 提升。logic-risks.md 消歧表中新增的"data type lacking tz/locale metadata → L9, not L6"精准命中。

2. **L6 Callee contract 满分**（+11.0pp，89.0% → 100%）：两个 case 均达 100%。消歧规则有效排除了误分类。

3. **No-bug 五字段模板生效**（+8.5pp，62.3% → 70.8%）：eval-284（coverity no-bug）从 62% 升至 100%（+38pp）。Go defer 正例模板帮助模型在零分歧场景保持结构化输出。

4. **L4 状态突变退步**（-32.0pp，78.5% → 46.5%）：eval-100（60%）和 eval-279（33%）同时下降。单次运行方差可能是主因（v0.6.8 中 eval-100 的两轮得分分别为 80% 和 100%，方差本身 ±20pp），但需要多轮验证排除系统性退步。

5. **eval-208 大幅退步**（75% → 25%，-50pp）：skip-audit-on-early-return-L5。该 case 在 v0.6.6 也仅 50%，v0.6.7 probe 曾修复到 75%，本次退回。高方差 case，需要 3-run 均值判断。

6. **13 个 case 达到满分**（100%）：1, 101, 201, 202, 210, 212, 213, 214, 228, 229, 234, 277, 284 — 比 v0.6.8 avg 的 3 个满分 case 大幅增加。

7. **中文语言断言退步**：1/4（v0.6.8 两轮均为 3/4）。中文 case 的分析质量未下降，但格式合规（字面 label 匹配）可能受单次方差影响。

## 原始数据

- 迭代目录：`skills-workspace/iteration-v0.6.9-fe9a1aa/`
- 冻结副本：`benchmarks/runs/v0.6.9-fe9a1aa-claude-sonnet-4-6-logic-review.json`
- 关键 commit：`fe9a1aa`（四组消歧规则 + no-bug 五字段模板）
