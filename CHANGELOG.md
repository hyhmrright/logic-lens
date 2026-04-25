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

### Also in v0.4.0 (delivered across commits `bfb1788` / `49da8ee` / `1f91319`)

- **`_shared/report-template.md`** — single-source Report Template file. Full English + Chinese layouts + 5 rendering rules. All six skills render by referencing this file (common.md §4 now points here instead of inlining).
- **`_shared/semiformal-checklist.md`** — single-source Premises Construction Checklist. Four sections (Name Resolution / Type Contracts / State Preconditions / Control Flow Assumptions) with anti-cheat notes. review/explain/diff guides now reference this rather than re-list.
- **Guide Step numbering unified** — `logic-locate-guide.md` normalized from 1/2/3/4a/4b/5/6 to a flat 1..7. All six guides use the same numbering scheme.
- **`logic-fix-all-guide.md` split** — 647-line guide decomposed into a 68-line navigation file + three phase-detail files (`guide-phases-0-2-consent-scope-health.md` / `guide-phases-3-5-review-locate-clarify.md` / `guide-phases-6-9-fix-iterate-report.md`). Readers load only the phase they need.
- **120-case trigger eval set** — `evals/v2/trigger-evals-<skill>.json` × 6 (20 per skill, 10 positive + 10 near-miss negative). Surface for `skill-creator` description-optimization via `run_loop.py`.
- **`scripts/`** infrastructure — `validate-repo.sh` (offline 22-check sanity) + `run-trigger-evals.sh` (wrapper around `skill-creator/scripts/run_loop.py`) + README. `package.json` scripts updated to point at them.

### Verification data (iteration-2 against v0.4.0 SKILL.md)

9-case evaluation batch covering 6 ZH (new language-assertion cases) + 3 EN cases that v0.3.0 iteration-1 had left unfinished (diff / health / fix-all). Machine-graded via `scripts/grade-iteration.py` against the assertions in `evals/v2/evals-v2.json`. Full artifacts under `skills-workspace/iteration-2/` (summary.json + per-case grading.json + COMPARISON.md).

| Metric | v0.3.0 (iteration-1) | v0.4.0 (iteration-2) | Δ |
|---|---|---|---|
| with_skill execution completion | 3/6 | **9/9** | **+50 pp** |
| Assertion pass_rate | 1.00 (n=3 only) | **1.000 (38/38)** | sample widened |
| Chinese-language assertion | 0/0 (no samples) | **6/6 = 100%** | from nothing to full |

v0.3.0 had three skills (`logic-diff` / `logic-health` / `logic-fix-all`) whose with_skill runs returned `null` in iteration-1. All three now produce structured reports with the correct mode-specific header (Verdict / Module Breakdown / Fix Log + before/after Logic Score) and pass every assertion.

### Known Limitations (deferred to v0.4.1 / v0.5.0)

- **Phase 4 trigger-description optimization (`run-trigger-evals.sh`) was not executed** — the 6 SKILL.md descriptions in v0.4.0 are hand-tuned against the SCOPE HARD RULE rubric, not data-optimized via `run_loop.py`. The 120-case trigger eval set (`evals/v2/trigger-evals-*.json`) is ready for v0.5.0.
- **`pr-review-toolkit:code-reviewer` agent** was not run on the full v0.4.0 diff — recommend running manually before merging to main.
- **6 DEEP cases** (cross-file L6, async resolution, Go nil interface refactor, flaky race, systemic cross-module L6, shared-root-cause dedupe) were not part of this verification batch — left for v0.4.1 hygiene.

## [0.3.0] — 2026-04

- **logic-fix-all** 重构为完整仓库编排管道（autonomous audit-and-fix）。

## [0.2.0]

- 新增 **logic-fix-all** skill。

## [0.1.x]

- 初始 5 skill 套件：logic-review / logic-explain / logic-diff / logic-locate / logic-health。
- Karpathy guideline 审计：去除冗余、增强清晰度。
