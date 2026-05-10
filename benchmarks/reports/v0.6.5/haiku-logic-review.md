# Benchmark Report — v0.6.5 / Haiku / logic-review

| 字段 | 值 |
|------|-----|
| 版本 Tag | v0.6.5 (commit `549719a`) |
| 模型 | claude-haiku-4-5-20251001 |
| Skill | logic-review |
| 运行日期 | 2026-05-10 |
| 用例来源 | evals/content/v2/evals-v2.json |
| 已评测用例 | 36 / 104（仅 logic-review 模式） |
| **整体通过率** | **43.6%** |
| 中文语言断言 | 4 / 4 |

## 用例得分详情

| id | 用例名 | 通过 | 总分 | 通过率 | L-code |
|----|--------|------|------|--------|--------|
| 1 | python-shadow-override-builtin | 2 | 4 | 50% | L1 |
| 100 | zh-python-mutation-during-iteration | 3 | 5 | 60% | L4 |
| 101 | deep-cross-file-callee-contract-L6 | 2 | 4 | 50% | L6 |
| 200 | logic-review-asyncio-shared-state-across-await | 1 | 4 | 25% | L7 |
| 201 | logic-review-resource-leak-on-exception | 1 | 4 | 25% | L8 |
| 202 | logic-review-naive-datetime-dst-arithmetic | 2 | 4 | 50% | L9 |
| 203 | zh-go-goroutine-loop-variable-race | 2 | 5 | 40% | L7 |
| 206 | logic-review-js-implicit-coercion-fragile | 1 | 4 | 25% | L2 |
| 207 | zh-python-str-int-comparison-L2 | 3 | 5 | 60% | L2 |
| 208 | logic-review-skip-audit-on-early-return-L5 | 1 | 4 | 25% | L5 |
| 210 | ts-type-assertion-bypass-L2 | 1 | 5 | 20% | L2 |
| 211 | python-float-equality-L2 | 3 | 5 | 60% | L2 |
| 212 | go-deadlock-mutex-order-L7 | 1 | 5 | 20% | L7 |
| 213 | python-n-plus-one-query-L3 | 3 | 5 | 60% | L3 |
| 214 | java-optional-get-without-check-L6 | 3 | 5 | 60% | L6 |
| 215 | rust-integer-overflow-release-L3 | 1 | 5 | 20% | L3 |
| 216 | zh-python-bare-except-swallows-L5 | 4 | 5 | 80% | L5 |
| 228 | ruby-class-shadows-stdlib-logger-L1 | 3 | 5 | 60% | L1 |
| 229 | kotlin-coroutine-nonatomic-counter-L7 | 3 | 5 | 60% | L7 |
| 230 | php-fopen-resource-leak-exception-L8 | 3 | 5 | 60% | L8 |
| 231 | cpp-size-t-underflow-infinite-loop-L3 | 3 | 5 | 60% | L3 |
| 232 | js-constructor-const-shadow-L1 | 2 | 5 | 40% | L1 |
| 233 | go-import-shadows-builtin-len-L1 | 2 | 5 | 40% | L1 |
| 234 | sql-timestamp-no-tz-locale-hazard-L9 | 3 | 5 | 60% | L9 |
| 235 | python-strptime-locale-dependent-L9 | 3 | 5 | 60% | L9 |
| 236 | bash-or-true-suppresses-error-L5 | 3 | 6 | 50% | L5 |
| 249 | python-none-sentinel-no-bug | 2 | 4 | 50% | no-bug |
| 250 | go-defer-unlock-all-paths-no-bug | 1 | 4 | 25% | no-bug |
| 251 | js-let-loop-closure-no-bug | 2 | 4 | 50% | no-bug |
| 252 | python-with-statement-no-bug | 3 | 4 | 75% | no-bug |
| 253 | sql-parameterized-query-no-bug | 2 | 4 | 50% | no-bug |
| 276 | lu2008-style-double-checked-locking-broken-AV-L7 | 1 | 4 | 25% | L7 |
| 277 | lu2008-style-wait-without-loop-OV-L7 | 2 | 4 | 50% | L7 |
| 279 | quixbugs-style-quicksort-aliased-input-mutation-L4 | 0 | 3 | **0%** | L4 |
| 280 | therac25-style-race-mode-flag-L7-L4 | 0 | 4 | **0%** | L7+L4 |
| 284 | coverity-bessey-style-clean-cache-no-bug | 1 | 4 | 25% | no-bug |

## 按 L-code 分组

| L-code | 用例数 | 平均通过率 | 备注 |
|--------|--------|-----------|------|
| L1 Shadow | 4 | 47.5% | js-constructor-const-shadow 较弱 |
| L2 类型 | 4 | 41.3% | ts-type-assertion 最弱（20%） |
| L3 边界 | 3 | 46.7% | rust-integer-overflow 弱（20%） |
| L4 状态 | 2 | 30% | quicksort 0%，zh-mutation 60% |
| L5 控制流 | 3 | 51.7% | bare-except 最强（80%） |
| L6 Callee | 2 | 55% | java-optional 好（60%） |
| L7 并发 | 5 | 41% | 最弱维度；therac25 0%，deadlock 20% |
| L8 资源 | 2 | 42.5% | |
| L9 时区 | 3 | 56.7% | 最强维度 |
| no-bug | 5 | 45% | go-defer 最差（25%），伪阳性风险 |

## 关键观察

1. **最弱用例**：`therac25-style-race-mode-flag-L7-L4`（0%）和 `quixbugs-style-quicksort-aliased-input-mutation-L4`（0%）——两者均涉及复杂跨调用栈 mutation 或竞态条件。

2. **并发（L7）整体偏弱**（41%）：asyncio shared state 25%、go deadlock 20%、double-checked locking 25%，仅 kotlin-coroutine 达到 60%。

3. **no-bug 误报风险**：5 个"无 bug"用例平均 45%，`go-defer-unlock` 仅 25%，说明 Haiku 容易在安全代码上生成假阳性 finding。

4. **中文支持稳定**：4/4 中文语言断言全部通过。

5. **与 v0.6.4 Haiku baseline 对比**：v0.6.4 全 79 用例为 38.7%；本次仅跑 36 个 logic-review 用例为 43.6%，不直接可比（用例集不同）。

## 原始数据

- 迭代目录：`skills-workspace/iteration-549719a/`
- 汇总 JSON：`skills-workspace/iteration-549719a/summary.json`
- 冻结副本：`benchmarks/runs/v0.6.5-haiku-logic-review.json`
