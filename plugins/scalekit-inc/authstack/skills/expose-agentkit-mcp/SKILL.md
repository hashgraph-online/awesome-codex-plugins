---
name: expose-agentkit-mcp
description: >
  Exposes AgentKit tools over MCP so a client can call them
  on one static mcp_server_url plus a per-run session token.
  Use when the user wants to expose AgentKit over MCP, generate
  a per-user MCP URL, or connect LangChain via MCP.
  It does not list connectors (that's `discover-connectors`)
  or create a connected account and call a tool in app code (that's `integrate-agentkit`).
---

# Expose AgentKit over MCP

Create an AgentKit MCP config, mint a per-run session token, and make one Streamable HTTP client call. Then stop.

## Guardrails

- **MUST** use Streamable HTTP. stdio and SSE are not supported.
- **MUST** pass the exact dashboard Connection Name (`connection_name`). Never invent a slug. Never use a `connector` field for that value.
- **MUST** reuse one static `mcp_server_url`. Mint a session token per identifier and per run with `create_session_token`.

## Gotchas

- Read SDK credentials from `SCALEKIT_ENVIRONMENT_URL`, `SCALEKIT_CLIENT_ID`, and `SCALEKIT_CLIENT_SECRET`. Some samples use `SCALEKIT_ENV_URL`; use `SCALEKIT_ENVIRONMENT_URL` here. Do not prepend `https://` if the value already has a scheme.
- A **connection** is dashboard connector config. A **connected account** is one user authorized on that connection. This skill authorizes through `list_mcp_connected_accounts` auth links, not `integrate-agentkit` app-code `execute_tool` calls.
- `create_session_token` is remint. Call it again before the next run. Do not reuse a token from a previous session.
- New environments ship one connection: GitHub, Connection Name `github-connect`. Every other connector, Gmail and Google Calendar included, needs its own connection in **AgentKit → Connections**. Record each name exactly.
- Default language is Python. If the repo is Node, follow [references/node.md](references/node.md): the Node SDK has the same API on `scalekit.actions.mcp` (`createConfig`, `listConnectedAccounts`, `createSessionToken`).
- Confirm every tool name on the connector's page in https://docs.scalekit.com/agentkit/connectors.md, or with `discover-connectors`, before you put it in a config. Do not copy connector pages into the repo.

## Step 1 — Confirm Connection Names

Default path: Gmail plus Google Calendar, so one email fetch and one reminder event.

- Gmail: use the dashboard Gmail Connection Name. If there is no Gmail row, have the user create it at **Scalekit Dashboard → AgentKit → Connections → Add connection → Gmail** → Save.
- Google Calendar: have the user create it at **Scalekit Dashboard → AgentKit → Connections → Add connection → Google Calendar** → **Connection Name = `MY_CALENDAR`** → Save.

Wait for the user to confirm both rows. Do not invent either name.

To test with no setup, map only `github-connect` and a GitHub tool such as `github_user_repos_list`.

**Done when:** Gmail and Calendar each have an exact dashboard Connection Name.

## Step 2 — Init the SDK

If the repo is Node, follow [references/node.md](references/node.md) from here.

If env vars are missing, collect them from [app.scalekit.com](https://app.scalekit.com) → Developers → Settings → API Credentials. Put them in the project env file. Do not invent values.

```bash
pip install scalekit-sdk-python langgraph>=0.6.5 langchain langchain-openai langchain-mcp-adapters>=0.1.9 python-dotenv>=1.0.1
```

```python
import os
import asyncio
from dotenv import load_dotenv
from scalekit import ScalekitClient
from scalekit.actions.models.mcp_config import McpConfigConnectionToolMapping
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

sk_client = ScalekitClient(
    client_id=os.getenv("SCALEKIT_CLIENT_ID"),
    client_secret=os.getenv("SCALEKIT_CLIENT_SECRET"),
    env_url=os.getenv("SCALEKIT_ENVIRONMENT_URL"),
)
my_mcp = sk_client.actions.mcp
```

Set `OPENAI_API_KEY` in the environment for the LangChain client in Step 5.

**Done when:** the client initializes from those three env vars, and source files do not hardcode the secret.

## Step 3 — Create the MCP config

Replace `"gmail"` and `"MY_CALENDAR"` with the recorded Connection Names. Create the config once. Reuse `config_id` and `mcp_server_url`.

```python
cfg_response = my_mcp.create_config(
    name="reminder-manager",
    description="Summarizes latest email and creates a reminder event",
    connection_tool_mappings=[
        McpConfigConnectionToolMapping(
            connection_name="gmail",
            tools=["gmail_fetch_mails"],
        ),
        McpConfigConnectionToolMapping(
            connection_name="MY_CALENDAR",
            tools=["googlecalendar_create_event"],
        ),
    ],
)
config_id = cfg_response.config.id
mcp_server_url = cfg_response.config.mcp_server_url
print("MCP server URL:", mcp_server_url)
```

**Done when:** `config_id` and a static `mcp_server_url` exist.

## Step 4 — Print auth links if needed

Replace `"user_123"` with the project's user id.

```python
accounts_response = my_mcp.list_mcp_connected_accounts(
    config_id=config_id,
    identifier="user_123",
    include_auth_link=True,
)
for account in accounts_response.connected_accounts:
    print(
        "Connection:", account.connection_name,
        " Auth Link:", account.authentication_link,
        " Status:", account.connected_account_status,
    )
```

Tell the user to open every printed auth link and finish OAuth. A non-interactive run stops here until they do.

**Done when:** each mapped connection is authorized, or every needed auth link is printed.

## Step 5 — Mint a session token and call over Streamable HTTP

```python
from datetime import timedelta

token_response = my_mcp.create_session_token(
    mcp_config_id=config_id,
    identifier="user_123",
    expiry=timedelta(hours=1),
)
token = token_response.token

async def main():
    client = MultiServerMCPClient(
        {
            "reminder_demo": {
                "transport": "streamable_http",
                "url": mcp_server_url,
                "headers": {"Authorization": f"Bearer {token}"},
            },
        }
    )
    tools = await client.get_tools()
    agent = create_react_agent("openai:gpt-4o", tools)
    response = await agent.ainvoke(
        {"messages": "get 1 latest email and create a calendar reminder event in next 15 mins for a duration of 15 mins."}
    )
    print(response)

asyncio.run(main())
```

**Done when:** the Streamable HTTP client loads the tools and one invoke succeeds.

## Reach for

- `discover-connectors` for live tool names and schemas
- `integrate-agentkit` to create a connected account and call a tool in app code
- [references/node.md](references/node.md) for the Node SDK path
- `setup-agentkit` if the connection or env is missing

## Live lookups

- Docs index: https://docs.scalekit.com/llms.txt
- Connector catalog: https://docs.scalekit.com/agentkit/connectors.md
- MCP: https://mcp.scalekit.com
