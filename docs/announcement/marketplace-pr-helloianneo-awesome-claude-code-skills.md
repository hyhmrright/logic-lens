# PR Draft: helloianneo/awesome-claude-code-skills

## Status

CONFIRMED EXISTS (substituted for non-existent Pi-Cla/awesome-claude-code-skills).
91 stars, Chinese-language curated list, updated 2026-04-23. Accepts PRs or Issues.

## File to Modify

`README.md` — add a row to the `## 代码质量` (Code Quality) table.

---

## Exact Table Row to Add

In the `## 代码质量` section, append after the last row:

```markdown
| [Logic-Lens](https://github.com/hyhmrright/logic-lens) | hyhmrright | 强推 | 半形式化执行追踪，捕捉 linter 看不到的逻辑 bug（隐式名遮蔽、类型契约违反、边界遗漏等 L1–L6 风险类），六个命令覆盖审查/解释/对比/定位/健康检查/全自动修复 | `npx skills add hyhmrright/logic-lens@logic-review` |
```

Current table (for context — add after the Code Review row):

```markdown
| Skill | 作者 | 推荐 | 一句话 | 安装 |
|-------|------|------|--------|------|
| [Superpowers](https://github.com/obra/superpowers) | obra | 必装 | TDD / 并行 Agent / 代码审查 / Git 工作流，一套全有 | `npx skills add obra/superpowers` |
| [Code Review](https://skills.sh/supercent-io/skills-template/code-review) | Supercent | 强推 | 自动代码审查（注释 / 测试 / 类型 / 质量） | `npx skills add supercent-io/skills-template@code-review` |
| [Logic-Lens](https://github.com/hyhmrright/logic-lens) | hyhmrright | 强推 | 半形式化执行追踪，捕捉 linter 看不到的逻辑 bug（隐式名遮蔽、类型契约违反、边界遗漏等 L1–L6 风险类），六个命令覆盖审查/解释/对比/定位/健康检查/全自动修复 | `npx skills add hyhmrright/logic-lens@logic-review` |
```

---

## PR Title

```
feat: 添加 Logic-Lens — 半形式化逻辑审查 skill
```

Or in English (if the maintainer prefers):

```
feat: add Logic-Lens — logic-first code review via semi-formal execution tracing
```

---

## PR Body

```markdown
## 改动说明

在「代码质量」分类下新增 [Logic-Lens](https://github.com/hyhmrright/logic-lens)。

Logic-Lens 是一个逻辑优先的代码审查 skill，通过半形式化执行追踪，捕捉 linter 和类型检查器都发现不了的逻辑 bug：

- L1 — Shadow Override（隐式名遮蔽：模块级 `format` 遮蔽 builtin、import 改写内置类型等）
- L2 — Type Contract Breach（类型契约违反：`Optional[str]` 当 `str` 用、None 流入 `.upper()` 等）
- L3 — Boundary Blindspot（边界条件遗漏：空集合除法、首尾元素、最大/最小值未覆盖）
- L4 — State Mutation Hazard（状态变更隐患：迭代中改容器、aliasing、双阶段 reservation 非原子）
- L5 — Control Flow Escape（控制流逃逸：异常路径漏 `close()`、`return` 跳过 cleanup）
- L6 — Callee Contract Mismatch（调用契约不一致：调用方假设 callee 不返回 None、不抛异常等）

六个斜线命令：`/logic-review`、`/logic-explain`、`/logic-diff`、`/logic-locate`、`/logic-health`、`/logic-fix-all`。

- 项目地址：https://github.com/hyhmrright/logic-lens
- 最新版本：v0.5.0 — https://github.com/hyhmrright/logic-lens/releases/tag/v0.5.0
- eval 通过率：58/58 assertions（Opus 4.7 + Sonnet 4.6 双模型验证）
- 协议：MIT

## 安装验证

```bash
# 安装
/plugin install logic-lens@hyhmrright/logic-lens

# 验证（对任意有边界逻辑的函数运行）
/logic-review
```
```

---

## Prerequisites / Gotchas

- **No CONTRIBUTING.md**: The repo has no contribution guidelines. Submission is via Issue or PR per the README footer: "发现好用的 Skill 但这里没收？欢迎提 Issue 或 PR。"
- **No merged community PRs visible**: Cannot assess maintainer cadence from PR history alone. Repo was last updated 2026-04-23, suggesting active maintenance.
- **Chinese-language repo**: PR body in Chinese is preferred; English is acceptable.
- **推荐等级 rationale**: Rated `强推` (highly recommended) rather than `必装` (must-install) because Logic-Lens is specialized for logic review rather than general workflow; matches the same tier as the existing Code Review entry.
- **Install command format**: The list uses `npx skills add <owner>/<repo>@<skill>` format — Logic-Lens supports this via its `.claude-plugin/plugin.json`.

---

## Maintainer Responsiveness Signal

- 91 stars, last updated 2026-04-23 (2 days before this draft)
- No visible merged PRs — owner appears to maintain it solo
- Low barrier: simple README table addition, no validation bot
- Fastest path: open a PR directly with the table row change
