---
name: integrate-agentkit-host
description: >
  Integrates AgentKit into an always-on host
  so OpenClaw or Hermes can act as a named user.
  Use when the user wants OpenClaw, Hermes,
  clawhub install, or an always-on host skill.
  It does not write AgentKit in app code
  (that's `integrate-agentkit`)
  or expose tools over MCP
  (that's `expose-agentkit-mcp`).
---

# Integrate AgentKit Host

Wire an always-on **host** so it can act as a named user through AgentKit. Then stop.

A **host** is a long-lived agent process (OpenClaw or Hermes). It is not this git repo.

## Guardrails

- **MUST** wait for dashboard credential values. **MUST NOT** invent them.
- **MUST** pass the exact dashboard Connection Name. Never invent a slug.
- **MUST** put only Scalekit client credentials on the host. Provider tokens stay in Scalekit.
- **MUST** confirm a tool name with `tool_exec.py --get-tool` or the connector's page in https://docs.scalekit.com/agentkit/connectors.md before calling it.

## Gotchas

- Read `SCALEKIT_ENVIRONMENT_URL`, `SCALEKIT_CLIENT_ID`, `SCALEKIT_CLIENT_SECRET`, and `SCALEKIT_IDENTIFIER`. OpenClaw also accepts `TOOL_*` aliases. Never `SCALEKIT_ENV_URL`.
- A **connection** already exists from `setup-agentkit`. This skill starts there.
- The Slack gateway bot is a channel. It is not the named user.
- Do not run `hermes mcp login` against Scalekit. Do not mint a Virtual MCP session token for another end user inside this host. A single-operator host may hold one operator bearer. See https://docs.scalekit.com/agentkit/hermes/
- Default host is OpenClaw. Hermes is [references/hermes.md](references/hermes.md).

## Step 1 — Pick the host

- OpenClaw → stay here.
- Hermes → open [references/hermes.md](references/hermes.md). Stop reading this file.
- App code in this repo → name `integrate-agentkit`. Stop.
- Per-user MCP URL → name `expose-agentkit-mcp`. Stop.

If env is missing, collect the three Scalekit client values from [app.scalekit.com](https://app.scalekit.com) → Developers → Settings → API Credentials. Ask for the named-user identifier (email or user id). Do not invent values.

**Done when:** the host is OpenClaw, and the four names exist.

## Step 2 — Confirm the connection

Use the Connection Name already recorded by `setup-agentkit`.

If none is recorded: GitHub is `github-connect`, the one connection new environments ship. Every other connector, Gmail included, needs its own dashboard row. If that row is missing, name `setup-agentkit` and stop.

**Done when:** a Connection Name is written down.

## Step 3 — Install the OpenClaw skill

```bash
clawhub install scalekit-agent-auth
```

That slug is the shipped ClawHub listing. Do not create a new GitHub repo for it.

**Done when:** `clawhub` lists `scalekit-agent-auth`.

## Step 4 — Write host env

Put Scalekit **client** credentials in the OpenClaw env file (`.env` next to the skill, or the host env). These are not Gmail or Slack tokens.

```bash
SCALEKIT_ENVIRONMENT_URL=https://your-env.scalekit.cloud
SCALEKIT_CLIENT_ID=<from dashboard>
SCALEKIT_CLIENT_SECRET=<from dashboard>
SCALEKIT_IDENTIFIER=<named user>
```

`TOOL_ENV_URL`, `TOOL_CLIENT_ID`, `TOOL_CLIENT_SECRET`, and `TOOL_IDENTIFIER` also work.

From this skill directory:

```bash
cd scripts && uv sync
uv run tool_exec.py --list-connections --provider GMAIL
```

**Done when:** the env file has those names, and `--list-connections` returns a completed connection or a clear empty list.

## Step 5 — Authorize if needed

```bash
uv run tool_exec.py --generate-link --connection-name <CONNECTION_NAME>
```

OAuth: if not `ACTIVE`, show the magic link and wait. API key: if missing or not `ACTIVE`, send the user to the Dashboard and stop.

**Done when:** the connected account is `ACTIVE`, or the next action is on screen.

## Step 6 — Stop

Name one real host prompt for the user, for example “Show my latest unread emails.” Do not write app-code SDK calls.

OpenClaw follows the ClawHub skill `scalekit-agent-auth` at chat time. Hermes follows the installed `hermes-delegated-auth` skill.

**Done when:** OpenClaw is installed, env is set, and this skill has stopped.

## Reach for

- `setup-agentkit` if the connection or env is missing
- `integrate-agentkit` for AgentKit in app code
- `expose-agentkit-mcp` for a per-user MCP URL
- [references/hermes.md](references/hermes.md) for Hermes
- ClawHub `scalekit-agent-auth` for the OpenClaw chat loop

## Live lookups

- Docs index: https://docs.scalekit.com/llms.txt
- Connector catalog: https://docs.scalekit.com/agentkit/connectors.md
- OpenClaw skill: https://github.com/scalekit-inc/openclaw-skill
- ClawHub: https://clawhub.ai/avinash-kamath/skills/scalekit-agent-auth
- MCP: https://mcp.scalekit.com
