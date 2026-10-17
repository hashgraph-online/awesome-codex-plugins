---
framework: autogen
version: "0.4.x"
language: python
verified_date: "2025-01-15"
---

# AutoGen (Microsoft) 适配器

## 框架概述

- **语言**: Python
- **核心库**: `autogen-agentchat`, `autogen-core`, `autogen-ext`
- **特点**: 多 Agent 对话优先、事件驱动架构、微软开源
- **适用**: 多 Agent 协作、代码生成、群聊式讨论

> AutoGen v0.4 是完全重写版本，与 v0.2 API 不兼容。本适配器基于 v0.4。

## 项目模板

```
{project_name}/
├── pyproject.toml
├── .env.example
├── README.md
├── src/
│   ├── __init__.py
│   ├── agents.py          # Agent 定义
│   ├── tools.py           # 工具定义
│   ├── team.py            # 团队/对话编排
│   └── config.py          # 配置管理
├── tests/
│   ├── __init__.py
│   ├── test_agents.py
│   └── conftest.py
└── scripts/
    └── run.py
```

## 依赖配置

```toml
# pyproject.toml
[project]
name = "{project_name}"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "autogen-agentchat>=0.4.0",
    "autogen-ext[openai]>=0.4.0",
    # "autogen-ext[azure]>=0.4.0",    # Azure OpenAI
    # "autogen-ext[docker]>=0.4.0",   # Docker 代码执行
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-asyncio>=0.24"]
```

## Agent 创建模式

### AssistantAgent（基础 Agent）

```python
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

model_client = OpenAIChatCompletionClient(model="gpt-4o")

agent = AssistantAgent(
    name="research_assistant",
    model_client=model_client,
    system_message="你是一个研究助手，负责搜索和整理信息。",
    tools=[search_tool, summarize_tool],
)
```

### Multi-Agent Team

```python
from autogen_agentchat.teams import RoundRobinGroupChat, SelectorGroupChat
from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination

# 定义多个 Agent
researcher = AssistantAgent(
    name="researcher",
    model_client=model_client,
    system_message="你是研究员，负责信息收集。",
    tools=[search_tool],
)

analyst = AssistantAgent(
    name="analyst",
    model_client=model_client,
    system_message="你是分析师，负责数据分析和洞察提取。",
    tools=[analysis_tool],
)

# 终止条件
termination = TextMentionTermination("DONE") | MaxMessageTermination(20)

# 轮转式群聊
team = RoundRobinGroupChat(
    participants=[researcher, analyst],
    termination_condition=termination,
)

# 或 LLM 选择发言者
team = SelectorGroupChat(
    participants=[researcher, analyst],
    model_client=model_client,
    termination_condition=termination,
)
```

## 工具定义模式

```python
from autogen_core import FunctionCall
from typing import Annotated

async def search_orders(
    query: Annotated[str, "搜索关键词：订单号或客户名"],
    status: Annotated[str | None, "可选，按状态过滤"] = None,
) -> list[dict]:
    """按订单号或客户名搜索订单列表。"""
    # 实现
    return results
```

## 对话编排

```python
import asyncio
from autogen_agentchat.ui import Console

async def main():
    team = build_team()
    
    # 方式 1: 单次运行
    result = await team.run(task="分析最近一个月的销售趋势")
    print(result.messages[-1].content)
    
    # 方式 2: 流式输出
    stream = team.run_stream(task="分析最近一个月的销售趋势")
    await Console(stream)
    
    # 方式 3: 交互式
    while True:
        user_input = input("You: ")
        if user_input.lower() in ("exit", "quit"):
            break
        stream = team.run_stream(task=user_input)
        await Console(stream)
        
asyncio.run(main())
```

## Memory 配置

```python
# AutoGen v0.4 的 Agent 自动维护对话历史
# 通过 team 的 run() 跨轮次保持状态

# 长期记忆可通过 tool 访问外部存储
async def recall_memory(
    query: Annotated[str, "要回忆的信息关键词"],
) -> str:
    """从长期记忆中检索相关信息。"""
    results = await vector_store.search(query, top_k=5)
    return format_results(results)
```

## 运行入口

```python
import asyncio
from dotenv import load_dotenv
from src.team import build_team
from autogen_agentchat.ui import Console

load_dotenv()

async def main():
    team = build_team()
    
    print("Agent Team 就绪，输入 exit 退出")
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ("exit", "quit"):
            break
        
        stream = team.run_stream(task=user_input)
        await Console(stream)

if __name__ == "__main__":
    asyncio.run(main())
```

## 注意事项

- AutoGen v0.4 架构完全重写，不要参考 v0.2 文档
- 核心范式是"多 Agent 对话"，单 Agent 也通过团队机制运行
- `SelectorGroupChat` 用 LLM 动态选择发言者，比 RoundRobin 更灵活
- 代码执行建议用 Docker 沙箱（`autogen-ext[docker]`）
- 终止条件可以用 `|`（或）和 `&`（与）组合
