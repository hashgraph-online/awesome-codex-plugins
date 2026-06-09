# dev-finish · Examples

## 例 1 — 正常 PR 收尾

前置:
- `dev-verify` 通过
- `dev-code-review` READY
- 当前分支 `feat/user-export`

期望输出:

```
分支已验证。请选择:

1. 本地 merge 回 main
2. push 当前分支并创建 PR
3. 保留当前分支,我稍后自己处理
4. 丢弃这个分支的工作

你选哪一个?
```

用户选 2 后:
- push branch
- 创建 PR
- 保留 worktree

## 例 2 — tests failed

如果 preflight 里测试失败:

```
不能 finish: npm test 失败(2 failures)。
下一步: 修复失败测试后重跑 dev-verify / dev-code-review。
```

不要展示 merge / PR 选项。

## 例 3 — discard

用户选 discard 时必须要求精确输入 `discard`。`yes`、`确认`、`ok` 都不够。
