# Logic-Lens v0.4.0 — 架构重构 + 语言落地 + 触发精准化

## TL;DR

一次系统性"刮骨"：6 个 logic-* skill 底层架构重构，输出严格跟随用户语言，触发边界明确，prompt 精炼。`_shared/common.md` 升级为 12 节一体化单一来源；6 个 SKILL.md 全部精简，全部加上 SCOPE HARD RULE；新增 18 条扩展评测含中文用例与强制语言通过断言。

## 🎯 核心改进

### 1. 用户语言自动跟随（HIGHEST PRIORITY）

`common.md` § 1 落地"语言硬约束"：检测用户消息主要语言（CJK ≥ 50% 字符即中文），所有响应文本必须用同一语言 — 包含每一个 section header（`# Findings` / `## Summary` 等）、每个 finding 的四字段标签（Premises / Trace / Divergence / Remedy）、Summary 段落等。提供完整 16 项中英对照表（Findings → 发现，Premises → 前提，Logic Score → 逻辑评分 等）。

### 2. SCOPE HARD RULE — 触发精准化

每个 SKILL.md description 内嵌硬规则：

| 用户场景 | 触发的 skill |
|---|---|
| 单文件 / 单函数 + 怀疑有 bug | `logic-review` |
| 目录 / 模块 / 全仓库 | `logic-health` |
| confirmed failure（stack trace / 失败值 / 错误信息）| `logic-locate` |
| 两个版本对比 | `logic-diff` |
| 一段代码"为什么这样行为" | `logic-explain` |
| repo-wide 自动修复 | `logic-fix-all` |

去除全部 6 处 "Use this skill proactively whenever..." — 不再过度热切。

### 3. 架构去重（单一来源）

- **Iron Law** 集中到 `common.md` § 2，6 个 guide 改为引用。
- **Report Template** 集中到 `common.md` § 4（含中英本地化版），不再散落 health/SKILL.md 与 fix-all/SKILL.md。
- **Confidence 口径** `common.md` § 5 列 Mode-specific header variants，§ 7 列 High/Medium/Low Confidence Rubric。
- **Remedy Discipline** § 10 强约束：必须可粘贴（diff / 代码块），禁止散文式弱建议。

### 4. SKILL.md 全部精简

- description 从 ~25 行 → ≤ 12 行
- Process 加 Step 0：语言识别 + scope 路由
- `logic-fix-all/SKILL.md` 116 行 → 90 行（Process 不再重复 guide 细节）

### 5. 评测扩展

- `evals/v2/evals-v2.json`：18 条用例 = 6 EN（保留）+ 6 中文（语言通过强制断言）+ 6 深度（跨文件 L6 / 边界 / 系统性模式）

## 💥 Breaking Changes

无 — 所有重构保持 skill 命令名（`/logic-review` 等）和触发词不变。`.logic-lens.yaml` schema 兼容。

## 📊 评测数据（iteration-2，2026-04-25）

| 指标 | v0.3.0 | v0.4.0 | Δ |
|------|--------|--------|---|
| with_skill 执行完成率 | 3/6 | **9/9** | **+50 pp** |
| Assertion pass_rate | 1.00 (n=3) | **1.000 (38/38)** | 样本显著扩大 |
| 中文用例语言通过 | 0/0（无样本） | **6/6 = 100%** | 从无到满分 |

`logic-diff` / `logic-health` / `logic-fix-all` 三个 skill 在 v0.3.0 iteration-1 执行时全部返回 `null`（未完成）；v0.4.0 下全部产出符合 Report Template 的完整报告（Verdict / Module Breakdown / Fix Log + 修复前/后 Logic Score）。完整证据见 `skills-workspace/iteration-2/` 与 `skills-workspace/COMPARISON.md`。

## ⚠️ 已知遗留

- **Phase 4 触发描述自动优化（`run_loop.py` × 6）未跑** — 当前 6 个 SKILL.md 的 description 是按 SCOPE HARD RULE 手工精调的版本，未经过数据驱动优化。120 条 trigger eval 集（`evals/v2/trigger-evals-*.json`）已就绪，v0.5.0 补做。
- **`pr-review-toolkit:code-reviewer` agent 总审**未跑 — 建议 merge 前人工触发。
- **6 DEEP 深度用例**（跨文件 L6 / 异步 microtask / Go nil interface / flaky race / 系统性 L6 / 共享根因 dedupe）未在本轮验证，留作 v0.4.1 hygiene。

## 📦 升级

Claude Code 用户：
```bash
/plugin update logic-lens
```

手动 clone：
```bash
cd /path/to/logic-lens
git pull
bash hooks/session-start  # 重新安装 command wrappers
```

## 🙏 致谢

本次重构由 Claude Opus 4.7 (1M context) 驱动 — 完整审阅报告、架构提案、SKILL.md 精简、评测设计、CHANGELOG 与 release notes 均自动生成。

🤖 Generated with [Claude Code](https://claude.com/claude-code)
