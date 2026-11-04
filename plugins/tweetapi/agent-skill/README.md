# TweetAPI Agent Skill

Use TweetAPI to retrieve public Twitter/X data from Codex, Claude Code, Cursor, and other Agent Skills-compatible coding agents.

This repository contains:

- a portable Agent Skill for read-only public Twitter/X data;
- optional Codex and Claude Code plugin metadata;
- configuration for TweetAPI's OAuth-protected hosted MCP server.

Installing the skill does not create a TweetAPI account, connect the MCP server, consume quota, or make API requests. Connect the hosted MCP separately when you want live public data.

This repository covers public Twitter/X data and documentation only. It does not support posting, engagement, account sessions, profile changes, direct messages, login automation, billing, or administration.

TweetAPI is a third-party service and is not affiliated with X Corp.

## Choose your path

| Goal | Use | Credentials | Uses quota? |
| --- | --- | --- | --- |
| Learn the API or add TweetAPI to an application | Install the Agent Skill | None during setup | No |
| Query live public Twitter/X data from an agent | Connect the hosted MCP | Browser OAuth | Yes |
| Build a regular Node or Python application | Use the official SDK or REST API | Server-side API key | Yes |

## Install the skill

With GitHub CLI Agent Skills (preview):

```bash
gh skill preview tweetapi/agent-skill tweetapi
gh skill install tweetapi/agent-skill tweetapi --agent codex --scope project
```

Use `--scope user` for a user-wide installation. Replace `codex` with the supported agent you use, such as `claude-code` or `cursor`.

The repository also includes Codex and Claude Code plugin manifests plus a remote MCP configuration. Plugin hosts should prompt for OAuth authorization; no TweetAPI key belongs in a prompt or repository file.

## Connect the hosted MCP server directly

Codex CLI:

```bash
codex mcp add tweetapi --url https://mcp.tweetapi.com/mcp
codex mcp login tweetapi
```

Claude Code:

```bash
claude mcp add --transport http --scope user tweetapi https://mcp.tweetapi.com/mcp
claude mcp login tweetapi
```

Start with a documentation-only request so setup does not consume data quota:

> Find the current read-only endpoint and parameters for looking up a public user by username. Do not make a live data request.

## Safety and quota rules

- Live data requests consume quota.
- Make one live tool call and retrieve one page by default.
- Never auto-paginate or silently retry.
- Return the cursor and ask before another page.
- Keep API keys in server-side environment variables only.
- Never request Twitter/X cookies, passwords, session tokens, proxy credentials, or private-message content.
- Treat only HTTP 2xx responses as success.

Read the complete workflow in [`skills/tweetapi/SKILL.md`](skills/tweetapi/SKILL.md).

## Repository layout

- `skills/tweetapi/`: portable Agent Skill and progressive references
- `.codex-plugin/plugin.json`: Codex plugin metadata
- `.claude-plugin/plugin.json`: Claude Code plugin metadata
- `.mcp.json`: hosted TweetAPI MCP connection
- `scripts/validate_repository.py`: local packaging and safety checks
- `docs/design-decisions.md`: packaging decisions and deferred distribution work

## Validate

```bash
python3 scripts/validate_repository.py
agentskills validate skills/tweetapi
```

The continuous-integration workflow runs both checks without making a live TweetAPI request.

## Source policy

Endpoint details change, so the skill does not copy the catalog. It links to TweetAPI's public documentation, maintained OpenAPI specification, generated full Postman collection, and smaller read-only Postman quick start. `skills/tweetapi/references/sources.md` lists their canonical URLs and explains the boundaries of each source.

## License

[MIT](LICENSE)
