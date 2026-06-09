---
name: graphify
description: >
  将 Graphify 作为可选知识图谱能力接入，用于 brownfield 结构扫描、依赖路径分析与架构问答。
  不替代 `/team-*` 主链；输出统一回落到 handoff 与 artifacts 证据。
origin: safishamsi/graphify (adapted)
---

# Graphify

## 用途

- 对已有仓库做结构化认知：模块关系、调用路径、关键依赖、热点边界。
- 在设计和实现前补“证据层”，降低只靠直觉拆任务的风险。
- 为 `/team-plan`、`/team-execute`、`/team-review` 提供可回溯的图谱证据。

## 触发信号

- brownfield 项目，且改动面跨多个目录或服务。
- 需求涉及“这个能力到底在哪里实现”“改这个会影响哪些模块”。
- 评审阶段需要对依赖路径、耦合点和影响范围做结构化证明。

## 默认工作流

1. 先跑 `npm run graphify:doctor`，确认 Python 与 Graphify CLI 可用。
2. 在项目根目录生成/更新图谱，统一输出到 `graphify-out/`。
3. 用 `query/path/explain` 回答任务相关的结构问题，形成可引用结论。
4. 把关键发现回落到主链：
   - 规划阶段 -> `/team-plan` 的 challenge/design/readiness 证据
   - 执行阶段 -> `/team-execute` 的 story slice 影响面说明
   - 评审阶段 -> `/team-review` 的风险与回归边界说明
5. 结论需要通过 handoff 或 artifact 写入项目文档，不停留在临时会话。

## 输出约定

- 统一目录：`graphify-out/`
- 最小交付内容：
  - 本次分析目标（问题是什么）
  - 查询/路径命令与核心结果（结果是什么）
  - 对主链决策的影响（接下来做什么）

## 边界与禁用项

- Graphify 只是可选能力，不替代 workflow-engine，也不创建并行责任链。
- 不在本仓库执行 `graphify codex install` 或 `graphify claude install`，避免改写现有 AGENTS/hooks 契约。
- 不自动安装 Python 或 `graphifyy`；环境依赖由使用方负责。

## 推荐组合

- 结构不清的 brownfield 任务：`/team-help -> graphify(build/query/path/explain) -> /team-plan`
- 高风险改动评估：`/team-execute -> graphify(path/explain) -> /handoff -> /team-review`
