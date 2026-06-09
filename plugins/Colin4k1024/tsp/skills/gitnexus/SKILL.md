---
name: gitnexus
description: >
  将 GitNexus 作为受控可选代码智能能力接入，用于 brownfield MCP 查询、影响面分析、
  detect_changes、多仓分析和更深代码图谱证据。输出必须回落到 `/team-*` 主链和 artifacts。
origin: abhigyanpatwari/GitNexus (reference-only controlled integration)
---

# GitNexus

## 用途

- 对存量仓库做更深代码图谱分析：符号上下游、调用链、执行流、跨仓影响面。
- 在改动前用 `impact` / `detect_changes` 类证据确认 blast radius。
- 为 `/team-plan`、`/team-execute`、`/team-review` 提供可追溯的 MCP/图谱证据。

## 触发信号

- brownfield 项目改动跨多个模块、服务或仓库。
- 需要回答“改这个 symbol/API 会影响谁”“这段流程从哪里进入、流向哪里”。
- 评审或发布前需要对 git diff 做影响面确认。
- Graphify 的轻量结构扫描不够，需要 MCP tool、资源或多仓上下文。

## 默认工作流

1. 先跑 `npm run gitnexus:doctor`，确认 Node、npm/npx 与上游包元数据。
2. 用户自行确认 GitNexus 上游许可证和项目使用场景是否匹配。
3. 在目标项目根目录显式执行索引命令，并保留 TSP 的 AGENTS/CLAUDE 契约：
   ```bash
   npx --yes gitnexus@latest analyze --skip-agents-md
   ```
4. 通过 MCP 或 CLI 查询 `query/context/impact/detect_changes` 等结果。
5. 把关键发现回落到主链：
   - 规划阶段 -> `/team-plan` 的 Brownfield Context Snapshot 和 readiness 证据
   - 执行阶段 -> `/team-execute` 的 story slice 影响面说明
   - 评审阶段 -> `/team-review` 的风险、回归边界和放行建议

## 输出约定

- GitNexus 索引由上游工具管理，通常写入目标仓库 `.gitnexus/` 与用户级 registry。
- TSP 侧只沉淀结论，不沉淀上游数据库：
  - 分析目标
  - 查询入口（MCP tool/resource 或 CLI 命令）
  - 核心发现
  - 对 `/team-*` 决策的影响
  - 后续验证或回退建议

## 边界与禁用项

- 不把 GitNexus 当作 TSP 依赖或默认安装项。
- 不自动运行 `gitnexus setup`，避免改写用户全局 MCP/editor 配置。
- 不在 TSP 管理仓库里运行不带 `--skip-agents-md` 的 `gitnexus analyze`。
- 不复制 GitNexus 源码、hooks、skills 或生成产物到 TSP canonical source。
- 当前按上游 npm 元数据视为非商业许可证约束；商业使用前需要用户自行确认授权。

## 推荐组合

- 轻量 brownfield 结构扫描：`/team-help -> /update-codemaps -> graphify -> /team-plan`
- 深影响面分析：`/team-help -> /update-codemaps -> GitNexus impact/detect_changes -> /team-plan`
- 高风险评审：`/team-execute -> GitNexus detect_changes -> /handoff -> /team-review`
