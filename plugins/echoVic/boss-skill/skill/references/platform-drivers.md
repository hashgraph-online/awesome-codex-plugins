# Platform Driver 模式

Boss 使用统一 Runtime Core 和多个 Platform Driver。所有平台都以 `.boss/<feature>/.meta/execution.json` 为状态源；不要从聊天上下文推断流水线状态。

## Shared Rules

- Runtime Core 负责状态、waves、gates、QA findings 和 final evidence。
- Platform Driver 只决定 enforcement 方式，不改变状态语义。
- Codex 适配是 additive，不得删除或弱化 Claude Code hooks。
- **不重造宿主原语。** 子 Agent 派发、文件读写、代码检索、会话内临时清单一律使用当前宿主
  提供的工具（各宿主命名不同，如子 Agent 派发在 Claude Code 是 `Task`、在其他宿主可能是
  `Agent`），Boss 不自建等价物。Boss 只负责宿主不提供的三件事：事件溯源审计、不可绕过的
  门禁、产物 provenance。
- Boss 事件流中的 todo 与宿主的会话清单不是同一层：前者是会话收敛后带 owner 与
  successCriteria 的跨 Agent 交付项，需持久化与审计；后者是单次会话内的工作记录。
  不要用前者替代后者，也不要反过来。

## Claude Code Driver

- 继续优先使用 hooks、artifact guard、stop guard、subagent 协议和现有 Skill 流程。
- `boss status <feature>`、`boss gate final <feature>` 可作为可观测性和兜底命令，但不得替代 hooks。
- `boss gate <feature>` 可运行或汇总当前阶段/波次门禁。
- hooks 可用时，checkpoint 文本只是透明提示，不是唯一约束来源。

## Codex Driver

- 每轮先运行 `boss status <feature> --json --driver codex`。
- 只执行 Runtime Core 返回的单个下一步或 checkpoint。
- 看到 `CHECKPOINT_REQUIRED` 时，必须运行 `requiredChecks` 并读取结果，再调用 `boss continue <feature> --driver codex` 重新获取当前 checkpoint/阻塞原因。
- 最终回答前必须运行 `boss gate final <feature>` 并确认通过；需要攻击式 QA 时先运行 `boss qa attack <feature>`。

## OpenClaw / Antigravity / Hermes

- 使用同一个 `.boss/<feature>/.meta/execution.json` read model。
- 若平台不支持 hooks，则更频繁调用 `boss status <feature>` 和 `boss continue <feature>`。
- 不要把平台 transcript 当成状态真相。
