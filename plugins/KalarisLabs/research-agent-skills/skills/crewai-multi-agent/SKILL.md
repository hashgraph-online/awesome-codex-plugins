---
name: crewai-multi-agent
description: Multi-agent orchestration framework for autonomous AI collaboration. Use when building teams of specialized agents working together on complex tasks, when you need role-based agent collaboration with memory, or for production workflows requiring sequential/hierarchical execution. Built without LangChain dependencies for lean, fast execution.
license: MIT
metadata:
  version: 1.0.0
  category: llm-applications
  maintainer: Kalaris Labs
  tags: Agents, CrewAI, Multi-Agent, Orchestration, Collaboration, Role-Based, Autonomous, Workflows, Memory, Production
  dependencies: crewai>=1.2.0, crewai-tools>=1.2.0
---

# CrewAI - Multi-Agent Orchestration Framework

Build teams of autonomous AI agents that collaborate to solve complex tasks.

## When to use CrewAI

**Use CrewAI when:**
- Building multi-agent systems with specialized roles
- Need autonomous collaboration between agents
- Want role-based task delegation (researcher, writer, analyst)
- Require sequential or hierarchical process execution
- Building production workflows with memory and observability
- Need simpler setup than LangChain/LangGraph

**Key features:**
- **Standalone**: No LangChain dependencies, lean footprint
- **Role-based**: Agents have roles, goals, and backstories
- **Dual paradigm**: Crews (autonomous) + Flows (event-driven)
- **50+ tools**: Web scraping, search, databases, AI services
- **Memory**: Short-term, long-term, and entity memory
- **Production-ready**: Tracing, enterprise features

**Use alternatives instead:**
- **LangChain**: General-purpose LLM apps, RAG pipelines
- **LangGraph**: Complex stateful workflows with cycles
- **AutoGen**: Microsoft ecosystem, multi-agent conversations
- **LlamaIndex**: Document Q&A, knowledge retrieval

## Quick start

### Installation

```bash
# Core framework
pip install crewai

# With 50+ built-in tools
pip install 'crewai[tools]'
```

### Create project with CLI

```bash
# Create new crew project
crewai create crew my_project
cd my_project

# Install dependencies
crewai install

# Run the crew
crewai run
```

### Simple crew (code-only)

```python
from crewai import Agent, Task, Crew, Process

# 1. Define agents
researcher = Agent(
    role="Senior Research Analyst",
    goal="Discover cutting-edge developments in AI",
    backstory="You are an expert analyst with a keen eye for emerging trends.",
    verbose=True
)

writer = Agent(
    role="Technical Writer",
    goal="Create clear, engaging content about technical topics",
    backstory="You excel at explaining complex concepts to general audiences.",
    verbose=True
)

# 2. Define tasks
research_task = Task(
    description="Research the latest developments in {topic}. Find 5 key trends.",
    expected_output="A detailed report with 5 bullet points on key trends.",
    agent=researcher
)

write_task = Task(
    description="Write a blog post based on the research findings.",
    expected_output="A 500-word blog post in markdown format.",
    agent=writer,
    context=[research_task]  # Uses research output
)

# 3. Create and run crew
crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, write_task],
    process=Process.sequential,  # Tasks run in order
    verbose=True
)

# 4. Execute
result = crew.kickoff(inputs={"topic": "AI Agents"})
print(result.raw)
```

## Core concepts

### Agents - Autonomous workers

```python
from crewai import Agent

agent = Agent(
    role="Data Scientist",                    # Job title/role
    goal="Analyze data to find insights",     # What they aim to achieve
    backstory="PhD in statistics...",         # Background context
    llm="gpt-4o",                             # LLM to use
    tools=[],                                 # Tools available
    memory=True,                              # Enable memory
    verbose=True,                             # Show reasoning
    allow_delegation=True,                    # Can delegate to others
    max_iter=15,                              # Max reasoning iterations
    max_rpm=10                                # Rate limit
)
```

### Tasks - Units of work

```python
from crewai import Task

task = Task(
    description="Analyze the sales data for Q4 2024. {context}",
    expected_output="A summary report with key metrics and trends.",
    agent=analyst,                            # Assigned agent
    context=[previous_task],                  # Input from other tasks
    output_file="report.md",                  # Save to file
    async_execution=False,                    # Run synchronously
    human_input=False                         # No human approval needed
)
```

### Crews - Teams of agents

```python
from crewai import Crew, Process

crew = Crew(
    agents=[researcher, writer, editor],      # Team members
    tasks=[research, write, edit],            # Tasks to complete
    process=Process.sequential,               # Or Process.hierarchical
    verbose=True,
    memory=True,                              # Enable crew memory
    cache=True,                               # Cache tool results
    max_rpm=10,                               # Rate limit
    share_crew=False                          # Opt-in telemetry
)

# Execute with inputs
result = crew.kickoff(inputs={"topic": "AI trends"})

# Access results
print(result.raw)                             # Final output
print(result.tasks_output)                    # All task outputs
print(result.token_usage)                     # Token consumption
```

## Process types

### Sequential (default)

Tasks execute in order, each agent completing their task before the next:

```python
crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, write_task],
    process=Process.sequential  # Task 1 → Task 2 → Task 3
)
```

### Hierarchical

Auto-creates a manager agent that delegates and coordinates:

```python
crew = Crew(
    agents=[researcher, writer, analyst],
    tasks=[research_task, write_task, analyze_task],
    process=Process.hierarchical,  # Manager delegates tasks
    manager_llm="gpt-4o"           # LLM for manager
)
```

## Using tools

### Built-in tools (50+)

```bash
pip install 'crewai[tools]'
```

```python
from crewai_tools import (
    SerperDevTool,           # Web search
    ScrapeWebsiteTool,       # Web scraping
    FileReadTool,            # Read files
    PDFSearchTool,           # Search PDFs
    WebsiteSearchTool,       # Search websites
    CodeDocsSearchTool,      # Search code docs
    YoutubeVideoSearchTool,  # Search YouTube
)

# Assign tools to agent
researcher = Agent(
    role="Researcher",
    goal="Find accurate information",
    backstory="Expert at finding data online.",
    tools=[SerperDevTool(), ScrapeWebsiteTool()]
)
```

### Custom tools

```python
from crewai.tools import BaseTool
from pydantic import Field
from scripts.safe_arithmetic import calculate

class CalculatorTool(BaseTool):
    name: str = "Calculator"
    description: str = "Performs mathematical calculations. Input: expression"

    def _run(self, expression: str) -> str:
        try:
            result = calculate(expression)
            return f"Result: {result}"
        except Exception as e:
            return f"Error: {str(e)}"

# Use custom tool
agent = Agent(
    role="Analyst",
    goal="Perform calculations",
    tools=[CalculatorTool()]
)
```

## YAML configuration (recommended)

Details, code examples and parameter tables: [references/yaml-configuration-recommended.md](references/yaml-configuration-recommended.md). Read it when this step applies.

## Flows - Event-driven orchestration

For complex workflows with conditional logic, use Flows:

```python
from crewai.flow.flow import Flow, listen, start, router
from pydantic import BaseModel

class MyState(BaseModel):
    confidence: float = 0.0

class MyFlow(Flow[MyState]):
    @start()
    def gather_data(self):
        return {"data": "collected"}

    @listen(gather_data)
    def analyze(self, data):
        self.state.confidence = 0.85
        return analysis_crew.kickoff(inputs=data)

    @router(analyze)
    def decide(self):
        return "high" if self.state.confidence > 0.8 else "low"

    @listen("high")
    def generate_report(self):
        return report_crew.kickoff()

# Run flow
flow = MyFlow()
result = flow.kickoff()
```

See [Flows Guide](references/flows.md) for complete documentation.

## Memory system

```python
# Enable all memory types
crew = Crew(
    agents=[researcher],
    tasks=[research_task],
    memory=True,           # Enable memory
    embedder={             # Custom embeddings
        "provider": "openai",
        "config": {"model": "text-embedding-3-small"}
    }
)
```

**Memory types:** Short-term (ChromaDB), Long-term (SQLite), Entity (ChromaDB)

## LLM providers

```python
from crewai import LLM

llm = LLM(model="gpt-4o")                              # OpenAI (default)
llm = LLM(model="claude-sonnet-4-5-20250929")                       # Anthropic
llm = LLM(model="ollama/llama3.1", base_url="http://localhost:11434")  # Local
llm = LLM(model="azure/gpt-4o", base_url="https://...")              # Azure

agent = Agent(role="Analyst", goal="Analyze data", llm=llm)
```

## CrewAI vs alternatives

| Feature | CrewAI | LangChain | LangGraph |
|---------|--------|-----------|-----------|
| **Best for** | Multi-agent teams | General LLM apps | Stateful workflows |
| **Learning curve** | Low | Medium | Higher |
| **Agent paradigm** | Role-based | Tool-based | Graph-based |
| **Memory** | Built-in | Plugin-based | Custom |

## Best practices

1. **Clear roles** - Each agent should have a distinct specialty
2. **YAML config** - Better organization for larger projects
3. **Enable memory** - Improves context across tasks
4. **Set max_iter** - Prevent infinite loops (default 15)
5. **Limit tools** - 3-5 tools per agent max
6. **Rate limiting** - Set max_rpm to avoid API limits

## Common issues

**Agent stuck in loop:**
```python
agent = Agent(
    role="...",
    max_iter=10,           # Limit iterations
    max_rpm=5              # Rate limit
)
```

**Task not using context:**
```python
task2 = Task(
    description="...",
    context=[task1],       # Explicitly pass context
    agent=writer
)
```

**Memory errors:**
```python
# Use environment variable for storage
import os
os.environ["CREWAI_STORAGE_DIR"] = "./my_storage"
```

## References

- **[Flows Guide](references/flows.md)** - Event-driven workflows, state management
- **[Tools Guide](references/tools.md)** - Built-in tools, custom tools, MCP
- **[Troubleshooting](references/troubleshooting.md)** - Common issues, debugging

## Resources

- **GitHub**: https://github.com/crewAIInc/crewAI
- **Docs**: https://docs.crewai.com
- **Tools**: https://github.com/crewAIInc/crewAI-tools
- **Examples**: https://github.com/crewAIInc/crewAI-examples
- **Version**: 1.2.0+
- **License**: MIT

## Agent operating procedure

1. **Check the environment.** Confirm the framework version, model provider, API keys and rate limits.
2. **Pin down the inputs.** Confirm formats, identifiers and parameters from the data or the user. Ask rather than guess any value that changes the result.
3. **Run a small version first.** Test a single call or chain with a known input and inspect raw outputs.
4. **Execute the full task** using the instructions and references above.
5. **Validate the result.** Evaluate on a small labeled set; check structured outputs against their schema; log prompts and responses.
6. **Report.** State what was run (versions, commands, parameters), what was checked, and what is still uncertain.

| If this happens | Do this |
|---|---|
| Outputs do not match the expected schema | Add validation and retries, tighten the schema, or simplify the prompt. |
| A function, flag or endpoint in these instructions is missing in the installed version | Check the installed version's own documentation (`help()`, `--help`, official docs), adapt, and tell the user. Never invent an API. |
| A required input, identifier or parameter is ambiguous | Ask the user, or state the assumption explicitly before running. |

**Integrity rules**

- Never fabricate results, parameters, identifiers, citations or statistics. If something cannot be run or verified, say so plainly.
- Never send private or sensitive data to external APIs without the user's consent.
- Treat version-specific details here as possibly outdated: confirm them against the official documentation for the installed version.
- Ask before actions that cost money, consume shared GPUs or cloud quota, touch personal or patient data, or cannot be undone.

## Related skills

- `autogpt-agents`: Autonomous AI agent platform for building and deploying continuous agents.
- `langchain`: Framework for building LLM-powered applications with agents, chains, and RAG.
- `aeon`: This skill should be used for time series machine learning tasks including classification, regression, clustering, forecasting, anomaly det…
