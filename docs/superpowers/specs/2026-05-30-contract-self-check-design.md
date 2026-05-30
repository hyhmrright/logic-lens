# Contract Self-Check — Step 7.5 设计

**日期**：2026-05-30
**目标 skill**：`logic-review`
**版本基线**：v0.6.9（commit `fe9a1aa`）

## 1. 问题

离线重打分（`skills-workspace/iteration-v0.6.9-fe9a1aa/`，零 token，run 即当前 HEAD）暴露的拆分基线：

| 指标 | 值 |
|------|-----|
| overall | 78.3% |
| **logic 子分** | **84.6%** |
| **format 子分** | **61.1%** ← 瓶颈 |

format 才是拖累项，不是 logic。

### 根因

7/7 个 `format=0.00` 用例**全挂在同一条 grader 规则**：缺少字面标签 `Premises/前提` + `Trace/追踪` + `Divergence/偏差`（grader `_FOUR_FIELD_RULE`，`scripts/grade-iteration.py:188-196`）。模型输出语义完整，但用了变体：

- eval-208：表格里写 "Buggy Premise"（单数）→ `Premises` 子串不命中
- eval-279：用"触发路径"代替"追踪"、整块降级成自由格式

### 决定性事实：散文警告已被证明无效

benchmark run（`fe9a1aa`，2026-05-24 20:58）跑的就是当前 HEAD 的 SKILL.md。点名 eval-279/252/201 的详尽 Output Skeleton Contract 警告，在 5/24 **之前**就已加好（`ed85087` 5/17、`3a9ab19` 5/23）。git 历史显示 5/17→5/23 连续 4 次提交（`8dd2403`/`ed85087`/`58f1be3`/`3a9ab19`）都在用"加更强的散文警告"修格式——结果仍是 61.1%。**「再加一段更狠的生成前警告」这条路已走到头。**

### 「一改两收」边界

| 子集 | logic 失分项 | 与 format 同根 |
|------|-------------|---------------|
| no-bug（250/253，可能含 249） | "concludes no lock leak / injection" | ✅ 失的就是 `Divergence: None — [原因]` 这一行；补齐骨架 = format + logic 一起回收 |
| 有 bug（208/232/276/279） | 误标 L-code、漏第二处发现、漏 recommendation | ❌ 独立真实推理缺陷，骨架修不了 |

## 2. 方案 A：定稿前自审步骤（Step 7.5）

与前 4 次失败的差异**在时机与机制**，不在语气：把"生成前要记住的规则"变成"对已写文本的审计动作"。模型渲染完草稿后回看自己刚写的具体文本，是不同的认知时刻——此刻它是审计员而非生成者。再要求它**外显一行核对结论**，使该步无法被静默跳过。

### 诚实声明（范式局限）

skill 范式内没有"模型外后处理脚本"这种硬保证；Step 7.5 仍是给模型的指令，无法 100% 保证依从。机制改进在于审计时机 + 外显结论，依从率应显著高于生成前警告。验证靠下方廉价手检，不靠承诺。

## 3. 改动清单

两处，均在 `skills/logic-review/`，**不动 grader / evals / report-template**：

### 3a. `SKILL.md` — Process 段，Step 7 与 Step 8 之间插入一行

```
**Step 7.5. Contract Self-Check** (guide Step 7.5) — before emitting, re-read your own
rendered draft and audit each `## Findings` block against the five literal labels. Confirm
`Premises:`/`Trace:`/`Divergence:`/`Trigger:`/`Remedy:` (中文 `前提：`/`追踪：`/`偏差：`/`触发：`/`修复：`)
each appear as a line-starting prefix inside the block — not as a heading, table cell, or
paraphrase ("Buggy Premise", "执行路径", "触发路径", "结论"). Any miss → rewrite that block from
the template before output. This audits concrete text you already wrote; it is not satisfied
by remembering the rule.
```

### 3b. `logic-review-guide.md` — `## Step 7` 与 `## Step 8` 之间插入 `## Step 7.5: Contract Self-Check`

机制：

- **7.5a** 扫描刚渲染的草稿，对每个 finding block 逐条核对：
  - ☐ `Divergence:`/`偏差：` 行首出现？（#1 失败模式）
  - ☐ `Premises:`/`前提：` 行首？（不是 "Buggy Premise"、"前置条件"）
  - ☐ `Trace:`/`追踪：` 行首？（不是 "执行路径"、"触发路径"）
  - ☐ `Trigger:`/`触发：`（Critical/Warning）与 `Remedy:`/`修复：` 齐全？
- **7.5b** no-bug 结论必须用 `Divergence: None — [原因]`/`偏差：无——[原因]`，不是 "未发现问题"/"结论：安全" 这类散文。
- **7.5c** 任一缺失/被改写 → 用 `report-template.md` 的模板块重写该 finding，**再**进入输出。
- **7.5d** 审计通过后，外显一行 token-free 自检结论（见下方防护 1）。

### 防护（硬约束，写进 guide）

1. **自检结论必须 token-free**：核对结论只能写成 `字段自检：2 findings 五字段均行首齐全 ✓` 这类**不含** `Premises`/`Trace`/`Divergence` 字面词的形式。否则自检行本身会命中 grader 子串匹配 = 伪造合规 = 放宽/欺骗 grader（违反项目红线）。此约束确保 grader 只在**真实 finding 块**含标签时才通过——保持修复诚实。
2. 自检结论放报告**末尾 HTML 注释**或报告前一行前言（token-free），证明"查过"而不污染报告结构。

## 4. 验证与成功标准

- **廉价手检（先做）**：in-session 单跑标志用例 **279 / 208 / 250**，看骨架是否回来。
- **成功标准**：
  - 三个用例的 `has Premises+Trace+Divergence labels` 断言 FAIL→PASS；
  - no-bug 用例 250 的 "concludes no lock leak" 同步 FAIL→PASS（验证一改两收）。
- **回归红线**：不得为提分改 grader/evals。手检通过后，由用户决定是否烧 token 跑全量 content-evals 锁定基线。

## 5. 非目标（YAGNI）

- 不修 bug 子集的真实推理缺陷（208 L5/L7 误标、276 漏 publish race 第二面）——独立工作，本 spec 不含。
- 不改 grader 匹配逻辑、不放宽 format 规则。
- 不动其他 5 个 skill（先在 logic-review 验证有效再考虑外推）。
