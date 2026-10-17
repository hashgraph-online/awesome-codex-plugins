# Phase 1: 需求发现（Discovery）引导细则

## 入口检查

- 如果用户选择 `--import` 模式，先执行代码分析流程（见文末），提取 spec 后直接跳到用户确认。
- 如果用户选择 `--quick` 模式，自动推断以下所有字段，跳过逐个提问，直接生成 agent-spec.md 交用户一次性确认。

## 标准模式提问顺序

### Round 1: 业务场景

> 请描述你要构建的 Agent 的目标场景：
> - 这个 Agent 帮谁解决什么问题？
> - 典型的使用流程是什么？
> - 输入是什么？期望输出是什么？

从用户描述中提取：`target_user`、`core_problem`、`typical_flow`、`input_format`、`output_format`。

### Round 2: Agent 类型选择

根据场景推荐最匹配的 Agent 类型，并解释为什么：

| Agent 类型 | 适用场景 | 关键特征 |
|-----------|---------|---------|
| **ReAct** | 需要推理+多步行动的通用任务 | 思考→行动→观察循环 |
| **Multi-Agent Conversation** | 多角色协作、辩论、评审 | 角色间自由对话 |
| **Multi-Agent Workflow** | 固定阶段、流水线式处理 | DAG 或链式执行 |
| **RAG Agent** | 知识问答、文档分析 | 检索→生成 |
| **Tool-Use Agent** | API 集成、数据处理 | 工具调用为主 |
| **Autonomous Agent** | 开放式任务、自主规划 | plan→execute→reflect |

- 如果用户场景不清晰，给出 2-3 个候选并说明优缺点
- 允许混合类型（如 RAG + Tool-Use）

### Round 3: 框架与语言

**自动推荐逻辑**：

| 用户指定 | 推荐框架 | 原因 |
|---------|---------|------|
| Python + 未指定框架 | LangChain/LangGraph | 生态最全、社区最大 |
| Go | EINO | Go 生态首选 ADK |
| 多 Agent 协作 + Python | AutoGen 或 CrewAI | 原生多 Agent 支持 |
| 阿里云生态 | AgentScope | 原生集成通义千问 |
| TypeScript | LangChain.js | TS 生态唯一成熟 ADK |
| 未指定 | LangChain (Python) | 最通用默认选择 |

询问用户确认或替换。

### Round 4: LLM Provider 与约束

- LLM Provider：OpenAI / Azure OpenAI / Anthropic / 通义千问 / DeepSeek / 本地模型
- 模型选择：如 gpt-4o / claude-sonnet-4 / qwen-max / deepseek-chat
- 部署环境：本地 / Docker / K8s / Serverless
- 外部依赖：数据库、向量存储、已有 API、文件系统
- 约束：预算、延迟要求、数据隐私

### Round 5: 成功标准

- Agent 能正确完成哪些操作算"成功"？
- 需要通过的 smoke test case 是什么？
- 性能要求（响应时间、并发量）

## agent-spec.md 输出模板

```markdown
# Agent Specification

## 基本信息

| 字段 | 值 |
|------|-----|
| Agent 名称 | {name} |
| 描述 | {description} |
| Agent 类型 | {type} |
| 目标框架 | {framework} |
| 编程语言 | {language} |
| LLM Provider | {provider} |
| 模型 | {model} |
| 部署环境 | {deployment} |

## 核心能力

1. {capability_1}
2. {capability_2}
3. ...

## 输入/输出契约

**输入**:
- 格式: {input_format}
- 示例: {input_example}

**输出**:
- 格式: {output_format}
- 示例: {output_example}

## 约束与依赖

- 外部 API: {apis}
- 数据库: {databases}
- 其他: {others}

## 成功标准

1. {criterion_1}
2. {criterion_2}
```

## --import 模式: 代码分析流程

1. 用户提供代码路径（目录或文件列表）
2. 扫描代码，识别：
   - 使用的框架（通过 import 语句判断）
   - Agent 类型（通过类名、装饰器、模式判断）
   - 工具列表（tool 定义、function 注册）
   - System Prompt 内容
   - Memory 配置
   - 编排逻辑
3. 生成 agent-spec.md（逆向提取）
4. **标注不确定项**，列出 `[UNCERTAIN]` 标签
5. 展示给用户逐项确认，修正不确定项
6. 用户选择目标框架
7. 跳转 Phase 2（架构映射到新框架）
