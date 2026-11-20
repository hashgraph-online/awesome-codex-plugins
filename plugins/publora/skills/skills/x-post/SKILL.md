---
name: x-post
description: Use when the user wants to post or schedule to X (Twitter) through Publora, including threads auto-split past 280 characters, up to 4 images, or a video up to 140 seconds. X needs a paid Publora plan. Not for Threads or Bluesky (each has its own skill).
---

# X/Twitter Post

Create and schedule posts to X (Twitter) using the Publora MCP server. Supports text posts, images (up to 4), videos, and automatic thread splitting for long-form content.

## Prerequisites

**Plans:** Requires a paid plan (X API costs are passed through). Current limits and pricing: [publora.com/pricing](https://publora.com/pricing).

**Important:** X/Twitter is NOT available on the free Starter plan due to Twitter API costs.

### Getting Started

1. **Create account** at [publora.com/register](https://publora.com/register)
2. **Choose Pro or Premium plan** (X/Twitter requires paid plan)
3. **Connect X/Twitter** via OAuth in [Publora Dashboard](https://app.publora.com/dashboard)
4. **Get an API key** at [app.publora.com/dashboard/api](https://app.publora.com/dashboard/api), only if your agent cannot sign in with OAuth or you will use the REST API fallback below
5. **Connect your agent** to the MCP server at `https://mcp.publora.com/mcp`:
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

If MCP is unavailable, use the REST API directly:

**Base URL:** `https://api.publora.com/api/v1`

**Authentication:** `x-publora-key` header

```bash
# Get connected platforms
curl -X GET "https://api.publora.com/api/v1/platform-connections" \
  -H "x-publora-key: sk_your_api_key"

# Create a post
curl -X POST "https://api.publora.com/api/v1/create-post" \
  -H "x-publora-key: sk_your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "platforms": ["twitter-123456789"],
    "content": "Your tweet content",
    "scheduledTime": "2026-03-25T10:00:00Z"
  }'
```

**Platform ID Format:** `twitter-{id}` (e.g., `twitter-123456789`)

📖 **Docs:** [docs.publora.com](https://docs.publora.com)

## Platform Limits

| Feature | API Limit | Notes |
|---------|-----------|-------|
| Characters | 280 | Emojis count as 2 characters |
| Images | Up to 4 | Auto-converted to PNG (max 1000px width) |
| Video duration | **2 min 20 s (140 s)** | Publora validates X videos at 140 s |
| Video size | 512 MB | MP4, MOV formats |
| Threading | Automatic | Content over 280 chars split with `(1/N)` markers |

## Character Counting

X has specific character counting rules that Publora handles automatically:

- Standard characters = 1
- **Emojis = 2 characters**
- URLs counted by literal length
- Thread markers reserve 10 characters per tweet

## Auto-Threading

When content exceeds 280 characters, Publora automatically creates a connected thread:

1. Content split at paragraph breaks, then sentence boundaries, then word boundaries
2. Each part numbered with `(1/N)`, `(2/N)` format
3. Tweets connected via X's `reply_to_id` parameter

### Manual Thread Breaks

Use `---` on its own line to force a thread break:

```
This is my first tweet in the thread.

---

This is my second tweet in the thread.

---

And this is my third tweet!
```

## Available Tools

### create_post
Create a new X/Twitter post or thread.

**Parameters:**
- `platforms`: Array with your X connection ID (e.g., `["twitter-12345678"]`)
- `content`: Post text (auto-threads if over 280 chars)
- `scheduledTime`: ISO 8601 UTC datetime. **Optional**: omit it and the post is created as a draft. Send a future time to schedule. A time five or more minutes in the past is rejected with `SCHEDULED_TIME_IN_PAST`, so for immediate posting use the current time plus a minute.
- `mediaUrls`: up to 10 public **https** image or video URLs. Publora downloads them server-side and attaches them *before* validation, so media and scheduling happen in one call. This is the one-shot alternative to the draft then `get_upload_url` then `complete_media` flow. Ingestion is rate-limited to 60 URLs per hour.

### get_upload_url
Get presigned URL for media uploads.

**Parameters:**
- `postGroupId`: Post ID to attach media to
- `fileName`: File name (e.g., "image.png", "video.mp4")
- `contentType`: `image/png`, `image/jpeg`, `video/mp4`
- `type`: `"image"` or `"video"`

### complete_media
Finalize a file uploaded through `get_upload_url`, after the presigned `PUT` succeeds. Optional, because scheduling also finalizes pending media, but calling it early surfaces format and probe errors before publish. Not needed for media attached with `mediaUrls`.

**Parameters:**
- `mediaId`: the id returned by `get_upload_url`

### list_connections
List your connected accounts with their platform IDs. Call this first and copy the IDs verbatim; they are never guessable.

### list_posts / get_post / update_post / delete_post
Manage scheduled and draft posts. `update_post` also patches `content` and `platforms` on a draft or scheduled post, so fixing a typo or retargeting no longer means delete and recreate. `delete_media` and `prune_media_reference` clean up uploaded files.

## Examples

### Simple Tweet
```
Post this to X:
"Just shipped our new API documentation. Check it out!"
```

### Tweet with Images
```
Post this to Twitter with screenshots of the new dashboard:
"Before and after our redesign. What do you think?"
```
Note: Up to 4 images allowed. All images auto-converted to PNG.

### Long-Form Thread
```
Create a Twitter thread:
"Thread: 5 lessons from building our startup

---

1. Ship early, iterate fast. We launched with a buggy MVP and improved based on real feedback.

---

2. Talk to users daily. Our best features came from customer conversations.

---

3. Focus beats features. We killed 3 products to focus on the one that worked."
```

### Scheduled Tweet
```
Schedule this for tomorrow at 9 AM:
"Monday motivation: Start before you're ready."
```

## Important Restrictions

1. **Pro plan required**: X/Twitter is excluded from the free Starter plan due to Twitter API costs.

2. **140-second video limit**: Publora validates X videos at 2 minutes 20 seconds (140 seconds). Longer videos fail validation.

3. **Image auto-conversion**: All images are converted to PNG (max 1000px width) before upload. Animated GIFs lose animation.

4. **No image+video mix**: A tweet can have images OR video, not both.

5. **Media on first tweet only**: In threads, images/video attach to the first tweet only.

## Best Practices

### Content
1. **Hook in first line**: Most engagement happens on the first tweet
2. **Optimal thread length**: 3-7 tweets for best engagement
3. **Emoji awareness**: Remember emojis count as 2 characters

### Timing
- **Best times**: 8-10 AM, 12-1 PM, 5-6 PM in target timezone
- **Frequency**: 3-5 tweets per day for growth
- **Threads**: Post in morning for maximum visibility

### Engagement
- Reply to comments within the first hour
- Quote tweet your own threads for visibility
- Use relevant hashtags (1-2 per tweet)

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| "X/Twitter requires Pro plan" | Using Starter plan | Upgrade to Pro at publora.com/settings |
| "Content too long" | Over 280 chars and threading failed | Add manual `---` breaks |
| "Video too long" | Over 140 seconds | Trim video to under 2 min 20 s |
| "Too many images" | More than 4 images | Reduce to 4 or fewer |
| "Rate limit exceeded" | X API limit reached | Wait and retry |
