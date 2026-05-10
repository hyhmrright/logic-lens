# Benchmark Report — v0.6.5 / Sonnet 4.6 / logic-review

| 字段 | 值 |
|------|-----|
| 版本 Tag | v0.6.5 (commit `549719a`) |
| 模型 | claude-sonnet-4-6 |
| Skill | logic-review |
| 运行日期 | 2026-05-10 |
| 用例来源 | evals/content/v2/evals-v2.json |
| 已评测用例 | 36 / 104（仅 logic-review 模式） |
| **整体通过率** | **53.9%** |
| 中文语言断言 | 4 / 4 |

## 用例得分详情（含 Haiku 对比）

| id | 用例名 | Sonnet | Haiku | Delta | L-code |
|----|--------|--------|-------|-------|--------|
| 1 | python-shadow-override-builtin | 2/4=50% | 50% | 0 | L1 |
| 100 | zh-python-mutation-during-iteration | 3/5=60% | 60% | 0 | L4 |
| 101 | deep-cross-file-callee-contract-L6 | 2/4=50% | 50% | 0 | L6 |
| 200 | logic-review-asyncio-shared-state-across-await | 2/4=50% | 25% | **+25%** | L7 |
| 201 | logic-review-resource-leak-on-exception | 4/4=**100%** | 25% | **+75%** | L8 |
| 202 | logic-review-naive-datetime-dst-arithmetic | 2/4=50% | 50% | 0 | L9 |
| 203 | zh-go-goroutine-loop-variable-race | 3/5=60% | 40% | **+20%** | L7 |
| 206 | logic-review-js-implicit-coercion-fragile | 1/4=25% | 25% | 0 | L2 |
| 207 | zh-python-str-int-comparison-L2 | 4/5=80% | 60% | **+20%** | L2 |
| 208 | logic-review-skip-audit-on-early-return-L5 | 1/4=25% | 25% | 0 | L5 |
| 210 | ts-type-assertion-bypass-L2 | 1/5=20% | 20% | 0 | L2 |
| 211 | python-float-equality-L2 | 4/5=80% | 60% | **+20%** | L2 |
| 212 | go-deadlock-mutex-order-L7 | 2/5=40% | 20% | **+20%** | L7 |
| 213 | python-n-plus-one-query-L3 | 3/5=60% | 60% | 0 | L3 |
| 214 | java-optional-get-without-check-L6 | 3/5=60% | 60% | 0 | L6 |
| 215 | rust-integer-overflow-release-L3 | 4/5=**80%** | 20% | **+60%** | L3 |
| 216 | zh-python-bare-except-swallows-L5 | 4/5=80% | 80% | 0 | L5 |
| 228 | ruby-class-shadows-stdlib-logger-L1 | 3/5=60% | 60% | 0 | L1 |
| 229 | kotlin-coroutine-nonatomic-counter-L7 | 3/5=60% | 60% | 0 | L7 |
| 230 | php-fopen-resource-leak-exception-L8 | 3/5=60% | 60% | 0 | L8 |
| 231 | cpp-size-t-underflow-infinite-loop-L3 | 3/5=60% | 60% | 0 | L3 |
| 232 | js-constructor-const-shadow-L1 | 3/5=60% | 40% | **+20%** | L1 |
| 233 | go-import-shadows-builtin-len-L1 | 3/5=60% | 40% | **+20%** | L1 |
| 234 | sql-timestamp-no-tz-locale-hazard-L9 | 3/5=60% | 60% | 0 | L9 |
| 235 | python-strptime-locale-dependent-L9 | 3/5=60% | 60% | 0 | L9 |
| 236 | bash-or-true-suppresses-error-L5 | 4/6=67% | 50% | **+17%** | L5 |
| 249 | python-none-sentinel-no-bug | 3/4=75% | 50% | **+25%** | no-bug |
| 250 | go-defer-unlock-all-paths-no-bug | 1/4=25% | 25% | 0 | no-bug |
| 251 | js-let-loop-closure-no-bug | 2/4=50% | 50% | 0 | no-bug |
| 252 | python-with-statement-no-bug | 3/4=75% | 75% | 0 | no-bug |
| 253 | sql-parameterized-query-no-bug | 1/4=25% | 50% | **-25%** | no-bug |
| 276 | lu2008-style-double-checked-locking-broken-AV-L7 | 1/4=25% | 25% | 0 | L7 |
| 277 | lu2008-style-wait-without-loop-OV-L7 | 2/4=50% | 50% | 0 | L7 |
| 279 | quixbugs-style-quicksort-aliased-input-mutation-L4 | 0/3=**0%** | 0% | 0 | L4 |
| 280 | therac25-style-race-mode-flag-L7-L4 | 2/4=50% | 0% | **+50%** | L7+L4 |
| 284 | coverity-bessey-style-clean-cache-no-bug | 2/4=50% | 25% | **+25%** | no-bug |

## 按 L-code 分组（Sonnet vs Haiku）

| L-code | 用例数 | Sonnet avg | Haiku avg | Delta |
|--------|--------|-----------|-----------|-------|
| L1 Shadow | 4 | 57.5% | 47.5% | +10% |
| L2 类型 | 4 | 51.3% | 41.3% | +10% |
| L3 边界 | 3 | 66.7% | 46.7% | **+20%** |
| L4 状态 | 2 | 30% | 30% | 0 |
| L5 控制流 | 3 | 57.3% | 51.7% | +5.6% |
| L6 Callee | 2 | 55% | 55% | 0 |
| L7 并发 | 6 | 47.5% | 41% | +6.5% |
| L8 资源 | 2 | **80%** | 42.5% | **+37.5%** |
| L9 时区 | 3 | 56.7% | 56.7% | 0 |
| no-bug | 6 | 50% | 45% | +5% |

## 关键观察

1. **最大提升：L8 资源泄漏**（+37.5pp）：`logic-review-resource-leak-on-exception` Haiku 仅 25%，Sonnet 达到 100%——Sonnet 对异常路径上的资源泄漏（finally/with 缺失）识别能力明显更强。

2. **第二大提升：L3 边界**（+20pp）：`rust-integer-overflow-release-L3` Haiku 仅 20%，Sonnet 达 80%。Haiku 在 release 模式下的整数 overflow 静默行为上理解不足。

3. **L7 并发持续弱**（47.5%）：尽管比 Haiku 提升了 6.5pp，但 `therac25`（+50%）拉动了均值。`double-checked-locking`（25%）和 `deadlock-mutex-order`（40%）仍是短板。

4. **L4 无改善**（30%）：两个模型都在 `quixbugs-quicksort`（aliased input mutation）上得 0%——这是共同弱点，可能需要 skill 层面改进。

5. **唯一回归：253**（no-bug sql-parameterized-query，-25pp）：Sonnet 在这个"无 bug"用例上反而更容易报假阳性。no-bug 用例整体仍有改进空间（avg 50%）。

6. **中文支持稳定**：两个模型 4/4 全过。

## 原始数据

- 迭代目录：`skills-workspace/iteration-sonnet-logic-review/`
- 汇总 JSON：`skills-workspace/iteration-sonnet-logic-review/summary.json`
- 冻结副本：`benchmarks/runs/v0.6.5-sonnet-logic-review.json`
