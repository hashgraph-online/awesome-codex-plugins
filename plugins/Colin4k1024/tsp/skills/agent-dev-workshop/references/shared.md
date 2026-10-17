# 共享引用：框架映射与通用常量

## 框架-语言映射表

| 框架 | 语言 | 包管理器 | 依赖文件 | 测试框架 | 最低版本要求 |
|------|------|---------|----------|----------|-------------|
| LangChain | Python | pip/uv | pyproject.toml | pytest | Python 3.9+ |
| LangGraph | Python | pip/uv | pyproject.toml | pytest | Python 3.9+ |
| LangChain.js | TypeScript | npm/pnpm | package.json | vitest/jest | Node 18+ |
| EINO | Go | go modules | go.mod | go test | Go 1.21+ |
| AutoGen | Python | pip/uv | pyproject.toml | pytest | Python 3.9+ |
| AgentScope | Python | pip/uv | pyproject.toml | pytest | Python 3.9+ |
| CrewAI | Python | pip/uv | pyproject.toml | pytest | Python 3.9+ |

## Agent 类型 → 架构模式映射

| Agent 类型 | 默认架构模式 | 典型组件 |
|-----------|-------------|---------|
| ReAct | 单 Agent + Tool Loop | Agent Core, LLM, Tool Registry |
| Multi-Agent Conversation | 多 Agent + Router | Orchestrator, N×Agent, Shared Memory |
| Multi-Agent Workflow | DAG / Pipeline | Orchestrator, N×Agent, State Manager |
| RAG Agent | Retrieve → Generate | Agent, Retriever, Vector Store, LLM |
| Tool-Use Agent | Tool Chain | Agent Core, LLM, Tool Registry |
| Autonomous Agent | Plan → Execute → Reflect | Planner, Executor, Reflector, Memory |

## LLM Provider 配置模板

```yaml
# OpenAI
provider: openai
model: gpt-4o
api_key: ${OPENAI_API_KEY}
base_url: https://api.openai.com/v1              # 可选自定义

# Azure OpenAI
provider: azure_openai
model: gpt-4o
api_key: ${AZURE_OPENAI_API_KEY}
azure_endpoint: ${AZURE_OPENAI_ENDPOINT}
api_version: "2024-10-21"

# Anthropic
provider: anthropic
model: claude-sonnet-4-20250514
api_key: ${ANTHROPIC_API_KEY}

# 通义千问
provider: dashscope
model: qwen-max
api_key: ${DASHSCOPE_API_KEY}

# DeepSeek
provider: deepseek
model: deepseek-chat
api_key: ${DEEPSEEK_API_KEY}
base_url: https://api.deepseek.com

# 本地模型 (Ollama)
provider: ollama
model: llama3.1:8b
base_url: http://localhost:11434
```

## 向量存储选型指南

| 向量存储 | 适用规模 | 部署方式 | 特点 |
|---------|---------|---------|------|
| FAISS | 小/中 | 内嵌（无服务器） | 快速原型，无持久化 |
| Chroma | 小/中 | 内嵌或独立服务 | 简单易用，适合入门 |
| Milvus | 中/大 | 需独立部署 | 分布式，生产级别 |
| Weaviate | 中/大 | 需独立部署 | GraphQL API，多模态 |
| Qdrant | 中/大 | 需独立部署 | Rust 实现，高性能 |
| pgvector | 小/中 | PostgreSQL 扩展 | 复用已有 PG 实例 |

## .gitignore 模板

```gitignore
# Environment
.env
.env.local

# Python
__pycache__/
*.pyc
.pytest_cache/
*.egg-info/
dist/
build/
.venv/
venv/

# Go
/vendor/

# Node
node_modules/
dist/

# IDE
.vscode/
.idea/
*.swp

# Data
data/*.pdf
data/*.db
*.faiss

# OS
.DS_Store
Thumbs.db
```

## 状态符号约定

| 符号 | 含义 |
|------|------|
| ✅ | 已完成并确认 |
| ⏳ | 进行中 |
| 🔲 | 未开始 |
| ❌ | 失败 |
| ⏭️ | 已跳过 |
| ⚠️ | 需关注 |
