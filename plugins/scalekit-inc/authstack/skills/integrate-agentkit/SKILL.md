---
name: integrate-agentkit
description: >
  Integrates AgentKit so an agent can create a connected account,
  authorize it, then call one tool through Scalekit.
  Use when the user wants AgentKit in app code, a GitHub/Gmail/Slack/Notion
  connected account, or an authorization link.
  It does not list connectors (that's `discover-connectors`)
  or wire an always-on host (that's `integrate-agentkit-host`).
---

# Integrate AgentKit

Take this repo from a **connection** to a **connected account**, an authorization link, and one tool call with `execute_tool`. Then stop.

This is the docs quickstart path: https://docs.scalekit.com/agentkit/quickstart/

## Guardrails

- **MUST** pass the exact dashboard Connection Name (`connection_name` in Python, `connectionName` in Node). Never invent a slug. Never use a `connector` field for that value.
- **MUST** call tools with `execute_tool` (`executeTool` in Node). Scalekit adds the user's token to the outgoing request. Scalekit does not return raw user tokens to your app.
- **MUST** confirm a tool name on the connector's page in https://docs.scalekit.com/agentkit/connectors.md, or with `list_tools` scoped to the Connection Name, before you call it.
- **MUST** re-check the connected account status after the user finishes OAuth. Call the tool only when it is `ACTIVE`.
- **MUST** print the authorization link and stop when the process is not interactive. Re-run the script after the user finishes OAuth.
- **MUST** take missing `SCALEKIT_*` values from the user. **MUST NOT** copy them from another project, home directory, or skill folder.

## Gotchas

- Read SDK credentials from `SCALEKIT_ENVIRONMENT_URL`, `SCALEKIT_CLIENT_ID`, and `SCALEKIT_CLIENT_SECRET`. Some samples use `SCALEKIT_ENV_URL`; use `SCALEKIT_ENVIRONMENT_URL` here.
- A **connection** is dashboard connector config. A **connected account** is one user authorized on that connection.
- New environments ship one connection: GitHub, Connection Name `github-connect`. Every other connector, Gmail included, needs its own connection in **AgentKit → Connections**. `setup-agentkit` creates it.
- Default language is Python. If the repo is Node, open [references/node.md](references/node.md). If the language is unknown, stay on Python.

## Step 1 — Confirm the Connection Name

Use the Connection Name already recorded by `setup-agentkit`.

If none is recorded:

- User named no connector: GitHub, Connection Name `github-connect`.
- User named a connector: use its dashboard **Connection Name** exactly as shown.
- That connector has no dashboard connection yet: name `setup-agentkit` and stop.

**Done when:** a Connection Name that exists in the dashboard is written down.

## Step 2 — Init the SDK

If the repo is Node, follow [references/node.md](references/node.md) from here.

If env vars are missing, collect them from [app.scalekit.com](https://app.scalekit.com) → Developers → Settings → API Credentials. Ask the user to put them in this project's env file. Do not invent values. Do not copy values from another directory.

```bash
pip install scalekit-sdk-python python-dotenv
```

```python
import os
from dotenv import load_dotenv
from scalekit import ScalekitClient

load_dotenv()

scalekit_client = ScalekitClient(
    env_url=os.environ["SCALEKIT_ENVIRONMENT_URL"],
    client_id=os.environ["SCALEKIT_CLIENT_ID"],
    client_secret=os.environ["SCALEKIT_CLIENT_SECRET"],
)
actions = scalekit_client.actions
```

**Done when:** the client initializes from those three env vars, and source files do not hardcode the secret.

## Step 3 — Create the connected account

Replace `"user_123"` with the project's stable user id. Replace `"github-connect"` with the recorded Connection Name.

```python
connection_name = "github-connect"
user_id = "user_123"

account = actions.get_or_create_connected_account(
    connection_name=connection_name,
    identifier=user_id,
).connected_account
```

**Done when:** a connected account exists for that identifier and Connection Name.

## Step 4 — Authorize, then re-check status

If `account.status` is `ACTIVE`, skip this step.

```python
import sys

if account.status != "ACTIVE":
    link = actions.get_authorization_link(
        connection_name=connection_name,
        identifier=user_id,
    ).link
    print(f"Open this link and approve access:\n{link}")
    if not sys.stdin.isatty():
        raise SystemExit("Finish OAuth in a browser, then run this script again.")
    input("Press Enter when you're done...")

    account = actions.get_connected_account(
        connection_name=connection_name,
        identifier=user_id,
    ).connected_account
    if account.status != "ACTIVE":
        raise SystemExit(f"The account is {account.status}, not ACTIVE. Run the script again.")
```

In a web app, redirect the browser to `link`, then check the status again when the user returns.

**Done when:** status is `ACTIVE` after the re-check, or the link is printed and a non-interactive run has stopped.

## Step 5 — Call one tool

Default: `github_user_get_authenticated`, a read-only GitHub tool with no input.

```python
result = actions.execute_tool(
    tool_name="github_user_get_authenticated",
    tool_input={},
    connected_account_id=account.id,
)
print(result.data)
```

For another connector, pick a read-only tool from its page in https://docs.scalekit.com/agentkit/connectors.md, or list the tools on that connection:

```python
tools = actions.list_tools(
    connection_name=connection_name,
    identifier=user_id,
    page_size=100,
)
print(tools.tool_names)
```

Change only `tool_name` and `tool_input` in Step 5. Keep Steps 3–4.

**Done when:** one `execute_tool` call returns data for the connected account.

## Reach for

- `setup-agentkit` if the connection or env is missing
- `discover-connectors` for the live tool catalog and input schemas
- `integrate-agentkit-host` for OpenClaw or Hermes
- `expose-agentkit-mcp` to expose tools over MCP
- [references/node.md](references/node.md) for the Node SDK path
- [references/frameworks.md](references/frameworks.md) for LangChain and Google ADK

## Live lookups

- Quickstart: https://docs.scalekit.com/agentkit/quickstart/
- Docs index: https://docs.scalekit.com/llms.txt
- Connector catalog: https://docs.scalekit.com/agentkit/connectors.md
- MCP: https://mcp.scalekit.com
