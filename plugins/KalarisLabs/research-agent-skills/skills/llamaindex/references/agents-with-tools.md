# Agents with tools

### Basic agent

```python
from llama_index.core.agent import FunctionAgent
from llama_index.llms.openai import OpenAI

# Define tools
def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b

def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

# Create agent
llm = OpenAI(model="gpt-4o")
agent = FunctionAgent.from_tools(
    tools=[multiply, add],
    llm=llm,
    verbose=True
)

# Use agent
response = agent.chat("What is 25 * 17 + 142?")
print(response)
```

### RAG agent (document search + tools)

```python
from llama_index.core.tools import QueryEngineTool

# Create index as before
index = VectorStoreIndex.from_documents(documents)

# Wrap query engine as tool
query_tool = QueryEngineTool.from_defaults(
    query_engine=index.as_query_engine(),
    name="python_docs",
    description="Useful for answering questions about Python programming"
)

# Agent with document search + calculator
agent = FunctionAgent.from_tools(
    tools=[query_tool, multiply, add],
    llm=llm
)

# Agent decides when to search docs vs calculate
response = agent.chat("According to the docs, what is Python used for?")
```
