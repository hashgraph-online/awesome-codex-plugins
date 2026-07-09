# Boss No-CLI Fallback — 纯 Markdown 降级模式

本文件定义 Boss 在**检测不到 `boss` CLI runtime** 时的降级运行协议。目标：把准入门槛从「必须先装二进制」降到「agent 能读写文件」。CLI 是**可审计性增强**，不是准入条件。

## 何时进入降级模式

派发流水线前先探测 CLI：

```bash
boss --version 2>/dev/null
```

- 命令成功 → **完整模式**：状态真相源是 runtime 事件流（`references/runtime-surface.md`），本文件不适用。
- 命令失败 / 未安装 → **降级模式**：按本文件用纯 Markdown 承载状态。

在降级模式下必须**明确告知用户**：

> ⚠️ 未检测到 boss CLI，进入纯 Markdown 降级模式。流水线仍会运行，但状态记录在 `.boss/<feature>/STATE.md` 而非可审计事件流；门禁为「协议约束」而非「CLI 强制」。安装 `npm i -g @blade-ai/boss-skill` 可启用事件溯源 + 不可绕过门禁 + 确定性 eval。

## 状态承载：STATE.md 取代事件流

降级模式下，`.boss/<feature>/STATE.md` 是唯一状态文件。用**追加式**记录，模拟事件流的不可回改语义——只在文件末尾追加，不修改历史行。

STATE.md 结构：

```markdown
# <feature> — Boss State (fallback mode)

## Meta
- mode: fallback
- created: <date>
- roles: <full|core>
- lang: <zh|en>

## Stage Status
| stage | status | updated |
|-------|--------|---------|
| 1 planning | completed | <date> |
| 2 review   | running   | <date> |
| 3 dev+qa   | pending   | - |
| 4 deploy   | pending   | - |

## Artifacts
| artifact | stage | status | path |
|----------|-------|--------|------|
| prd.md          | 1 | done | .boss/<feature>/prd.md |
| architecture.md | 1 | done | .boss/<feature>/architecture.md |

## Gates
| gate | when | result | notes |
|------|------|--------|-------|
| Gate 0 | after dev | - | - |

## Event Log (append-only)
- <date> stage-1 started
- <date> artifact prd.md recorded
- <date> stage-1 completed
```

## CLI 动作 → 降级等价物

| 完整模式 CLI | 降级等价动作 |
|--------------|--------------|
| `boss project init <feature>` | 创建 `.boss/<feature>/` 与 `STATE.md` 骨架 |
| `boss runtime init-pipeline` | 在 STATE.md 写入 Stage Status 表（全 pending） |
| `boss runtime update-stage <f> <N> running` | 在 Stage Status 表更新该行 status，并向 Event Log 追加一行 |
| `boss runtime record-artifact <f> <a> <N>` | 在 Artifacts 表追加该产物行，向 Event Log 追加一行 |
| `boss runtime get-ready-artifacts` / `nextNodeIds` | 按 `references/orchestration-loop.md` 默认 DAG 手动推导下一批就绪产物 |
| `boss runtime evaluate-gates <f> <gate>` | 手动执行门禁检查（编译/lint/测试/覆盖率），把结论写入 Gates 表 + Event Log；**失败仍不得宣布通过** |
| `boss packs detect` | 读取项目文件手动判断技术栈（见 `agents/shared/tech-detection.md`），默认 pack |
| `boss runtime generate-summary` | 汇总 STATE.md 各表，产出 `summary-report.md` |
| `boss runtime query-memory` | 跳过（降级模式无记忆库）；改为读取 `.boss/<feature>/` 已有产物作上下文 |
| `boss runtime record-feedback` / `retry-agent` | 在 Event Log 追加 feedback 行，重新派发目标 Agent |

## 降级模式下仍然保持的不变量

即使没有 CLI，以下不变量**不放松**：

1. **编排职责不变**：Boss 仍只编排，不替专业 Agent 写正式产物。
2. **产物驱动不变**：文档写入 `.boss/<feature>/`，完成后在 STATE.md 的 Artifacts 表登记。
3. **门禁不可绕过（协议级）**：测试/门禁失败时不得宣布交付完成。降级只是让门禁从「CLI 强制」变为「协议约束」，判定标准不变（见 `references/quality-gate.md`）。
4. **渐进式披露不变**：仍按需读取 reference / prompt / template。
5. **append-only**：STATE.md 的 Event Log 段只追加不回改，保留最低限度可审计性。

## 降级模式的诚实边界

降级模式**不能**提供的（需要 CLI）：

- 事件流指纹级 resume / reuse 决策（`workflow-plan.json`、`runId`）。
- 确定性 eval（`npm run evals`）对 transcript 的自动评分。
- projector 物化的只读 `execution.json` 与机器可读 `nextNodeIds`。
- `boss design preview`、`render-diagnostics` 等 CLI-only 渲染。

需要以上能力时，提示用户安装 CLI 后用 `--continue-from` 迁移到完整模式：已有 `.boss/<feature>/` 产物可被 `boss project init` 复用，STATE.md 作为迁移前的历史参考保留。
