---
name: threads-post
description: Create and schedule Threads posts, multi-part chains, image carousels and reply control via Publora MCP. Use when the user wants to post to Meta's Threads, including long content that Publora splits into a connected chain of replies past 500 characters. Not for Instagram (use instagram-post) or X threads (use x-post).
---

# Threads Post

Create and schedule posts on Meta's Threads using the Publora MCP server. Supports single posts, multi-part chains (connected replies), image carousels (2-20 images) and reply control.

## Prerequisites

**Plans:** Works on the free Starter plan. Current limits and pricing: [publora.com/pricing](https://publora.com/pricing).

### Getting Started

1. **Create account** at [publora.com/register](https://publora.com/register) (free)
2. **Connect Threads** via Instagram OAuth in [Publora Dashboard](https://app.publora.com/dashboard)
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
    "platforms": ["threads-12345"],
    "content": "Your post content",
    "scheduledTime": "2026-03-25T10:00:00Z"
  }'
```

**Platform ID Format:** `threads-{id}` (from `/platform-connections`)

📖 **Docs:** [docs.publora.com](https://docs.publora.com)

## Platform Limits

| Feature | Limit |
|---------|-------|
| Characters per post | 500 (per part in a chain) |
| Hashtags | 1 per post maximum |
| Links | 5 per post maximum |
| Images per carousel | 2-20 |
| Image size | 8 MB |
| Image formats | JPEG, PNG (WebP auto-converted) |
| Video duration | 5 minutes |
| Video size | 1 GB |
| Video formats | MP4, MOV |
| Posts per day | 250 |
| Replies per day | 1,000 |

## Available Tools

### create_post
Create a new Threads post or thread.

**Parameters:**
- `platforms`: Array with your Threads connection ID (e.g., `["threads-12345"]`)
- `content`: Post text (auto-threads if over 500 chars)
- `scheduledTime`: ISO 8601 UTC datetime. **Optional**: omit it and the post is created as a draft. Send a future time to schedule. A time five or more minutes in the past is rejected with `SCHEDULED_TIME_IN_PAST`, so for immediate posting use the current time plus a minute.
- `mediaUrls`: up to 10 public **https** image or video URLs. Publora downloads them server-side and attaches them *before* validation, so media and scheduling happen in one call. This is the one-shot alternative to the draft then `get_upload_url` then `complete_media` flow. Ingestion is rate-limited to 60 URLs per hour.

### get_upload_url
Get a presigned URL to upload images.

### complete_media
Finalize a file uploaded through `get_upload_url`, after the presigned `PUT` succeeds. Optional, because scheduling also finalizes pending media, but calling it early surfaces format and probe errors before publish. Not needed for media attached with `mediaUrls`.

**Parameters:**
- `mediaId`: the id returned by `get_upload_url`

### list_connections
List your connected accounts with their platform IDs. Call this first and copy the IDs verbatim; they are never guessable.

### list_posts / get_post / update_post / delete_post
Manage scheduled and draft posts. `update_post` also patches `content` and `platforms` on a draft or scheduled post, so fixing a typo or retargeting no longer means delete and recreate. `delete_media` and `prune_media_reference` clean up uploaded files.

## Multi-Part Chains

Put the whole text in one `content` field. Publora publishes it as a chain of connected replies, each part a reply to the previous one.

- **Automatic split:** content over 500 characters is split into a chain instead of being rejected. Splits prefer paragraph breaks, then line breaks, then sentence endings, then word boundaries. Automatically split parts get a ` (1/3)`-style suffix, and 10 of each part's 500 characters are reserved for it, so roughly 490 characters of your text land in each part. Emoji count as 2.
- **Your own breaks:** a line containing only `---` (with a newline before and after) sets a break. A complete set of `[1/3]`, `[2/3]`, `[3/3]` markers works too. Parts you separate yourself are published exactly as written, with no numbering added. An oversized `---` part is re-split automatically; an oversized `[n/m]` part is rejected with `THREAD_PART_TOO_LONG`.
- **Media:** attached to the first part only; later parts are text-only.
- **Permission:** a chain needs `threads_manage_replies` on the connection. Without it the post is rejected with `THREADS_PERMISSION_REQUIRED` **before any part is published**; reconnect the account in Publora Channels and approve every permission. Single posts and carousels don't need it.
- **Checking the result:** `get_post` returns `isThread: true` and one `threadParts[]` entry per part (`index`, `content`, `status`, `publishedId`). If a chain fails part-way (`THREAD_PARTIALLY_PUBLISHED`) or the outcome is unknown, the published parts are live: publish only the missing parts, never recreate the whole chain.

There is no `parts` array and no numbering or threading switch in MCP or REST: `content` is the only input.

## Reply Control

Control who can reply to your posts via REST API `platformSettings`:

| Value | Description |
|-------|-------------|
| `""` (empty) | Default platform behavior (anyone can reply) |
| `"everyone"` | Explicitly allow anyone to reply |
| `"accounts_you_follow"` | Only accounts you follow can reply |
| `"mentioned_only"` | Only mentioned accounts can reply |

Note: `platformSettings` is accepted by the MCP `create_post` and `update_post` tools as well as over REST. The schema is **strict**: a mistyped platform or key is rejected with a validation error rather than silently dropped.

## Important Restrictions

1. **Single hashtag limit**: Threads allows maximum 1 hashtag per post. Additional hashtags are ignored by the platform.

2. **No post editing**: Once posted, Threads posts cannot be edited via API. Delete and repost if needed.

3. **Video carousels not supported**: Publora's carousel implementation supports images only. Standalone video posts work normally.

4. **Chains need `threads_manage_replies`**: connections made before that permission was granted must be reconnected before a multi-part chain can publish. Single posts and carousels are unaffected.

## Examples

### Simple Text Post
```
Post this to Threads:
"Just discovered an amazing productivity hack that saved me 2 hours today. The key is batching similar tasks together."
```

### Image Carousel
```
Create a Threads carousel with these 5 product evolution screenshots.
Caption: "From concept to launch - our 6-month journey. #buildinpublic"
```
Note: Requires 2-20 images. Videos in carousels are not supported.

### Multi-Part Chain

Each `---`-separated block becomes its own reply in the chain, published as written with no numbering added:

```
Post this to Threads as a thread:
"Thread: 7 mistakes I made as a first-time founder

---

1. Hiring too fast. We went from 2 to 15 in 3 months. The culture suffered.

---

2. Ignoring unit economics. Revenue felt great until we calculated CAC..."
```

### Scheduled Post
```
Schedule this for tomorrow at 10 AM:
"Monday motivation: The best time to start was yesterday. The second best time is now."
```

## Best Practices

1. **Hook first**: First 2 lines determine engagement - make them count
2. **Optimal length**: 100-250 characters for single posts perform well
3. **Native content**: Original, conversational posts are rewarded
4. **Single hashtag**: Use one highly relevant hashtag (platform limit)
5. **No edit option**: Double-check content before posting

### Timing
- **Best times**: 7-9 AM, 12-1 PM, 7-9 PM in target timezone
- **Frequency**: 1-3 posts per day for growth
- **Consistency**: Regular posting signals active account

### Engagement
- Reply to comments within first hour
- Cross-reference your Instagram (accounts are linked)
- Use relevant topics/keywords for discovery

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| "Account not connected" | Threads/Instagram OAuth expired | Reconnect via Publora dashboard |
| `THREADS_PERMISSION_REQUIRED` | Chain needs `threads_manage_replies` | Reconnect Threads in Publora Channels and approve all permissions |
| `THREAD_PART_TOO_LONG` | A `[n/m]` part exceeds 500 chars | Shorten that part or use `---` breaks, which re-split automatically |
| `THREAD_PARTIALLY_PUBLISHED` | A part failed after earlier parts published | Read `threadParts` in `get_post`, publish only the missing parts |
| "Media upload failed" | Wrong format or size | Check: images < 8 MB, JPEG/PNG only |
| "Carousel requires 2-20 items" | Wrong number of images | Ensure 2-20 images for carousel |
| 250 posts/day exceeded | Rate limit reached | Wait 24 hours |
