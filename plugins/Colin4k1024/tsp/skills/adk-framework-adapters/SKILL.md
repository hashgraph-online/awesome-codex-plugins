---
name: adk-framework-adapters
description: >
  ADK 框架适配层。为 LangChain / EINO / AutoGen / AgentScope / CrewAI 提供框架特定的
  代码模板、惯用模式、API 映射和项目结构，供 agent-dev-workshop Phase 5 代码生成使用。
  每个框架 reference 文件标注 verified_date 用于版本锁定。
origin: ECC
---

# ADK Framework Adapters

为 AI Agent 代码生成提供框架特定的适配层。

## 何时激活

- `agent-dev-workshop` Phase 5 自动调用
- 用户需要特定框架的 Agent 代码模板
- 需要对比不同框架的 API 差异时

## 支持的框架

| 框架 | 语言 | 维护方 | Reference | 版本锁定 |
|------|------|--------|-----------|---------|
| LangChain / LangGraph | Python, TypeScript | LangChain Inc. | `references/langchain.md` | ✅ |
| EINO | Go | ByteDance | `references/eino.md` | ✅ |
| AutoGen | Python | Microsoft | `references/autogen.md` | ✅ |
| AgentScope | Python | Alibaba | `references/agentscope.md` | ✅ |
| CrewAI | Python | CrewAI Inc. | `references/crewai.md` | ✅ |

## 版本锁定机制

每个 reference 文件头部包含：

```yaml
framework: langchain
version: "0.3.x"
verified_date: "2025-01-15"
```

**使用规则**:
- `verified_date` 距今 ≤ 90 天 → 正常使用
- `verified_date` 距今 > 90 天 → 生成代码前提醒用户检查 API 变化
- `/harness-audit` 会检查所有 reference 文件的 staleness

## 框架能力对照表

| 能力 | LangChain | EINO | AutoGen | AgentScope | CrewAI |
|------|-----------|------|---------|------------|--------|
| ReAct Agent | ✅ AgentExecutor | ✅ ReactAgent | ✅ AssistantAgent | ✅ ReActAgent | ✅ Agent |
| Multi-Agent | ✅ LangGraph | ⚠️ 自定义 | ✅ GroupChat | ✅ Pipeline | ✅ Crew |
| RAG Pipeline | ✅ Retriever chain | ✅ flow chain | ⚠️ 需集成 | ✅ Knowledge module | ✅ Knowledge |
| Tool Definition | ✅ @tool decorator | ✅ ToolsNode | ✅ Function | ✅ ServiceToolkit | ✅ @tool |
| Memory | ✅ 内置多种 | ✅ ChatTemplate | ✅ 内置 | ✅ Memory module | ✅ 内置 |
| Streaming | ✅ | ✅ | ✅ | ✅ | ⚠️ 有限 |
| Async | ✅ | ✅ (goroutine) | ✅ | ✅ | ⚠️ 有限 |

图例：✅ 原生支持 / ⚠️ 部分支持或需额外集成

## 使用方式

```
# 在 agent-dev-workshop Phase 5 中
1. 确认目标框架
2. 读取 references/{framework}.md
3. 检查 verified_date
4. 使用 reference 中的 code templates 生成项目
5. 根据 agent-spec 和 architecture 填充模板变量
```

## 新增框架

新增框架适配器时：
1. 在 `references/` 下创建 `{framework}.md`
2. 包含 frontmatter（framework, version, verified_date）
3. 至少覆盖：项目模板、Agent 创建、Tool 定义、Memory 配置、运行入口
4. 更新本文件的框架表
