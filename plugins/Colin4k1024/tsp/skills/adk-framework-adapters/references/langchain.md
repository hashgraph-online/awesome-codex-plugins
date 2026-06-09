---
framework: langchain
version: "0.3.x"
language: python
verified_date: "2025-01-15"
---

# LangChain / LangGraph 适配器

## 框架概述

- **语言**: Python / TypeScript
- **核心库**: `langchain-core`, `langchain-community`, `langgraph`
- **Agent 实现**: LangGraph（推荐）或 LangChain AgentExecutor（旧版）
- **特点**: 生态最丰富，集成最多，社区最大

## 项目模板

```
{project_name}/
├── pyproject.toml
├── .env.example
├── README.md
├── src/
│   ├── __init__.py
│   ├── agent.py           # Agent 定义
│   ├── tools.py           # 工具定义
│   ├── prompts.py         # Prompt 模板
│   ├── memory.py          # Memory 配置
│   ├── graph.py           # LangGraph 工作流（如适用）
│   └── config.py          # 配置管理
├── tests/
│   ├── __init__.py
│   ├── test_agent.py
│   ├── test_tools.py
│   └── conftest.py
└── scripts/
    └── run.py             # 入口脚本
```

## 依赖配置

```toml
# pyproject.toml
[project]
name = "{project_name}"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "langchain-core>=0.3.0",
    "langchain-openai>=0.3.0",     # OpenAI 模型
    # "langchain-anthropic>=0.3.0", # Anthropic 模型
    # "langchain-community>=0.3.0", # 社区集成
    "langgraph>=0.2.0",             # 工作流编排
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-asyncio>=0.24"]
rag = ["langchain-chroma>=0.2.0", "langchain-text-splitters>=0.3.0"]
```

## Agent 创建模式

### ReAct Agent（LangGraph）

```python
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o", temperature=0)

agent = create_react_agent(
    model=llm,
    tools=tools,
    state_modifier=system_prompt,  # 系统提示
)

# 运行
result = agent.invoke({"messages": [("user", "你好")]})
```

### 自定义 LangGraph 工作流

```python
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    context: str

graph = StateGraph(AgentState)

graph.add_node("retrieve", retrieve_node)
graph.add_node("generate", generate_node)
graph.add_node("review", review_node)

graph.add_edge(START, "retrieve")
graph.add_edge("retrieve", "generate")
graph.add_conditional_edges("review", should_retry, {
    "retry": "generate",
    "done": END,
})

app = graph.compile()
```

## 工具定义模式

```python
from langchain_core.tools import tool

@tool
def search_orders(query: str, status: str = None) -> list[dict]:
    """按订单号或客户名搜索订单。
    
    Args:
        query: 搜索关键词
        status: 可选，按状态过滤 (pending/shipped/delivered)
    
    Returns:
        匹配的订单列表
    """
    # 实现
    return results
```

## Memory 配置

```python
# 对话历史
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()
agent = create_react_agent(model=llm, tools=tools, checkpointer=checkpointer)

# 带 thread_id 的调用
config = {"configurable": {"thread_id": "user-123"}}
result = agent.invoke({"messages": [("user", "查询我的订单")]}, config)
```

## Multi-Agent 模式

```python
from langgraph.graph import StateGraph

# 定义专家 Agent
researcher = create_react_agent(model=llm, tools=research_tools)
analyst = create_react_agent(model=llm, tools=analysis_tools)

# 组合工作流
workflow = StateGraph(TeamState)
workflow.add_node("researcher", researcher)
workflow.add_node("analyst", analyst)
workflow.add_node("router", router_node)

workflow.add_conditional_edges("router", route_to_agent, {
    "researcher": "researcher",
    "analyst": "analyst",
    "done": END,
})
```

## 运行入口

```python
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def main():
    agent = build_agent()
    
    # 交互模式
    while True:
        user_input = input("You: ")
        if user_input.lower() in ("exit", "quit"):
            break
        result = await agent.ainvoke({"messages": [("user", user_input)]})
        print(f"Agent: {result['messages'][-1].content}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 注意事项

- LangGraph 是 LangChain 团队推荐的 Agent 框架，替代旧版 AgentExecutor
- `langchain-core` 是稳定 API，`langchain-community` 更新频繁
- TypeScript 版本 API 略有不同，参考 `@langchain/langgraph`
