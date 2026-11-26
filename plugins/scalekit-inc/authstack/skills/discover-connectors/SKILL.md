---
name: discover-connectors
description: >
  Discovers AgentKit connectors from the live catalog and MCP
  so an agent can name tools and schemas.
  Use when the user asks what connectors exist, wants connector
  tools, or needs input/output schemas.
  It does not create a connected account or token (that's `integrate-agentkit`)
  or expose tools over MCP (that's `expose-agentkit-mcp`).
---

# Discover connectors

Name tools and schemas from the live catalog and Scalekit MCP. Then stop.

## Guardrails

- **MUST** treat the live catalog and Scalekit MCP as the source of truth. Do not cache a connector list in the repo.
- **MUST** page `list_tools` / `search_tools` until the next-page token is empty. One call is not the full catalog.
- **MUST NOT** execute tools or authorize a connected account. Name `integrate-agentkit` for that.
- **MUST** ask the user to write missing `SCALEKIT_*` values into this project's `.env` when Scalekit MCP is not connected. **MUST NOT** invent them or skip the ask.

## Gotchas

- Read SDK credentials from `SCALEKIT_ENVIRONMENT_URL`, `SCALEKIT_CLIENT_ID`, and `SCALEKIT_CLIENT_SECRET`. Some samples use `SCALEKIT_ENV_URL`; use `SCALEKIT_ENVIRONMENT_URL` here.
- A **connection** is dashboard connector config. A **connected account** is one user authorized on that connection. This skill names tools. It does not create either.
- Use `connector` in prose. Use `provider` only when the SDK field is literally `provider` or `providers`.
- `Filter.provider` is the connector identifier from the catalog or `search_connectors` (for example `GMAIL`). It is not the dashboard Connection Name.
- Framework helpers such as `actions.langchain.get_tools` need a connected-account identifier and hide pagination. Use `actions.tools.list_tools` here.
- Output schemas are not in the tool definition. Use the connector's official API docs for response shape.
- Default language is Python. If the repo is Node, open [references/node.md](references/node.md). If the language is unknown, stay on Python.

## Step 1 — Name the connector

Open https://docs.scalekit.com/agentkit/connectors.md. If Scalekit MCP at https://mcp.scalekit.com is connected, call `search_connectors` instead of copying that page.

If the user already named a connector, use that identifier. Do not invent a slug.

**Done when:** a connector identifier is written down (for example `GMAIL`).

## Step 2 — Init the SDK

If the repo is Node, follow [references/node.md](references/node.md) from here.

If Scalekit MCP is already connected, skip this step and go to Step 3.

If env vars are missing, collect them from [app.scalekit.com](https://app.scalekit.com) → Developers → Settings → API Credentials. Ask the user to put them in this project's env file. Do not invent values. Do not skip this ask because the catalog page already lists tools.

```bash
pip install scalekit-sdk-python python-dotenv
```

```python
from scalekit import ScalekitClient
from scalekit.v1.tools.tools_pb2 import Filter
from google.protobuf.json_format import MessageToDict
import os
from dotenv import load_dotenv
load_dotenv()

sk_client = ScalekitClient(
    client_id=os.getenv("SCALEKIT_CLIENT_ID"),
    client_secret=os.getenv("SCALEKIT_CLIENT_SECRET"),
    env_url=os.getenv("SCALEKIT_ENVIRONMENT_URL"),
)
tools = sk_client.actions.tools
```

**Done when:** MCP is connected, or you have asked the user to write the three names into this project's `.env` and shown the client init from those env vars. Source files do not hardcode the secret.

## Step 3 — Page tools and schemas

If Scalekit MCP is connected, call `search_tools` with the connector identifier. Set `summary=false` for input schemas. Pass `pageToken` until the response has no next page.

Otherwise page the SDK. Replace `"GMAIL"` with the identifier from Step 1.

```python
page_token = None
while True:
    page, _ = tools.list_tools(
        filter=Filter(provider="GMAIL"),
        page_size=100,
        page_token=page_token,
    )
    for tool in page.tools:
        definition = MessageToDict(tool.definition) if tool.definition else {}
        print(definition.get("name"), definition.get("description"))
        print(definition.get("input_schema"))
    page_token = page.next_page_token or None
    if not page_token:
        break
```

For one tool by name:

```python
page, _ = tools.list_tools(
    filter=Filter(tool_name=["gmail_fetch_mails"]),
    page_size=1,
)
```

If the list is empty, the identifier does not match the live catalog. Re-run Step 1.

**Done when:** every page is collected, or the named tool's schema is printed.

## Step 4 — Summarize and stop

For each useful tool, record:

- tool name
- connector
- what it does
- required fields from `input_schema.required`
- optional fields from `input_schema.properties`

Recommend the smallest tool set for the user's workflow. Then stop.

**Done when:** the user has a named tool list and input schemas. No tool was executed. No connected account was authorized.

## Reach for

- `integrate-agentkit` to create a connected account and call one API
- `expose-agentkit-mcp` to expose tools over MCP
- [references/node.md](references/node.md) for the Node SDK path

## Live lookups

- Docs index: https://docs.scalekit.com/llms.txt
- Connector catalog: https://docs.scalekit.com/agentkit/connectors.md
- MCP: https://mcp.scalekit.com
