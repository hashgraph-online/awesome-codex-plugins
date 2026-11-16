# tossithere

Share HTML as a link people can comment on, element by element, and read every
comment back with the exact markup it points at.

Your agent publishes a report, plan, dashboard or prototype. You get a link that
opens on any screen. Reviewers click any element or highlight any text to comment,
with nothing to install. The agent reads the open threads, publishes the fix to
the same link, and resolves what it fixed.

## Install

**Claude Code**

```
/plugin marketplace add kush-daga/tossithere-plugin
/plugin install tossithere@tossithere
```

Or the server alone: `claude mcp add --transport http tossithere https://tossithere.com/mcp`

**Claude, ChatGPT and other apps with connectors:** add a custom connector with
the URL `https://tossithere.com/mcp`. You sign in with your tossithere account.

**Gemini CLI:** `gemini extensions install https://github.com/kush-daga/tossithere-plugin`

**Cursor, VS Code, Windsurf and other MCP clients:** add a remote (HTTP) server at
`https://tossithere.com/mcp`. Clients without OAuth can send an API key from
https://tossithere.com/keys as `Authorization: Bearer toss_sk_...`.

## Tools

| Tool | What it does |
|---|---|
| `publish_page` | Publish HTML as a page, or a new version of one, at a stable link |
| `list_pages` | The user's pages, with open comment counts |
| `read_page` | A page's HTML as published, any version |
| `list_comments` | Comment threads with the markup each one points at |
| `reply_to_comment` | Reply in a thread |
| `resolve_comment` | Resolve or reopen a thread |
| `share_page` | Private, team or public, and read, comment or edit |
| `list_teams` | Who is signed in, and their teams |

Nothing here deletes a page.

## What's in this repo

- `skills/tossithere/SKILL.md`: when and how an agent should use tossithere
- `.claude-plugin/`, `.mcp.json`: Claude Code plugin and marketplace
- `plugin.json`, `mcp.json`: Agent Plugins format, used by ChatGPT and Codex
- `gemini-extension.json`: Gemini CLI extension

Privacy: https://tossithere.com/privacy · Terms: https://tossithere.com/terms
