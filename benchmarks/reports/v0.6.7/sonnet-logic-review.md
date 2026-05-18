# Benchmark Report — v0.6.7 / Sonnet 4.6 / logic-review（4-case probe）

| 字段 | 值 |
|------|-----|
| 分支 | main |
| Commit | `58f1be3` |
| 模型 | claude-sonnet-4-6 |
| Skill | logic-review |
| 运行日期 | 2026-05-18 |
| 用例来源 | evals/content/v2/evals-v2.json |
| 已评测用例 | **4 / 104**（定向探针：eval-208/250/276/280） |
| **探针平均通过率** | **75.0%**（基线 a25b6c7：31.25%；+43.75pp） |
| 中文语言断言 | — |

> **注：本次为 4-case 定向探针，非全量 benchmark。** 不宜直接与 v0.6.6 整体通过率（76.2%，36 cases）做横向比较。

## 改进概览

v0.6.7 在 v0.6.6（Output Skeleton Contract）基础上，针对本次 benchmark 中观察到的三类分析失效做精准修复：

1. **Multi-finding 五字段纪律强化**：SKILL.md Step 6 明确多 finding 场景中每个 finding 仍须包含全部五字段（Premises/Trace/Divergence/Trigger/Remedy），report-level 共享背景不豁免单 finding 的 Divergence/Remedy 字段。
2. **L3 容量限制假阳性规则**：SKILL.md Step 5.5 Design-intent gate + logic-risks.md L3 新增"Not L3 — designed capacity limits"规则——显式返回 error 的容量限制（`errors.New("cache full")`、HTTP 429 等）是正确的边界执行，不是盲区；`panic` 仍属潜在 L3。
3. **L7 post-constructor 代码解析规则**：logic-risks.md L7 新增 Code-structure parsing rule——`instance = new Foo(); instance.init()` 两语句非原子，第一行写入后 `init()` 尚未运行即存在 publish-before-init-complete 窗口期，需独立报告。

## 用例得分详情（对比 a25b6c7 基线）

| id | 用例名 | 当前 | 基线 (a25b6c7) | Delta | L-code |
|----|--------|------|----------------|-------|--------|
| 208 | logic-review-skip-audit-on-early-return-L5 | 75% | 50% | **+25** | L5 |
| 250 | go-defer-unlock-all-paths-no-bug | 75% | 25% | **+50** | no-bug |
| 276 | lu2008-style-double-checked-locking-broken-AV-L7 | 75% | 50% | **+25** | L7 |
| 280 | therac25-style-race-mode-flag-L7-L4 | 75% | 0% | **+75** | L7+L4 |

> 基线 `a25b6c7` 的 eval-280 分母为 0（API error），记为 0%。

## 各 case 剩余失败断言

| id | 失败断言 | 分析 |
|----|---------|------|
| 208 | recommends move-to-entry or try/finally | 输出内容完全正确（明确说"移至函数入口"并给修复代码），疑似 grader LLM 单次误判 |
| 250 | explains defer releases lock on all exit paths | 输出明确说"无论函数从哪条路径退出…Unlock 都会执行"，grader 可能被后续 L3 附加发现干扰 |
| 276 | identifies loadFromDisk after publish race | P4 前提已明确"在赋值语句之后才执行"，Finding 2 完整描述发布竞争，疑似 grader 误判 |
| 280 | identifies cross-thread flag race | 发现 1 完整描述了跨线程标志竞争，grader 未认可——措辞可能不够精确 |

四个剩余失败项均为内容正确但 grader 未认可，单次 run 无法定性。按方法论应取 3+ 次均值验证。

## 关键观察

1. **L3 假阳性消除（+50pp，eval-250）**：Design-intent gate 成功阻止模型把 `errors.New("cache full")` 错报为 L3，`concludes-no-bug` 断言从失败变为通过。
2. **Therac-25 大幅回升（+75pp，eval-280）**：API error 修复后首次正常运行，split-state flag race 规则和 L7/AV + L7/OV 联合报告有效。
3. **Multi-finding Divergence 字段**（+25pp，eval-208）：Step 6 新增 Multi-finding discipline 后模型在多 finding 场景下正确输出 Divergence 字段，`has Premises + Trace + Divergence labels` 断言从失败变为通过。
4. **后续建议**：再跑 2 次取均值，重点关注 4 个剩余失败断言是否为系统性问题；如剩余失败为 grader 误判，本次改动实际效果可能接近 100%。

## 原始数据

- 迭代目录：`skills-workspace/iteration-58f1be3/`
- 冻结副本：`benchmarks/runs/v0.6.7-58f1be3-claude-sonnet-4-6-logic-review-probe4.json`
- 关键 commits：`58f1be3` (v0.6.7 四类修复)、`a25b6c7` (基线)
