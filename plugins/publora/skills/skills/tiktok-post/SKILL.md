---
name: tiktok-post
description: Use when the user wants to upload or schedule a TikTok video through Publora, with privacy, comment, duet, stitch and commercial-disclosure settings. Video runs 3 seconds to 10 minutes at 23+ FPS; carousels take up to 35 images. Unaudited apps can publish private videos only. Not for Reels (use instagram-post).
---

# TikTok Post

Upload and schedule videos to TikTok using the Publora MCP server. Supports privacy controls, interaction settings (comments, duet, stitch), and commercial content disclosure.

## Prerequisites

**Plans:** Works on the free Starter plan. Current limits and pricing: [publora.com/pricing](https://publora.com/pricing).

### Getting Started

1. **Create account** at [publora.com/register](https://publora.com/register) (free)
2. **Connect TikTok** via OAuth in [Publora Dashboard](https://app.publora.com/dashboard)
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
    "platforms": ["tiktok-99887766"],
    "content": "Video caption here #hashtag",
    "scheduledTime": "2026-03-25T10:00:00Z",
    "platformSettings": {
      "tiktok": {
        "viewerSetting": "PUBLIC_TO_EVERYONE",
        "allowComments": true
      }
    }
  }'
```

**Platform ID Format:** `tiktok-{id}` where `{id}` is from `/platform-connections` response.

Example IDs: `tiktok-99887766`, `tiktok-123456789`

📖 **Full API documentation:** [docs.publora.com](https://docs.publora.com)

## Platform Limits (API vs Native App)

**Critical API limits that differ from native TikTok app:**

### Video Requirements

| Specification | API Limit | Native App |
|---------------|-----------|------------|
| **Max duration** | **10 minutes** | 60 minutes |
| Min duration | 3 seconds | 3 seconds |
| Max file size | 4 GB | 4 GB |
| Min frame rate | **23 FPS** | 23 FPS |
| Formats | MP4, MOV, WebM | MP4, MOV, WebM |

### Caption Limits

| Element | API Limit | Native App |
|---------|-----------|------------|
| Caption length | **2,200 characters** | 4,000 characters |
| Hashtags | Included in caption count | Included in caption count |

### Rate Limits

| Limit | Value |
|-------|-------|
| Posts per day | 15-20 |
| Videos per minute | Max 2 |

## Available Tools

### create_post
Create a new TikTok post.

**Parameters:**
- `platforms`: Array with your TikTok connection ID (e.g., `["tiktok-99887766"]`)
- `content`: Video caption (up to 2,200 characters)
- `scheduledTime`: ISO 8601 UTC datetime. **Optional**: omit it and the post is created as a draft. Send a future time to schedule. A time five or more minutes in the past is rejected with `SCHEDULED_TIME_IN_PAST`, so for immediate posting use the current time plus a minute.
- `mediaUrls`: up to 10 public **https** image or video URLs. Publora downloads them server-side and attaches them *before* validation, so media and scheduling happen in one call. This is the one-shot alternative to the draft then `get_upload_url` then `complete_media` flow. Ingestion is rate-limited to 60 URLs per hour.

### get_upload_url
Get presigned URL for video upload.

**Parameters:**
- `postGroupId`: Post ID to attach video to
- `fileName`: Video file name (e.g., "video.mp4")
- `contentType`: `video/mp4`, `video/quicktime`, or `video/webm`
- `type`: `"video"`

### complete_media
Finalize a file uploaded through `get_upload_url`, after the presigned `PUT` succeeds. Optional, because scheduling also finalizes pending media, but calling it early surfaces format and probe errors before publish. Not needed for media attached with `mediaUrls`.

**Parameters:**
- `mediaId`: the id returned by `get_upload_url`

### list_connections
List your connected accounts with their platform IDs. Call this first and copy the IDs verbatim; they are never guessable.

### list_posts / get_post / update_post / delete_post
Manage scheduled and draft posts. `update_post` also patches `content` and `platforms` on a draft or scheduled post, so fixing a typo or retargeting no longer means delete and recreate. `delete_media` and `prune_media_reference` clean up uploaded files.

## Platform Settings (via REST API)

TikTok has 7 platform-specific settings controlled via `platformSettings`:

```json
{
  "platformSettings": {
    "tiktok": {
      "viewerSetting": "PUBLIC_TO_EVERYONE",
      "allowComments": true,
      "allowDuet": false,
      "allowStitch": false,
      "commercialContent": false,
      "brandOrganic": false,
      "brandedContent": false
    }
  }
}
```

### Viewer Settings (Required)

| Value | Description |
|-------|-------------|
| `PUBLIC_TO_EVERYONE` | Anyone can view (default) |
| `MUTUAL_FOLLOW_FRIENDS` | Only mutual followers |
| `FOLLOWER_OF_CREATOR` | Only your followers |
| `SELF_ONLY` | Only you (draft-like) |

### Interaction Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `allowComments` | `true` | Whether viewers can comment |
| `allowDuet` | `false` | Whether viewers can create Duets |
| `allowStitch` | `false` | Whether viewers can Stitch |

### Commercial Content Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `commercialContent` | `false` | Is this commercial content? |
| `brandOrganic` | `false` | Organic brand promotion |
| `brandedContent` | `false` | Paid partnership/sponsored |

**Note:** If `commercialContent` is `true`, at least one of `brandOrganic` or `brandedContent` must also be `true`.

Note: `platformSettings` is accepted by the MCP `create_post` and `update_post` tools as well as over REST. The schema is **strict**: a mistyped platform or key is rejected with a validation error rather than silently dropped.

## Critical Restrictions

### 1. Unaudited Apps = PRIVATE Only

**CRITICAL:** If your TikTok app hasn't passed TikTok's review process, you can **ONLY post PRIVATE videos** (`SELF_ONLY`). All other `viewerSetting` values will be overridden to `SELF_ONLY`.

To post public videos, your app must be audited by TikTok.

### 2. Media Required, Video or Image Carousel

TikTok does NOT support text-only posts: every post needs media.

It does take **image carousels**: up to 35 images, JPEG, PNG or WebP, 20 MB each. A post is either a carousel or a single video, never both.

### 3. Minimum 23 FPS

Videos below 23 frames per second will be rejected by TikTok.

## Examples

### Basic Video Post
```
Post this video to TikTok:
"How we built our startup in 60 seconds #startup #tech #coding"
```

### Private Draft (Testing)
```
Upload this video as a private draft to TikTok (only I can see it):
"Testing new content format"
```
Use `viewerSetting: "SELF_ONLY"` for testing before making public.

### Branded Content
```
Post this sponsored video to TikTok with proper disclosure:
"Loving this new product from @brand! #ad #sponsored"
```
Set `commercialContent: true` and `brandedContent: true` for paid partnerships.

### Scheduled Post
```
Schedule this TikTok video for tomorrow at 6 PM:
"Weekend vibes incoming! #weekend #fun"
```

## Supported Video Formats

| Format | Recommended | Notes |
|--------|-------------|-------|
| MP4 | Yes | Most reliable |
| MOV | Yes | Apple format |
| WebM | Yes | Web format |
| AVI | Accepted by Publora | May be rejected by TikTok |
| MKV | Accepted by Publora | May be rejected by TikTok |

**Recommendation:** Use MP4 for best compatibility.

## Best Practices

### Content
1. **Hook in first 3 seconds**: Grab attention immediately
2. **Optimal length**: 15-60 seconds for best engagement
3. **Trending sounds**: Use trending audio when possible
4. **Hashtag strategy**: 3-5 relevant hashtags

### Technical
1. **Vertical video**: 9:16 aspect ratio performs best
2. **High quality**: At least 720p resolution
3. **23+ FPS**: Ensure smooth playback
4. **MP4 format**: Most reliable format

### Timing
- **Best times**: 7-9 AM, 12-3 PM, 7-11 PM in target timezone
- **Frequency**: 1-3 posts per day for growth
- **Consistency**: Regular posting schedule helps algorithm

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `unaudited_client_can_only_post_to_private_accounts` | App not approved | Submit app for TikTok review or use `SELF_ONLY` |
| `spam_risk_too_many_posts` | Daily limit reached | Wait 24 hours |
| `duration_check_failed` | Video too long/short | Ensure 3 seconds to 10 minutes |
| `file_format_check_failed` | Wrong video format | Use MP4, MOV, or WebM |
| "23 FPS required" | Low frame rate | Re-encode video at 23+ FPS |
| "TikTok requires selecting who can view" | Missing viewerSetting | Always include `viewerSetting` in platformSettings |
