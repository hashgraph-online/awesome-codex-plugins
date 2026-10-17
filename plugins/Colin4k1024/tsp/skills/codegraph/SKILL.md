---
name: codegraph
description: >
  将 CodeGraph 作为默认内置 MCP-backed 代码图谱能力接入，用于 brownfield 符号搜索、
  调用链、影响面和上下文查询。输出必须回落到 `/team-*` 主链和 artifacts。
origin: colbymchenry/codegraph (official standalone installer with target-scoped wrapper)
---

# CodeGraph

## 用途

- 对已初始化的目标项目做本地代码图谱查询：符号搜索、callers/callees、impact、focused context。
- 在设计、执行和评审前补结构证据，减少依赖纯文本搜索造成的遗漏。
- 为 `/team-plan`、`/team-execute`、`/team-review` 提供可追溯的 MCP-backed 影响面证据。

## 触发信号

- brownfield 项目需要快速回答“这个 symbol 在哪里”“谁调用它”“改它会影响谁”。
- 目标 agent 已通过 TSP 安装流程配置 CodeGraph MCP，且目标项目存在 `.codegraph/`。
- Graphify 的轻量结构证据不足，或者需要比 GitNexus 更贴近当前 agent MCP 工具面的本地查询。

## 默认工作流

1. 先跑 `npm run codegraph:doctor`，确认 standalone CodeGraph binary、官方 installer 依赖和当前 target wrapper 可用。
2. Claude 新项目会通过 `SessionStart` 自动初始化索引；非 Claude 或关闭自动初始化时，在消费方目标项目根目录手动初始化：
   ```bash
   codegraph init -i
   ```
3. 通过 MCP 或 CLI 使用 `search/context/callers/callees/impact/node/files/status` 查询。
4. 把关键发现回落到主链：
   - 规划阶段 -> `/team-plan` 的 Brownfield Context Snapshot 和 readiness 证据
   - 执行阶段 -> `/team-execute` 的 story slice 影响面说明
   - 评审阶段 -> `/team-review` 的风险、回归边界和放行建议

## 输出约定

- CodeGraph 数据库由上游工具管理，通常写入目标项目 `.codegraph/`。
- TSP 侧只沉淀结论，不沉淀上游数据库：
  - 分析目标
  - 查询入口（MCP tool 或 CLI 命令）
  - 核心发现
  - 对 `/team-*` 决策的影响
  - 后续验证或回退建议

## 边界与禁用项

- TSP 安装时只运行 `scripts/install-codegraph.js` wrapper，不使用上游 `--target=auto`。
- Claude `SessionStart` 可在新项目缺少 `.codegraph/codegraph.db` 时静默执行 `codegraph init -i <projectRoot>`；用 `TSP_CODEGRAPH_AUTO_INIT=0` 可关闭。
- Codex / OpenCode 不做侵入式自动 hook，只依赖全局 MCP 配置、说明和 doctor 诊断。
- 不提交 `.codegraph/` 数据库或将其作为 TSP artifact。
- CodeGraph 结论不能绕过 `/team-plan`、`/team-review` 或验证门禁。

## 推荐组合

- 默认 brownfield 结构证据：`/team-help -> /update-codemaps -> npm run codegraph:doctor -> Claude 自动初始化或 codegraph init -i -> /team-plan`
- 快速影响面确认：`/team-execute -> CodeGraph impact/callers/callees -> /handoff -> /team-review`
- 深度多仓或许可证受限场景：按需选择 GitNexus 或 Graphify，并把结论统一回落到主链。
