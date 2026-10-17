---
framework: crewai
version: "0.100.x"
language: python
verified_date: "2025-01-15"
---

# CrewAI 适配器

## 框架概述

- **语言**: Python
- **核心库**: `crewai`, `crewai-tools`
- **特点**: 角色扮演式多 Agent、高层抽象、任务委派、流程编排
- **适用**: 业务流程自动化、角色化团队协作、报告生成

## 项目模板

```
{project_name}/
├── pyproject.toml
├── .env.example
├── README.md
├── src/
│   ├── __init__.py
│   ├── crew.py            # Crew 定义（核心）
│   ├── agents.py          # Agent 角色定义
│   ├── tasks.py           # 任务定义
│   ├── tools.py           # 自定义工具
│   └── config.py          # 配置
├── tests/
│   ├── __init__.py
│   ├── test_crew.py
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
    "crewai>=0.100.0",
    "crewai-tools>=0.17.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0"]
```

## Agent 创建模式

### 角色定义

```python
from crewai import Agent

researcher = Agent(
    role="高级研究员",
    goal="查找和整理关于{topic}的最新信息",
    backstory="""你是一位经验丰富的研究员，擅长从海量信息中
    提取关键洞察。你以严谨著称，总是引用可靠来源。""",
    tools=[search_tool, web_scraper],
    llm="openai/gpt-4o",
    verbose=True,
    allow_delegation=True,  # 允许委派任务给其他 Agent
)

analyst = Agent(
    role="数据分析师",
    goal="分析研究数据并提取有价值的商业洞察",
    backstory="""你是一位数据分析专家，擅长将复杂数据转化为
    清晰的商业建议。你的分析总是数据驱动的。""",
    tools=[analysis_tool],
    llm="openai/gpt-4o",
    verbose=True,
)

writer = Agent(
    role="报告撰写人",
    goal="将研究和分析结果撰写成专业报告",
    backstory="""你是一位专业的商业写手，擅长将复杂信息
    组织成清晰、可操作的报告。""",
    llm="openai/gpt-4o",
    verbose=True,
)
```

## 任务定义模式

```python
from crewai import Task

research_task = Task(
    description="研究{topic}的最新趋势和关键数据点",
    expected_output="包含关键发现、数据点和来源引用的研究报告",
    agent=researcher,
)

analysis_task = Task(
    description="基于研究报告，分析数据并提取商业洞察",
    expected_output="包含数据分析、趋势预测和建议的分析报告",
    agent=analyst,
    context=[research_task],  # 依赖上一个任务
)

report_task = Task(
    description="将研究和分析整合成最终报告",
    expected_output="格式规范的最终报告，包含摘要、分析和建议",
    agent=writer,
    context=[research_task, analysis_task],
    output_file="output/report.md",  # 输出到文件
)
```

## 工具定义模式

```python
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

class SearchOrdersInput(BaseModel):
    query: str = Field(description="搜索关键词：订单号或客户名")
    status: str | None = Field(default=None, description="可选，按状态过滤")

class SearchOrdersTool(BaseTool):
    name: str = "search_orders"
    description: str = "按订单号或客户名搜索订单列表"
    args_schema: type[BaseModel] = SearchOrdersInput
    
    def _run(self, query: str, status: str = None) -> str:
        results = do_search(query, status)
        return str(results)

# 或使用 crewai-tools 内置工具
from crewai_tools import SerperDevTool, WebsiteSearchTool

search_tool = SerperDevTool()
web_tool = WebsiteSearchTool()
```

## Crew 编排

```python
from crewai import Crew, Process

# 顺序流程
crew = Crew(
    agents=[researcher, analyst, writer],
    tasks=[research_task, analysis_task, report_task],
    process=Process.sequential,
    verbose=True,
)

# 层级流程（带管理者）
crew = Crew(
    agents=[researcher, analyst, writer],
    tasks=[research_task, analysis_task, report_task],
    process=Process.hierarchical,
    manager_llm="openai/gpt-4o",
    verbose=True,
)
```

### CrewAI Flow（高级编排）

```python
from crewai.flow.flow import Flow, listen, start

class ResearchFlow(Flow):
    @start()
    def collect_requirements(self):
        return self.state.get("topic", "AI Agent")
    
    @listen(collect_requirements)
    def run_research(self, topic):
        crew = Crew(
            agents=[researcher],
            tasks=[research_task],
            process=Process.sequential,
        )
        return crew.kickoff(inputs={"topic": topic})
    
    @listen(run_research)
    def run_analysis(self, research_result):
        crew = Crew(
            agents=[analyst, writer],
            tasks=[analysis_task, report_task],
            process=Process.sequential,
        )
        return crew.kickoff(inputs={"research": research_result})

flow = ResearchFlow()
result = flow.kickoff(inputs={"topic": "AI Agent 开发趋势"})
```

## Memory 配置

```python
# CrewAI 内置 Memory 支持
crew = Crew(
    agents=[researcher, analyst],
    tasks=[research_task, analysis_task],
    process=Process.sequential,
    memory=True,                    # 启用记忆
    # embedder 配置（用于语义记忆）
    embedder={
        "provider": "openai",
        "config": {"model": "text-embedding-3-small"},
    },
)
```

## 运行入口

```python
from dotenv import load_dotenv
from src.crew import build_crew

load_dotenv()

def main():
    crew = build_crew()
    
    topic = input("请输入研究主题: ")
    
    result = crew.kickoff(inputs={"topic": topic})
    
    print("\n" + "=" * 50)
    print("最终结果:")
    print("=" * 50)
    print(result.raw)

if __name__ == "__main__":
    main()
```

## 注意事项

- CrewAI 的核心抽象是 Agent（角色）+ Task（任务）+ Crew（团队）
- `backstory` 对 Agent 行为影响很大，是角色扮演的关键
- `allow_delegation=True` 允许 Agent 将子任务委派给其他 Agent
- `context` 参数建立 Task 之间的依赖关系
- `Process.hierarchical` 自动添加 Manager Agent 进行协调
- CrewAI Flow 提供更灵活的编排，支持条件分支和循环
