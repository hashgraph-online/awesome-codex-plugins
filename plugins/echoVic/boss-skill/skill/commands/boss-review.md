---
name: boss:review
description: "只跑评审环节：Tech Lead 技术评审 + 风险评估。可对任意已有代码或规划产物单独用，产出 tech-review.md，不改代码。"
allowed-tools: Task, Read, Write, Edit, Bash, Glob, Grep
---

# /boss:review — 单环节：技术评审（Tech Lead）

`/boss:review` 是 Boss 流水线的**评审环节独立入口**。以 Tech Lead 身份对现有代码、架构或规划产物做技术评审与风险评估，产出 `tech-review.md`。**只读评审，不改代码。**

> 这是 gstack `/review` 的对应能力，但带 Boss 的可追溯产物：评审结论落在 `.boss/<feature>/tech-review.md`，可被后续阶段或门禁引用。

## 适合 / 不适合

| 适合 `/boss:review` | 不适合 |
|---------------------|--------|
| 对已有代码/PR 做技术评审、风险打分 | 想让 agent 直接改代码（用 `/boss` 或直接编辑） |
| 评审 `/boss:plan` 产出的架构 | 需要跑测试证据（用 `/boss:qa`） |
| 上线前的技术风险 checklist | 纯代码解释问答（直接读） |

## 执行步骤

1. 读取 `SKILL.md` 取得不变量；本命令**只执行 Tech Lead 评审**，不派发开发/QA/DevOps。
2. 确定评审目标：
   - 有 feature slug 且 `.boss/<feature>/` 存在 → 评审其 `prd.md` / `architecture.md` / 代码。
   - 只给了代码路径或 PR → 归一化一个 slug，评审对应代码。
3. 读取 `agents/boss-tech-lead.md` 与 `skills/tech-lead/code-review/SKILL.md`、`skills/tech-lead/technical-standards/SKILL.md`。
4. 以 Tech Lead 身份产出 `tech-review.md`（模板 `templates/tech-review.md.template`）：技术选型合理性、风险等级、Blast Radius、必须修复项。
5. 若挂在完整流水线上：`boss runtime record-artifact <feature> tech-review.md 2`；独立使用时可只产出文档。
6. 输出：评审结论、风险等级、阻塞项、建议下一步（可接 `/boss:qa` 或 `/boss --continue-from 3`）。

## 用法

```
/boss:review                       # 评审当前项目
/boss:review src/auth               # 评审指定目录
/boss:review user-auth              # 评审已有 .boss/user-auth 产物
```

## 选项

| 参数 | 说明 |
|------|------|
| `--lang <zh\|en>` | 评审文档语言（默认 zh） |
