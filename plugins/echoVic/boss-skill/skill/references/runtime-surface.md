# Boss Runtime Surface

本文件保存 runtime-first 编排面。所有正式状态变更都通过 `boss runtime ...` 追加事件，再物化 `.boss/<feature>/.meta/execution.json`。

## Canonical Runtime Surface

| 编排动作 | Runtime CLI | Runtime API |
|---------|-------------|-------------|
| 初始化流水线（低阶；`project init` 未执行时使用） | `boss runtime init-pipeline` | `initPipeline(feature)` |
| 恢复 Workflow 执行图 | `boss runtime resume <feature> --from-run <run-id>` | `resumeWorkflow(feature, options)` |
| 查询 ready artifacts | `boss runtime get-ready-artifacts` | `getReadyArtifacts(feature, options)` |
| 阶段状态变更 | `boss runtime update-stage` | `updateStage(feature, stage, status, options)` |
| 记录产物 | `boss runtime record-artifact <feature> <artifact-name> <N>` | `recordArtifact(feature, artifact, stage)` |
| Agent 状态变更 | `boss runtime update-agent` | `updateAgent(feature, stage, agent, status, options)` |
| 门禁评估 | `boss runtime evaluate-gates` | `evaluateGates(feature, gate, options)` |
| 插件注册 | `boss runtime register-plugins <feature>` | `registerPlugins(feature, options)` |
| 插件 Hook 执行 | `boss runtime run-plugin-hook` | `runHook(hook, feature, options)` |
| 阶段状态检查 | `boss runtime check-stage` | `checkStage(feature, stage, options)` |
| 事件回放 | `boss runtime replay-events` | `replayEvents(feature, options)`, `replaySnapshot(feature, at, options)` |
| Progress 诊断 | `boss runtime inspect-progress` | `inspectProgress(feature, options)` |
| 生成流水线报告 | `boss runtime generate-summary` | `buildSummaryModel(feature)`, `renderMarkdown(model)`, `renderJson(model)` |
| 生成诊断页 | `boss runtime render-diagnostics` | `renderHtml(model)` |

## Helper CLI

| CLI | 用途 |
|------|------|
| `boss runtime retry-stage` | 阶段重试（检查上限 -> retrying -> running） |
| `boss runtime retry-agent` | 单个 Agent 重试（不重跑整个阶段） |
| `boss packs detect` | Pipeline Pack 自动检测（匹配项目文件） |
| `boss runtime query-memory <feature> --agent <agent-name>` | 查询指定 Agent 记忆摘要，用于派发前注入上下文 |
| `boss runtime inspect-progress` | 实时进度监控（读取 progress.jsonl） |
| `boss runtime record-feedback` | Agent 间反馈循环记录（REVISION_NEEDED） |
| `boss design preview <feature>` | 预览 `.boss/<feature>/ui-design.json` |
| `boss status <feature>` | 读取 Runtime Core 状态并输出下一 checkpoint |
| `boss continue <feature>` | 重新读取状态并输出当前 checkpoint / 阻塞原因 |
| `boss gate <feature>` | 运行或汇总当前阶段/波次门禁 |
| `boss gate final <feature>` | 最终回答前统一完成门禁 |
| `boss qa attack <feature>` | 生成结构化 QA findings |

## Workflow Definition vs Run Instance

- 初始化时将 pipeline pack + artifact DAG 编译成 `.boss/<feature>/.meta/workflow-plan.json`。
- `workflowPlanPath` / `workflowHash` / `packHash` / `artifactDagHash` 描述 Workflow 定义。
- `runId` 描述一次运行实例。
- 恢复时调用 `boss runtime resume <feature> --from-run <run-id>`，runtime 重新加载 workflow plan，并按节点输入指纹输出 `reuse` / `run` / `skip` 决策。
- resume 决策会进入 `execution.workflow.nodes`；`execution.workflow.nextNodeIds` 是下一批机器可调度节点。
- `GateEvaluated` 和 `WaveVerified` 也会更新 workflow node 状态，门禁 / Evidence Wave 结果不再只存在于外围报告。

## Runtime Invariants

- 不直接编辑 `.meta/execution.json`；它是 projector 物化出的 read model。
- DAG loop 不从 Markdown 自行猜下一步；读取 `execution.workflow.nextNodeIds`，并用 `workflow node 状态` 判断 `ready` / `reused` / `completed` / `failed`。
- 不用 shell 日志代替事件流。Pack 选择通过 `PackApplied`，插件生命周期通过 `PluginDiscovered` / `PluginActivated` / `PluginHookExecuted` / `PluginHookFailed`。
- 报告生成走 runtime summary model，不在 shell 中拼接状态。
