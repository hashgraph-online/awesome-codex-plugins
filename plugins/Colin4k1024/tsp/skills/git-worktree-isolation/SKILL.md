---
name: git-worktree-isolation
description: >
  基于 Git Worktree 的任务隔离工作流：每个开发任务在独立 worktree 中执行，
  确保主工作区干净、并行任务互不干扰，完成后结构化决策合并/PR/保留/丢弃。
  与 parallel-execution 的 worktree 基础设施互补，本 skill 聚焦任务级隔离策略。
origin: superpowers-using-git-worktrees + harness-engineering
---

# Git Worktree Isolation

## 用途

- 确保每个开发任务（feature / fix / spike）在 **隔离的 worktree + 分支** 中执行，主工作区始终保持可切换状态。
- 在多 agent 并行场景下，每个 agent 拥有独立文件系统视图，避免写冲突。
- 任务完成后提供 **结构化收口决策**（merge / PR / keep / discard），而不是任凭 worktree 积累。

## 触发信号

- `/team-execute` 分派的并行实现任务。
- `wave-execution` 中同一 Wave 的多个工作项。
- 需要在不影响主分支的情况下进行探索性实现或 spike。
- 当前工作区有未提交变更，但需要紧急处理另一个任务。
- Code review 后的修改需要在隔离环境中完成。

## 核心原则

1. **一个任务 = 一个 worktree = 一个分支**——不共用 worktree。
2. **worktree 有明确生命周期**——创建时绑定任务 ID，完成后必须做收口决策。
3. **主工作区是调度中心**——编排和合并在主工作区进行，实现在 worktree 中进行。

## 工作流

### 1. 创建隔离环境

```bash
# 命名规则: .worktrees/{slug}-{task-id}
git worktree add .worktrees/{slug}-{task-id} -b task/{slug}/{task-id}

# 验证隔离
cd .worktrees/{slug}-{task-id}
git branch --show-current   # → task/{slug}/{task-id}
```

**命名约定：**

| 元素 | 格式 | 示例 |
|------|------|------|
| Worktree 路径 | `.worktrees/{slug}-{task-id}` | `.worktrees/auth-T001` |
| 分支名 | `task/{slug}/{task-id}` | `task/auth/T001` |
| Spike 分支 | `spike/{slug}/{description}` | `spike/auth/oauth-flow` |

### 2. 在 worktree 中执行

```
进入 worktree 目录 →
  加载任务上下文（STATE.md 对应工作项）→
  执行实现 →
  运行测试 →
  提交到 worktree 分支
```

**执行约束：**

- 每个 worktree 中的 agent 只操作任务范围内的文件。
- 不在 worktree 中修改共享配置（package.json / pom.xml 等），除非任务明确要求。
- 提交信息包含任务 ID：`feat(T001): implement auth flow`。

### 3. 收口决策

任务完成后，在 **主工作区** 执行收口：

| 决策 | 条件 | 操作 |
|------|------|------|
| **Merge** | 代码通过 review + 测试 | `git merge task/{slug}/{task-id}` + 清理 worktree |
| **PR** | 需要异步 review 或 CI | 创建 PR + 保留 worktree 直到合并 |
| **Keep** | 任务暂停但稳定 | 标记为 `paused`，保留 worktree |
| **Discard** | spike 完成或方向废弃 | 删除 worktree + 分支 |

```bash
# Merge 路径
cd /path/to/main-worktree
git merge --no-ff task/{slug}/{task-id} -m "feat(T001): implement auth flow"
git worktree remove .worktrees/{slug}-{task-id}
git branch -d task/{slug}/{task-id}

# Discard 路径
git worktree remove --force .worktrees/{slug}-{task-id}
git branch -D spike/{slug}/{description}
```

### 4. 清理巡检

定期（或每次 `/team-review` 前）执行清理：

```bash
# 列出所有 worktree
git worktree list

# 清理已删除的 worktree 引用
git worktree prune

# 查找已合并但未清理的任务分支
git branch --merged main | grep 'task/'
```

## 与 parallel-execution 的关系

| 关注点 | parallel-execution | git-worktree-isolation |
|--------|-------------------|----------------------|
| 核心目标 | 多实例并行加速 | 任务级文件隔离 |
| Worktree 使用 | 作为并行基础设施 | 作为隔离策略 |
| 分支管理 | 自动创建/合并 | 结构化收口决策 |
| 清理策略 | 任务结束自动清理 | 显式四选一决策 |
| 集成点 | wave-execution 调用 | 为 parallel-execution 提供隔离规范 |

`parallel-execution` 调用 `git-worktree-isolation` 的隔离规范创建 worktree，`git-worktree-isolation` 依赖 `parallel-execution` 的任务分发能力。

## 与 session-continuity 的关系

- `/pause` 时：记录活跃 worktree 列表到 HANDOFF.json 的 `active_worktrees` 字段。
- `/resume` 时：检查 worktree 状态，标记哪些仍然有效、哪些需要清理。

## 配套约束

1. `.worktrees/` 目录加入 `.gitignore`，不提交到远程仓库。
2. worktree 中不执行 `git rebase` 主分支——避免在隔离环境中引入合并复杂度。
3. 超过 7 天未活动的 worktree 在清理巡检时标记为候选清理项。
4. 共享锁文件（lockfile）变更在 merge 阶段统一解决，不在 worktree 中各自更新。

## 验证标准

- [ ] 创建的 worktree 路径遵循 `.worktrees/{slug}-{task-id}` 命名规范
- [ ] 每个 worktree 对应唯一分支，无分支共用
- [ ] 任务完成后在 24h 内执行收口决策（merge / PR / keep / discard）
- [ ] `git worktree list` 无孤立 worktree
- [ ] 已合并分支已被删除
