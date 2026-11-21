---
name: linkedin-post
description: "Use when the user wants to publish or schedule a LinkedIn post through Publora: text, a multi-image grid, a video, a PDF document, or @mentions. Not for analytics, reactions, comments or reshares (use linkedin-analytics), and not for other platforms."
---

# LinkedIn Post

Create and schedule LinkedIn posts using the Publora MCP server. Supports text posts, single images, multi-image posts (grid layout), videos, and PDF documents.

## Prerequisites

**Plans:** Works on the free Starter plan. Current limits and pricing: [publora.com/pricing](https://publora.com/pricing).

### Getting Started

1. **Create account** at [publora.com/register](https://publora.com/register) (free)
2. **Connect LinkedIn** via OAuth in [Publora Dashboard](https://app.publora.com/dashboard)
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
    "platforms": ["linkedin-Tz9W5i6ZYG"],
    "content": "Your post content here",
    "scheduledTime": "2026-03-25T10:00:00Z"
  }'
```

**Platform ID Format:** `linkedin-{id}` where `{id}` is from `/platform-connections` response.

Example IDs: `linkedin-Tz9W5i6ZYG`, `linkedin-abc123xyz`

📖 **Full API documentation:** [docs.publora.com](https://docs.publora.com)

## Platform Limits

| Feature | Limit |
|---------|-------|
| Characters | 3,000 max |
| Visible before "see more" | First 210 characters |
| Images | Up to 10 (grid layout, not swipeable carousel) |
| Image size | 36,152,320 pixels is the primary gate; 50 MB ceiling |
| Image formats | JPEG, PNG, GIF, WebP (WebP auto-converted) |
| Video duration | 30 minutes |
| Video size | 500 MB max |
| Video format | MP4 only |

## Available Tools

### create_post
Create a new LinkedIn post or schedule for later.

**Parameters:**
- `platforms`: Array including your LinkedIn connection ID (e.g., `["linkedin-abc123"]`)
- `content`: Post text (up to 3,000 characters)
- `scheduledTime`: ISO 8601 UTC datetime. **Optional**: omit it and the post is created as a draft. Send a future time to schedule. A time five or more minutes in the past is rejected with `SCHEDULED_TIME_IN_PAST`, so for immediate posting use the current time plus a minute.
- `mediaUrls`: up to 10 public **https** image or video URLs. Publora downloads them server-side and attaches them *before* validation, so media and scheduling happen in one call. This is the one-shot alternative to the draft then `get_upload_url` then `complete_media` flow. Ingestion is rate-limited to 60 URLs per hour.

### get_upload_url
Get a presigned URL to upload media.

**Parameters:**
- `postGroupId`: The post ID to attach media to
- `fileName`: File name (e.g., "chart.png")
- `contentType`: MIME type (e.g., "image/jpeg", "video/mp4", "application/pdf")
- `type`: "image" or "video"

### complete_media
Finalize a file uploaded through `get_upload_url`, after the presigned `PUT` succeeds. Optional, because scheduling also finalizes pending media, but calling it early surfaces format and probe errors before publish. Not needed for media attached with `mediaUrls`.

**Parameters:**
- `mediaId`: the id returned by `get_upload_url`

### list_connections
List your connected accounts with their platform IDs. Call this first and copy the IDs verbatim; they are never guessable.

### list_posts / get_post / update_post / delete_post
Manage scheduled and draft posts. `update_post` also patches `content` and `platforms` on a draft or scheduled post, so fixing a typo or retargeting no longer means delete and recreate. `delete_media` and `prune_media_reference` clean up uploaded files.

## Mentioning People and Companies

LinkedIn posts support @mentions using URN syntax:

```
@{urn:li:person:MEMBER_ID|Display Name}       # Mention a person
@{urn:li:organization:ORG_ID|Company Name}    # Mention a company
```

**Example:**
```
Great insights from @{urn:li:person:4986615|Serge Bulaev} at @{urn:li:organization:107107343|Creative Content Crafts Inc}!
```

**Important:** The display name must exactly match the LinkedIn profile name (case-sensitive), including company suffixes like "Inc", "LLC", etc.

**Do not hand-write member ids.** The `linkedin_list_mentionables` MCP tool resolves a name to the correct URN; see the `linkedin-analytics` skill.

## Important API Restrictions

1. **No organic carousels**: Swipeable multi-image carousels are NOT available via API (only for sponsored content). Multi-image posts appear as a grid layout.

2. **No mixed media**: Cannot combine images with videos or documents in the same post.

3. **No rich text**: LinkedIn API does not support bold, italic, or other formatting. Use plain text or Unicode characters for emphasis.

4. **PDF alternative for carousels**: To share multi-page swipeable content, upload a PDF document instead.

## Examples

### Simple Text Post
```
Schedule a LinkedIn post for tomorrow at 9 AM:
"We're thrilled to announce the release of our AI writing assistant. After 18 months of development, we're ready to help teams write better content faster."
```

### Post with Mention
```
Create a LinkedIn post mentioning our CEO:
"Excited to share insights from @{urn:li:person:4986615|Serge Bulaev} on the future of AI in content creation."
```

### Multi-Image Post
```
Create a LinkedIn post with 4 product screenshots showing our new dashboard features.
```
Note: Images will appear in a grid layout, not as a swipeable carousel.

### PDF Document Post
```
Share our Q4 report as a PDF on LinkedIn with a summary caption.
```
This is the best way to share multi-page carousel-like content.

## Best Practices

1. **First line matters**: First 210 characters appear before "see more" - make them compelling
2. **Optimal length**: Posts under 1,300 characters tend to perform better
3. **Posting times**: Tuesday-Thursday, 8-10 AM in your audience's timezone
4. **Hashtags**: Use 3-5 relevant hashtags - they're supported as plain text
5. **Engagement**: End with a question to encourage comments

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| "Account not connected" | LinkedIn OAuth expired | Reconnect in Publora dashboard |
| "MEDIA_ASSET_PROCESSING_FAILED" | File too large or wrong format | Check: images < 5 MB, videos < 500 MB MP4 |
| "Rate limited" (429) | Too many API calls | Wait and retry with backoff |
| "Cannot mix media types" | Images + video in same post | Use only one media type per post |
| MCP unavailable | Server issue | Use REST API fallback (see above) |
