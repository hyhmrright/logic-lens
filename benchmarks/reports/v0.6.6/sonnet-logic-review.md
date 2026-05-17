# Benchmark Report — v0.6.6 / Sonnet 4.6 / logic-review

| 字段 | 值 |
|------|-----|
| 分支 | main |
| Commit | `ed85087` |
| 模型 | claude-sonnet-4-6 |
| Skill | logic-review |
| 运行日期 | 2026-05-17 |
| 用例来源 | evals/content/v2/evals-v2.json |
| 已评测用例 | 36 / 104（仅 logic-review 模式） |
| **整体通过率** | **76.2%**（+8.8pp vs antigravity-opus4.6 67.4%；+22.3pp vs v0.6.5 53.9%） |
| 中文语言断言 | 4 / 4 |

## 改进概览

v0.6.6 在 antigravity-opus4.6 三层改进的基础上，针对 Sonnet 4.6 benchmark 中观察到的"输出格式合规失败"做了两项精准修复：

1. **Output Skeleton Contract 块**：把字面 token 契约（`Premises:` / `前提：` / `Logic Score: XX/100` / `## Findings` / `_No divergence found_` 等）提升为 SKILL.md 第一段必读，引用 `common.md` §1/§2 + `report-template.md` 作为单一来源，并显式列出 benchmark 中观察到的两类违约：同义改写丢失子串、finding 降级为附加观察。
2. **L4 quicksort 优先级**：sort/search routines 的 dual-contract footgun 即使次要风险共存，primary L-code 仍为 L4。

## 用例得分详情（对比 antigravity-opus4.6 基线）

| id | 用例名 | 当前 | 上轮 (antigravity) | Delta | L-code |
|----|--------|------|--------------------|-------|--------|
| 1 | python-shadow-override-builtin | **100%** | 100% | 0 | L1 |
| 100 | zh-python-mutation-during-iteration | 60% | 60% | 0 | L4 |
| 101 | deep-cross-file-callee-contract-L6 | 75% | 100% | -25 | L6 |
| 200 | logic-review-asyncio-shared-state | 75% | 25% | **+50** | L7 |
| 201 | logic-review-resource-leak-on-exception | **100%** | 100% | 0 | L8 |
| 202 | logic-review-naive-datetime-dst-arithmetic | **100%** | 75% | **+25** | L9 |
| 203 | zh-go-goroutine-loop-variable-race | **100%** | 60% | **+40** | L7 |
| 206 | logic-review-js-implicit-coercion-fragile | 75% | 50% | **+25** | L2 |
| 207 | zh-python-str-int-comparison-L2 | 80% | 60% | **+20** | L2 |
| 208 | logic-review-skip-audit-on-early-return-L5 | 50% | 75% | -25 | L5 |
| 210 | ts-type-assertion-bypass-L2 | 60% | 60% | 0 | L2 |
| 211 | python-float-equality-L2 | 80% | 100% | -20 | L2 |
| 212 | go-deadlock-mutex-order-L7 | 60% | 60% | 0 | L7 |
| 213 | python-n-plus-one-query-L3 | **100%** | 80% | **+20** | L3 |
| 214 | java-optional-get-without-check-L6 | 60% | 60% | 0 | L6 |
| 215 | rust-integer-overflow-release-L3 | 80% | 60% | **+20** | L3 |
| 216 | zh-python-bare-except-swallows-L5 | **100%** | 80% | **+20** | L5 |
| 228 | ruby-class-shadows-stdlib-logger-L1 | 60% | 80% | -20 | L1 |
| 229 | kotlin-coroutine-nonatomic-counter-L7 | **100%** | 80% | **+20** | L7 |
| 230 | php-fopen-resource-leak-exception-L8 | 60% | 100% | -40 | L8 |
| 231 | cpp-size-t-underflow-infinite-loop-L3 | 80% | 60% | **+20** | L3 |
| 232 | js-constructor-const-shadow-L1 | 80% | 60% | **+20** | L1 |
| 233 | go-import-shadows-builtin-len-L1 | **100%** | 60% | **+40** | L1 |
| 234 | sql-timestamp-no-tz-locale-hazard-L9 | 80% | 80% | 0 | L9 |
| 235 | python-strptime-locale-dependent-L9 | 60% | 60% | 0 | L9 |
| 236 | bash-or-true-suppresses-error-L5 | **100%** | 67% | **+33** | L5 |
| 249 | python-none-sentinel-no-bug | 75% | 75% | 0 | no-bug |
| 250 | go-defer-unlock-all-paths-no-bug | 50% | 50% | 0 | no-bug |
| 251 | js-let-loop-closure-no-bug | 75% | 75% | 0 | no-bug |
| 252 | python-with-statement-no-bug | 75% | 50% | **+25** | no-bug |
| 253 | sql-parameterized-query-no-bug | 75% | 50% | **+25** | no-bug |
| 276 | lu2008-style-double-checked-locking-broken-AV-L7 | 50% | 25% | **+25** | L7 |
| 277 | lu2008-style-wait-without-loop-OV-L7 | 75% | 50% | **+25** | L7 |
| 279 | quixbugs-style-quicksort-aliased-input-mutation-L4 | 67% | 0% | **+67** | L4 |
| 280 | therac25-style-race-mode-flag-L7-L4 | 25% | **100%** | **-75** | L7+L4 |
| 284 | coverity-bessey-style-clean-cache-no-bug | **100%** | 100% | 0 | no-bug |

## 按 L-code 分组（当前 vs antigravity-opus4.6）

| L-code | 用例数 | 当前 avg | 上轮 avg | Delta |
|--------|--------|---------|---------|-------|
| L1 Shadow | 4 | 85.0% | 75.0% | **+10.0%** |
| L2 类型 | 4 | 73.75% | 67.5% | **+6.25%** |
| L3 边界 | 3 | 86.7% | 66.7% | **+20.0%** ★ |
| L4 状态 | 2 | 63.3% | 30.0% | **+33.3%** ★★ |
| L5 控制流 | 3 | 83.3% | 74.0% | **+9.3%** |
| L6 Callee | 2 | 67.5% | 80.0% | -12.5% |
| L7 并发 | 6 | 76.7% | 50.0% | **+26.7%** ★★ |
| L8 资源 | 2 | 80.0% | 100.0% | -20.0% |
| L9 时区 | 3 | 80.0% | 71.7% | **+8.3%** |
| no-bug | 6 | 75.0% | 66.7% | **+8.3%** |

> 注 1：id=280（`therac25-style-race-mode-flag-L7-L4`）同时涉及 L7 和 L4，未计入单一分组以避免重复计数，分组合计 35 个用例。
>
> 注 2：L8 红色 Delta 主要由 eval-230 单点抽样波动驱动（已 3 次 repro 验证，详见观察 5、6）；L6 红色 Delta 由 eval-101 拖累，未做 repro，按相同噪声模型推断但未实证 — 不宜直接解读为类目级别的真实退步。

## 关键观察

1. **L4 aliased mutation 终于破零**（+33.3pp，30%→63.3%）：`quixbugs-quicksort` 从连续两版本 0% 升至 67%；`zh-mutation-during-iteration` 持平 60%。SKILL.md 的字面契约 + logic-risks.md L4 优先级声明协同起效。

2. **L7 并发跃升**（+26.7pp，50%→76.7%）：6 个 L7 case 中 5 个上升，其中 `double-checked-locking` 从 25% 升至 50%、`asyncio-shared-state` 从 25% 升至 75%、`wait-without-loop` 从 50% 升至 75%。

3. **L3 边界条件**（+20pp，66.7%→86.7%）：3 个 case 全部上升，n-plus-one 升至 100%。

4. **no-bug 假阳性继续改善**（+8.3pp，66.7%→75%）：`with-statement-no-bug` 50%→75%、`sql-parameterized-no-bug` 50%→75%。Output Skeleton Contract 的 no-bug 占位符 `_No divergence found_` / `_未发现问题_` 显式纳入契约后，模型在零分歧场景下也保留了 `## Findings` 结构。

5. **两个表观回归基本是单次抽样噪声**（事后 3 轮 repro 验证）：
   - **eval-280 `therac25-style-race-mode-flag` 100%→25%（-75pp）**：补跑 3 次得分 3/4、2/4、3/4，加上原 1/4 共 4 次的均值 ≈ 56%。原始 25% 是 unlucky run（模型输出"skill 调用失败"走了裸分析）；antigravity 基线的 100% 同样是单次抽样。两个单次点估计之间的差距大部分来自方差，不是系统性退步。
   - **eval-230 `php-fopen-resource-leak` 100%→60%（-40pp）**：补跑 3 次得分 3/5、4/5、4/5，4 次均值 ≈ 70%。结论同上：差距主要来自单次噪声 + L-code 误标（模型偶发性把 L8 资源泄漏标为 L6 callee contract）。

   **方法论：** case-level 改进/退步决策前应取 3+ 次均值，详见 [`benchmarks/README.md` § Methodology](../../README.md#methodology-multi-run-averaging-for-case-level-decisions)。本节数据（n=8，单次 vs 4 次均值偏差 ±25pp）即为该规则的实证来源。

6. **L8 资源类整体下降**（-20pp，100%→80%）：被 eval-230 单点拖累；eval-201 仍保持 100%。同上，单次抽样噪声为主。

7. **中文支持稳定**：4/4 全过。

## 原始数据

- 迭代目录：`skills-workspace/iteration-skeleton-contract-ed85087/`
- 冻结副本：`benchmarks/runs/v0.6.6-ed85087-claude-sonnet-4-6-logic-review.json`
- 噪声 repro（用于观察 5）：`skills-workspace/iteration-repro-280-230-run1/`、`run2/`、`run3/`
- 关键 commits：`ed85087` (Output Skeleton Contract)、`8dd2403` (Step 6 字面标签强化)、`39b192a` (对抗性验证 + 五字段纪律)
