---
name: telegram-post
description: Use when the user wants to post or schedule to a Telegram channel or group through Publora, using a bot. Covers Telegram markdown, silent delivery, link previews and forward protection. Bot API caps media captions at 1,024 characters and videos at 50 MB. Not for other platforms (each has its own skill).
---

# Telegram Post

Create and schedule posts to Telegram channels and groups using the Publora MCP server. Supports rich markdown formatting, photos, videos, and message delivery options.

## Prerequisites

**Plans:** Works on the free Starter plan. Current limits and pricing: [publora.com/pricing](https://publora.com/pricing).

### Getting Started

1. **Create account** at [publora.com/register](https://publora.com/register) (free)
2. **Create Telegram bot:**
   - Message [@BotFather](https://t.me/BotFather) on Telegram
   - Send `/newbot` and follow instructions
   - Save the bot token
4. **Add bot to your channel:**
   - Add the bot as **administrator** to your channel/group
   - Grant `can_post_messages` permission
5. **Connect in Publora** at [Dashboard](https://app.publora.com/dashboard) with the bot token and the channel:
   - Public channel: `@username` or `t.me/username`
   - Private channel: its `-100…` chat ID, or the `t.me/c/…` link of any message in it (Copy Link on the message)
   - Invite links (`t.me/+…`) are rejected: the Bot API cannot identify a channel from them
6. **Get an API key** at [app.publora.com/dashboard/api](https://app.publora.com/dashboard/api), only if your agent cannot sign in with OAuth or you will use the REST API fallback below
7. **Connect your agent** to the MCP server at `https://mcp.publora.com/mcp`:
   - **Upgrading a manual connection without `/mcp`:** Claude treats `https://mcp.publora.com` as a different server from the bundled one. Change that existing connection to `https://mcp.publora.com/mcp` in its current scope, preserving its authentication and chosen account; sign in again if requested. Alternatively, verify the bundled connection uses the intended account, then remove only the old manual entry. Do not add a second entry or delete credentials automatically.
   - **Publora tools already available** (the `publora-skills` plugin or the Publora connector in Claude): nothing to set up. Claude asks you to sign in to Publora the first time a tool runs.
   - **Agents that support OAuth** (Claude Code, Cursor, and the Claude and ChatGPT apps): add the server by URL and sign in, no API key needed. In Claude Code, add it and then run `/mcp` to sign in:

```bash
claude mcp add --transport http --scope user publora https://mcp.publora.com/mcp
```

   - **Agents without OAuth:** send the API key as `Authorization: Bearer sk_YOUR_API_KEY`:

```bash
claude mcp add --transport http --scope user publora https://mcp.publora.com/mcp \
  --header "Authorization: Bearer sk_YOUR_API_KEY"
```

   Claude Desktop, Cursor, Codex, OpenClaw and the claude.ai connector each need a different config file or flow: see [client setup](https://docs.publora.com/mcp/client-setup) for the exact path and snippet.

### REST API Fallback

If the MCP server is unavailable or returns errors, use the REST API directly:

**Base URL:** `https://api.publora.com/api/v1`

**Authentication:** Use `x-publora-key` header (NOT `Authorization: Bearer`):

```bash
# Get your connected platforms
curl -X GET "https://api.publora.com/api/v1/platform-connections" \
  -H "x-publora-key: sk_your_api_key"

# Create a post
curl -X POST "https://api.publora.com/api/v1/create-post" \
  -H "x-publora-key: sk_your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "platforms": ["telegram--1001234567890"],
    "content": "*Announcement*\n\nYour message here",
    "scheduledTime": "2026-03-25T10:00:00Z"
  }'
```

**Platform ID Format:** `telegram-{chat_id}` where `{chat_id}` is the channel/group numeric ID from `/platform-connections`. A bot connection's chat ID is negative (`-100…`), so the ID has a double dash. Copy it verbatim; never rebuild it.

Example IDs: `telegram--1001234567890`, `telegram--1002345678901`

📖 **Full API documentation:** [docs.publora.com](https://docs.publora.com)

## Platform Limits (Bot API)

| Feature | Limit |
|---------|-------|
| Text message | 4,096 characters |
| **Media caption** | **1,024 characters** (critical limit!) |
| Images | 10 MB max, 10 per media group |
| Image formats | JPEG, PNG, GIF, BMP, WebP |
| **Video size** | **50 MB max** (not 4 GB - that's for users!) |
| Video formats | MP4, MOV, AVI, MKV, WebM |
| Rate limit | 30 msg/sec global, 20 msg/min per group |

**Critical:** Bot API has much lower limits than regular Telegram users. Videos over 50 MB and captions over 1,024 characters will fail.

## Markdown Formatting

Telegram uses its own markdown flavor with **single asterisks** for bold:

| Syntax | Result |
|--------|--------|
| `*bold*` | **bold** |
| `_italic_` | *italic* |
| `` `code` `` | `inline code` |
| ``` ```code``` ``` | Code block |
| `[text](url)` | [hyperlink](url) |
| `> text` | Blockquote |

**Note:** This differs from standard Markdown where `**double asterisks**` make bold.

## Available Tools

### create_post
Create a new Telegram post.

**Parameters:**
- `platforms`: Array with your Telegram connection ID (e.g., `["telegram--1001234567890"]`)
- `content`: Message text (supports markdown)
- `scheduledTime`: ISO 8601 UTC datetime. **Optional**: omit it and the post is created as a draft. Send a future time to schedule. A time five or more minutes in the past is rejected with `SCHEDULED_TIME_IN_PAST`, so for immediate posting use the current time plus a minute.
- `mediaUrls`: up to 10 public **https** image or video URLs. Publora downloads them server-side and attaches them *before* validation, so media and scheduling happen in one call. This is the one-shot alternative to the draft then `get_upload_url` then `complete_media` flow. Ingestion is rate-limited to 60 URLs per hour.

### get_upload_url
Get presigned URL for media uploads.

### complete_media
Finalize a file uploaded through `get_upload_url`, after the presigned `PUT` succeeds. Optional, because scheduling also finalizes pending media, but calling it early surfaces format and probe errors before publish. Not needed for media attached with `mediaUrls`.

**Parameters:**
- `mediaId`: the id returned by `get_upload_url`

### list_connections
List your connected accounts with their platform IDs. Call this first and copy the IDs verbatim; they are never guessable. A private channel has no public username: its `username` is `null`, so match it by `displayName` (the channel title).

### list_posts / get_post / update_post / delete_post
Manage scheduled and draft posts. `update_post` also patches `content` and `platforms` on a draft or scheduled post, so fixing a typo or retargeting no longer means delete and recreate. `delete_media` and `prune_media_reference` clean up uploaded files.

## Post Options (via REST API)

Telegram-specific options available via REST API `platformSettings.telegram`:

| Option | Description |
|--------|-------------|
| `disableNotification` | Send silently (no sound) |
| `disableWebPagePreview` | No link preview cards |
| `protectContent` | Prevent forwarding/saving |

Caption-above-media is **not** settable: `showCaptionAboveMedia` is not an accepted key and sending it returns `400 PLATFORM_SETTING_UNKNOWN`.

Note: `platformSettings` is accepted by the MCP `create_post` and `update_post` tools as well as over REST. The schema is **strict**: a mistyped platform or key is rejected with a validation error rather than silently dropped.

## Examples

### Simple Channel Post
```
Post this to my Telegram channel:
"*Product Update v2.5*

We have shipped the following improvements:
- _Faster API response times_ (avg 45ms)
- New `batch` endpoint for bulk operations

[Read the changelog](https://example.com/changelog)"
```

### Formatted Announcement
```
Create a Telegram post with this formatting:
"*Important Update*

We're launching our new feature tomorrow at 10 AM UTC.

_What's new:_
- Feature A improvements
- Feature B release

[Read the full announcement](https://example.com/update)"
```

### Post with Image
```
Post this image to my Telegram channel with caption:
"*New Dashboard Preview*

Here's a sneak peek at our redesigned analytics dashboard."
```
**Important:** Caption must be under 1,024 characters when posting with media.

### Scheduled Post
```
Schedule this for tomorrow at 8 AM Moscow time:
"*Good morning!* Here's your daily market summary..."
```

## Important Restrictions

1. **Caption limit is 1,024 chars**: When posting with media (images/videos), text is sent as a caption limited to 1,024 characters. Text-only messages allow 4,096 characters.

2. **Video max 50 MB**: Bot API limits videos to 50 MB (not 4 GB like regular users). Large videos will fail.

3. **Bot must be admin**: Your bot needs administrator role with `can_post_messages` permission. This is verified at connection time and re-checked by `POST /test-connection/{platformId}`, not before each post.

4. **No mixed media**: A single post cannot contain both images and videos.

5. **Caption overflow**: If caption exceeds 1,024 chars on a media post, it's sent as a separate reply message instead of being truncated.

## Best Practices

### Content
1. **Use formatting**: Bold headlines, italic emphasis improves readability
2. **Link previews**: Great for articles; disable for cleaner announcements
3. **Emoji usage**: Common and expected on Telegram
4. **Post length**: No penalty for longer posts on text-only messages

### Timing
- **Global audience**: Telegram users are worldwide; consider timezone posts
- **Best times**: 8-10 AM, 12-2 PM, 7-9 PM in target regions
- **Frequency**: Channels can post more frequently (5-10/day)

### Engagement
- Enable comments in channel settings for discussions
- Use polls for engagement
- Pin important announcements

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| "Bot not admin" | Bot missing admin permissions | Add bot as admin with `can_post_messages` |
| "Channel not found" | Wrong channel name/ID, or the bot is not in the channel | Verify `@channelname` or the `-100…` chat ID, and add the bot as an administrator |
| "Invite links cannot identify a channel for a bot" | A `t.me/+…` invite link was entered | Use the channel's `-100…` chat ID or a `t.me/c/…` message link |
| `MEDIA_CAPTION_TOO_LONG` | Caption > 1,024 chars | Shorten caption or use text-only post |
| "Bad Request: file is too big" | File > 50 MB | Compress video/image to under 50 MB |
| "Mixed media not supported" | Images + video in same post | Use one media type per post |
