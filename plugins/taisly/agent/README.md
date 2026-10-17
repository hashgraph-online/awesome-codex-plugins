![Taisly Agent Kit: AI agent social media posting for TikTok, Instagram Reels, YouTube Shorts, X, and Facebook](assets/taisly-agent-banner.jpg)

# Taisly Agent Kit

[![Taisly MCP server](https://glama.ai/mcp/servers/taisly/agent/badges/card.svg)](https://glama.ai/mcp/servers/taisly/agent)
[![Taisly MCP score](https://glama.ai/mcp/servers/taisly/agent/badges/score.svg)](https://glama.ai/mcp/servers/taisly/agent)

Free AI-first social media posting for short-form video. Taisly Agent Kit is a JSON-first SDK, CLI, Agent Skill, and MCP server that lets AI agents, developer tools, and automation workflows publish videos to TikTok, Instagram Reels, YouTube Shorts, X, Facebook, and other connected social platforms through Taisly.

Use it when your agent can create content, write captions, or prepare a campaign, but still needs a reliable video publishing API to put that content online. The package is free to install and designed to get an agent from idea to published video without building every platform integration yourself.

[Website](https://taisly.com/en) | [Agent Kit](https://taisly.com/en/ai-agent-kit) | [API Docs](https://docs.taisly.com/en/docs) | [npm](https://www.npmjs.com/package/@taisly/agent) | [GitHub](https://github.com/taisly/agent) | [MCP Registry](https://registry.modelcontextprotocol.io/v0.1/servers?search=io.github.taisly%2Fagent) | [Glama](https://glama.ai/mcp/servers/taisly/agent) | [Guide](https://taisly.com/en/blog/ai-agent-social-media-posting-api)

## Languages

Read this guide in:
[English](docs/i18n/README.en.md),
[Español](docs/i18n/README.es.md),
[Deutsch](docs/i18n/README.de.md),
[Français](docs/i18n/README.fr.md),
[Português](docs/i18n/README.pt-PT.md),
[ไทย](docs/i18n/README.th.md),
[中文](docs/i18n/README.zh-CN.md),
[Bahasa Indonesia](docs/i18n/README.id.md),
[Русский](docs/i18n/README.ru.md),
[Nederlands](docs/i18n/README.nl.md),
[한국어](docs/i18n/README.ko.md),
[日本語](docs/i18n/README.ja.md),
[العربية](docs/i18n/README.ar.md),
[Türkçe](docs/i18n/README.tr.md),
[Polski](docs/i18n/README.pl.md).

## Why developers use it

- Build AI agent social media posting into Codex, Claude Code, Cursor, OpenClaw, and custom automation tools.
- Automate video publishing from one local file to multiple connected social accounts.
- Give agents a safe JSON workflow: discover accounts, validate payloads, create posts, and check status.
- Add TikTok API posting automation, Instagram Reels automation, YouTube Shorts publishing, and cross-platform social media automation without building every platform integration yourself.
- Start free, then upgrade only when the publishing workflow grows.

Taisly handles the connected accounts and posting execution. Your agent handles planning, caption writing, campaign logic, or workflow orchestration.

## Free AI-first posting

- Install the package for free.
- Create or connect a Taisly account from your AI agent.
- Let the agent authenticate, connect social accounts, validate videos, and publish through a JSON-first workflow.
- Upgrade later when you need higher-volume publishing, larger account sets, or automatic repost workflows.

No credit card is required to get started. Paid plans are for teams and workflows that need more scale.

## Agent Skill

This package includes the **Taisly Social Media Posting Skill** in `SKILL.md`. Use it with Claude Code, Codex, Cursor, OpenClaw, and other agents when you want the agent to understand the safe posting workflow before it touches live social accounts.

Recommended skill workflow:

```txt
auth -> platforms -> validate -> confirm -> create -> status
```

The skill tells agents to discover connected accounts, validate the post, ask for explicit user confirmation, create the post, and save the returned `historyId` for status checks.

## Codex plugin

This package includes a Codex plugin manifest in `.codex-plugin/plugin.json`. The plugin points Codex to the canonical `SKILL.md` file and the official remote MCP server:

```txt
https://app.taisly.com/mcp
```

Use the plugin when you want Codex to discover both the posting workflow instructions and the Taisly MCP tools from one package. The root `SKILL.md` is the single source of truth for the agent workflow.

## Install

```bash
npm install -g @taisly/agent
```

Or run it without a global install:

```bash
npx @taisly/agent help
```

Start the stdio MCP server:

```bash
npx @taisly/agent mcp
```

For local development inside this repository:

```bash
node packages/agent/src/cli.js help
```

## Authentication

The easiest flow is to let your AI agent open the browser login for you. Use any short agent slug, for example `claude-code`, `codex`, `cursor`, `windsurf`, `openclaw`, `hermes-agent`, `cline`, or `aider`.

```txt
Help me set up Taisly Agent Kit.

1. Install the CLI: npm i -g @taisly/agent
2. Run taisly setup --agent <agent-slug> and send me the login URL so I can finish authentication.
3. Wait for me to finish login in the browser.
4. Run taisly checkin --agent <agent-slug>.
5. Tell me if Taisly is connected and ready. If not, tell me what failed.

If you cannot install or run the Taisly CLI in this environment, stop and tell me to open Taisly Settings instead.
```

The setup command stores a local Taisly agent credential, so later CLI and MCP commands can run without manually copying an API key.

Manual fallback: create an API key in [Taisly Settings](https://app.taisly.com/en/settings), then set:

```bash
export TAISLY_API_KEY="taisly_..."
```

Advanced: by default, the browser setup stores the local credential in `~/.taisly/config.json`. Most users should not change this. Set `TAISLY_CONFIG_HOME=/path/to/dir` only for CI, tests, or isolated agent profiles that need a separate credential store.

## Quick start

List the connected social accounts available to the API key:

```bash
taisly auth:status
taisly platforms:list
```

Connect a social account from an AI-agent flow:

```bash
taisly platforms:connect:start --platform instagram
# Open the returned connectUrl and finish authorization in the browser.
taisly platforms:connect:check --platform instagram
taisly platforms:list
```

Supported connect slugs: `instagram`, `tiktok`, `youtube`, `x`, `facebook`.

Validate a local video before publishing:

```bash
taisly posts:validate \
  --video ./launch.mp4 \
  --platforms platform_id_1,platform_id_2 \
  --description "Launch day"
```

Publish now:

```bash
taisly posts:create \
  --video ./launch.mp4 \
  --platforms platform_id_1,platform_id_2 \
  --description "Launch day"
```

Schedule for later:

```bash
taisly posts:create \
  --video ./launch.mp4 \
  --platforms platform_id_1,platform_id_2 \
  --description "Launch day" \
  --scheduled "2026-06-14T09:00:00+07:00"
```

Check the returned post:

```bash
taisly posts:status --id <historyId>
```

Every command prints JSON so agents can parse results without scraping terminal text.

## MCP server

Taisly is published in the official MCP Registry as:

```txt
io.github.taisly/agent
```

Display name: **Taisly Social Media Posting**

Remote MCP endpoint:

```txt
https://app.taisly.com/mcp
```

The remote MCP server uses streamable HTTP and OAuth. Remote MCP tools can publish only from public `videoUrl` values because they cannot read local files from your machine.

Codex remote MCP setup:

```bash
codex mcp add taisly --url https://app.taisly.com/mcp
codex mcp login taisly
```

Claude Code remote MCP setup:

```bash
claude mcp add --transport http taisly https://app.taisly.com/mcp
```

Then ask Claude Code to verify the connection. If OAuth is needed, Claude Code can guide the browser login from the session. You can also authenticate explicitly with `claude mcp login taisly` if you want to complete the OAuth flow from the shell before using tools.

Taisly Agent Kit also includes a local stdio MCP server in the same package. Use local MCP when your agent needs to read local video files:

```json
{
  "mcpServers": {
    "taisly": {
      "command": "npx",
      "args": ["@taisly/agent", "mcp"]
    }
  }
}
```

If you already use a manual API key, you can still pass `TAISLY_API_KEY` in the MCP server `env` block.

Codex local MCP setup:

```bash
codex mcp add taisly -- npx @taisly/agent mcp
```

Claude Code local MCP setup:

```bash
claude mcp add taisly -- npx @taisly/agent mcp
```

Then ask the agent:

```txt
Use the local Taisly MCP server you just added and run the Taisly agent setup start tool with agentId: "<agent-slug>".

Send me the login URL and wait for me to finish in the browser.
Then run the Taisly agent checkin tool with agentId: "<agent-slug>".
After checkin, run the Taisly auth status tool.
Tell me if Taisly is connected and ready. If not, tell me what failed.
```

Available MCP tools:

- `taisly_agent_setup_start`
- `taisly_agent_checkin`
- `taisly_auth_status`
- `taisly_platforms_list`
- `taisly_platform_schema`
- `taisly_platform_connect_start`
- `taisly_platform_connect_check`
- `taisly_posts_validate`
- `taisly_posts_create`
- `taisly_posts_status`
- `taisly_posts_list`
- `taisly_reposts_list`
- `taisly_reposts_create`

`taisly_posts_create` requires `confirmed: true`. Set it only after the user explicitly approves the video, destination accounts, caption, and schedule.

## JSON workflow for agents

Agents can write a payload file and pass it to the CLI:

```json
{
  "video": "./launch.mp4",
  "platforms": ["platform_id_1", "platform_id_2"],
  "description": "Launch day. Short demo, big update.",
  "scheduled": "2026-06-14T09:00:00+07:00"
}
```

Then run:

```bash
taisly posts:validate --json ./campaign.json
taisly posts:create --json ./campaign.json
```

The `video` path must point to a real local file available to the agent. Supported local preflight extensions are `.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`, `.flv`, `.mpeg`, and `.mpg`.

## Commands

```bash
taisly auth:status
taisly setup --agent <agent-slug>
taisly checkin --agent <agent-slug>
taisly platforms:list
taisly integrations:list
taisly platforms:schema --platform TikTok
taisly posts:validate --video ./launch.mp4 --platforms platform_id_1 --description "Launch day"
taisly posts:create --video ./launch.mp4 --platforms platform_id_1 --description "Launch day"
taisly posts:create --json ./campaign.json
taisly posts:list --page 1
taisly posts:status --id <historyId>
taisly reposts:list
taisly reposts:create --from <platform_id> --to <platform_id_1,platform_id_2>
taisly mcp
```

`integrations:*` commands are aliases for `platforms:*` commands. Taisly calls connected social accounts platforms in the app, while many public APIs call them integrations.

## SDK

```js
import { Taisly } from "@taisly/agent";

const taisly = new Taisly({
  apiKey: process.env.TAISLY_API_KEY,
});

const platforms = await taisly.platforms.list();

const validation = await taisly.posts.validate({
  video: "./launch.mp4",
  platforms: [platforms.data[0].id],
  description: "Launch day",
});

const post = await taisly.posts.create({
  video: "./launch.mp4",
  platforms: [platforms.data[0].id],
  description: "Launch day",
  scheduled: "2026-06-14T09:00:00+07:00",
});

console.log(validation.success);
console.log(post.historyId);
```

## Use with AI agents

Taisly Agent Kit is designed for agentic workflows where the user gives a high-level instruction and the agent executes a safe posting path.

- Codex: let a coding agent publish demo videos, launch clips, or build updates after user confirmation.
- Claude Code: add social posting to local content workflows and campaign scripts.
- Cursor: ship video publishing from developer tools, content apps, and internal automation.
- OpenClaw and other agents: connect planning, caption writing, and posting execution through a single CLI.

Recommended agent path:

```txt
auth:status -> platforms:list -> platforms:schema -> posts:validate -> user confirmation -> posts:create -> posts:status
```

## Agent recipes

The `examples/` folder includes copy-paste workflows for common coding agents:

- `examples/codex/post-video.md`
- `examples/claude-code/schedule-video.md`
- `examples/cursor/post-build-demo-video.md`
- `examples/post-video.sh`
- `examples/schedule-video.sh`

## What this package is not

- It is not a social media dashboard.
- It is not a video editor.
- It does not replace a Taisly account.
- It requires connected social accounts and a Taisly agent credential or API key.
- It does not bypass platform rules, account permissions, or media validation.

## Current limits

- `posts:create` uses the existing multipart `/post` API.
- `posts:status` reads recent history because a single-post status endpoint is not available yet.
- `posts:validate` is local preflight; final validation still happens in Taisly.
- Local MCP uses stdio transport. Remote MCP uses streamable HTTP at `https://app.taisly.com/mcp`.
- Remote MCP requires public video URLs; use local MCP or the CLI for local video files.
- Media upload reuse is planned later.

## Links

- Taisly: <https://taisly.com/en>
- Agent Kit page: <https://taisly.com/en/ai-agent-kit>
- API docs: <https://docs.taisly.com/en/docs>
- npm package: <https://www.npmjs.com/package/@taisly/agent>
- GitHub repo: <https://github.com/taisly/agent>
- MCP Registry: <https://registry.modelcontextprotocol.io/v0.1/servers?search=io.github.taisly%2Fagent>
- SEO guide: <https://taisly.com/en/blog/ai-agent-social-media-posting-api>
