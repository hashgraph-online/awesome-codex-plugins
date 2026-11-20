---
name: instagram-post
description: "Use when the user wants to post or schedule to Instagram through Publora: a single image, a 2-10 image carousel, a Reel or a Story. Requires a Business account and an image or video; text-only posts are rejected by the API. Not for Threads (use threads-post)."
---

# Instagram Post

Create and schedule Instagram posts using the Publora MCP server. Supports image posts, carousels (2-10 images), Reels, and Stories. Requires an Instagram Business account.

## Prerequisites

**Plans:** Works on the free Starter plan. Current limits and pricing: [publora.com/pricing](https://publora.com/pricing).

### Getting Started

1. **Create account** at [publora.com/register](https://publora.com/register) (free)
2. **Convert to Business account** in Instagram settings (Personal and Creator accounts are NOT supported by the API)
3. **Connect Instagram** via OAuth in [Publora Dashboard](https://app.publora.com/dashboard)
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
    "platforms": ["instagram-11223344"],
    "content": "Your caption here #hashtag",
    "scheduledTime": "2026-03-25T10:00:00Z"
  }'
```

**Platform ID Format:** `instagram-{id}` where `{id}` is from `/platform-connections` response.

Example IDs: `instagram-11223344`, `instagram-55667788`

📖 **Full API documentation:** [docs.publora.com](https://docs.publora.com)

## Platform Limits (API vs Native App)

These limits are specific to the Instagram Graph API and differ from native app limits:

### Images

| Feature | API Limit |
|---------|-----------|
| **Formats** | JPEG, PNG, WebP (WebP is auto-converted). Animated GIF, BMP and TIFF are rejected. |
| Max file size | 8 MB |
| Carousel images | 2-10 (native app allows 20) |
| Aspect ratios | 4:5 (portrait) to 1.91:1 (landscape) |

### Videos

| Feature | Reels | Stories | Carousel Videos |
|---------|-------|---------|-----------------|
| Max duration | **15 minutes** (only 5-90s eligible for Reels tab) | 60 seconds | 60 seconds |
| Min duration | 3 seconds | 3 seconds | 3 seconds |
| Max file size | 300 MB | 100 MB | 300 MB |
| Formats | MP4, MOV | MP4, MOV | MP4, MOV |

### Captions

| Feature | Limit |
|---------|-------|
| Caption length | 2,200 characters |
| Visible before "more" | First 125 characters |
| Hashtags | 30 per post (included in caption) |

### Rate Limits

- **50 posts per 24 hours** (some accounts report 25)

## Available Tools

### create_post
Create a new Instagram post.

**Parameters:**
- `platforms`: Array with your Instagram connection ID (e.g., `["instagram-11223344"]`)
- `content`: Caption text (up to 2,200 characters)
- `scheduledTime`: ISO 8601 UTC datetime. **Optional**: omit it and the post is created as a draft. Send a future time to schedule. A time five or more minutes in the past is rejected with `SCHEDULED_TIME_IN_PAST`, so for immediate posting use the current time plus a minute.
- `mediaUrls`: up to 10 public **https** image or video URLs. Publora downloads them server-side and attaches them *before* validation, so media and scheduling happen in one call. This is the one-shot alternative to the draft then `get_upload_url` then `complete_media` flow. Ingestion is rate-limited to 60 URLs per hour.

### get_upload_url
Get presigned URL for media uploads.

**Parameters:**
- `postGroupId`: Post ID to attach media to
- `fileName`: File name (e.g., "photo.jpg")
- `contentType`: Must be `image/jpeg` for images, `video/mp4` for video
- `type`: `"image"` or `"video"`

### complete_media
Finalize a file uploaded through `get_upload_url`, after the presigned `PUT` succeeds. Optional, because scheduling also finalizes pending media, but calling it early surfaces format and probe errors before publish. Not needed for media attached with `mediaUrls`.

**Parameters:**
- `mediaId`: the id returned by `get_upload_url`

### list_connections
List your connected accounts with their platform IDs. Call this first and copy the IDs verbatim; they are never guessable.

### list_posts / get_post / update_post / delete_post
Manage scheduled and draft posts. `update_post` also patches `content` and `platforms` on a draft or scheduled post, so fixing a typo or retargeting no longer means delete and recreate. `delete_media` and `prune_media_reference` clean up uploaded files.

## Video Type Settings (via REST API)

Control how videos are published via `platformSettings`:

```json
{
  "platformSettings": {
    "instagram": {
      "videoType": "REELS"
    }
  }
}
```

| Setting | Values | Default | Description |
|---------|--------|---------|-------------|
| `videoType` | `"REELS"`, `"STORIES"` | `"REELS"` | Determines how videos are published |

Note: `platformSettings` is accepted by the MCP `create_post` and `update_post` tools as well as over REST. The schema is **strict**: a mistyped platform or key is rejected with a validation error rather than silently dropped.

## Examples

### Single Image Post
```
Post this to Instagram:
"Morning coffee and code. Best way to start the day. #devlife #coding"

[Attach JPEG image]
```
**Formats:** JPEG, PNG and WebP all work; WebP is converted before publishing.

### Carousel Post
```
Create an Instagram carousel with these 5 product screenshots.
Caption: "Our app evolution over 6 months. Swipe to see the journey! #buildinpublic"
```
Note: Requires 2-10 JPEG images. Cannot mix images and videos in carousels.

### Reel
```
Post this video as a Reel:
"60-second tutorial on our new feature. #tutorial #app"
```
Videos default to Reels. Set `videoType: "STORIES"` via REST API for Stories.

### Story
```
Post this 30-second clip as a Story (will disappear after 24 hours).
```
Requires `platformSettings.instagram.videoType: "STORIES"` via REST API.

### Scheduled Post
```
Schedule this for tomorrow at 10 AM:
"New feature announcement coming soon! Stay tuned."
[Attach JPEG image]
```

## Important Restrictions

1. **Animated GIF, BMP and TIFF are rejected.** JPEG, PNG and WebP are accepted, with WebP auto-converted.

2. **Business account required**: Personal and Creator accounts cannot post via API. Only Business accounts work.

3. **Media required on every post**: Instagram does not support text-only posts. Every post needs at least one image or video.

4. **No mixed media in carousels**: A carousel must be either all images OR all videos (via separate posts), not both.

5. **Stories disappear**: Stories are ephemeral and disappear after 24 hours.

6. **Reel is the default**: Videos are published as Reels by default. To post a Story, use the REST API with `videoType: "STORIES"`.

## Best Practices

### Content
1. **First 125 chars matter**: This is what users see before tapping "more"
2. **Hashtag strategy**: Use 5-15 relevant hashtags (max 30)
3. **Image quality**: Use high-quality JPEG images for best results
4. **Carousel engagement**: Carousels get higher engagement than single images

### Timing
- **Best times**: 11 AM - 1 PM, 7 PM - 9 PM in target timezone
- **Frequency**: 1-2 posts per day for growth
- **Reels boost**: Reels get algorithmic preference over static images

### Engagement
- Reply to comments within the first hour
- Use location tags when relevant
- Cross-promote from Stories to Feed

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| "Business account required" | Using Personal/Creator account | Convert to Business account in Instagram settings |
| "Invalid image format" | PNG or other non-JPEG format | Convert image to JPEG before uploading |
| "Media upload failed" | File too large or wrong format | Check: images < 8 MB JPEG, videos < 300 MB MP4 |
| "Carousel requires 2-10 items" | Wrong number of images | Ensure 2-10 images for carousel |
| "Account not connected" | OAuth expired | Reconnect via Publora dashboard |
| Rate limit (429) | Exceeded 50 posts/day | Wait 24 hours |
