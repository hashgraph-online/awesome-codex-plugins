# TaskPackage 编写、Ready Gate 与任务提交

> Status: AUTHORITATIVE
> Last updated: 2026-10-24
> Last verified: 2026-10-29，仅静态核对独立功能候选的引用、授权与JSON主线边界；历史离线记录不代表本候选运行时验收。真实Worker、Host按需加载强制与token收益 NOT RUN。
> Verified against: master 73af9d60ff9bbcbbc1ae1d7b1f9b9fb9fca48bb0 + 本独立功能候选；来源74d4764和经审查的JSON文案。

### 构造任务 Prompt

已确认本次任务的 Bridge 调用授权后，简短说明所选 `whole_task`/`staged` 策略及依据；`auto` 不作为 TaskPackage 参数或提交字段。TaskPackage 只包含当前任务特有的目标、约束、决策边界和验收要求；Skill 或 Prompt Builder 已规定的通用监控、终态处理、独立验收和返工流程不重复展开，除非本任务存在特殊要求或明确例外。

按当前策略读取 [任务模板](task-package-templates.md) 的对应部分，只使用现有字段：`objective` 写本次交付结果；`requirements` 写必要行为、冻结决定、非目标、局部自主权及升级/停止条件；路径数组写修改边界；`acceptance_criteria` 和 `test_commands` 对齐本次交付层级；`context` 只放必要的决策背景、相关文件与前置证据。

- `whole_task` 明确最终行为、兼容要求和端到端验收，让 Worker 自主安排实现与修复，不无必要地列出每个函数、命令或实现顺序，也不要求低影响选择逐次审批。
- `staged` 明确当前阶段目标、已冻结决定、前置输入、本阶段范围、后续非目标、交接证据和停止点。当前阶段就是 Worker 负责完整交付的“本任务”，不要让它重新规划整个项目或启动后续实现。
- 必须遵守的约束和停止条件放入 `requirements` 或对应路径字段，不能只放在会被截断的 `context`（当前上限 2,000 字符）中。只读取并传递相关上下文，不复制全部对话或所有文档。五个数组字段必须存在，无适用项目时可为空；不要发明字段或重复 Prompt Builder 已提供的通用决策规则与五字段 JSON 输出合同。

### 准备与调用

**调用前授权门**：明确本次目标由用户指定 ZCode/Bridge，或用户已给予覆盖本目标的会话/持续目标授权；没有此依据时不调用 `zcode_task`。一次历史调用不延长授权。用户明确要求使用 ZCode 时，Master 仍负责 Ready Gate、验收和必要的阶段决策。

提交前读取[监控与审批](monitoring-and-approval.md)，准备在 `zcode_task` 返回后立即读取事件；明确授权的持续目标还须先按 [Goal 指引](goal-lifecycle.md) 建立或核对 Goal。不要把这两项前置留到任务已经启动之后。

派发前 Ready Gate 检查信息是否充分，不要求所有字段都有非空值：确认目标、项目根目录和实际执行目录，并判断修改边界、必要输入、验收标准、测试要求和时间预算是否适用，记录必要信息。

- 使用 worktree 时，必须先由 Codex 创建并确认实际执行目录存在；不需要时直接使用项目根目录，不额外创建。
- 验收标准必须明确且可检查。测试命令来自仓库中已核实存在且适用的命令；没有适用命令时 `test_commands` 可为空，并说明可行的验证方式或不适用原因，不虚构命令或测试结果。
- 路径数组可以为空。空的 `allowed_paths` 不表示禁止写入，仍须遵守实际执行目录和其他授权边界；只有需要额外限制时才填写具体路径。
- 沿用既有通用执行、审批和返工规则；仅在任务有特殊预算、审批门槛或返工条件时补充。`worktree_path`、`model`、`timeout_ms` 是可选字段，无需为填表而指定；省略预算时沿用已配置默认值，不编造数值。
- 必要的目标、授权、关键依赖或验收信息不明确时，先补齐或向用户询问；不适用项目可以留空或说明原因，不强行补造路径、输入或资源。

1. 确认 Codex 项目根目录，并始终把它作为 zcode_task 的 `workspace`。根据 Codex 对任务的执行指示决定是否需要 worktree；需要时由 Codex 创建并准备，再把其现存绝对路径作为 `worktree_path`。Bridge 不创建、选择或删除 worktree；未提供该字段时任务直接在项目根目录执行。
2. 将 objective、requirements 和 acceptance_criteria 写具体，五个数组字段均须存在，路径及测试数组按适用性填写或留空；相对路径以实际执行目录为基准，路径约束只是任务指令，不是强制沙箱。验收标准描述可观察的交付结果；只有确实属于必要约束的内部步骤才写进 requirements。只在任务需要时传入精简的 `context`，按 `PROJECT DECISIONS`、`CONSTRAINTS`、`RELEVANT FILES`、`OPEN DECISIONS — DO NOT CHOOSE` 组织；不要复制整段 Codex 对话。没有未决事项时省略该小节。不要把验收责任交给 ZCode。
3. 模型优先级固定为：任务或用户指定 → Bridge 持久默认（`ZCODE_BRIDGE_DEFAULT_PROVIDER_ID` / `ZCODE_BRIDGE_DEFAULT_MODEL_ID`）→ ZCode session 默认。用户指定时传入 model: { provider_id, model_id }，优先使用 runtime 报告的精确标识；Bridge 会识别配置中声明的旧版 builtin ID 和账户 provider ID。若模型预检失败，从 `model_catalog` 事件复制 runtime 实际报告的完整标识再重试；不要猜思考档位。用户未指定时省略 model，由 Bridge 决定是否应用持久默认。
4. 初始预算可沿用已配置默认值，仅在任务需要时显式设置 timeout_ms。超时或失败后先检查最后业务事件、执行目录中的文件变化和实际未完成项，再决定续作；不要只缩短预算或用新 task_id 原样重派。需要返工时写明上一轮的具体失败证据和新的验收条件。
5. 调用 zcode_task。同一完整交付只用一个 task_id；MCP 报错时先解释和解决具体配置问题，不要重复提交相同 task_id。

`staged` 的下一阶段是新的完整交付，应在本阶段独立验收、依赖和决策门满足且该下一阶段处于现有授权目标的范围内或重新获用户授权后，以新的 task_id 派发；不通过 `zcode_continue` 偷渡下一阶段。同一阶段的验收返工仍复用原任务。仅在另已部署Ledger时，跨多个交付目标需要长期追踪才按需使用它，不因使用 `staged` 就新增调度状态机。
