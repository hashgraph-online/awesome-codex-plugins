---
framework: agentscope
version: "0.1.x"
language: python
verified_date: "2025-01-15"
---

# AgentScope (Alibaba) 适配器

## 框架概述

- **语言**: Python
- **核心库**: `agentscope`
- **特点**: 分布式多 Agent、消息驱动、可视化 Studio、阿里开源
- **适用**: 大规模多 Agent 系统、游戏 NPC、社会模拟、分布式场景

## 项目模板

```
{project_name}/
├── pyproject.toml
├── .env.example
├── README.md
├── src/
│   ├── __init__.py
│   ├── agents.py          # Agent 定义
│   ├── tools.py           # Service 函数
│   ├── pipeline.py        # 编排逻辑
│   ├── prompts.py         # Prompt 模板
│   └── config.py          # 配置管理
├── configs/
│   ├── model_configs.json # 模型配置
│   └── agent_configs.json # Agent 配置
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
requires-python = ">=3.9"
dependencies = [
    "agentscope>=0.1.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0"]
distribute = ["agentscope[distribute]"]  # 分布式支持
```

## 初始化配置

```python
import agentscope

# 模型配置
model_configs = [
    {
        "config_name": "gpt-4o",
        "model_type": "openai_chat",
        "model_name": "gpt-4o",
        "api_key": "${OPENAI_API_KEY}",
        "temperature": 0,
    },
    # {
    #     "config_name": "qwen-turbo",
    #     "model_type": "dashscope_chat",
    #     "model_name": "qwen-turbo",
    #     "api_key": "${DASHSCOPE_API_KEY}",
    # },
]

agentscope.init(model_configs=model_configs)
```

## Agent 创建模式

### DialogAgent（对话 Agent）

```python
from agentscope.agents import DialogAgent, UserAgent

# 创建对话 Agent
assistant = DialogAgent(
    name="assistant",
    model_config_name="gpt-4o",
    sys_prompt="你是一个有用的助手。根据用户问题提供准确回答。",
)

# 用户代理
user = UserAgent(name="user")
```

### ReActAgent

```python
from agentscope.agents import ReActAgent

agent = ReActAgent(
    name="research_agent",
    model_config_name="gpt-4o",
    sys_prompt="你是一个研究助手。",
    tools=[search_tool, calc_tool],
    max_iters=10,
)
```

## 工具定义模式

```python
from agentscope.service import ServiceToolkit, ServiceResponse, ServiceExecStatus

def search_orders(query: str, status: str = None) -> ServiceResponse:
    """按订单号或客户名搜索订单。
    
    Args:
        query (str): 搜索关键词
        status (str, optional): 按状态过滤
    
    Returns:
        ServiceResponse: 匹配的订单列表
    """
    try:
        results = do_search(query, status)
        return ServiceResponse(
            status=ServiceExecStatus.SUCCESS,
            content=results,
        )
    except Exception as e:
        return ServiceResponse(
            status=ServiceExecStatus.ERROR,
            content=str(e),
        )

# 注册到 toolkit
toolkit = ServiceToolkit()
toolkit.add(search_orders)
```

## 编排模式

### Pipeline（顺序/并行）

```python
from agentscope.pipelines import SequentialPipeline, ForLoopPipeline
from agentscope.message import Msg

# 顺序执行
pipe = SequentialPipeline([researcher, analyst, reviewer])
result = pipe(Msg(name="user", content="分析销售趋势", role="user"))

# 循环对话
pipe = ForLoopPipeline(
    loop_body=SequentialPipeline([agent_a, agent_b]),
    max_loop=5,
)
```

### MsgHub（群聊）

```python
from agentscope.msghub import MsgHub

with MsgHub(
    participants=[moderator, researcher, analyst, reviewer],
    announcement=Msg(name="system", content="请开始讨论销售策略。", role="system"),
) as hub:
    for _ in range(max_rounds):
        moderator()
        researcher()
        analyst()
        reviewer()
        if check_convergence(hub):
            break
```

## Memory 配置

```python
# AgentScope Agent 自动维护对话记忆
# 可通过 memory 参数配置
from agentscope.memory import TemporaryMemory

agent = DialogAgent(
    name="assistant",
    model_config_name="gpt-4o",
    sys_prompt="你是助手。",
    memory_config={
        "class": "TemporaryMemory",
        "args": {"max_length": 20},
    },
)
```

## Multi-Agent 模式

```python
# 分布式多 Agent
import agentscope

agentscope.init(
    model_configs=model_configs,
    project="multi_agent_demo",
)

# 本地 Agent
moderator = DialogAgent(name="moderator", ...)

# 分布式 Agent（在独立进程运行）
researcher = DialogAgent(name="researcher", ...).to_dist()
analyst = DialogAgent(name="analyst", ...).to_dist()
```

## 运行入口

```python
import agentscope
from agentscope.agents import DialogAgent, UserAgent
from dotenv import load_dotenv

load_dotenv()

def main():
    agentscope.init(model_configs=model_configs)
    
    assistant = DialogAgent(
        name="assistant",
        model_config_name="gpt-4o",
        sys_prompt=system_prompt,
    )
    user = UserAgent(name="user")
    
    msg = None
    print("Agent 就绪，输入 exit 退出")
    while True:
        msg = user(msg)
        if msg.content.strip().lower() in ("exit", "quit"):
            break
        msg = assistant(msg)
        print(f"Agent: {msg.content}")

if __name__ == "__main__":
    main()
```

## 注意事项

- AgentScope 的消息传递基于 `Msg` 对象，不是原始字符串
- 分布式模式通过 `.to_dist()` 一行代码启用
- AgentScope Studio 提供可视化监控和调试
- 与达摩院模型（通义千问）有天然集成
- Pipeline 和 MsgHub 是两种主要编排方式，前者适合固定流程，后者适合自由讨论
