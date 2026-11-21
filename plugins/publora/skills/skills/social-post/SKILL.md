---
name: social-post
description: Use when the user wants to post or schedule to YouTube, a Facebook Page or Mastodon through Publora. YouTube needs a video on every post, Facebook publishes to Pages only, Mastodon caps at 500 characters. Not for the platforms that have their own skill.
---

# Social Post (YouTube, Facebook, Mastodon)

Create and schedule posts to YouTube, Facebook Pages, and Mastodon using the Publora MCP server. This skill covers platforms that work through standard posting without platform-specific complexity.

## Prerequisites

**Plans:** Works on the free Starter plan. Current limits and pricing: [publora.com/pricing](https://publora.com/pricing).

### Getting Started

1. **Create account** at [publora.com/register](https://publora.com/register) (free)
2. **Connect platforms** via OAuth in [Publora Dashboard](https://app.publora.com/dashboard):
   - **YouTube**: Google OAuth (requires YouTube channel)
   - **Facebook**: Facebook OAuth (Pages only, not personal profiles)
   - **Mastodon**: OAuth (mastodon.social instance)
3. **Get an API key** at [app.publora.com/dashboard/api](https://app.publora.com/dashboard/api), only if your agent cannot sign in with OAuth or you will use the REST API fallback below
4. **Connect your agent** to the MCP server at `https://mcp.publora.com/mcp`:
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
    "platforms": ["youtube-UCxxx", "facebook-123456", "mastodon-789"],
    "content": "Your post content",
    "scheduledTime": "2026-03-25T10:00:00Z"
  }'
```

**Platform ID Formats:**
- YouTube: `youtube-{channel_id}` (e.g., `youtube-UCxxx`)
- Facebook: `facebook-{page_id}` (e.g., `facebook-112233445566`)
- Mastodon: `mastodon-{id}` (e.g., `mastodon-456`)

📖 **Docs:** [docs.publora.com](https://docs.publora.com)

---

## YouTube

**Video-only platform** - every post requires a video file.

### Platform Limits

| Feature | Limit |
|---------|-------|
| Video title | 100 characters |
| Video description | 5,000 characters |
| Video duration | 12 hours |
| Video size | 256 GB |
| Video formats | MP4, MOV, AVI, WebM |

### Platform Settings (via REST API)

```json
{
  "platformSettings": {
    "youtube": {
      "privacy": "public",
      "title": "My Video Title"
    }
  }
}
```

| Setting | Values | Default |
|---------|--------|---------|
| `privacy` | `"public"`, `"unlisted"`, `"private"` | `"public"` |
| `title` | string | Derived from first 70 chars of content |

Note: `platformSettings` is accepted by the MCP `create_post` and `update_post` tools as well as over REST. The schema is **strict**: a mistyped platform or key is rejected with a validation error rather than silently dropped.

### YouTube Examples

```
Upload this tutorial video to YouTube:
"How to Build a REST API in 10 Minutes - Complete guide for beginners"
```

```
Upload this as an unlisted video (for internal sharing):
"Internal demo - Q1 dashboard features"
```

### YouTube Restrictions

1. **Video required**: YouTube does not support text-only or image posts
2. **Single video only**: One video per post
3. **Processing time**: Videos take seconds to minutes to process after upload
4. **Token refresh**: YouTube tokens expire after ~6 months, reconnect if needed

---

## Facebook

**Pages only** - posts go to Facebook Pages, not personal profiles.

### Platform Limits

| Feature | Limit |
|---------|-------|
| Post text | 2,200 characters (frontend) / 63,206 (API) |
| Images | Up to 10 per post |
| Image size | 10 MB |
| Video duration | 45 minutes |
| Video size | 2 GB |

### Multi-Page Support

If you manage multiple Facebook Pages, each gets its own platform ID:
- `facebook-112233445566` (Page 1)
- `facebook-778899001122` (Page 2)

You can post to multiple pages in a single request.

### Facebook Examples

```
Post this announcement to my Facebook Page:
"We're thrilled to announce our new product launch! Visit our website to learn more."
```

```
Post this to both my Facebook Pages:
"Holiday notice: Our offices will be closed on Monday."
```

```
Share these event photos on Facebook:
"Highlights from our company retreat! Great team, great memories."
```

### Facebook Restrictions

1. **Pages only**: Cannot post to personal profiles via API
2. **WebP auto-converted**: WebP images become JPEG automatically
3. **59-day token**: Tokens auto-refresh, but may need reconnection if it fails
4. **No mixed media**: A post can have images OR video, not both

---

## Mastodon

**Fediverse platform** - posts federate across the decentralized network.

### Platform Limits

| Feature | Limit |
|---------|-------|
| Post text | 500 characters |
| Images | Up to 4 per post |
| Image size | 16 MB |
| Video size | ~99 MB |
| Image formats | JPEG, PNG, GIF, WebP |
| Video formats | MP4, WebM, MOV |

### Mastodon Examples

```
Post this to Mastodon:
"Hello fediverse! We just shipped a major update to our open-source project. #opensource"
```

```
Share this screenshot on Mastodon:
"New feature: dark mode is here! #ui #darkmode"
```

### Mastodon Restrictions

1. **mastodon.social only**: Currently connects only to mastodon.social instance
2. **Public visibility**: All posts are public by default
3. **No auto-threading**: Unlike X/Twitter and Threads, Mastodon doesn't split long content
4. **500-char strict**: Content over 500 characters will be rejected

---

## Available Tools (All Platforms)

### create_post
Create a new post on any platform.

**Parameters:**
- `platforms`: Array of platform IDs (e.g., `["youtube-UCxxx", "facebook-123", "mastodon-456"]`)
- `content`: Post text
- `scheduledTime`: ISO 8601 UTC datetime. **Optional**: omit it and the post is created as a draft. Send a future time to schedule. A time five or more minutes in the past is rejected with `SCHEDULED_TIME_IN_PAST`, so for immediate posting use the current time plus a minute.
- `mediaUrls`: up to 10 public **https** image or video URLs. Publora downloads them server-side and attaches them *before* validation, so media and scheduling happen in one call. This is the one-shot alternative to the draft then `get_upload_url` then `complete_media` flow. Ingestion is rate-limited to 60 URLs per hour.

### get_upload_url
Get presigned URL for media uploads.

**Parameters:**
- `postGroupId`: Post ID to attach media to
- `fileName`: File name
- `contentType`: MIME type
- `type`: `"image"` or `"video"`

### complete_media
Finalize a file uploaded through `get_upload_url`, after the presigned `PUT` succeeds. Optional, because scheduling also finalizes pending media, but calling it early surfaces format and probe errors before publish. Not needed for media attached with `mediaUrls`.

**Parameters:**
- `mediaId`: the id returned by `get_upload_url`

### list_connections
List your connected accounts with their platform IDs. Call this first and copy the IDs verbatim; they are never guessable.

### list_posts / get_post / update_post / delete_post
Manage scheduled and draft posts. `update_post` also patches `content` and `platforms` on a draft or scheduled post, so fixing a typo or retargeting no longer means delete and recreate. `delete_media` and `prune_media_reference` clean up uploaded files.

---

## Cross-Platform Posting

Post to multiple platforms at once:

```
Post this video to YouTube and this text to Facebook and Mastodon:
"Announcing our new feature - watch the demo!"
```

Publora handles platform-specific requirements automatically:
- YouTube gets the video with title/description
- Facebook gets the text + video
- Mastodon gets the text (500 char limit applies)

Before cross-posting or scheduling a batch, call `account_context` to check your remaining post quota and the latest date you can schedule.

---

## Troubleshooting

| Platform | Error | Solution |
|----------|-------|----------|
| YouTube | "Video required" | Attach a video file |
| YouTube | "Account disconnected" | Reconnect via dashboard |
| Facebook | "Page not found" | Verify page connection |
| Facebook | "Token expired" | Reconnect page in dashboard |
| Mastodon | "Content too long" | Shorten to under 500 chars |
| Mastodon | "Too many images" | Reduce to 4 or fewer |
| All | Rate limit errors | Wait and retry |

> The 512 MB figure that used to appear here belongs to the dashboard's `/media/process-video` multipart endpoint. API and MCP uploads are presigned and use the platform ceilings above.
