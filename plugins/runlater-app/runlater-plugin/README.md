# RunLater plugin

Call any URL at an exact time or on a cron schedule from your coding agent. [RunLater](https://runlater.app) retries failures and keeps a log of each run's status code, timing and response.

This repository holds the plugin config and agent skill. The MCP server is hosted at `https://runlater.app/api/mcp`.

## Install

Claude Code plugin:

```
/plugin marketplace add runlater-app/runlater-plugin
/plugin install runlater@runlater
```

Agent skill only:

```
npx skills add runlater-app/runlater-plugin
```

Or add only the MCP server:

```
claude mcp add --transport http --scope user runlater https://runlater.app/api/mcp
```

[![Add to Replit](https://replit.com/badge?caption=Add%20to%20Replit)](https://replit.com/integrations?mcp=eyJkaXNwbGF5TmFtZSI6IlJ1bkxhdGVyIiwiYmFzZVVybCI6Imh0dHBzOi8vcnVubGF0ZXIuYXBwL2FwaS9tY3AifQ==)

Then run `/mcp` and sign in. [Setup for claude.ai, Cursor, VS Code, Codex and Windsurf](https://runlater.app/docs/mcp).

## What you can ask

- "Call https://example.com/api/sync every weekday at 9am Chicago time."
- "Send a POST to my webhook next Tuesday at 3pm UTC."
- "Did last night's run succeed? Show me the response."
- "Pause that job until I say so."

## Tools

`schedule_get_request`, `schedule_send_request`, `list_schedules`, `get_schedule`, `run_now`, `pause_schedule`, `resume_schedule`, `delete_schedule`, `account_status`

## Pricing

Scheduling needs a plan: Starter $15/month, Team $39/month, Pro $149/month, each with a 14-day trial. [Plans](https://runlater.app/#pricing)

## Support

hello@greatwork.company
