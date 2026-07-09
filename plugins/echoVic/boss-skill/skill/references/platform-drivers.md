# Platform Driver 模式

Boss 使用统一 Runtime Core 和多个 Platform Driver。所有平台都以 `.boss/<feature>/.meta/execution.json` 为状态源；不要从聊天上下文推断流水线状态。

## Shared Rules

- Runtime Core 负责状态、waves、gates、QA findings 和 final evidence。
- Platform Driver 只决定 enforcement 方式，不改变状态语义。
- Codex 适配是 additive，不得删除或弱化 Claude Code hooks。

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
