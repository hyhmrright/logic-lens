# Changelog

All notable changes to Logic-Lens are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [SemVer](https://semver.org/).

## [0.4.0] — 2026-04-25

### Changed (架构重构 / Architecture refactor)

- **`_shared/common.md` 一体化**：12 节结构覆盖语言硬约束、Iron Law、Report Template、Mode-specific header 变体、Logic Score、Confidence Rubric、Scope Management、Remedy Discipline、Fallback Behavior、`.logic-lens.yaml` 配置矩阵 — 单一来源，去除多文件重复。
- **6 个 SKILL.md 全部精简**：description 从 ~25 行压到 ≤ 12 行；新增 **SCOPE HARD RULE**（单文件 / 单函数 → review；目录 / 模块 → health；confirmed failure → locate；两版本 → diff；repo-wide → fix-all）；去掉 "proactively whenever" 措辞；Process 第 0 步统一为"语言识别 + scope 路由"。
- **logic-fix-all/SKILL.md** 从 116 行压到 90 行，细节下沉到 guide。

### Added (新能力)

- **语言硬约束（HIGHEST PRIORITY）**：识别用户输入语言，所有响应（含 section header、四字段标签 Premises/Trace/Divergence/Remedy、Summary 段）必须用同一语言；提供完整中英 header 对照表（Findings → 发现，Premises → 前提，Logic Score → 逻辑评分 等 16 项）。
- **Mode-specific header 变体表**：明确 review/health 用 Logic Score，locate 用 Fault Confidence，diff 用 Verdict。
- **Confidence Rubric 统一**：High/Medium/Low 跨 skill 同口径定义。
- **Remedy Discipline 强约束**：Remedy 必须可粘贴（diff 或代码块），禁止散文式 "add validation" 这类弱建议。
- **`evals/v2/evals-v2.json`**：18 条扩展评测（6 EN + 6 中文 + 6 深度 / 跨文件 / 边界），中文用例含强制语言通过断言。

### Fixed (问题修复)

- **Iron Law 多处重复定义** → 集中到 `common.md` § 2 单一来源，guide 通过引用。
- **Report Template 散落三处**（common.md / health/SKILL.md / fix-all/SKILL.md）→ 统一到 `common.md` § 4。
- **Confidence 口径不一**（review 用 Score / locate 用 Fault Confidence / diff 用 Verdict）→ `common.md` § 5 集中变体表。
- **触发过度热切** → 移除全部 6 处 "Use this skill proactively whenever..." 模式，改为基于 SCOPE 的硬规则触发。
- **中文输入收到英文 Report** → 通过 § 1 语言硬约束 + § 4 中英 header 对照表 + 各 SKILL.md Step 0 路由三层强制落地。

### Known Limitations

- 本版本主评测 baseline 仅完成 6/18 个 case 的初步验证（外部资源限额所致），完整 36-run 对比与 trigger eval 优化推迟到 v0.4.1 / v0.5.0。
- `logic-locate-guide.md` 的 Step 4a/4b 与 `logic-fix-all-guide.md` 647 行未拆分尚为后续 hygiene 工作。

## [0.3.0] — 2026-04

- **logic-fix-all** 重构为完整仓库编排管道（autonomous audit-and-fix）。

## [0.2.0]

- 新增 **logic-fix-all** skill。

## [0.1.x]

- 初始 5 skill 套件：logic-review / logic-explain / logic-diff / logic-locate / logic-health。
- Karpathy guideline 审计：去除冗余、增强清晰度。
