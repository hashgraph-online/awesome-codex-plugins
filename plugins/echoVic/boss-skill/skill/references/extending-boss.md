# Extending Boss — 扩展契约

本文件定义 Boss 三类项目级扩展的契约与 schema，供 `/boss:extend` 引导式生成，也供手写扩展参考。所有扩展落在项目级扩展点，`/boss` 运行时通过 `boss packs detect` / `boss runtime register-plugins` 发现（降级模式手动加载）。

## 扩展点总览

| 类型 | 位置 | 发现方式 |
|------|------|----------|
| Pipeline Pack | `.boss/pipeline-packs/<name>/pack.json` | `boss packs detect <dir>` |
| Plugin（gate / agent / template） | `.boss/plugins/<name>/plugin.json` | `boss runtime register-plugins <feature>` |
| Artifact DAG 覆盖 | `.boss/artifact-dag.json` | 初始化时编译进 workflow-plan |
| 模板覆盖 | `.boss/templates/` | 查找优先级高于包内置 `templates/` |

## Pipeline Pack 契约

`pack.json` 字段：

| 字段 | 说明 |
|------|------|
| `name` / `version` / `description` / `author` / `license` | 元数据 |
| `type` | 固定 `"pipeline-pack"` |
| `when.fileExists` / `when.noFileExists` | 自动匹配条件（探测项目文件） |
| `priority` | 多 pack 匹配时的优先级（数字越大越优先） |
| `config.stages` | 启用的阶段数组，如 `[1,2,3,4]` |
| `config.roles` | `full` / `core` / `custom` |
| `config.agents` | 参与的 agent 列表（`boss-pm` 等） |
| `config.gates` | 启用门禁，如 `["gate0","gate1","gate2"]` |
| `config.agentStages` | agent → stage 映射 |
| `config.skipUI` / `skipFrontend` | 可选跳过标记 |
| `enabled` | 是否启用 |

参考内置：`packages/boss-cli/assets/pipeline-packs/api-only/`（后端专用）、`web-app/`、`solana-contract/`。

## Gate 插件契约

`plugin.json`：`type: "gate"`，`hooks.gate` 指向 gate 脚本。

`gate.js` 契约（CommonJS 或 ESM，导出一个函数）：

```js
// 输入：{ feature, stage, artifactsDir, config }
// 输出：{ passed: boolean, score?: number, reasons: string[] }
export default async function gate(ctx) {
  // 读取 ctx.artifactsDir 下产物，执行检查
  return { passed: true, score: 0.9, reasons: ['all checks passed'] };
}
```

- `passed: false` 时，Boss **不得宣布交付完成**（不变量 4）。
- 门禁执行进事件流：`PluginHookExecuted` / `PluginHookFailed`（降级模式写 STATE.md Gates 表）。
- `config` 来自 `plugin.json` 的 `config` 字段。

参考内置：`packages/boss-cli/assets/plugins/llm-judge/`（LLM-as-Judge）、`owasp-scan/`、`security-audit/`。

## 自定义 Agent 契约

`.boss/plugins/<name>/agent.md`，以 `agents/boss-*.md` 为范式。必须包含：

1. **角色定位**：一句话职责。
2. **触发时机 / stage**：在哪个阶段被派发。
3. **输入产物**：依赖哪些已完成产物。
4. **输出产物**：产出什么文件到 `.boss/<feature>/`。
5. **状态报告**：沿用子代理协议 `DONE` / `DONE_WITH_CONCERNS` / `NEEDS_CONTEXT` / `BLOCKED` / `REVISION_NEEDED`（见 `agents/prompts/subagent-protocol.md`）。
6. **门禁归属**：产物完成后走哪道 gate。

在 pack 的 `config.agents` 与 `config.agentStages` 里登记后，`/boss` 才会在 DAG 里派发它。

## 验证清单

生成扩展后：

- [ ] `boss packs detect <dir> --json` 列出新 pack（pack 类）
- [ ] `boss runtime register-plugins <feature>` 事件流出现 `PluginDiscovered`（plugin 类）
- [ ] JSON schema 合法（`enabled: true`、必填字段齐全）
- [ ] agent 状态报告沿用标准协议
- [ ] 无 CLI 时提示用户文件已就位，降级模式会手动加载
