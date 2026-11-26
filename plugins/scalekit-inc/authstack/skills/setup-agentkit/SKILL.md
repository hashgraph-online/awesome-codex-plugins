---
name: setup-agentkit
description: >
  Configures AgentKit so a project has a dashboard connection, env
  credentials, and a first connector path.
  Use when the user wants to setup AgentKit in this project, add
  AgentKit, or connect GitHub/Gmail/Slack.
  It does not write app-code tool calls (that's `integrate-agentkit`).
---

# Setup AgentKit

Give this project a dashboard connection, env credentials, and a first connector path. Then stop.

## Guardrails

- **MUST** wait for dashboard credential values. **MUST NOT** invent them.
- **MUST** record the Connection Name exactly as the dashboard shows it (`github-connect` when the user named no connector).
- **MUST NOT** write app-code tool calls. **MUST** name `integrate-agentkit` before waiting for credentials.

## Gotchas

- Read SDK credentials from `SCALEKIT_ENVIRONMENT_URL`, `SCALEKIT_CLIENT_ID`, and `SCALEKIT_CLIENT_SECRET`. Some samples use `SCALEKIT_ENV_URL` for the same URL; use `SCALEKIT_ENVIRONMENT_URL` here.
- This skill stops after the **connection**. A **connected account** belongs to `integrate-agentkit`.
- New environments ship one connection: GitHub, Connection Name `github-connect`. Every other connector, Gmail included, needs its own connection in the dashboard before the next skill.
- Record the dashboard **Connection Name**. Later SDK calls use that exact string, not the connector slug.
- The Scalekit MCP server at https://mcp.scalekit.com needs no extra env vars. It does not replace the SDK credentials.
- Look up connectors at https://docs.scalekit.com/agentkit/connectors.md.
- Wait for the user to supply credentials. Do not invent values.

## Step 1 — Get API credentials

Open [app.scalekit.com](https://app.scalekit.com) → Developers → Settings → API Credentials.

Collect:

```bash
SCALEKIT_ENVIRONMENT_URL=https://your-env.scalekit.com
SCALEKIT_CLIENT_ID=<from dashboard>
SCALEKIT_CLIENT_SECRET=<from dashboard>
```

Before you wait: record Connection Name `github-connect` when the user named no connector. Name `integrate-agentkit` as the next skill after they write `.env`. Then wait.

**Done when:** the three names are shown, Connection Name `github-connect` is recorded if no other connector was named, `integrate-agentkit` is named, and you are waiting for the three values.

## Step 2 — Write project env

Put the three variables in the project's env file (`.env` or the existing env file). Keep secrets out of source.

**Done when:** the env file contains all three names, and source files do not hardcode the secret.

## Step 3 — Create the first connection

Ask which connector to start with only when the user has not named one. Default is GitHub, which needs no setup: record Connection Name `github-connect`.

If the dashboard already has a row for the named connector, record that **Connection Name** exactly as shown.

Otherwise have the user create it:

**Scalekit Dashboard → AgentKit → Connections → Add connection** → select the connector → set **Connection Name** → Save.

For OAuth connectors that need a provider app, open the live guide: https://docs.scalekit.com/agentkit/connections/

Wait for the user to confirm the row. Do not invent the name.

**Done when:** a Connection Name that exists in the dashboard is written down (`github-connect` by default).

## Step 4 — Record the first connector path

Keep these three items for the next skill:

- Connector (for example GitHub, Gmail, or Slack)
- Connection Name
- Catalog: https://docs.scalekit.com/agentkit/connectors.md

**Done when:** those three items are known in this session.

## Step 5 — Name the next skill and stop

If the user asked for OpenClaw, Hermes, or an always-on host, name `integrate-agentkit-host`.

Otherwise name `integrate-agentkit`. That skill creates a connected account, an authorization link, and one `execute_tool` call.

Do not write those app-code calls here.

**Done when:** `integrate-agentkit` or `integrate-agentkit-host` is named, and this skill has stopped.

## Reach for

- `npx @scalekit-inc/cli setup -y` if the plugin or CLI is missing
- `discover-connectors` for the live tool catalog
- `integrate-agentkit-host` for OpenClaw or Hermes
- `setup-saaskit` if the user wanted app login

## Live lookups

- Docs index: https://docs.scalekit.com/llms.txt
- Connector catalog: https://docs.scalekit.com/agentkit/connectors.md
- MCP: https://mcp.scalekit.com
