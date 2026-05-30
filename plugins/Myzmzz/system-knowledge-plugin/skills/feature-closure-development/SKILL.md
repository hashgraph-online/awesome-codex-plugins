---
name: feature-closure-development
description: 指导在动手写代码前做"功能闭环分析"（pre-development feature-closure analysis）。当用户准备 develop / modify / refactor a feature（开发或修改某功能）、问"开发前要先弄清什么"、或需要回答"这个功能依赖什么 / 产出什么 / 谁使用它 / 失败后怎么恢复 / 状态如何变化 / 需要回归什么"这六个问题时触发。在真正改动业务代码之前先跑这套分析。当任务只是宽泛地查依赖图或维护知识库（用 system-knowledge-map）、或已进入测试阶段要组织业务链路测试（用 business-chain-testing）时，不要触发本 skill。
---

# 开发前功能闭环分析

在为某个功能写或改代码**之前**，先用知识图把这个功能的"闭环"看清楚，避免只盯单点、漏掉上下游和异常恢复。本 Skill 把六个核心问题逐一映射到具体的 MCP 工具调用。

工作流位置（§9.2 开发前）：用户提需求 → `feature_get` → `dependency_trace` → `impact_analyze` → 输出功能闭环分析 → 再进入开发。

> 约定：工具名用下划线（`feature_get` 等），点号写法为别名。读取类工具均为只读，可放心调用。

## 第 0 步：锁定目标功能

先确认目标功能在知识图中的 `featureId`。不确定时用 `feature_list` 浏览，或直接 `feature_get` 让其在找不到时返回相近 ID 建议。

## 六个核心问题 → 工具映射

### 1. 这个功能依赖什么？（depends on）

调用 `feature_get`（看 `dependsOn` / `provides` 概览），再调用 `dependency_trace` 取上游细节：

```json
{ "featureId": "deploy-config", "direction": "upstream", "depth": 1 }
```

逐条读 `upstream[].reason`，确认每个上游真实 `provides` 你需要的数据/状态。若上游是 `external` 类型依赖（Kubernetes/Helm/数据库/第三方 API），记下"状态来源"，开发时不要伪造其状态。

### 2. 它产出什么？（produces）

继续看 `feature_get` 返回的 `provides`（产出的数据或状态名，如 `helm-values`、`deploy-task-config`）。这些是下游契约——改动时不可随意删改产出，否则会断链。

### 3. 谁使用它？（who uses it）

调用 `dependency_trace` 取下游：

```json
{ "featureId": "deploy-config", "direction": "downstream", "depth": 1 }
```

读 `downstream[].reason`，明确每个消费方依赖你的哪一项产出。`feature_get` 的 `usedBy` 给出同样的消费方清单，可交叉核对。

### 4. 失败后怎么恢复？（failure recovery）

调用 `journey_get` 取该功能所在的业务链路，重点读 `failure_recovery`（按步骤列出的恢复动作，如 preflight 失败 → fix-config / re-run-preflight；execution-verify 失败 → view-log / retry / rollback / uninstall）：

```json
{ "journeyId": "full-deploy" }
```

如果该功能属于危险操作（部署、删除、卸载、权限、凭证类），必须确认它有明确的失败恢复路径；缺失则在闭环报告里标注为待补，并提示用 system-knowledge-map 的 `journey_upsert` 补登记。

### 5. 状态如何变化？（state transitions）

查实体状态机：用 CLI 生成可读图，或在功能定义里看 `states` 字段。

```bash
knowledge graph --type state-machine --entity DeployTask
# 产物：reports/state-machine-DeployTask.md
```

关注每个状态的 `allowed_actions` 与 `disabled_actions`——开发时要保证你的改动遵守状态门禁（如 draft 状态下 deploy/uninstall 必须 disabled）。

### 6. 需要回归什么？（regression scope）

调用 `impact_analyze`，传目标功能与你计划改动的文件：

```json
{
  "featureId": "deploy-config",
  "changeType": "modify",
  "changedFiles": ["部署系统/prototype/Page1Deploy.jsx"]
}
```

读取 `directImpact`（直接受影响功能）、`affectedEntities`、`regressionTests`（由测试路径的 `regression_scope` 汇总）、`knowledgeUpdateSuggestions`。`regressionTests` 就是开发后要回归的最小集合。

## 输出：功能闭环分析报告

把上述结果汇总成一份简明报告再开始编码，至少包含：

1. **依赖（上游）**：功能 + 原因 + 是否外部系统。
2. **产出（契约）**：provides 列表，标注哪些是下游强依赖、不可破坏。
3. **消费方（下游）**：used_by + 各自依赖的产出。
4. **失败恢复**：链路中该功能的恢复动作；危险操作是否齐备。
5. **状态变化**：相关状态机的 allowed/disabled actions 约束。
6. **回归范围**：impact 给出的 `regressionTests` 与受影响实体。

报告产出后，再进入实际开发。开发中若新增了功能、状态、实体或测试路径，切回 system-knowledge-map 用 `*_upsert`（默认草稿，确认后加 `confirm:true`）同步知识图，并跑 `knowledge validate`。
