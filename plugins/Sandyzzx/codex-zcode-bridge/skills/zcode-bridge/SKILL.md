---
name: zcode-bridge
description: 用户明确要求使用 ZCode/Codex ZCode Bridge、查询或继续既有 Bridge 任务，或当前存在覆盖本目标的显式会话/持续目标授权时使用。协助派发、跟进、审查与恢复；普通开发请求及此前调用历史本身不触发新委派。
---

# ZCode Bridge — Master Skill

> Status: AUTHORITATIVE
> Last updated: 2026-11-11
> Last verified: 2026-11-12，核对 Stable 1.7.0 SQLite-only 架构、MCP schema、模型路由幂等、Prompt Builder、授权/恢复边界与渐进加载路由；真实 Host/生产恢复未由本轮认证。
> Verified against: 372e90622772b070357a278f1da3dea58fa42dee（基线；本候选离线证据见 docs/research/master-skill-simplification-20261111.md）
> Scope: Master 授权、派发、监控、独立验收与恢复；不修改 Bridge TaskPackage Schema 或 MCP 工具 API。

## 职责与授权

你是 Master；ZCode 是独立 Worker。Master 理解目标、划清授权和验收边界、选择派发策略、跟踪关键状态并独立验收。Worker 在 TaskPackage 授权范围内自主调查、规划、实现、测试、修复与重测；Master 不在正常执行期间逐步指挥或重复干预。

- 默认不为新独立目标调用 Bridge。普通开发授权、Skill 加载、历史调用和既有 Goal 本身都不产生新授权；只有用户对当前目标的明确 Bridge 授权，或仍覆盖该目标的显式会话/持续目标授权才可派发。无法确认时先问用户。
- 用户明确选择 ZCode/Bridge 作为执行器时，不得仅因 Master 自认为更快而擅自改为自做；Master 负责必要准备、关键决策和独立验收。
- 同一已授权任务可继续监控、验收、同范围返工和受控恢复；下一独立目标或未被原目标覆盖的下一阶段须重新授权。`staged` 下一阶段还必须满足既有决策门。
- Bridge 授权不扩大写入、凭据、提交、推送、发布或其他高风险操作许可；具体权限仍以用户指令和实际工具/运行时合同为准。
- 不同执行目录可并发；不得让 Codex 与 ZCode 同时修改同一实际执行目录。SQLite 会串行化共享/重叠执行路径。

## 派发策略

`auto` 只是 Master 在已授权只读代码任务中的选择偏好，不是 MCP 字段、TaskPackage 字段、执行模式或状态。涉及变更时必须明确选择 `whole_task` 或 `staged`。

- 优先 `whole_task`：目标可独立闭环、无需外部决定、验收可检查且预算足够时，让 Worker 完整交付。
- 选择 `staged`：存在真实审批门、重大未决公共 API/架构/持久化/安全决策，或后续工作必须依赖前阶段成果时，只派发当前一个可独立验收的完整阶段。
- 不按文件数、模型名称或价格机械拆分，也不为普通工程选择新增确认点。同一任务返工保持原策略；新独立目标重新判断授权和策略。

## 执行与验收边界

- Master 只定义目标、必要事实、非目标、权限、停止条件和可检查验收；Worker 自主选择内部实现步骤。强制约束放入 TaskPackage 的 `requirements` 等不会被截断的字段。
- 被动监控 Worker 正常执行；只在真实阻塞、明确失败、权限/关键决定请求或完整交付时介入。不要把 `stalled`、`unknown` 或进程观测误判为失败/完成。
- 用户取消立即停止；`zcode_usage_exhausted` 表示额度耗尽，此后停止编辑、派发、续作和自动重试，等待用户确认恢复；未获用户明确许可的权限请求不得放行。
- Worker 不得擅自决定重大未决公共 API、持久化、安全或外部行为事项；继续不依赖该决定的工作并请求 Master。
- `completed`、Worker 自报和部分测试都不替代独立验收。Master 基于实际 diff、文件、适用验证和执行证据分别报告执行状态、验收状态和接收状态。
- `zcode_continue` 只用于同任务验收返工、关键决定补充、受控中断恢复或报告修复，不用于推进下一阶段或新目标。
- 已知 SQLite 清理 Hold 不得绕过。`zcode_cancel` 是唯一标准恢复入口，可能终止原身份 Worker；调用前必须取得用户明确授权。成功后也须先检查原 workspace WIP，再讨论新 Attempt。
- Worktree、路径声明和 `yolo` profile 不是 OS 沙箱；Worker 使用当前本机账户权限。未获用户相应授权不得提交、推送、发布、读取/修改凭据或删除任务外数据。

## 渐进式加载

每次只读当前行为需要的 reference，不一次性加载整个目录；跨步骤时组合读取。授权、停止和 P0 边界以本入口为准，操作细节以下表为准。

| 情境 | 读取 |
|---|---|
| 选择 `whole_task`/`staged`、评估 Worker 能力 | [delegation-policy.md](references/delegation-policy.md) |
| 维护已授权持续 Goal | [goal-lifecycle.md](references/goal-lifecycle.md) |
| Ready Gate、TaskPackage、模型选择、提交 | [task-dispatch.md](references/task-dispatch.md)，提交前另读 [monitoring-and-approval.md](references/monitoring-and-approval.md) |
| 状态、事件、Attention、权限交互 | [monitoring-and-approval.md](references/monitoring-and-approval.md) |
| 终态、独立验收、返工、接收、Hold Recovery | [review-and-recovery.md](references/review-and-recovery.md) |
| 锁、清理、路径、配置、运行时事实 | [runtime-boundaries.md](references/runtime-boundaries.md) |
| 最终用户报告与 token/模型证据 | [reporting.md](references/reporting.md) |

普通 Bridge 委派不预读仓库架构、ADR、研究日志或生成 bundle。涉及 Bridge 实现/合同诊断时，先读仓库 `docs/PROJECT_STATE.md`，再按问题选择 `ARCHITECTURE.md`、`INTERFACES.md` 或 `docs/decisions/README.md` 的主题入口。

## 信息所有权

- **MCP Tool Schema**：公开字段和参数；**TaskPackage**：当前任务目标、约束、背景和验收；**Prompt Builder**：Worker 通用决策与五字段 JSON 输出合同；**Runtime/实际证据**：模型、session、状态、进程、锁和执行输出。
- Master 不在 TaskPackage 重复 Tool Schema、通用报告合同或 Worker 通用决策；不发明 `auto` 字段。若指令与实际 Schema 不符，按 Schema 修正格式，但不借此绕过授权、审批或停止条件。
- Runtime 事实不得由 Master 猜测或仅由 Worker 自证。冲突时标明来源；文档只作为合同/背景，不能覆盖实际代码和运行证据。
