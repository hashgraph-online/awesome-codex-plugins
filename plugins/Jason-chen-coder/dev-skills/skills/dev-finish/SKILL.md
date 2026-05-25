---
name: dev-finish
description: Use when implementation and verification are complete and the user needs to finish a development branch by merging locally, creating a PR, keeping the branch, or discarding work. Applies after tests pass and code review is ready.
---

# Dev Finish

Branch completion workflow. The goal is to make the last mile explicit: verify, inspect git state, present safe choices, then execute only what the user selects.

This skill does not implement code, write tests, or review code. Run `dev-verify` and `dev-code-review` first unless the user explicitly overrides.

---

## Step 0 — Load baseline

执行前先加载 `references/dev-baseline.md`。**不假设**、**最小代码**、**外科手术式改动**、**可验证成功标准** 全程生效。

baseline 与本 skill 的关联:
- **不假设** —— 不替用户决定 merge / PR / keep / discard。
- **可验证成功标准** —— 完成分支前必须有 fresh verification evidence。
- **外科手术式改动** —— 不顺手清理未被确认的分支、stash、worktree。

---

## Step 1 — Preflight verification

先确认:
1. `dev-verify` 已给出当前回合的 PASS 证据,或你现在运行等价验证。
2. `dev-code-review` verdict 是 READY,或用户明确接受跳过 review 的风险。
3. `git status --short` 已读取,知道是否有未提交改动。

如果测试或 review 未通过,停止:

```
不能 finish: <tests/review/status> 未通过。
下一步: 修复后重跑 dev-verify / dev-code-review。
```

---

## Step 2 — Detect workspace state

运行只读命令:

```bash
git status --short
git branch --show-current
git rev-parse --show-toplevel
git rev-parse --git-dir
git rev-parse --git-common-dir
```

判断:
- 普通 checkout:`git-dir == git-common-dir`
- linked worktree:`git-dir != git-common-dir`
- detached HEAD:`git branch --show-current` 为空

如果工作区有未提交改动,先问用户是否要 commit / stash / keep uncommitted。不要继续 merge / PR。

---

## Step 3 — Determine base branch

优先探测:

```bash
git merge-base HEAD main
git merge-base HEAD master
git remote -v
```

如果无法判断 base branch,问用户确认。不要默认推送到未知目标。

---

## Step 4 — Present choices

普通分支输出四选一:

```
分支已验证。请选择:

1. 本地 merge 回 <base-branch>
2. push 当前分支并创建 PR
3. 保留当前分支,我稍后自己处理
4. 丢弃这个分支的工作

你选哪一个?
```

Detached HEAD 输出三选一:

```
当前是 detached HEAD。请选择:

1. 新建分支后 push 并创建 PR
2. 保留当前 workspace,我稍后自己处理
3. 丢弃这个 workspace 的工作

你选哪一个?
```

不要在同一步执行动作。等用户选择。

---

## Step 5 — Execute selected option

### Option 1: merge locally

1. 切到 base branch。
2. pull 最新 base。
3. merge feature branch。
4. 在 merge 后结果上重新运行关键验证。
5. merge 成功且验证通过后,再考虑删除分支 / 清理 worktree。

禁止在 merge 成功前删除任何东西。

### Option 2: push and create PR

1. `git push -u origin <branch>`
2. 用仓库现有 PR 工具创建 PR。
3. PR body 必须包含 Summary 和 Test Plan。
4. 不清理 worktree,因为后续可能要处理 review。

### Option 3: keep as-is

报告 branch 和 path。不要清理。

### Option 4: discard

必须要求用户输入精确确认:

```
这会删除:
- branch: <branch>
- commits: <commit list>
- worktree: <path, if owned>

请输入 discard 确认。
```

没有精确 `discard` 就停止。

---

## Step 6 — Worktree cleanup rules

只在用户选择 merge 后清理或 discard 后清理。

只能清理明确由项目拥有的 worktree:
- `.worktrees/`
- `worktrees/`
- `~/.config/dev-skills/worktrees/`

不清理平台 / harness 拥有的 workspace。无法判断归属时保留并报告。

---

## Hard rules

- 测试或 review 未过,不 finish。
- 不替用户选择 merge / PR / keep / discard。
- 丢弃必须有精确确认。
- 不在 merge 成功前删除 branch 或 worktree。
- PR 路径不清理 worktree。
- 无法判断 base branch 或 workspace 归属时,先问。

---

## Multi-Agent Note

`dev-finish` is main-agent-controlled because it can merge, push, create PRs, keep branches, or discard work.

Sub-agents may provide verification or review evidence before this phase, but final branch decisions and destructive operations stay with the main agent and the user. Follow `../../docs/multi-agent-policy.md` before relying on any delegated verifier or reviewer output.
