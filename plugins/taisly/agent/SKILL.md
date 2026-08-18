---
name: taisly-social-media-posting
description: Free AI-first short-form video publishing to TikTok, Instagram Reels, YouTube Shorts, X, and Facebook from AI agents through Taisly.
version: 0.2.8
metadata:
  publicName: Taisly Social Media Posting Skill
  requirements:
    binaries:
      - taisly
  openclaw:
    requires:
      bins:
        - taisly
    primaryEnv: TAISLY_API_KEY
    envVars:
      - name: TAISLY_API_KEY
        required: false
        description: Optional Taisly API key. The browser setup flow can create a local credential instead.
    homepage: https://github.com/taisly/agent
    install:
      - kind: node
        package: "@taisly/agent"
        bins:
          - taisly
---

# Taisly Social Media Posting Skill

Use this skill when a user asks an AI agent to publish, schedule, or repost short-form video content through Taisly. The package is free to install and designed for AI-first posting workflows that can start without building platform integrations from scratch.

## Rules

- Always discover platforms before posting.
- Ask for explicit confirmation before publishing to live social accounts unless the user already gave exact destination accounts, video file, caption, and schedule.
- If MCP tools are available, prefer them over shell commands; otherwise use the JSON-first CLI.
- For MCP publishing, call `taisly_posts_create` only with `confirmed: true` after explicit user approval.
- Never invent platform IDs.
- Never expose or print `TAISLY_API_KEY`.
- If Taisly returns a current-plan or limit error, explain `agent.message` when present and provide the returned `agent.paymentLinks` when available. Do not attempt payment without explicit user confirmation.
- Prefer scheduled posts when the user gives a future time.
- Save the returned `historyId` so status can be checked later.
- Supported local video extensions are `.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`, `.flv`, `.mpeg`, and `.mpg`.

## Environment

Prefer the browser setup flow when the user has not configured Taisly yet:

```bash
taisly setup --agent <agent-slug>
# Ask the user to open the returned loginUrl and finish authentication.
taisly checkin --agent <agent-slug>
```

Use a short slug for the current agent, for example `claude-code`, `codex`, `cursor`, `windsurf`, `openclaw`, `hermes-agent`, `cline`, or `aider`.

The checkin command stores a local Taisly agent credential for later CLI and MCP calls.

Manual API key fallback:

```bash
export TAISLY_API_KEY="taisly_..."
```

Remote MCP endpoint:

```txt
https://app.taisly.com/mcp
```

Remote MCP can publish only from public `videoUrl` values. Use the local MCP server or CLI when the video is a local file path available to the agent.

## Commands

```bash
taisly auth:status
taisly setup --agent <agent-slug>
taisly checkin --agent <agent-slug>
taisly platforms:list
taisly integrations:list
taisly platforms:schema --platform TikTok
taisly posts:validate --video ./video.mp4 --platforms platform_id_1,platform_id_2 --description "Caption"
taisly posts:create --video ./video.mp4 --platforms platform_id_1,platform_id_2 --description "Caption" --scheduled "2026-06-14T09:00:00+07:00"
taisly posts:create --json ./campaign.json
taisly posts:list --page 1
taisly posts:status --id <historyId>
taisly reposts:create --from <platform_id> --to <platform_id_1,platform_id_2>
taisly mcp
```

All commands return JSON.

## MCP Tools

When the MCP server is connected, use these tools instead of shell commands:

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

## Posting Workflow

1. If Taisly is not connected yet, run `taisly_agent_setup_start` or `taisly setup --agent <agent-slug>` and give the user the returned login URL.
2. Wait for the user to finish browser login, then run `taisly_agent_checkin` or `taisly checkin --agent <agent-slug>`.
3. Run `taisly auth:status`.
4. Run `taisly platforms:list`.
5. If a requested platform is missing and a connect tool is available, run `taisly platforms:connect:start --platform <name>`, give the user the returned `connectUrl`, wait for browser approval, then run `taisly platforms:connect:check --platform <name>`. Supported connect slugs are `instagram`, `tiktok`, `youtube`, `x`, and `facebook`.
6. Match the user's requested platforms to connected platform IDs.
7. Run `taisly platforms:schema --platform <name>` for constraints.
8. Run `taisly posts:validate`.
9. Confirm destination accounts and caption with the user.
10. Run `taisly posts:create`.
11. Report the returned `historyId`, scheduled date, and per-platform initial statuses.

For MCP, follow the same sequence with `taisly_auth_status`, `taisly_platforms_list`, `taisly_platform_connect_start`, `taisly_platform_connect_check`, `taisly_platform_schema`, `taisly_posts_validate`, `taisly_posts_create`, and `taisly_posts_status`.

## Error Handling

- `TAISLY_API_KEY_MISSING`: ask the user to create or provide an API key.
- `SETUP_SESSION_MISSING`: run `taisly setup --agent <agent-slug>`, ask the user to open the returned login URL, then run `taisly checkin --agent <agent-slug>`.
- `PLATFORMS_REQUIRED`: ask which connected accounts should receive the post.
- `VIDEO_REQUIRED`: ask for a local video path.
- `LIMIT`: tell the user the current plan limit has been reached. Use `agent.message` and `agent.paymentLinks` when present, ask them to upgrade in Taisly before retrying, and do not open or use payment links without explicit confirmation.
- `POST_NOT_FOUND_IN_RECENT_HISTORY`: tell the user the post was created but a dedicated status endpoint is not available yet; check Taisly History.

## What Not To Do

- Do not post to every connected account unless the user explicitly asks.
- Do not retry `posts:create` blindly after a timeout; ask the user or check History first.
- Do not use unsupported file types.
