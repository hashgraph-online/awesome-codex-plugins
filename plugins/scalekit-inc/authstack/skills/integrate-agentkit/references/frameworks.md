# Integrate AgentKit — framework samples

Not the default path. Finish connection → connected account → re-check status → one `execute_tool` call in `SKILL.md` first.

The LangChain and Google ADK tool helpers are Python only in the Scalekit SDK. Install the framework packages. The Scalekit SDK alone is not enough.

Scope tools with `connection_names`, the dashboard Connection Name used in `SKILL.md`. Pass `page_size` so a connector with many tools is not cut off at the default page.

Confirm tool names on the connector's page in https://docs.scalekit.com/agentkit/connectors.md, or with `actions.list_tools`, before you name one in a prompt or config.

For Node agents, keep the `executeTool` path in [node.md](node.md), or expose the tools over MCP with `expose-agentkit-mcp`. The Node SDK has the Virtual MCP API (`actions.mcp.createConfig`, `listConnectedAccounts`, `createSessionToken`).

Replace `"gmail"` below with the recorded Connection Name. Gmail needs its own dashboard connection; new environments ship only `github-connect`.

## LangChain

Docs: https://docs.scalekit.com/agentkit/examples/langchain/

```bash
pip install scalekit-sdk-python langchain-openai
```

`actions.langchain.get_tools()` returns native `StructuredTool` objects. Bind them to the model and run the tool-calling loop. This works on LangChain 1.x.

```python
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, ToolMessage

tools = actions.langchain.get_tools(
    identifier="user_123",
    connection_names=["gmail"],
    page_size=100,
)
tool_map = {t.name: t for t in tools}

llm = ChatOpenAI(model="gpt-4o").bind_tools(tools)
messages = [HumanMessage("Fetch my last 5 unread emails and summarize them")]

while True:
    response = llm.invoke(messages)
    messages.append(response)
    if not response.tool_calls:
        print(response.content)
        break
    for tc in response.tool_calls:
        result = tool_map[tc["name"]].invoke(tc["args"])
        messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
```

To let LangChain run the loop, use `create_agent` from `langchain` 1.x (`pip install "langchain>=1,<2"`):

```python
from langchain.agents import create_agent

agent = create_agent("openai:gpt-4o", tools=tools)
result = agent.invoke(
    {"messages": [{"role": "user", "content": "Fetch my last 5 unread emails and summarize them"}]}
)
print(result["messages"][-1].content)
```

`AgentExecutor` and `create_openai_tools_agent` moved to `langchain-classic` in 1.x. Use one of the two patterns above.

## Google ADK

Docs: https://docs.scalekit.com/agentkit/examples/google-adk/

```bash
pip install "scalekit-sdk-python[google-adk]" "google-adk>=2,<3"
```

`actions.google.get_tools()` returns native ADK tools. Run the agent with an ADK `Runner` and a session service.

```python
import asyncio
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

tools = actions.google.get_tools(
    identifier="user_123",
    connection_names=["gmail"],
    page_size=100,
)

agent = Agent(
    name="gmail_assistant",
    model="gemini-2.0-flash",
    instruction="You are a helpful Gmail assistant.",
    tools=tools,
)

async def main():
    session_service = InMemorySessionService()
    runner = Runner(agent=agent, app_name="gmail_app", session_service=session_service)
    session = await session_service.create_session(app_name="gmail_app", user_id="user_123")

    message = types.Content(
        role="user",
        parts=[types.Part(text="Fetch my last 5 unread emails and summarize them")],
    )
    async for event in runner.run_async(
        user_id="user_123",
        session_id=session.id,
        new_message=message,
    ):
        if event.is_final_response() and event.content and event.content.parts:
            print(event.content.parts[0].text)

asyncio.run(main())
```

More framework patterns: https://docs.scalekit.com/agentkit/examples/
