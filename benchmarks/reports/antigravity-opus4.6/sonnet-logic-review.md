# Benchmark Report — antigravity-opus4.6 / Sonnet 4.6 / logic-review

| 字段 | 值 |
|------|-----|
| 分支 | antigravity-opus4.6 |
| Commit | `e01490b` |
| 模型 | claude-sonnet-4-6 |
| Skill | logic-review |
| 运行日期 | 2026-05-10 |
| 用例来源 | evals/content/v2/evals-v2.json |
| 已评测用例 | 36 / 104（仅 logic-review 模式） |
| **整体通过率** | **67.4%**（+13.5pp vs v0.6.5 基线 53.9%） |
| 中文语言断言 | 4 / 4 |

## 改进概览

本次评测的 skill 改进包含四层：
1. **对抗性自检** — 输出前强制执行反驳检查
2. **五字段纪律** — 每条 finding 必须填写完整结构化字段
3. **执行验证闭环** — 追踪执行路径确认 bug 可达性
4. **Reachability Gate** — Class A/B 分类系统，Class B 需完成可达性探针才可上报

## 用例得分详情（对比 v0.6.5 Sonnet 基线）

| id | 用例名 | 当前 | 基线 | Delta | L-code |
|----|--------|------|------|-------|--------|
| 1 | python-shadow-override-builtin | 4/4=**100%** | 50% | **+50%** | L1 |
| 100 | zh-python-mutation-during-iteration | 3/5=60% | 60% | 0 | L4 |
| 101 | deep-cross-file-callee-contract-L6 | 4/4=**100%** | 50% | **+50%** | L6 |
| 200 | logic-review-asyncio-shared-state-across-await | 1/4=25% | 50% | -25% | L7 |
| 201 | logic-review-resource-leak-on-exception | 4/4=**100%** | 100% | 0 | L8 |
| 202 | logic-review-naive-datetime-dst-arithmetic | 3/4=75% | 50% | **+25%** | L9 |
| 203 | zh-go-goroutine-loop-variable-race | 3/5=60% | 60% | 0 | L7 |
| 206 | logic-review-js-implicit-coercion-fragile | 2/4=50% | 25% | **+25%** | L2 |
| 207 | zh-python-str-int-comparison-L2 | 3/5=60% | 80% | -20% | L2 |
| 208 | logic-review-skip-audit-on-early-return-L5 | 3/4=75% | 25% | **+50%** | L5 |
| 210 | ts-type-assertion-bypass-L2 | 3/5=60% | 20% | **+40%** | L2 |
| 211 | python-float-equality-L2 | 5/5=**100%** | 80% | **+20%** | L2 |
| 212 | go-deadlock-mutex-order-L7 | 3/5=60% | 40% | **+20%** | L7 |
| 213 | python-n-plus-one-query-L3 | 4/5=80% | 60% | **+20%** | L3 |
| 214 | java-optional-get-without-check-L6 | 3/5=60% | 60% | 0 | L6 |
| 215 | rust-integer-overflow-release-L3 | 3/5=60% | 80% | -20% | L3 |
| 216 | zh-python-bare-except-swallows-L5 | 4/5=80% | 80% | 0 | L5 |
| 228 | ruby-class-shadows-stdlib-logger-L1 | 4/5=80% | 60% | **+20%** | L1 |
| 229 | kotlin-coroutine-nonatomic-counter-L7 | 4/5=80% | 60% | **+20%** | L7 |
| 230 | php-fopen-resource-leak-exception-L8 | 5/5=**100%** | 60% | **+40%** | L8 |
| 231 | cpp-size-t-underflow-infinite-loop-L3 | 3/5=60% | 60% | 0 | L3 |
| 232 | js-constructor-const-shadow-L1 | 3/5=60% | 60% | 0 | L1 |
| 233 | go-import-shadows-builtin-len-L1 | 3/5=60% | 60% | 0 | L1 |
| 234 | sql-timestamp-no-tz-locale-hazard-L9 | 4/5=80% | 60% | **+20%** | L9 |
| 235 | python-strptime-locale-dependent-L9 | 3/5=60% | 60% | 0 | L9 |
| 236 | bash-or-true-suppresses-error-L5 | 4/6=67% | 67% | 0 | L5 |
| 249 | python-none-sentinel-no-bug | 3/4=75% | 75% | 0 | no-bug |
| 250 | go-defer-unlock-all-paths-no-bug | 2/4=50% | 25% | **+25%** | no-bug |
| 251 | js-let-loop-closure-no-bug | 3/4=75% | 50% | **+25%** | no-bug |
| 252 | python-with-statement-no-bug | 2/4=50% | 75% | -25% | no-bug |
| 253 | sql-parameterized-query-no-bug | 2/4=50% | 25% | **+25%** | no-bug |
| 276 | lu2008-style-double-checked-locking-broken-AV-L7 | 1/4=25% | 25% | 0 | L7 |
| 277 | lu2008-style-wait-without-loop-OV-L7 | 2/4=50% | 50% | 0 | L7 |
| 279 | quixbugs-style-quicksort-aliased-input-mutation-L4 | 0/3=**0%** | 0% | 0 | L4 |
| 280 | therac25-style-race-mode-flag-L7-L4 | 4/4=**100%** | 50% | **+50%** | L7+L4 |
| 284 | coverity-bessey-style-clean-cache-no-bug | 4/4=**100%** | 50% | **+50%** | no-bug |

## 按 L-code 分组（当前 vs v0.6.5 Sonnet 基线）

| L-code | 用例数 | 当前 avg | 基线 avg | Delta |
|--------|--------|---------|---------|-------|
| L1 Shadow | 4 | 75.0% | 57.5% | **+17.5%** |
| L2 类型 | 4 | 67.5% | 51.3% | **+16.3%** |
| L3 边界 | 3 | 66.7% | 66.7% | 0 |
| L4 状态 | 2 | 30.0% | 30.0% | 0 |
| L5 控制流 | 3 | 74.0% | 57.3% | **+16.7%** |
| L6 Callee | 2 | 80.0% | 55.0% | **+25.0%** |
| L7 并发 | 6 | 50.0% | 47.5% | **+2.5%** |
| L8 资源 | 2 | 100.0% | 80.0% | **+20.0%** |
| L9 时区 | 3 | 71.7% | 56.7% | **+15.0%** |
| no-bug | 6 | 66.7% | 50.0% | **+16.7%** |

> 注：id=280（`therac25-style-race-mode-flag-L7-L4`）同时涉及 L7 和 L4，未计入单一分组以避免重复计数，分组合计 35 个用例。

## 关键观察

1. **全面提升，无明显短板类别**：10 个 L-code 分组中 8 个有正向提升，2 个（L3/L4）持平，无分组出现整体退步。

2. **最大提升：L6 Callee Contract**（+25pp）：`deep-cross-file-callee-contract-L6` 从 50% 升至 100%。执行验证闭环对跨函数契约违反的识别贡献最大。

3. **no-bug 假阳性改善显著**（+16.7pp，50%→66.7%）：`go-defer-unlock-all-paths`（+25%）、`js-let-loop-closure`（+25%）、`sql-parameterized-query`（+25%）全部提升。Reachability Gate 有效抑制了误报。

4. **L7 并发仍是最弱分组**（50.0%）：`double-checked-locking`（25%）和 `asyncio-shared-state`（25%，本次退步）是主要拖累。并发 bug 的可达性验证难度最高，现有机制收益有限。

5. **4 个退步 case**：
   - `asyncio-shared-state-across-await`（-25%）：Reachability Gate 可能过度过滤了这个 L7 异步 bug
   - `python-with-statement-no-bug`（-25%）：no-bug case 仍有波动
   - `zh-python-str-int-comparison-L2`（-20%）和 `rust-integer-overflow-release-L3`（-20%）：中文 case 和 release-mode bug 有小幅回归

6. **L4 aliased mutation 仍为 0%**：`quixbugs-quicksort` 连续两个版本全部失败，属于 skill 层面系统性盲区，需专项改进。

7. **中文支持稳定**：4/4 全过。

## 原始数据

- 迭代目录：`skills-workspace/iteration-antigravity-sonnet-20260510-2307/`
- 冻结副本：`benchmarks/runs/antigravity-opus4.6-e01490b-claude-sonnet-4-6-logic-review.json`
