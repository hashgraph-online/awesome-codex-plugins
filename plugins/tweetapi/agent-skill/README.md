# TweetAPI Agent Skill

Use TweetAPI to retrieve public Twitter/X data from Codex, Claude Code, Cursor, and other Agent Skills-compatible coding agents.

This repository contains:

- a portable Agent Skill for read-only public Twitter/X data;
- optional Codex and Claude Code plugin metadata;
- configuration for TweetAPI's OAuth-protected hosted MCP server.

Installing the skill doesn't create a TweetAPI account, connect the MCP server, spend units or make API requests. Connect the hosted MCP separately when you want live public data.

The skill covers public Twitter/X data, TweetAPI's docs, and the free unit check for your own API key. It doesn't post, like, follow, send or read DMs, handle X logins, or change accounts, billing or admin settings.

TweetAPI is a third-party service and is not affiliated with X Corp.

## Choose your path

| Goal | Use | Credentials | Uses units? |
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

This installs the latest release. To try unreleased changes from `main`, pin a commit with `tweetapi@<commit>` or `--pin <commit>`.

The repository also includes Codex and Claude Code plugin manifests and a remote MCP configuration. Plugin hosts ask you to sign in to TweetAPI. Never put a TweetAPI key in a prompt or in this repository.

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

To check the connection without spending units, start with a docs question:

> Find the current TweetAPI endpoint and parameters for looking up a public user by username. Don't make a live data request.

## How the skill behaves

- Live requests usually cost 1 unit each. The unit check is free.
- The agent says how many requests it plans, fetches one page at a time, and asks before fetching more.
- It reports failed calls instead of retrying them silently.
- API keys stay in server-side environment variables.
- It never asks for X cookies, passwords, session tokens or proxy credentials.

The full instructions are in [`skills/tweetapi/SKILL.md`](skills/tweetapi/SKILL.md).

## Repository layout

- `skills/tweetapi/`: the skill, and the guides it loads when needed
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

Endpoints change, so the skill links to TweetAPI's docs, OpenAPI spec and Postman collections instead of copying them. `skills/tweetapi/references/sources.md` lists each source and what it's for.

## License

[MIT](LICENSE)
