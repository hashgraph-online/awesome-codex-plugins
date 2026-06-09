---
name: agent-dev-workshop
description: >
  交互式 AI Agent 开发工作坊：通过 6 阶段深度协作对话，引导用户完成 Agent 需求分析、架构设计、
  工具定义、Prompt 与编排设计、代码生成、验证迭代，产出可直接运行的 Agent 项目。
  框架无关设计优先，支持 LangChain / EINO / AutoGen / AgentScope / CrewAI 等 ADK 框架。
origin: ECC
---

# Agent Dev Workshop

交互式 AI Agent 开发工作坊。用户通过深度协作式对话，逐阶段完成 Agent 设计并生成**可直接运行的项目代码**。

## 何时激活

- 用户说"开发 agent"、"创建 agent"、"构建 agent"、"agent 开发"
- 用户要基于 EINO / LangChain / AutoGen / AgentScope / CrewAI 创建 Agent 应用
- 用户要将已有 Agent 迁移到另一个框架
- 用户说"agent dev"、"build agent"、"create agent"、"develop agent"
- `/agent-dev` 命令入口

## 三种运行模式

### 默认模式（深度协作）

完整 6 阶段交互流程。每个阶段结束必须用户确认后才推进到下一阶段，每个工具/组件逐一交互确认。

### 快速模式（`--quick`）

用户给一句话需求 → 自动执行 Phase 1-4（推断 Agent 类型、匹配架构模式、生成默认工具和 Prompt）→ 仅在 Phase 5 代码生成后做一次整体确认 → Phase 6 验证。适合有经验用户或原型快速验证。

**快速模式约束**：
- 自动推断时，选择最常见的默认值（如：单 Agent 默认 ReAct，多角色默认 Multi-Agent Conversation）
- 框架选择依据用户指定语言自动匹配（Python → LangChain，Go → EINO，未指定 → LangChain）
- 生成后必须完整展示项目结构和核心文件内容，等待用户确认

### 导入模式（`--import`）

用户指定已有 Agent 代码路径：
1. **分析现有代码**：识别框架、Agent 类型、工具列表、Prompt、编排逻辑
2. **生成 `agent-spec.md`**（逆向提取）— 展示给用户确认
3. **用户确认**：确认提取结果 + 选择目标框架
4. **跳转 Phase 5**：用目标框架重新生成代码
5. **Phase 6**：对比验证原 Agent 行为是否保留

**导入模式约束**：
- 必须列出代码分析中的不确定项，让用户确认
- 原 Agent 的所有工具必须在新框架中保留等效实现
- 生成 diff 摘要：原框架 vs 目标框架的关键差异

---

## 严格约束

1. **每个阶段必须用户确认后才能进入下一阶段**。严禁静默推进。
2. **每个阶段开始前**，先读取 `references/phase{N}-*.md` 获取该阶段详细指引。
3. **遇到需求冲突或不明确的约束**，立即暂停并提问，不自行推测。
4. **每个阶段的核心产出必须立即写入磁盘**，不允许仅停留在对话上下文中。
5. **代码生成阶段（Phase 5）**，必须读取 `adk-framework-adapters` 对应框架的 reference 文件后再生成代码。
6. **框架适配 reference 文件标注了 `verified_date`**，若距今超过 90 天，应提醒用户 API 可能已变化。

## 工作方式

1. **阶段驱动**：按 Phase 1 → 6 顺序推进，每阶段有明确的输入、活动、产出和确认点。
2. **追踪表**：在 Phase 1 结束后创建 `{output_dir}/tracking.md`，每个阶段完成后更新状态。
3. **引用 reference**：每个阶段开始前，读取对应 `references/phase{N}-*.md` 获取详细引导。
4. **立即落盘**：每个阶段的产出文件在完成后立即写入 `{output_dir}/`，并展示给用户确认。
5. **跨 skill 调用**：Phase 2 调用 `agent-patterns-catalog` 匹配架构模式；Phase 5 调用 `adk-framework-adapters` 加载框架模板。

## 阶段概览

| Phase | 名称 | 核心活动 | 产出文件 | Reference |
|-------|------|----------|----------|-----------|
| 1 | 需求发现 | 业务场景、Agent 类型、框架、约束 | `agent-spec.md` | `references/phase1-discovery.md` |
| 2 | 架构设计 | 架构模式匹配、组件拓扑、数据流 | `agent-architecture.md` | `references/phase2-architecture.md` |
| 3 | 工具与能力 | 工具定义、Memory 策略、RAG pipeline | `agent-tools.md` | `references/phase3-tools.md` |
| 4 | Prompt 与编排 | System Prompt、编排逻辑、路由策略 | `agent-prompts.md` + `agent-orchestration.md` | `references/phase4-prompts.md` |
| 5 | 代码生成 | 框架代码、项目结构、配置、脚本 | 完整项目目录 | `references/phase5-codegen.md` |
| 6 | 验证迭代 | 依赖安装、测试、Smoke Test、迭代 | 验证报告 | `references/phase6-verification.md` |

## 输出目录规范

```
{agent-name}/                    # 项目根目录（Phase 5 生成）
├── README.md
├── pyproject.toml / go.mod / package.json
├── .env.example
├── src/
│   ├── agent.py / agent.go / agent.ts
│   ├── tools/
│   ├── prompts/
│   ├── memory/
│   └── orchestrator/            # multi-agent 时
├── tests/
├── configs/
└── scripts/
    └── run.sh

docs/agent-dev/                  # 设计文档目录（Phase 1-4 生成）
├── tracking.md                  # 进度追踪表
├── agent-spec.md                # Phase 1
├── agent-architecture.md        # Phase 2
├── agent-tools.md               # Phase 3
├── agent-prompts.md             # Phase 4
└── agent-orchestration.md       # Phase 4
```

## Phase 1: 需求发现（Discovery）

**交互方式**: 深度对话 + 结构化提问

**活动**:
1. 用户描述 Agent 要解决的业务场景
2. 引导确认：目标用户、核心能力、输入/输出、成功标准
3. 确定 Agent 类型（提供选项）：
   - ReAct Agent（推理+行动循环）
   - Multi-Agent 协作（多角色对话/编排）
   - RAG Agent（检索增强生成）
   - Tool-Use Agent（工具调用链）
   - Workflow Agent（固定流程编排）
   - Autonomous Agent（自主规划+执行）
4. 确定目标框架偏好（或根据场景推荐）
5. 确认约束：部署环境、编程语言、LLM provider、外部依赖
6. **导入模式入口**：如果用户有已有 Agent 代码，先分析代码再提取 spec

**产出**: `agent-spec.md`
- Agent 名称、描述、类型
- 核心能力列表
- 输入/输出契约
- 目标框架 + 编程语言
- LLM provider + 模型
- 约束与外部依赖
- 成功标准

**确认点**: 用户审批 agent-spec.md 后进入 Phase 2

## Phase 2: 架构设计（Architecture）

**交互方式**: 展示架构方案 + Mermaid 图 + 用户确认/调整

**活动**:
1. 读取 `agent-patterns-catalog` 中对应 Agent 类型的参考架构
2. 设计组件拓扑：Agent Core → Memory → Tools → LLM → Orchestrator
3. Multi-Agent 场景：角色拆分、通信拓扑（星型 / 链式 / 网状 / 层级）
4. RAG 场景：检索策略、向量存储选型、chunk 策略
5. 生成 Mermaid 架构图
6. 列出关键设计决策及其理由

**产出**: `agent-architecture.md`
- 架构模式名称与简述
- 组件拓扑图（Mermaid）
- 组件职责表
- 数据流描述
- 关键设计决策
- Multi-Agent 场景的角色定义（如适用）

**确认点**: 架构确认后进入 Phase 3

## Phase 3: 工具与能力定义（Tools & Capabilities）

**交互方式**: 逐个工具交互确认

**活动**:
1. 根据 agent-spec 和 architecture 列出所有需要的工具（Tool）
2. 每个工具逐一确认：
   - 名称（name）
   - 描述（description）
   - 输入参数 schema（JSON Schema 格式）
   - 输出 schema
   - 实现策略（API 调用 / 数据库查询 / 文件操作 / 自定义逻辑）
3. 定义 Memory 策略：
   - 类型（conversation_buffer / entity / summary / vector）
   - 存储后端（in-memory / Redis / SQLite / 向量数据库）
   - 窗口大小或 token 限制
4. RAG pipeline 定义（如适用）：
   - 数据源（文件 / API / 数据库）
   - Embedding 模型
   - 向量存储（FAISS / Chroma / Milvus / Weaviate）
   - 检索策略（similarity / MMR / hybrid）
   - Chunk 策略（大小 / 重叠 / 分隔符）

**产出**: `agent-tools.md`
- 工具清单表（name / description / input / output / strategy）
- Memory 配置
- RAG pipeline 定义（如适用）
- 外部依赖清单

**确认点**: 全部工具定义确认后进入 Phase 4

## Phase 4: Prompt 与编排设计（Prompt & Orchestration）

**交互方式**: 展示 prompt 草稿 + 用户迭代修改

**活动**:
1. 设计 System Prompt：
   - 角色定义
   - 行为约束与规则
   - 输出格式要求
   - 可用工具说明
2. 设计编排逻辑：
   - 单 Agent：执行循环（max_iterations / 终止条件）
   - Multi-Agent：状态机 / DAG / 对话轮次 / 投票机制
   - Workflow：阶段定义 / 条件分支 / 并行节点
3. Multi-Agent 特有：
   - 每个角色的 prompt
   - 路由策略（round-robin / LLM-based / rule-based）
   - 终止条件
4. 错误处理与兜底策略
5. Few-shot examples（如需要）

**产出**: 
- `agent-prompts.md`：所有 prompt 全文
- `agent-orchestration.md`：编排逻辑 + Mermaid 流程图 + 路由规则 + 错误处理

**确认点**: Prompt 和编排逻辑确认后进入 Phase 5

## Phase 5: 代码生成（Code Generation）

**交互方式**: 生成代码 + 逐文件审查确认

**活动**:
1. 读取 `adk-framework-adapters` 中目标框架的 reference 文件
2. 检查 reference 文件的 `verified_date`，若超 90 天则提醒用户
3. 根据 Phase 1-4 的全部设计文档 + 框架模板生成完整项目：
   - 项目结构（目录、依赖文件）
   - Agent 核心代码
   - 所有工具实现
   - Prompt 模板文件
   - Memory 配置
   - 编排逻辑代码
   - 配置文件（`.env.example` / `config.yaml`）
   - 启动脚本（`scripts/run.sh`）
   - README.md（含安装运行说明）
   - 基础测试文件
4. 每个核心代码文件生成后展示给用户确认
5. 需要用户提供的敏感配置（API Key 等）统一放在 `.env.example` 中标注

**产出**: 完整可运行项目目录

**确认点**: 项目结构和核心文件确认后进入 Phase 6

## Phase 6: 验证与迭代（Verification & Iteration）

**交互方式**: 自动验证 + 反馈循环

**活动**:
1. 依赖安装验证（`pip install` / `go mod tidy` / `npm install`）
2. 语法检查 / 类型检查
3. 单元测试执行
4. Agent 行为 Smoke Test：模拟一轮对话，验证 Agent 能正确调用工具并返回结果
5. 如有问题：定位 → 修复 → 重跑
6. 展示验证结果给用户
7. 用户手动测试后的反馈 → 迭代调整 prompt / 工具 / 编排逻辑

**产出**: 验证通过的可运行项目 + 验证报告

**确认点**: 用户确认项目可用

## 追踪表模板

Phase 1 完成后创建 `{output_dir}/tracking.md`：

```markdown
# Agent Dev Tracking

| Phase | 状态 | 产出文件 | 确认时间 |
|-------|------|----------|----------|
| 1. 需求发现 | ✅ 已确认 | agent-spec.md | {timestamp} |
| 2. 架构设计 | ⏳ 进行中 | — | — |
| 3. 工具定义 | 🔲 未开始 | — | — |
| 4. Prompt 与编排 | 🔲 未开始 | — | — |
| 5. 代码生成 | 🔲 未开始 | — | — |
| 6. 验证迭代 | 🔲 未开始 | — | — |

## 关键决策记录

| # | 决策 | 原因 | Phase |
|---|------|------|-------|
| 1 | Agent 类型: {type} | {reason} | 1 |
| 2 | 框架: {framework} | {reason} | 1 |
```

## 与其他 Skill 的协作

| Skill | 调用时机 | 用途 |
|-------|----------|------|
| `agent-patterns-catalog` | Phase 2 | 匹配最佳 Agent 架构模式 |
| `adk-framework-adapters` | Phase 5 | 加载框架特定代码模板和惯用模式 |
| `systematic-debugging` | Phase 6 | 遇到复杂错误时切换到系统化调试 |
| `tdd-workflow` | Phase 5-6 | 测试先行策略（可选） |

## 默认命令入口

- `/agent-dev`
- `/agent-dev --quick`
- `/agent-dev --import`
