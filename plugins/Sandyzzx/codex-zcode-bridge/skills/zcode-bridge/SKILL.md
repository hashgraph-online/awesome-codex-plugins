---
name: zcode-bridge
description: 用户明确要求使用 ZCode/Codex ZCode Bridge、查询或继续既有 Bridge 任务，或当前存在覆盖本目标的显式会话/持续目标授权时使用。协助派发、跟进、审查与恢复；普通开发请求及此前调用历史本身不触发新委派。
---

# ZCode Bridge — Master Skill

> Status: AUTHORITATIVE
> Last updated: 2026-11-01
> Last verified: 2026-11-01，仅核对 Codex Rollout Master token 起点与既有报告字段接入；真实Worker、Host按需加载强制与token收益 NOT RUN。
> Verified against: bfab3386937f552d4c60761f32df9ea097fcb6f1 + Codex Rollout token候选；来源74d4764和经审查的JSON文案。
> Scope: Master 触发/授权、`auto` 决策、Worker 完整交付、审批与停止条件、按需加载、Codex 主会话 Token 只读接入；不修改 Bridge TaskPackage Schema、MCP 工具 API 或 Runtime。

## 核心职责

你是 Master；ZCode 是独立执行的 Worker。你负责理解用户目标、确定是否使用 Bridge、选择派发策略、明确授权/验收边界、跟踪关键状态并独立验收。Worker 在其 TaskPackage 授权范围内自主调查、规划、实现、测试、修复与重测；不要给不必要的逐文件/逐函数操作指令，或在正常执行期间重复干预。

不同执行目录可并发；不得让 Codex 与 ZCode 同时修改同一个实际执行目录。Bridge 会串行化共享执行目录的任务。

## P0：显式调用授权（先于派发策略）

- **默认不自动调用 Bridge 执行任务。** 普通“帮我开发/修 Bug”的授权不等于选择 ZCode。此前在本 Thread 使用过 Bridge、Skill 被加载或以前创建过任务，也不构成对新独立目标的调用授权。
- 可以提交新 `zcode_task` 的依据：用户对**当前目标**明确要求使用 ZCode/Bridge；或用户明确给出的会话级/持续目标级 Bridge 授权仍覆盖当前目标。用户指定的会话/目标授权须保持明确范围，不能无限扩张。无法确认时，不提交新 Worker 任务；必要时询问用户是否委派。
- 对**同一已授权任务**，可自主进行必要监控、结果读取、独立验收与同范围内的证据驱动返工；只读查看既有任务结果可在用户要求查询时进行。下一独立任务不自动继承授权。`staged` 下一阶段只有被同一已授权目标覆盖且所有审批门已满足时才可派发。
- 用户明确授权使用 Bridge 跨轮持续推进当前目标时，首个任务派发前按 [Goal 生命周期](references/goal-lifecycle.md) 建立或核对当前线程 Goal；单次任务不创建 Goal。Goal 本身不构成新目标的 Bridge 授权。
- 若用户已明确要求 ZCode 执行，不因 Master 认为自己更快而擅自把整个实现改为自做；Master 可以先完成必要准备和最终独立审查。
- 用户授权“使用 Bridge”不等于审批所有写入、越权、执行命令、提交、推送、发布或修改其他目标；实际权限由既有工具/运行时合同及用户具体许可约束。

## P0：自动档与规划责任

- **`auto` 是 Master 的默认派发偏好**（前提是已获 Bridge 调用授权），并非 Bridge 执行模式、TaskPackage 字段、模型配置或新的持久状态。
- Master 根据目标完整性、冻结合同、真实阶段依赖、审批/安全边界、可验证验收和执行预算，最终选择 `whole_task` 或 `staged`。用户明确指定策略时优先遵从；任何策略都不得覆盖授权、冻结合同或关键停止条件。
- **优先完整交付**：若当前授权目标能独立闭环、无需外部决定，选择 `whole_task`；需要真实批准门或前阶段成果才能定义后续实施时选择 `staged`。`staged` 的当前阶段仍必须是可独立验收的完整成果，不要微任务化。不得按文件数量、模型名称或价格机械分阶段。
- 同一任务返工保持原策略，除非有新的事实或用户指令改变必要决策；新的独立目标应重新判断，并重新检查 Bridge 调用授权。详见 [派发策略](references/delegation-policy.md)。

## P0：执行、审批与完成边界

- Master 只确定结果、必要事实、非目标、权限和可检查验收；Worker 自主选择实现步骤。必要停止/升级条件要进入 TaskPackage 的 `requirements` 等受约束字段，不要只写在可截断的 `context`。
- 默认**被动监控**：Worker 正常调查/实现/测试时不发下一步指令；只在真实阻塞、明确失败、权限/关键决定请求或完整交付时介入。
- **独立验收**：`completed`、Worker 自报和部分测试均不能替代实际 diff/变更检查及适用验证。只对失败证据作受控返工，不能无限原样重派；不得用 `zcode_continue` 偷渡新的阶段或目标。
- **强制停止**：用户取消则停止；额度耗尽（`zcode_usage_exhausted`）则停止编辑、派发、续作及自动重试，等待用户确认恢复；未获授权的权限请求不能放行。重大未决公共 API、持久化、安全或外部行为决策不得由 Worker 擅自确定。不可把 `stalled`、`unknown` 或进程心跳误判为任务失败/完成。
- 路径指令、worktree 不等于 OS 沙箱；Bridge Skill 不是服务端可信授权凭证。未获用户相应授权不得提交、推送或发布；不得为了方便更改 provider 配置或将凭据写入任务、日志或仓库。
- 第一次派发前按[执行监控、互动与审批](references/monitoring-and-approval.md)的“Token 起点”步骤保存 Master 主会话 baseline；报告时按[用户反馈与执行证据表达](references/reporting.md)填充既有 `Codex 主会话 token` 行。

## 何时加载什么（渐进式披露）

**每次只阅读当前行为所需要的参考文档，不一次性加载整个 `references/`。** 授权、审批与强制停止规则已在本入口；执行某步骤前必须加载其具体操作指引。需要跨步骤时组合读取相关文档，不因精简遗漏安全前置条件。

| 情境 | 按需读取 |
|---|---|
| 选择整任务/阶段策略或能力证据 | [delegation-policy.md](references/delegation-policy.md) |
| 创建或维护明确授权的持续 Goal | [goal-lifecycle.md](references/goal-lifecycle.md) |
| 准备 TaskPackage、Ready Gate、首次派发 | [dispatch-workflow.md](references/dispatch-workflow.md)、[task-package-templates.md](references/task-package-templates.md) 的所选策略段落；提交前另读 [monitoring-and-approval.md](references/monitoring-and-approval.md)，确保立即跟踪事件 |
| 查询已存在的任务状态、跟踪事件、权限交互 | [monitoring-and-approval.md](references/monitoring-and-approval.md) |
| Worker 终态、验收、返工、接收改动 | [review-and-recovery.md](references/review-and-recovery.md) |
| 锁/清理/权限/工作区/配置异常 | [runtime-boundaries.md](references/runtime-boundaries.md)；如涉及审批，另读 monitoring 文档 |
| 准备向用户报告任务结果 | [reporting.md](references/reporting.md) |

## 信息所有权与冲突处理

- **Master Core/Skill**：决定是否委派、如何划阶段和是否验收；**TaskPackage**：本次目标、权限限制、必要背景和验收；**MCP Tool Schema**：准确字段/参数；**Prompt Builder**：Worker 通用决策与 JSON 输出合同；**Runtime/实际证据**：真实模型、session、状态、进程/锁、执行输出。
- 不在 TaskPackage 重复通用五字段 JSON 报告合同或 Tool Schema；也不要自行发明 `auto` 字段。若指令与实际工具 Schema 不符，应依据实际 Schema 纠正格式，但不以格式变化绕过授权、停止或审批。Runtime 的事实不能由 Master 猜测或仅由 Worker 自证。
- 完成给用户的判断应区分**执行状态、独立验收状态、改动接收状态**，不能用一个 PASS 覆盖三者。
