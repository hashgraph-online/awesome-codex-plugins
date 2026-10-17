---
name: agent-patterns-catalog
description: >
  AI Agent 架构模式目录。提供 ReAct、Multi-Agent Conversation、Multi-Agent Workflow、
  RAG Agent、Tool-Use Agent、Autonomous Agent 六种核心模式的参考架构、组件拓扑、
  数据流、设计决策和框架无关的最佳实践。供 agent-dev-workshop Phase 2 调用。
origin: ECC
---

# Agent Patterns Catalog

AI Agent 架构模式目录，为 Agent 设计提供**框架无关**的参考架构。

## 何时激活

- `agent-dev-workshop` Phase 2 自动调用
- 用户询问 Agent 架构模式选择
- 需要对比不同 Agent 架构方案时

## 模式索引

| 模式 | 核心思想 | 适用场景 | Reference |
|------|---------|---------|-----------|
| ReAct Agent | 思考→行动→观察循环 | 通用任务、搜索+操作 | `references/react-agent.md` |
| Multi-Agent Conversation | 多角色自由对话 | 辩论、评审、头脑风暴 | `references/multi-agent-conversation.md` |
| Multi-Agent Workflow | DAG/Pipeline 编排 | 阶段式处理、内容生产 | `references/multi-agent-workflow.md` |
| RAG Agent | 检索增强生成 | 知识问答、文档分析 | `references/rag-agent.md` |
| Tool-Use Agent | 工具调用链 | API 集成、数据处理 | `references/tool-use-agent.md` |
| Autonomous Agent | 自主规划+执行+反思 | 开放式任务、自主研究 | `references/autonomous-agent.md` |

## 模式选择决策树

```
Q1: Agent 需要自主分解复杂任务吗？
  ├─ Yes → Autonomous Agent
  └─ No → Q2

Q2: 涉及多个不同角色协作吗？
  ├─ Yes → Q3
  └─ No → Q4

Q3: 角色之间需要自由对话还是固定流程？
  ├─ 自由对话 → Multi-Agent Conversation
  └─ 固定流程 → Multi-Agent Workflow

Q4: 核心能力是知识检索吗？
  ├─ Yes → RAG Agent
  └─ No → Q5

Q5: 需要推理+多步操作还是简单工具调用？
  ├─ 推理+多步 → ReAct Agent
  └─ 简单调用 → Tool-Use Agent
```

## 混合模式

真实项目中常出现混合模式，常见组合：

| 组合 | 场景 | 设计要点 |
|------|------|---------|
| RAG + ReAct | 基于知识库的推理和操作 | 检索作为一种 Tool 嵌入 ReAct 循环 |
| RAG + Tool-Use | 知识问答 + 数据操作 | 检索和工具并列 |
| Workflow + ReAct | 流水线中某阶段需要推理 | 流水线节点内部嵌入 ReAct loop |
| Autonomous + Tool-Use | 自主规划 + 工具执行 | Plan 产出的子任务由 Tool Agent 执行 |

## 使用方式

```
# 在 agent-dev-workshop Phase 2 中
1. 根据 Phase 1 确认的 Agent 类型，读取对应 reference 文件
2. 从 reference 中提取参考架构图
3. 根据实际 spec 调整组件拓扑
4. 记录设计决策
```
