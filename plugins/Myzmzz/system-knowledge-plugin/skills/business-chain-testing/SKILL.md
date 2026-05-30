---
name: business-chain-testing
description: 指导按"业务链路"（business chain / journey）而非单个按钮来组织测试。当用户要 test a feature end-to-end（端到端测试某功能）、plan/organize tests（规划测试用例）、do regression testing（做回归测试）、或问"该按什么顺序测 / 前置条件是什么 / 要回归哪些链路 / 异常怎么验"时触发。把测试拆成前置条件、主链路、后置验收、异常恢复、上下游回归五层。当任务是开发前的功能闭环分析（用 feature-closure-development），或只是查询/维护知识图（用 system-knowledge-map）时，不要触发本 skill。
---

# 按业务链路组织测试

不要只测"点了某个按钮"。一个功能要放进它所属的**业务链路**里测：先满足前置条件，再走主链路，验收后置结果，验证异常恢复，最后回归受影响的上下游。本 Skill 用 `test_path_generate`、`journey_get` 和测试路径里的 `regression_scope` 把测试拆成五层。

工作流位置（§9.4 测试前）：`test_path_generate` 得到前置条件/步骤/验收项 → 执行浏览器/API/命令测试 → 对照验收项记录结果。

> 约定：工具名用下划线（`test_path_generate` 等），点号写法为别名。

## 第 0 步：取测试路径与链路

1. 调用 `test_path_generate` 生成目标功能的测试路径：

   ```json
   { "featureId": "execution-verify", "scope": "e2e" }
   ```

   返回 `testPath`、`preconditions`、`steps`、`assertions`。**注意区分**：结果会标明是"已登记测试路径"还是"基于链路+依赖图推导的草案"——草案需人工核对后再执行。

2. 调用 `journey_get` 取对应业务链路，拿到完整 `steps`、`failure_recovery`、`acceptance`：

   ```json
   { "journeyId": "full-deploy" }
   ```

3. 需要查回归范围时，从该功能登记的测试路径里读 `regression_scope`（也可由 `impact_analyze` 的 `regressionTests` 汇总得到）。

## 五层测试组织

### 第 1 层：前置条件测试（precondition）

来自 `test_path_generate` 的 `preconditions`（如：集群已接入、应用已选择、部署资产已解析、部署配置已保存、预检通过）。逐项搭建/校验前置状态——前置不满足，主链路结果不可信。每个 precondition 通常对应上游功能的某个产出状态（`feature.state`，如 `deploy-config.configured`）。

### 第 2 层：主链路测试（main chain）

按 `test_path_generate` 的 `steps` 顺序执行（如：保存部署配置 → 执行预检 → 点击部署 → 查看实时日志 → 同步资源），并与 `journey_get` 的 `steps` 对齐，确保覆盖整条链路而非单点。用浏览器/API/命令逐步执行。

### 第 3 层：后置验收测试（post-acceptance）

对照 `assertions`（来自测试路径）与链路的 `acceptance`（如：Helm Release 为 deployed、Deployment Ready、Pod Running、Service 已创建、报告可导出）逐条核验并记录结果。验收项来自真实外部系统状态时（Kubernetes/Helm/数据库），必须实查对应系统，不得用知识图伪造。

### 第 4 层：异常恢复测试（failure-recovery）

读 `journey_get` 的 `failure_recovery`，按步骤注入失败并验证恢复动作可用（如：preflight 失败 → fix-config / re-run-preflight；execution-verify 失败 → view-log / retry / rollback / uninstall）。危险操作（部署/删除/卸载/权限/凭证类）必须覆盖至少一个异常场景。

### 第 5 层：上下游回归测试（upstream/downstream regression）

读测试路径的 `regression_scope`（或 `impact_analyze` 的 `regressionTests`），对其中每个功能/链路再跑一遍其自身的主链路 + 验收：

```json
{ "featureId": "application-management", "changeType": "modify",
  "changedFiles": ["部署系统/prototype/Page1Deploy.jsx"] }
```

`impact_analyze` 返回的 `regressionTests`（如 `deploy-e2e`、`application-switching`、`asset-upload-and-parse`）即回归清单，逐个用 `test_path_generate` 取其路径后执行。

## 输出：测试执行与记录

- 按五层顺序执行，逐项对照 `assertions` / `acceptance` 记录通过/失败与证据。
- 若发现知识图中测试路径缺前置或缺验收（违反"测试路径不能只含按钮动作"的质量规则），切到 system-knowledge-map 用 `test_path_upsert` 补登记（默认草稿，确认后加 `confirm:true`），并跑 `knowledge validate`。
- 测试完成后，把回归结果回填，作为 §9.5 开发后审计（`audit-diff`）的输入。
