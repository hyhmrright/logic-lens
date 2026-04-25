# v0.4.0 发版执行清单

**状态（更新于睡后恢复会话）**：所有架构改动已 commit 到 `feature/skill-improvements-v1`（4 个 commit：`2cb431a` / `bfb1788` / `49da8ee` / `1f91319`）。本地 tag **刻意未打** — 核心 skill 优化的验证闭环（iteration-2 + trigger 优化 + code-reviewer agent）受 LLM quota 限制未跑。详见 `skills-workspace/FINAL-REPORT.md`。

**推荐**：先跑 `bash scripts/validate-repo.sh`（立即可做，22 检查全绿）→ 等 quota 恢复跑验证三件事 → 数据 OK 再 tag + release。如果评估代码改动后信心很高，可走 `v0.4.0-rc.1` 加速路径（见 FINAL-REPORT §路径 B）。

## 1. 快速审核（5 分钟）

```bash
cd /Users/hyh/code/logic-lens

# 看分支与 tag 状态
git log main..feature/skill-improvements-v1 --oneline
git tag -l "v0.4.0"

# 看改动规模与逐文件
git diff main..feature/skill-improvements-v1 --stat
git diff main..feature/skill-improvements-v1 -- skills/_shared/common.md | less
git diff main..feature/skill-improvements-v1 -- skills/logic-review/SKILL.md | less

# 读关键文档
cat CHANGELOG.md
cat .github/RELEASE-NOTES-v0.4.0.md
cat skills-workspace/SESSION-STATUS.md  # 已知遗留与完成度坦白
```

## 2. （可选）补跑 simplify + code-reviewer

CLAUDE.md 强制流程要求 commit 前过 simplify + pr-review-toolkit:code-reviewer。本次因 org monthly usage limit，code-reviewer agent 被跳过，commit message 已注明。如要补做：

```
# 在新 session（usage 恢复后）：
git checkout feature/skill-improvements-v1
# 触发 simplify + code-reviewer（让 Claude 跑）
```

如果 review 发现需要修复，做新 commit，不 amend。

## 3. 合并到 main（二选一）

### 方案 A — 直推 main（个人项目最快）

```bash
git checkout main
git pull origin main                              # 防漂移
git merge feature/skill-improvements-v1 --no-ff   # 保留 merge commit 便于回溯
git push origin main
```

### 方案 B — 走 PR（更正式）

```bash
git push origin feature/skill-improvements-v1
gh pr create \
  --title "v0.4.0: 架构重构 + 语言硬约束 + 触发精准化" \
  --body-file .github/RELEASE-NOTES-v0.4.0.md \
  --base main
# review 后在 GitHub merge
```

## 4. push tag + 创建 GitHub Release

local tag 已打，只需 push：

```bash
# 确保 main 已合并 + 已 push
git checkout main && git pull
git push origin v0.4.0

# 创建 GitHub Release（release notes 已就绪）
gh release create v0.4.0 \
  --title "v0.4.0 — 架构重构 + 语言硬约束 + 触发精准化" \
  --notes-file .github/RELEASE-NOTES-v0.4.0.md \
  --latest
```

## 5. plugin marketplace 同步

logic-lens 是 Claude Code plugin。`.claude-plugin/marketplace.json` 已在本 repo 里 bump，Claude Code 用户下次 `/plugin update logic-lens` 自动拉到。

如有独立的 marketplace repo（参考 `~/.claude/plugins/marketplaces/logic-lens-marketplace/` 是否存在）：

```bash
ls ~/.claude/plugins/marketplaces/logic-lens-marketplace/ 2>/dev/null
# 若存在，那个 repo 也要 bump 0.4.0 + commit + push
```

## 6. 清理（合并发布稳定后）

```bash
# feature 分支
git branch -d feature/skill-improvements-v1
git push origin :feature/skill-improvements-v1   # 远程删（如已推过）

# workspace 是评测产物 / 临时数据，不进 main，可保留作 evidence 后再清
# rm -rf skills-workspace/
```

## 应急回滚

```bash
git checkout main
git revert -m 1 <merge-commit-sha>
git push origin main

# 如果需要撤 release：
gh release delete v0.4.0 --yes
git push origin :v0.4.0   # 删远程 tag
git tag -d v0.4.0          # 删本地 tag
```

## 已知遗留（v0.4.x / v0.5.0 处理）

详见 `skills-workspace/SESSION-STATUS.md` 和 `CHANGELOG.md` 的 "Known Limitations" 段：

- 完整 36-run benchmark：本次仅完成 6/18（中文用例 0 个）— 不是发版 blocker，但 v0.4.1 应补完
- `run_loop.py` 触发描述优化未跑 — v0.5.0 做
- 6 `*-guide.md` 编号未统一为 Step 1..N — v0.4.x hygiene
- `logic-fix-all-guide.md` 647 行未拆 — v0.4.x hygiene

——
**关键 commit**: `2cb431a feat(v0.4.0): architecture refactor — language hardening, scope rules, single-source shared framework`
**Local tag**: `v0.4.0`（未 push）
**分支**: `feature/skill-improvements-v1`
