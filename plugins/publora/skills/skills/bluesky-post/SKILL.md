---
name: bluesky-post
description: Use when the user wants to post or schedule to Bluesky through Publora. Handles the 300-character cap, auto-detected hashtags and links, up to 4 images, and videos. Alt text cannot be set through the API. Needs a Bluesky app password, never the main password. Not for Mastodon (use social-post).
---

# Bluesky Post

Create and schedule posts to Bluesky using the Publora MCP server. Supports text posts with auto-detected hashtags and URLs, images and videos.

## Prerequisites

**Plans:** Works on the free Starter plan. Current limits and pricing: [publora.com/pricing](https://publora.com/pricing).

### Getting Started

1. **Create account** at [publora.com/register](https://publora.com/register) (free)
2. **Generate app password** in Bluesky Settings > App Passwords (NOT your main password)
3. **Connect Bluesky** in [Publora Dashboard](https://app.publora.com/dashboard) using your handle + app password
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
    "platforms": ["bluesky-did:plc:abc123xyz"],
    "content": "Your post content here",
    "scheduledTime": "2026-03-25T10:00:00Z"
  }'
```

**Platform ID Format:** `bluesky-{did}` where `{did}` is from `/platform-connections` response.

Example IDs: `bluesky-did:plc:abc123xyz`, `bluesky-did:plc:def456uvw`

📖 **Full API documentation:** [docs.publora.com](https://docs.publora.com)

## Platform Limits

| Feature | Limit |
|---------|-------|
| Characters | 300 |
| Images | Up to 4 per post |
| Image size | exactly 2,000,000 bytes (decimal, not 2 MiB) |
| Video duration | 3 minutes |
| Video size | 50-100 MB (based on duration) |
| Videos per day | 25 |
| Alt text | 2,000 characters on Bluesky itself, but **not settable through this API** (see below) |

### Video Size Tiers

| Duration | Max Size |
|----------|----------|
| Under 60s | 50 MB |
| 60s - 3min | 100 MB |

## Rich Text Facets

Bluesky uses a unique rich text system. Publora handles the complexity automatically:

- **Hashtags**: `#hashtag` auto-detected and made clickable
- **URLs**: Any URL auto-detected and made clickable
- **Byte offsets**: Calculated correctly for multi-byte characters (emojis, CJK)

No special formatting needed - just write naturally.

## Available Tools

### create_post
Create a new Bluesky post.

**Parameters:**
- `platforms`: Array with your Bluesky connection ID (e.g., `["bluesky-did:plc:abc123xyz"]`)
- `content`: Post text (up to 300 characters)
- `scheduledTime`: ISO 8601 UTC datetime. **Optional**: omit it and the post is created as a draft. Send a future time to schedule. A time five or more minutes in the past is rejected with `SCHEDULED_TIME_IN_PAST`, so for immediate posting use the current time plus a minute.
- `mediaUrls`: up to 10 public **https** image or video URLs. Publora downloads them server-side and attaches them *before* validation, so media and scheduling happen in one call. This is the one-shot alternative to the draft then `get_upload_url` then `complete_media` flow. Ingestion is rate-limited to 60 URLs per hour.

### get_upload_url
Get presigned URL for media uploads.

**Parameters:**
- `postGroupId`: Post ID to attach media to
- `fileName`: File name (e.g., "photo.jpg")
- `contentType`: `image/jpeg`, `image/png`, `video/mp4`
- `type`: `"image"` or `"video"`

### complete_media
Finalize a file uploaded through `get_upload_url`, after the presigned `PUT` succeeds. Optional, because scheduling also finalizes pending media, but calling it early surfaces format and probe errors before publish. Not needed for media attached with `mediaUrls`.

**Parameters:**
- `mediaId`: the id returned by `get_upload_url`

### list_connections
List your connected accounts with their platform IDs. Call this first and copy the IDs verbatim; they are never guessable.

### post_stats
Engagement counters for a published Bluesky post: reactions, comments, reposts, quotes and bookmarks. Live at request time, cached for roughly two hours.

**Parameters:**
- `platform`: `bluesky`
- `platformId`: your Bluesky connection ID
- `postedIds`: the published post ids to look up

### profile_stats
Followers, following and post count for the connected account.

**Parameters:**
- `platform`: `bluesky`
- `platformId`: your Bluesky connection ID

### list_posts / get_post / update_post / delete_post
Manage scheduled and draft posts. `update_post` also patches `content` and `platforms` on a draft or scheduled post, so fixing a typo or retargeting no longer means delete and recreate. `delete_media` and `prune_media_reference` clean up uploaded files.

## Examples

### Simple Post with Hashtags
```
Post this to Bluesky:
"Just launched our new API documentation! Check it out at https://docs.example.com #devtools #api"
```
Hashtags and URLs are automatically made clickable.

### Post with Image
```
Post this to Bluesky with a dashboard screenshot:
"Our new analytics view is live! #buildinpublic"
```

### Multiple Images
```
Create a Bluesky post with before/after comparison images:
"Office renovation complete! What a transformation."
```
Note: Up to 4 images allowed per post.

### Video Post
```
Post this 60-second demo video to Bluesky:
"Quick tour of our new mobile app features"
```

### Scheduled Post
```
Schedule this for tomorrow at 10 AM:
"Good morning! Here's your daily productivity tip..."
```

## Important Restrictions

0. **Alt text cannot be set through the API.** The Bluesky publisher reads an `alt`
   property on media, but nothing persists it: neither the presigned upload flow nor
   `mediaUrls` stores it, and an `altTexts` value sent to `create-post` is silently
   ignored. `platformSettings` is no help either, since Bluesky is rejected there with
   `400 PLATFORM_SETTING_UNKNOWN`. Post the image, then add alt text in the Bluesky app.
   Do not tell the user their alt text was published.


1. **App password required**: You must use a Bluesky app password, NOT your main account password. Generate one at Settings > App Passwords.

2. **All images converted to JPEG**: Regardless of input format (PNG, WebP, GIF), all images are converted to JPEG before upload.

3. **Hard 2,000,000-byte image limit**: the AT Protocol enforces an exact decimal byte ceiling, not a rounded 2 MiB. Compress to 80-85% JPEG quality and check the byte count.

4. **DID-based platform ID**: Unlike other platforms using numeric IDs, Bluesky uses `did:plc:xxx` format.

5. **Email verification for video**: You must verify your email in Bluesky before uploading videos.

6. **25 video daily limit**: Maximum 25 videos OR 10 GB per day.

## Best Practices

### Content
1. **Concise posts**: 300 chars is shorter than Twitter - be punchy
2. **Natural hashtags**: 1-2 relevant hashtags work well
3. **Alt text**: worth adding, but you have to do it in the Bluesky app after posting; the API cannot carry it
4. **URLs work**: Links are clickable (unlike some platforms)

### Timing
- **Growing platform**: Less crowded than X, easier to get noticed
- **Tech-savvy audience**: Developer and early-adopter heavy
- **Frequency**: 1-3 posts per day

### Engagement
- Bluesky favors authentic conversation
- Reply to comments to build community
- Follow relevant users to grow network

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| "Invalid credentials" | Wrong password type | Use app password, not main password |
| "Image too large" | Over 2,000,000 bytes | Compress to 80-85% JPEG quality |
| "Content too long" | Over 300 chars | Shorten content (no auto-threading) |
| "Video daily limit" | 25 videos reached | Wait 24 hours |
| "Email not verified" | Trying to upload video | Verify email in Bluesky settings |
