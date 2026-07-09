---
name: boss:plan
description: "只跑规划环节：PM 需求穿透 + Architect 架构设计。对任意需求或已有项目单独可用，产出 prd.md + architecture.md，不派发开发/测试/部署。"
allowed-tools: Task, Read, Write, Edit, Bash, Glob, Grep
---

# /boss:plan — 单环节：规划（PM + Architect）

`/boss:plan` 是 Boss 流水线的**规划环节独立入口**。你不需要跑完整 9 Agent，就能拿到一份可追溯的 PRD + 架构设计。适合「先想清楚再动手」或「给已有项目补一份架构文档」。

> 这是 `/boss` 的一个切片，不是另一套逻辑。底层复用同一套 agent prompt、runtime 与产物目录，只是把入口收窄到 stage 1。

## 适合 / 不适合

| 适合 `/boss:plan` | 用完整 `/boss` |
|-------------------|----------------|
| 只想要 PRD + 架构，先评估再决定做不做 | 想一路做到可运行/可部署 |
| 给已有代码库补规划文档 | 需要开发 + 测试 + 部署证据 |
| 规划完人工接手实现 | 需要门禁与 QA 证据链 |

## 执行步骤

1. 读取 `SKILL.md` 取得不变量与路由；本命令**只执行到 stage 1 结束**。
2. Feature slug 归一化（见 `references/orchestration-loop.md` Step 0a）。约束类输入不新建目录。
3. 除非 `--quick`，按 `references/orchestration-loop.md` Step 0 做需求澄清（缺「做什么/给谁用/核心场景」时读取 `skills/brainstorming/SKILL.md`）。
4. 初始化：`boss project init <feature-name>`（无 CLI 时按 `references/no-cli-fallback.md` 退化为纯 markdown）。
5. 按 DAG 派发 **PM**（`agents/boss-pm.md`）产出 `prd.md`，再派发 **Architect**（`agents/boss-architect.md`）产出 `architecture.md`。
6. 每份产物完成后 `boss runtime record-artifact <feature> <artifact> 1`。
7. **停在 stage 1 完成确认节点**，不进入 tech-review / 开发。输出：产物路径 + 下一步建议（可接 `/boss:review` 或完整 `/boss --continue-from 2`）。

## 用法

```
/boss:plan 做一个面向设计师的素材管理工具
/boss:plan 给现有 API 补一份架构设计 --skip-ui
/boss:plan 用户认证模块 --quick
```

## 选项

| 参数 | 说明 |
|------|------|
| `--skip-ui` | 跳过 UI 设计，只产出 PRD + 架构 |
| `--quick` | 跳过需求澄清与确认节点 |
| `--lang <zh\|en>` | 产出文档语言（默认 zh） |
