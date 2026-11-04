---

name: boss:review
description: "从技术评审开始：Tech Lead 做技术评审与风险评估，默认自动续跑后续环节（任务 → 开发 → 测试 → 部署）。"
allowed-tools: Task, Read, Write, Edit, Bash, Glob, Grep
---

# /boss:review — 技术评审与实施计划（Tech Lead）

`/boss:review` 是专家小队的**技术评审入口**。以 Tech Lead 身份对架构或代码做技术评审，评审通过后产出实施计划 `plan.md`。

**产物**：
- `tech-review.md` — 技术评审报告（方案可行性、风险、改进建议）
- `plan.md` — 实施计划（模块划分、里程碑、技术方案细节、任务拆解指引）

**默认行为**：评审 + 实施计划完成后自动续跑后续所有环节，除非用户主动叫停。

## 适合 / 不适合

| 适合 `/boss:review`               | 不适合                                  |
| --------------------------------- | --------------------------------------- |
| 对已有架构/代码做技术评审         | 想让 agent 直接改代码（用 `/boss:dev`） |
| 评审 `/boss:architect` 产出的架构 | 需求还不清晰（用 `/boss:pm`）           |

## 前置输入

- 优先读取 `.boss/<slug>/architecture.md`
- 若不存在，可评审指定代码路径或用户描述的架构

## 执行步骤

1. **Feature slug 归一化**：确定 feature slug。
2. **确定评审目标**：
   - 有 `.boss/<slug>/architecture.md` → 评审架构
   - 给了代码路径 → 评审代码
   - 否则向用户确认评审目标
3. **派发 Tech Lead Agent**：读取 `agents/boss-tech-lead.md`。
   - 产出 `.boss/<slug>/tech-review.md`：技术选型合理性、风险等级、必须修复项。
   - 评审通过后产出 `.boss/<slug>/plan.md`：模块划分、里程碑、技术方案细节、任务拆解指引。
4. **自检**：
   - tech-review.md：评审结论清晰、风险有缓解措施、阻塞项已标注。
   - plan.md：模块划分合理、里程碑可验收、技术方案细节完整、任务拆解指引可执行。
5. **续跑**：读取 `references/continuation-chain.md`，按链执行下一步（tasks），除非用户叫停。

## 用法

```
/boss:review user-auth
/boss:review src/auth
/boss:review --stop-after review
```

## 选项

| 参数                  | 说明                                                      |
| --------------------- | --------------------------------------------------------- |
| `--stop-after <环节>` | 跑到指定环节后停（如 `--stop-after review` 只评审不拆解） |
| `--lang <zh\|en>`     | 评审文档语言（默认 zh）                                   |
