# YAML configuration (recommended)

### Project structure

```
my_project/
├── src/my_project/
│   ├── config/
│   │   ├── agents.yaml    # Agent definitions
│   │   └── tasks.yaml     # Task definitions
│   ├── crew.py            # Crew assembly
│   └── main.py            # Entry point
└── pyproject.toml
```

### agents.yaml

```yaml
researcher:
  role: "{topic} Senior Data Researcher"
  goal: "Uncover cutting-edge developments in {topic}"
  backstory: >
    You're a seasoned researcher with a knack for uncovering
    the latest developments in {topic}. Known for your ability
    to find relevant information and present it clearly.

reporting_analyst:
  role: "Reporting Analyst"
  goal: "Create detailed reports based on research data"
  backstory: >
    You're a meticulous analyst who transforms raw data into
    actionable insights through well-structured reports.
```

### tasks.yaml

```yaml
research_task:
  description: >
    Conduct thorough research about {topic}.
    Find the most relevant information for {year}.
  expected_output: >
    A list with 10 bullet points of the most relevant
    information about {topic}.
  agent: researcher

reporting_task:
  description: >
    Review the research and create a comprehensive report.
    Focus on key findings and recommendations.
  expected_output: >
    A detailed report in markdown format with executive
    summary, findings, and recommendations.
  agent: reporting_analyst
  output_file: report.md
```

### crew.py

```python
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool

@CrewBase
class MyProjectCrew:
    """My Project crew"""

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher'],
            tools=[SerperDevTool()],
            verbose=True
        )

    @agent
    def reporting_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['reporting_analyst'],
            verbose=True
        )

    @task
    def research_task(self) -> Task:
        return Task(config=self.tasks_config['research_task'])

    @task
    def reporting_task(self) -> Task:
        return Task(
            config=self.tasks_config['reporting_task'],
            output_file='report.md'
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
```

### main.py

```python
from my_project.crew import MyProjectCrew

def run():
    inputs = {
        'topic': 'AI Agents',
        'year': 2025
    }
    MyProjectCrew().crew().kickoff(inputs=inputs)

if __name__ == "__main__":
    run()
```
