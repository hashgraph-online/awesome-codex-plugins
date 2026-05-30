---
name: system-knowledge-map
description: 指导智能体如何查询、维护和更新系统知识图（system knowledge graph / knowledge base）。当用户要求 analyze feature dependencies（分析功能依赖）、design a new feature（设计新功能）、assess change impact（评估改动影响）、或 maintain the knowledge base（维护/更新知识库 features/dependencies/entities/states/journeys/test-paths）时触发。也适用于"这个功能依赖谁/谁依赖它"、"改了某文件会影响什么"、"把新功能登记进知识图"。当任务只是纯写业务代码、调试逻辑、不涉及知识图谱的查询或维护时，不要触发；具体的"开发前功能闭环分析"请用 feature-closure-development，"按业务链路测试"请用 business-chain-testing。
---

# 系统知识图：查询、维护与更新

本 Skill 指导你（智能体）正确使用系统知识图插件的 MCP 工具与 `knowledge` CLI，去**查询**功能依赖、**评估**改动影响、并**维护**知识库（`knowledge/` 下的 6 个 YAML：`features` / `dependencies` / `entities` / `states` / `journeys` / `test-paths`）。

核心原则（务必遵守）：

- **智能体负责语义，脚本负责确定性**：依赖原因、业务判断由你补充；唯一性、引用完整性、图生成由 CLI/工具保证。
- **影响分析只给建议，不替用户做业务确认**：输出影响面与回归建议后，需要人工确认核心依赖再落地。
- **写入分草稿与正式两态**：所有 `*_upsert` 工具**默认只写 `knowledge/.drafts/`**；只有显式传 `confirm: true` 才写入正式 YAML。先写草稿、校验、人工确认，再正式落盘。
- 工具名按 MCP 约定用下划线（如 `feature_get`），文档中的点号写法（`feature.get`）是同一工具的别名。

下面按四类常见任务给出具体调用顺序。

## 场景 A：分析功能依赖（analyze feature dependencies）

目的：搞清一个功能"是什么、依赖谁、被谁依赖"。

1. 调用 `feature_get` 取功能定义。先用摘要，必要时再取全量：

   ```json
   { "featureId": "deploy-config", "detail": "summary" }
   ```

   关注返回的 `dependsOn` / `usedBy` / `provides`。若 `featureId` 不存在，工具会返回相近 ID 建议，据此纠正。

2. 调用 `dependency_trace` 取上下游及多级依赖。默认 `depth: 1`、`direction: "both"`，避免上下文膨胀；确需深链路时再加大 `depth`：

   ```json
   { "featureId": "deploy-config", "depth": 1, "direction": "both" }
   ```

   返回的 `upstream` / `downstream` 每条都带 `reason`（依赖原因），把它读给用户。

3. 需要整图视角时，用 CLI 生成 Mermaid 依赖图供人阅读：

   ```bash
   knowledge graph --type dependency
   # 产物：reports/dependency-graph.md
   ```

   状态机或链路图同理：`knowledge graph --type state-machine --entity DeployTask`、`knowledge graph --type journey --name full-deploy`。

## 场景 B：设计新功能（design a new feature）

目的：在登记新功能前，先确认它在系统中的位置，再写入草稿。

1. 用 `feature_list` 浏览现有功能，避免重复登记、确认命名风格。

2. 对新功能的每个上游候选调用 `feature_get` / `dependency_trace`，确认它真实 `provides` 你要消费的数据或状态。

3. 用 `feature_upsert` 写**草稿**（不带 confirm，落到 `knowledge/.drafts/`）。补齐建议字段：`name` `module` `description` `maturity`（idea/prototype/usable/production）`owner_role` `entry_points` `code_refs` `depends_on` `provides` `used_by` `states`：

   ```json
   {
     "featureId": "deploy-report",
     "feature": {
       "name": "部署报告", "module": "部署流程",
       "maturity": "prototype", "owner_role": "运维",
       "depends_on": ["execution-verify"], "provides": ["deploy-report-doc"],
       "used_by": [], "states": ["draft", "ready"]
     }
   }
   ```

4. 为每条新依赖边调用 `dependency_upsert`（草稿），务必写明 `type`（data/state/gate/ui/external）和 `reason`——没有原因的依赖边会被校验质量规则挑出。

5. 运行 `knowledge validate`（或 `knowledge_validate` 工具）校验草稿；按报错修正。

6. 与用户确认核心依赖无误后，**重发同一 upsert 调用并加 `"confirm": true`**，正式写入 `knowledge/` YAML。

## 场景 C：评估改动影响（assess change impact）

目的：改某功能或某文件前，先算清影响面与回归范围。

1. 调用 `impact_analyze`。可按功能、也可按变更文件（用 `code_refs` 反查功能）：

   ```json
   {
     "featureId": "application-management",
     "changeType": "modify",
     "changedFiles": ["部署系统/prototype/Page1Deploy.jsx"]
   }
   ```

   读取返回的 `directImpact`（直接受影响功能）、`affectedEntities`（受影响实体）、`regressionTests`（来自测试路径 `regression_scope`）、`knowledgeUpdateSuggestions`（知识图待更新提示）。

2. 需要落盘报告时，用 CLI：

   ```bash
   knowledge impact --feature deploy-config
   knowledge impact --changed-files 部署系统/prototype/Page1Deploy.jsx
   # 产物：reports/impact-report.md
   ```

3. 把 `regressionTests` 交给 business-chain-testing 去组织实际回归测试；把 `knowledgeUpdateSuggestions` 落到场景 D 去同步知识图。

## 场景 D：维护/更新知识库（maintain the knowledge base）

目的：代码变更后保持知识图与代码一致；初始建图同理。

1. 让脚本先发现变更，再由你补语义：

   ```bash
   knowledge audit-diff   # 结合 git diff，提示哪些 feature 的 code_refs 被命中、是否漏登记页面/状态/测试
   ```

   或用 `change_audit` 工具做同样的提示。新建图时先 `knowledge scan-code --root .` 生成 `reports/feature-draft.yaml`（**仅草稿**，不可直接作为最终业务图）。

2. 按提示补全：新功能 → `feature_upsert`；新依赖边 → `dependency_upsert`；新业务链路 → `journey_upsert`（含 `failure_recovery` 与 `acceptance`）；新测试路径 → `test_path_upsert`（含 `preconditions` / `steps` / `assertions` / `regression_scope`）。这些写入**默认是草稿**。

3. 运行 `knowledge validate`（或 `knowledge_validate`）跑全部基础规则 + 质量规则：唯一 `featureId`、引用存在性、核心功能须有测试路径与下游说明、危险操作（部署/删除/卸载/权限/凭证）须有前置条件与失败恢复、状态机须定义 allowed/disabled actions、依赖边须有原因等。按报错修正草稿。

4. 校验通过且与用户确认后，对相应 `*_upsert` 重发并加 `"confirm": true` 正式落盘；最后可再跑一次 `knowledge graph` 让图与文档同步。

## 安全与边界

- 知识库不写入任何敏感凭证明文；不要把密钥、令牌写进 YAML。
- 真实外部系统状态（Kubernetes、Helm、数据库、第三方 API）必须由对应系统查询，知识图只记录"状态来源"，不得伪造真实状态。
- MCP 工具默认只操作插件知识库，不直接调用业务系统 API。
