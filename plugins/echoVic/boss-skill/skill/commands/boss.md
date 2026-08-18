---
name: boss
description: "启动 BMAD 全自动研发流水线。编排 9 个专业 Agent，从需求到部署一键完成。"
allowed-tools: Task, Read, Write, Edit, Bash, Glob, Grep
---

# /boss — BMAD 全自动研发流水线

当用户执行 `/boss` 时，启动 Boss 流水线。

## 适合 / 不适合

| 适合 `/boss` | 不要用 `/boss` |
|--------------|----------------|
| 新 feature，需要 PRD → 架构 → 开发 → 测试证据 | 单文件修改、小 bug、解释代码 |
| 需要 `.boss/<feature>/` 可追溯产物 | 用户只补充技术约束（先问应用到哪个 feature） |

轻量首次体验：`/boss <需求> --roles core --skip-deploy`

## 执行步骤

1. 读取当前 Boss Skill 的 `SKILL.md`，获取完整的 Boss 编排指令
2. 自然语言需求会先归一化为 feature slug，再传给 `boss project init <feature-name>`
3. 约束类输入不会启动新流水线：如果用户只是补充技术栈、偏好或约束，先询问要应用到哪个已有或新 feature
4. 按照 SKILL.md 中定义的四阶段工作流执行
5. 用户传入的参数（如 `--skip-ui`、`--quick`、`--template` 等）直接透传给工作流

## 用法

```
/boss [需求描述] [选项]
```

### 示例

```
/boss 做一个 Todo 应用
/boss 用户认证 --template
/boss 给现有项目加用户认证 --skip-ui
/boss 把现有原生 HTML 组件迁移成 shadcn 组件
/boss 快速搭建 API 服务 --skip-deploy --quick
/boss 继续上次中断的任务 --continue-from 3
/boss 轻量模式 --roles core --hitl-level off
```

自然语言示例会先推导出稳定的产物目录名，例如“做一个 Todo 应用”使用 `.boss/todo-app/`，“把现有原生 HTML 组件迁移成 shadcn 组件”使用 `.boss/shadcn-component-migration/`。

### 选项

| 参数 | 说明 |
|------|------|
| `--skip-ui` | 跳过 UI 设计阶段（纯 API/CLI 项目） |
| `--skip-deploy` | 跳过部署阶段（只开发不部署） |
| `--quick` | 跳过常规确认节点；高 Blast Radius 变更仍按 SKILL.md 的强制确认 trigger 处理 |
| `--template` | 初始化项目级模板目录并暂停流水线 |
| `--continue-from <1-4>` | 从指定阶段继续 |
| `--hitl-level <level>` | 人机协作级别：`auto`（关键节点 + 风险触发）/ `interactive` / `off` |
| `--roles <preset>` | 角色预设：`full`（默认）/ `core` |
| `--lang <zh\|en>` | 交付文档语言（默认 `zh`） |

## 单环节切片命令

不需要跑完整流水线时，可用以下独立入口（同一底层，可对已有项目单点介入）：

| 命令 | 用途 |
|------|------|
| `/boss:plan` | 只做规划：PM + Architect → PRD + 架构 |
| `/boss:review` | 只做技术评审：Tech Lead 只读评审 |
| `/boss:qa` | 只做测试 + 门禁：QA 证据链 |
| `/boss:ship` | 只做构建部署：DevOps + Gate 2 |
| `/boss:extend` | 引导式扩展自定义 agent / pipeline pack |
