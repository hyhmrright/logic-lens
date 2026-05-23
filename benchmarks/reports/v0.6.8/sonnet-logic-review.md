# Benchmark Report — v0.6.8 / Sonnet 4.6 / logic-review（2-run 均值）

| 字段 | 值 |
|------|-----|
| 分支 | main |
| Commit | `3a9ab19` |
| 模型 | claude-sonnet-4-6 |
| Skill | logic-review |
| 运行日期 | 2026-05-23 |
| 用例来源 | evals/content/v2/evals-v2.json |
| 已评测用例 | **36 / 104**（仅 logic-review 模式） |
| **Run1 通过率** | **74.5%** |
| **Run2 通过率** | **77.4%** |
| **2-run 均值** | **75.9%**（vs v0.6.6 76.2%，-0.2pp） |
| 中文语言断言 | Run1: 3/4, Run2: 3/4 |

## 改进概览

v0.6.8 在 v0.6.6（Output Skeleton Contract）基础上做了两类改进：

1. **Divergence 字段合规强化**：SKILL.md Output Skeleton Contract 新增第三类失败模式（`Divergence:` 字段缺失）和完整五字段 finding 正例模板。格式合规率从 47% 升至 67%（+20pp）。
2. **L-code 消歧表扩展**：logic-risks.md 消歧表扩展为三列（含 "Common mistake to avoid"），新增 8 条高频误分类反向指引；SKILL.md Step 3 新增 L1 vs L6、L9 内联消歧规则，收紧 L4 适用范围。

## 用例得分详情（2-run 均值 vs v0.6.6）

| id | 用例名 | 2-Avg | v0.6.6 | Delta | L-code |
|----|--------|-------|--------|-------|--------|
| 1 | python-shadow-override-builtin | **100%** | 100% | 0 | L1 |
| 100 | zh-python-mutation-during-iteration | **90%** | 60% | **+30** | L4 |
| 101 | deep-cross-file-callee-contract-L6 | **88%** | 75% | **+12** | L6 |
| 200 | logic-review-asyncio-shared-state | **88%** | 75% | **+12** | L7 |
| 201 | logic-review-resource-leak-on-exception | 88% | 100% | -12 | L8 |
| 202 | logic-review-naive-datetime-dst-arithmetic | 75% | 100% | -25 | L9 |
| 203 | zh-go-goroutine-loop-variable-race | 70% | 100% | -30 | L7 |
| 206 | logic-review-js-implicit-coercion-fragile | 50% | 75% | -25 | L2 |
| 207 | zh-python-str-int-comparison-L2 | **100%** | 80% | **+20** | L2 |
| 208 | logic-review-skip-audit-on-early-return-L5 | **75%** | 50% | **+25** | L5 |
| 210 | ts-type-assertion-bypass-L2 | **70%** | 60% | **+10** | L2 |
| 211 | python-float-equality-L2 | **100%** | 80% | **+20** | L2 |
| 212 | go-deadlock-mutex-order-L7 | **100%** | 60% | **+40** | L7 |
| 213 | python-n-plus-one-query-L3 | 80% | 100% | -20 | L3 |
| 214 | java-optional-get-without-check-L6 | **90%** | 60% | **+30** | L6 |
| 215 | rust-integer-overflow-release-L3 | 70% | 80% | -10 | L3 |
| 216 | zh-python-bare-except-swallows-L5 | 80% | 100% | -20 | L5 |
| 228 | ruby-class-shadows-stdlib-logger-L1 | **90%** | 60% | **+30** | L1 |
| 229 | kotlin-coroutine-nonatomic-counter-L7 | 90% | 100% | -10 | L7 |
| 230 | php-fopen-resource-leak-exception-L8 | **80%** | 60% | **+20** | L8 |
| 231 | cpp-size-t-underflow-infinite-loop-L3 | 80% | 80% | 0 | L3 |
| 232 | js-constructor-const-shadow-L1 | 60% | 80% | -20 | L1 |
| 233 | go-import-shadows-builtin-len-L1 | 50% | 100% | -50 | L1 |
| 234 | sql-timestamp-no-tz-locale-hazard-L9 | 60% | 80% | -20 | L9 |
| 235 | python-strptime-locale-dependent-L9 | **90%** | 60% | **+30** | L9 |
| 236 | bash-or-true-suppresses-error-L5 | 67% | 100% | -33 | L5 |
| 249 | python-none-sentinel-no-bug | 62% | 75% | -12 | no-bug |
| 250 | go-defer-unlock-all-paths-no-bug | 50% | 50% | 0 | no-bug |
| 251 | js-let-loop-closure-no-bug | 75% | 75% | 0 | no-bug |
| 252 | python-with-statement-no-bug | 75% | 75% | 0 | no-bug |
| 253 | sql-parameterized-query-no-bug | 50% | 75% | -25 | no-bug |
| 276 | lu2008-style-double-checked-locking-broken-AV-L7 | 50% | 50% | 0 | L7 |
| 277 | lu2008-style-wait-without-loop-OV-L7 | 75% | 75% | 0 | L7 |
| 279 | quixbugs-style-quicksort-aliased-input-mutation-L4 | 67% | 67% | 0 | L4 |
| 280 | therac25-style-race-mode-flag-L7-L4 | **88%** | 25% | **+62** | L7+L4 |
| 284 | coverity-bessey-style-clean-cache-no-bug | 62% | 100% | -38 | no-bug |

## 关键观察

1. **格式合规显著提升**（47% → 67%，+20pp）：Divergence 字段正例模板使 13 个 case 从格式不合规翻转为合规，净增 +7（13 gained / 6 lost）。这是改动中最稳定的收益。

2. **低分 case 大幅拉升**：此前 ≤60% 的 case 中，7 个升至 ≥70%（eval-100, 212, 214, 228, 235, 280 均升 ≥30pp）。Therac-25 案例（eval-280）从 25% 升至 88%（+62pp），是单 case 最大提升。

3. **高分 case 出现波动**：此前 100% 的 case 中，6 个降至 ≤80%（eval-203, 213, 216, 233, 236, 284）。最大降幅为 eval-233（100% → 50%，-50pp）。

4. **Run-to-run 方差验证**：Run1 74.5% vs Run2 77.4%（差 2.9pp），与 v0.6.6 报告记录的 case 级 ±25pp 方差一致。v0.6.6 基线也是单次数据，其 76.2% 本身存在同等方差。

5. **L-code 消歧部分生效**：eval-212 deadlock L6→L7 修复（+40pp），eval-208 L2→L5 修复（+25pp），eval-228 L3→L1 修复（+30pp）。但 eval-233/232 出现新的 L-code 漂移，可能是 L4 规则过于激进的副作用。

6. **整体净效果持平**：2-run 均值 75.9% vs v0.6.6 单次 76.2%（-0.2pp），在统计噪声范围内。需要 3-run 均值（含 v0.6.6 基线重测）才能做出统计性结论。

## 原始数据

- Run1 迭代目录：`skills-workspace/iteration-v0.6.8-full/`
- Run2 迭代目录：`skills-workspace/iteration-v0.6.8-run2/`
- 10-case 探针：`skills-workspace/iteration-probe-v0.6.8-divergence/`
- 关键 commit：`3a9ab19`（v0.6.8 Divergence 正例 + 消歧表）
