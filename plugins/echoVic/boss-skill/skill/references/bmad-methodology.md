# BMAD 方法论参考文档

## 概述

BMAD（Breakthrough Method of Agile AI-Driven Development）是一种突破性的敏捷 AI 驱动开发方法论，专为人机协作设计，通过专业化的 AI Agent 团队完成完整的软件开发生命周期。

**v3.x 核心特性**：
- 事件溯源（Event Sourcing）驱动的状态管理
- DAG 依赖系统控制产物流转
- 三层质量门禁（Quality Gates）
- Pipeline Pack 自动适配项目类型
- 可扩展的插件系统
- Claude Code Hooks 生命周期集成

---

## 核心理念

### 1. 专业化分工

BMAD 将软件开发流程分解为 9 个专业化角色，每个角色由专门的 AI Agent 承担：

| 角色 | Agent 文件 | 职责 | 输出产物 |
|------|-----------|------|----------|
| 产品经理 (PM) | `boss-pm.md` | 需求分析、PRD 编写 | `prd.md` |
| 系统架构师 | `boss-architect.md` | 技术架构、选型决策、API 契约 | `architecture.md` |
| UI/UX 设计师 | `boss-ui-designer.md` | 界面设计、用户体验 | `ui-spec.md` + `ui-design.json`（可选） |
| 技术负责人 | `boss-tech-lead.md` | 技术评审、风险评估 | `tech-review.md` |
| Scrum Master | `boss-scrum-master.md` | 任务拆解、开发规划 | `tasks.md` |
| 前端开发 | `boss-frontend.md` | 前端代码实现 | 源代码 |
| 后端开发 | `boss-backend.md` | 后端代码实现 | 源代码 |
| QA 工程师 | `boss-qa.md` | 测试验证 | `qa-report.md` |
| DevOps | `boss-devops.md` | 部署运维 | `deploy-report.md` |

### 2. 产物驱动（DAG）

产物之间的依赖关系由 `packages/boss-cli/assets/artifact-dag.json` 定义为有向无环图（DAG），并可通过 `.boss/artifact-dag.json` 做项目级覆盖，而非简单线性流：

```
design-brief → prd.md ─┬→ architecture.md → tech-review.md → tasks.md → [code] → qa-report.md → deploy-report.md
                       ├→ ui-spec.md(opt) ┘
                       └→ ui-design.json(opt) ┘
```

**DAG 规则**：
- 每个产物声明其 `inputs`（依赖）和 `stage`
- 只有当所有 inputs 的产物状态为 `done` 时，该产物才进入 `ready` 状态
- `qa-report.md` 依赖 `code` + `prd.md`（QA 需要对照 PRD 验收标准）

### 3. 全自动流水线

区别于传统的分步确认模式，Boss Mode 采用全自动流水线：
- 一次性完成从需求到部署的完整流程
- 由事件溯源系统追踪每一步状态
- 质量门禁在阶段间自动执行
- 最终交付可运行、可访问的产物

---

## 五阶段工作流

### Stage 0：准备（可选）

**产物**：`design-brief`（设计摘要）
**说明**：用户可提供初始设计简介，作为后续 Agent 的参考输入。跳过时直接进入 Stage 1。

### Stage 1：规划（Planning）

**目标**：将用户想法转化为可执行规格

**参与 Agent**：
- PM Agent → 创建 `prd.md`
- Architect Agent → 设计 `architecture.md`（包含 API 契约定义）
- UI Designer Agent → 创建 `ui-spec.md` 和 `ui-design.json`（可选，`skipUI` 时跳过）

**并行执行**：三个 Agent 可以并行工作

**质量门禁**：Stage 1 完成后执行 Gate 0（代码质量基线）

### Stage 2：拆解（Decomposition）

**目标**：将规格转化为可实施的开发计划

**参与 Agent**：
- Tech Lead Agent → 技术评审，产出 `tech-review.md`
- Scrum Master Agent → 创建详细任务 `tasks.md`

**串行执行**：Tech Lead 评审完成后，Scrum Master 才能拆解任务

**Tech Lead 职责**（非故事分解）：
- 评审架构设计的合理性
- 识别技术风险和依赖
- 可发起 `REVISION_NEEDED` 请求架构师修订

### Stage 3：开发（Development）

**目标**：实现代码并持续验证

**参与 Agent**：
- Frontend Agent + Backend Agent → 并行实现代码
- QA Agent → 对照 PRD 验收标准验证

**工作模式**：
1. 按任务顺序实现代码（前后端并行）
2. 实现中允许 Agent 通过执行中会话层做点对点对齐或小范围 huddle
3. 代码完成后 QA 进行验证
4. 发现问题时，先落执行会话结论，再进入修复或正式修订循环

**质量门禁**：Gate 1（测试门禁）、Gate 2（性能门禁）

### Stage 4：部署（Deployment）

**目标**：部署应用并生成报告

**参与 Agent**：
- DevOps Agent → 部署应用

**产物**：
- `deploy-report.md`
- 可访问的 URL

---

## 事件溯源系统

### 核心架构

Boss Mode 采用 **Event Sourcing + CQRS** 模式管理流水线状态：

```
命令（Agent 动作）
    ↓
追加事件 → events.jsonl（append-only，唯一事实源）
    ↓
Projector 投影 → execution.json（物化视图，可随时从事件重建）
```

### 事件类型

| 类别 | 事件 | 说明 |
|------|------|------|
| Pipeline | `PipelineInitialized` | 流水线创建 |
| Pipeline | `PackApplied` | Pipeline Pack 应用 |
| Stage | `StageStarted` / `StageCompleted` / `StageFailed` | 阶段生命周期 |
| Stage | `StageRetrying` / `StageSkipped` | 重试与跳过 |
| Artifact | `ArtifactRecorded` | 产物写入完成 |
| Gate | `GateEvaluated` | 门禁评估结果 |
| Agent | `AgentStarted` / `AgentCompleted` / `AgentFailed` | Agent 执行追踪 |
| Agent | `AgentRetryScheduled` | Agent 重试调度 |
| Conversation | `ConversationOpened` / `ConversationMessageAppended` | 执行中会话线程与消息 |
| Conversation | `ConversationResolved` / `TodoMaterialized` | 会话结论与派生待办 |
| Feedback | `RevisionRequested` | 修订请求（如 Tech Lead 要求架构师修改） |
| Plugin | `PluginDiscovered` / `PluginActivated` / `PluginHookExecuted` | 插件生命周期 |

### 状态机

```
Pipeline: initialized → running → completed | failed
Stage:    pending → running → completed | failed | retrying | skipped
Agent:    pending → running → completed | failed
```

### 运行时数据结构

```
.boss/<feature>/.meta/
├── execution.json      # 物化状态（CQRS read model）
├── events.jsonl        # 事件日志（append-only truth source）
├── agent-log.jsonl     # Agent 执行记录
└── notifications.jsonl # 通知日志
```

### Projector

`runtime/projectors/materialize-state.js` 从 `events.jsonl` 重建 `execution.json`：
- 逐条读取事件 → apply 到状态
- 计算派生指标：totalDuration, stageTimings, gatePassRate, retryTotal, agentSuccessRate
- 同时物化 conversations、derivedTodos 和 conversationMetrics，保留执行中协作的可回放视图
- 支持随时从事件完全重建状态

---

## DAG 依赖系统

### 定义文件

`packages/boss-cli/assets/artifact-dag.json` 定义了内置产物依赖图，项目可用 `.boss/artifact-dag.json` 覆盖：

```json
{
  "artifacts": {
    "prd.md": {
      "stage": 1,
      "agent": "boss-pm",
      "inputs": ["design-brief"],
      "template": "templates/prd.md.template"
    },
    "qa-report.md": {
      "stage": 3,
      "agent": "boss-qa",
      "inputs": ["code", "prd.md"],
      "template": "templates/qa-report.md.template"
    }
  }
}
```

### DAG 规则

1. **就绪判断**：产物的所有 `inputs` 状态为 `done` 时，该产物进入 `ready`
2. **可选依赖**：标记为 `optional: true` 的产物（如 `design-brief`、`ui-spec.md`、`ui-design.json`）跳过时不阻塞下游
3. **并行检测**：同一 stage 内无互相依赖的产物可并行执行
4. **模板绑定**：每个产物关联 `templates/` 下的模板文件

### 相关 CLI

| CLI | 功能 |
|------|------|
| `boss runtime get-ready-artifacts` | 检查产物是否 ready |
| `boss runtime check-stage` | 检查阶段状态 |
| `boss runtime record-artifact` | 记录 ArtifactRecorded 事件 |
| `boss design preview <feature>` | 预览 `.boss/<feature>/ui-design.json` 可渲染设计产物 |

---

## 质量门禁（Quality Gates）

### 三层门禁体系

| 门禁 | 入口 | 执行时机 | 检查内容 |
|------|------|----------|----------|
| Gate 0 | `boss runtime evaluate-gates <feature> gate0` | Stage 1 后 | TypeScript 编译、Lint、npm audit、敏感信息扫描、不安全代码模式 |
| Gate 1 | `boss runtime evaluate-gates <feature> gate1` | Stage 3 后 | 单元测试、覆盖率（≥70%）、E2E 测试 |
| Gate 2 | `boss runtime evaluate-gates <feature> gate2` | Stage 3 后 | Lighthouse 性能分数（≥80）、API P99 延迟（<500ms） |

### Gate 0 默认安全检查

Gate 0 内置两类安全检查（无需额外插件）：

1. **敏感信息扫描**（secrets-scan）：检测 AWS Key、Private Key、GitHub Token、OpenAI Key 等
2. **不安全代码模式**（unsafe-patterns）：检测 `eval()`、`dangerouslySetInnerHTML`、`innerHTML =` 等

### 门禁输出格式

```json
{
  "checks": [
    { "name": "typescript-compile", "status": "pass" },
    { "name": "secrets-scan", "status": "fail", "detail": "发现敏感信息" }
  ]
}
```

### 统一入口

`boss runtime evaluate-gates` 是门禁统一入口：
- 内置 gate 由 Boss CLI 的 TypeScript runtime 实现
- 插件 gate 通过 `plugin.json` 的 `hooks.gate` 指向可执行文件
- exit 0 = 通过，exit 1 = 不通过

---

## Pipeline Pack

### 概念

Pipeline Pack 是预定义的流水线配置，指定启用哪些 Agent、Stage、Gate，以及跳过哪些环节。系统根据项目特征自动检测适用的 Pack。

### 内置 Pack

| Pack | Agent 数量 | 特点 | 自动检测条件 |
|------|-----------|------|-------------|
| **default** | 9（全部） | BMAD 全流程 | 默认 |
| **core** | 5 | 轻量核心，跳过 UI/评审/拆解 | — |
| **api-only** | 7（无 Frontend, UI） | 纯 API 项目 | `package.json` 存在但无 `app/` 或 `pages/` 目录 |
| **solana-contract** | 5 | Anchor 框架 Solana 合约 | 特定依赖 |

### Pack 配置结构

```json
{
  "name": "core",
  "agents": ["boss-pm", "boss-architect", "boss-frontend", "boss-backend", "boss-qa"],
  "stages": [1, 3, 4],
  "gates": ["gate0", "gate1"],
  "flags": { "skipUI": true, "skipReview": true }
}
```

### 自动检测

`boss packs detect` 根据以下条件自动选择 Pack：
- `when.fileExists` — 文件存在
- `when.noFileExists` — 文件不存在
- `when.packageJsonHas` — package.json 含特定字段
- `priority` — 数值越高优先级越高

---

## 插件系统

### 插件类型

| 类型 | 说明 | 示例 |
|------|------|------|
| `gate` | 自定义门禁 | `security-audit`（安全审计） |
| `agent` | 自定义 Agent | — |
| `pipeline-pack` | 自定义 Pack | — |
| `reporter` | 自定义报告生成 | — |

### 插件目录结构

```
.boss/plugins/<plugin-name>/
├── plugin.json    # 插件声明（类型、触发阶段、Schema 定义）
├── gate.js        # 门禁可执行文件示例（gate 类型）
└── ...
```

### 插件 Schema

`packages/boss-cli/assets/plugin-schema.json` 定义插件格式：
- Hook 阶段：`pre-stage, post-stage, pre-gate, gate, post-gate, report`
- 支持条件激活和优先级

### 插件事件

插件生命周期产生事件：
- `PluginDiscovered` — 发现插件
- `PluginActivated` — 激活插件
- `PluginHookExecuted` — 插件 Hook 执行成功
- `PluginHookFailed` — 插件 Hook 执行失败

---

## Hooks 生命周期

### 概念

Boss Mode 通过 Hooks 机制在关键时点注入行为，实现流水线自动化。Claude Code Hook 定义在 `hooks/claude/hooks.json`，Codex Hook 定义在 `hooks/codex/hooks.json`。

### Hook 事件类型

| 事件 | 触发时机 | 用途 |
|------|----------|------|
| `SessionStart` (startup) | 新会话启动 | 加载 pipeline 上下文 |
| `SessionStart` (resume) | 会话恢复 | 列出未完成 pipeline |
| `PreToolUse` (Write/Edit) | 写文件前 | 产物守卫：保护 execution.json、验证 stage 状态 |
| `PreToolUse` (Bash) | 执行命令前 | 危险命令拦截（rm -rf, git push --force 等） |
| `PostToolUse` (Write) | 写文件后 | 自动追踪产物到 execution.json |
| `PostToolUse` (Bash) | 执行命令后 | 捕获 gate/harness/test 上下文 |
| `SubagentStart` | 子 Agent 启动 | 注入 pipeline stage 上下文 |
| `SubagentStop` | 子 Agent 结束 | 记录执行到 agent-log.jsonl |
| `Stop` | 会话即将结束 | 阻止 pipeline 阶段运行时提前退出 |
| `Notification` | 通知事件 | 异步记录到 notifications.jsonl |
| `SessionEnd` | 会话结束 | 保存状态并生成摘要 |

### 危险命令拦截

`PreToolUse(Bash)` Hook 拦截以下模式：

| 模式 | 风险 |
|------|------|
| `rm -rf` / `rm -r` | 不可恢复数据丢失 |
| `git push --force` | 覆盖远程历史 |
| `git reset --hard` | 丢弃未提交更改 |
| `DROP TABLE/DATABASE` | 删除数据库对象 |
| `TRUNCATE TABLE` | 清空表数据 |
| `chmod 777` | 过于宽泛的权限 |
| `mkfs` | 格式化磁盘 |
| `dd of=/dev/` | 写入设备文件 |

### Hook 执行机制

所有 Hook 通过 `boss hooks run` 进入 Boss CLI hook dispatcher，由 CLI 负责解析插件根目录与 hook profile，并统一调度具体 Hook。

---

## 产物管理

### 目录结构

```
.boss/
├── <feature-name>/
│   ├── prd.md              # 产品需求文档
│   ├── architecture.md     # 系统架构文档（含 API 契约）
│   ├── ui-spec.md          # UI/UX 规范（可选）
│   ├── ui-design.json      # 可渲染 UI 设计（可选）
│   ├── tech-review.md      # 技术评审报告
│   ├── tasks.md            # 开发任务
│   ├── qa-report.md        # QA 测试报告
│   ├── deploy-report.md    # 部署报告
│   └── .meta/
│       ├── execution.json      # 物化状态
│       ├── events.jsonl        # 事件日志
│       ├── agent-log.jsonl     # Agent 执行记录
│       └── notifications.jsonl # 通知日志
```

### 模板

每种产物都有对应的模板文件，位于 `templates/` 目录：

| 模板 | 产物 |
|------|------|
| `templates/prd.md.template` | 产品需求文档 |
| `templates/architecture.md.template` | 架构设计文档 |
| `templates/ui-spec.md.template` | UI/UX 规范 |
| `templates/ui-design.json.template` | 可渲染 UI 设计 |
| `templates/tech-review.md.template` | 技术评审报告 |
| `templates/tasks.md.template` | 任务拆解 |
| `templates/qa-report.md.template` | QA 测试报告 |
| `templates/deploy-report.md.template` | 部署报告 |

---

## Agent 协作协议

### 状态报告

每个 Agent 任务完成后必须输出结构化状态块：

```
[BOSS_STATUS]
status: DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED | REVISION_NEEDED
summary: 一句话总结执行结果
conversation_id: [仅参与执行中会话时填写]
resolution_summary: [仅会话已收敛时填写]
todo_ids: [仅会话产出 todo 时填写]
concerns: [仅 DONE_WITH_CONCERNS 时填写]
missing: [仅 NEEDS_CONTEXT 时填写]
blocker: [仅 BLOCKED 时填写]
revision_target: [仅 REVISION_NEEDED 或会话升级为正式修订时填写，如 architecture.md]
revision_reason: [仅 REVISION_NEEDED 时填写]
[/BOSS_STATUS]
```

### 执行中会话闭环

- 任意 Agent 可发起 `ask`、`challenge`、`propose`、`request_change`、`escalate`、`huddle`、`resolve`
- 每条会话都必须 anchored 到 `artifact`、`task`、`scope` 或 `decision`
- 每次 `resolve` 都必须 materialize 为至少一个 executable、single-owner todo，或升级为正式 `RevisionRequested` 修订循环

### 修订循环

当 Tech Lead 发现架构问题时：
1. Tech Lead 输出 `REVISION_NEEDED`，指明 `revision_target` 和 `revision_reason`
2. 系统生成 `RevisionRequested` 事件
3. Architect 接收修订请求，针对性修改
4. 修订最多 2 轮，避免无限循环

### API 契约管理

- Architect 在 `architecture.md` §5 定义 API 契约
- Backend Agent 严格实现契约，偏差需记录
- Frontend Agent 基于契约实现统一 API 服务层
- 类型定义由后端导出，前端对齐

---

## 最佳实践

### 1. 需求描述

好的需求描述应该包含：
- 功能目标
- 用户类型
- 核心场景
- 技术约束（如有）

### 2. Pipeline Pack 选择

- 全功能项目 → `default`
- 纯 API 无前端 → `api-only`
- 快速原型 → `core`（跳过 UI 和评审）
- 系统会自动检测，也可手动指定

### 3. 质量门禁

- Gate 0 是基线，所有 Pack 都包含
- 如需额外安全审计，使用 `security-audit` 插件
- 门禁失败时 Stage 标记为 `failed`，可重试

---

## 参考资源

- [BMAD-METHOD GitHub](https://github.com/bmad-code-org/BMAD-METHOD)
- [Agile Manifesto](https://agilemanifesto.org/)
- [EARS Requirements Syntax](https://www.iaria.org/conferences2013/filesICCGI13/ICCGI_2013_Tutorial_Terzakis.pdf)
