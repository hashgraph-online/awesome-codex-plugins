---

name: boss:tasks
description: "从任务拆解开始：Scrum Master 将架构/需求拆分为可执行任务，默认自动续跑后续环节（开发 → 测试 → 部署）。"
allowed-tools: Task, Read, Write, Edit, Bash, Glob, Grep
---

# /boss:tasks — 任务拆解（Scrum Master）

`/boss:tasks` 是专家小队的**任务拆解入口**。以 Scrum Master 身份基于 `plan.md` 实施计划，产出文件级别的 `tasks.md`。

**默认行为**：任务拆解完成后自动续跑后续所有环节，除非用户主动叫停。

## 适合 / 不适合

| 适合 `/boss:tasks`                            | 不适合                              |
| --------------------------------------------- | ----------------------------------- |
| 已有实施计划（plan.md），需要拆成原子开发任务 | 需求还不清晰（用 `/boss:pm`）       |
| 想明确开发范围和写集                          | 只想做技术评审（用 `/boss:review`） |

## 前置输入

- **主要输入**：`.boss/<slug>/plan.md`（实施计划，含模块划分和任务拆解指引）
- 辅助输入：`.boss/<slug>/tech-review.md`、`.boss/<slug>/architecture.md`
- 若 plan.md 不存在，可用 `tech-review.md` + `architecture.md` + `prd.md` 或用户直接描述的需求替代

## 执行步骤

1. **Feature slug 归一化**：确定 feature slug。
2. **读取输入**：优先读 `plan.md`（模块划分、任务拆解指引），其次 `tech-review.md` + `architecture.md`，最后 `prd.md`。
3. **Repo Preflight**：探测项目事实（Git 状态、CI、测试脚本、技术栈），写入 `tasks.md`。
4. **派发 Scrum Master Agent**：读取 `agents/boss-scrum-master.md`，产出 `.boss/<slug>/tasks.md`。
   - 基于 plan.md 的模块划分和建议任务，细化到文件级别
   - 必须包含：任务分解、文件级写集、测试用例定义、风险分级、Blast Radius、Evidence Wave 拆分、Contract Matrix。
5. **自检**：对照 Scrum Master 的硬性要求检查。
6. **续跑**：读取 `references/continuation-chain.md`，按链执行下一步（dev），除非用户叫停。

## 用法

```
/boss:tasks user-auth
/boss:tasks 做一个素材管理工具
```

## 选项

| 参数                  | 说明                |
| --------------------- | ------------------- |
| `--stop-after <环节>` | 跑到指定环节后停    |
| `--lang <zh\|en>`     | 产物语言（默认 zh） |
