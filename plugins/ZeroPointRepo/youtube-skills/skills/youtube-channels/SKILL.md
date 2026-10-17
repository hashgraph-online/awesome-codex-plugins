---
name: youtube-channels
description: "Use when a YouTube channel is the focus: pasted @handles or channel URLs, requests to browse a creator's uploads, see what a channel has posted recently, search within a channel, or resolve a handle to a channel ID. Also use when the user names a creator and wants to explore their content or monitor their uploads. Not for creating channels or account management."
version: "1.6.3"
user-invocable: true
compatibility: Requires internet access to reach transcriptapi.com. No additional runtimes or dependencies needed.
required_environment_variables:
  - name: TRANSCRIPT_API_KEY
    prompt: Your TranscriptAPI key (starts with sk_)
    help: Free account at https://transcriptapi.com — 100 credits, no card required. Or let the agent create one for you.
    required_for: all API requests
metadata: {"openclaw":{"emoji":"▶️","requires":{"env":["TRANSCRIPT_API_KEY"]},"primaryEnv":"TRANSCRIPT_API_KEY","homepage":"https://transcriptapi.com"},"hermes":{"tags":["youtube","channels","video","uploads","creator","browsing"],"category":"media"}}
---

# YouTube Channels

YouTube channel tools via [TranscriptAPI.com](https://transcriptapi.com).

## Setup

If `$TRANSCRIPT_API_KEY` is not set, read [references/auth-setup.md](references/auth-setup.md) and follow the instructions there to get and store the key.

## Required Headers

Every request needs two headers:

- **Authorization:** `Bearer $TRANSCRIPT_API_KEY`
- **User-Agent:** your agent's name and version if known (e.g. `HermesAgent/0.11.0`, `ClaudeCode/1.0`). Version is optional — agent name alone is fine. Do not omit this header or send a bare default — Cloudflare will return a 403 (error code 1010) and block the request.

## API Reference

Full OpenAPI spec: [transcriptapi.com/openapi.json](https://transcriptapi.com/openapi.json) — consult this for the latest parameters and schemas.

All channel endpoints accept flexible input — `@handle`, channel URL, or `UC...` channel ID. No need to resolve first.

## GET /api/v2/youtube/channel/resolve — FREE

Convert @handle, URL, or UC... ID to canonical channel ID.

```http
GET https://transcriptapi.com/api/v2/youtube/channel/resolve?input=@TED
Authorization: Bearer $TRANSCRIPT_API_KEY
User-Agent: YourAgent/1.0
```

| Param   | Required | Validation                              |
| ------- | -------- | --------------------------------------- |
| `input` | yes      | 1-200 chars — @handle, URL, or UC... ID |

**Response:**

```json
{ "channel_id": "UCsT0YIqwnpJCM-mx7-gSA4Q", "resolved_from": "@TED" }
```

If input is already `UC[a-zA-Z0-9_-]{22}`, returns immediately.

## GET /api/v2/youtube/channel/latest — FREE

Latest 15 videos via RSS with exact stats.

```http
GET https://transcriptapi.com/api/v2/youtube/channel/latest?channel=@TED
Authorization: Bearer $TRANSCRIPT_API_KEY
User-Agent: YourAgent/1.0
```

| Param     | Required | Validation                                |
| --------- | -------- | ----------------------------------------- |
| `channel` | yes      | `@handle`, channel URL, or `UC...` ID     |

**Response:**

```json
{
  "channel": {
    "channelId": "UCsT0YIqwnpJCM-mx7-gSA4Q",
    "title": "TED",
    "author": "TED",
    "url": "https://www.youtube.com/channel/UCsT0YIqwnpJCM-mx7-gSA4Q",
    "published": "2006-04-17T00:00:00Z"
  },
  "results": [
    {
      "videoId": "abc123xyz00",
      "title": "Latest Video Title",
      "channelId": "UCsT0YIqwnpJCM-mx7-gSA4Q",
      "author": "TED",
      "published": "2026-01-30T16:00:00Z",
      "updated": "2026-01-31T02:00:00Z",
      "link": "https://www.youtube.com/watch?v=abc123xyz00",
      "description": "Full video description...",
      "thumbnail": { "url": "https://i1.ytimg.com/vi/.../hqdefault.jpg" },
      "viewCount": "2287630",
      "starRating": {
        "average": "4.92",
        "count": "15000",
        "min": "1",
        "max": "5"
      }
    }
  ],
  "result_count": 15
}
```

Great for monitoring channels — free and gives exact view counts + ISO timestamps.

## GET /api/v2/youtube/channel/videos — 1 credit/page

Paginated list of a channel's feed (~100 per page). Use `tab` to pick uploads (default), Shorts, or live streams, and the optional `sort` to order the Videos tab by latest, popular, or oldest.

```http
# First page
GET https://transcriptapi.com/api/v2/youtube/channel/videos?channel=@NASA&tab=videos
Authorization: Bearer $TRANSCRIPT_API_KEY
User-Agent: YourAgent/1.0

# Most-viewed first (channel Videos tab, ~30 per page)
GET https://transcriptapi.com/api/v2/youtube/channel/videos?channel=@NASA&sort=popular
Authorization: Bearer $TRANSCRIPT_API_KEY
User-Agent: YourAgent/1.0

# Next pages (repeat the same tab AND sort)
GET https://transcriptapi.com/api/v2/youtube/channel/videos?continuation=TOKEN&sort=popular
Authorization: Bearer $TRANSCRIPT_API_KEY
User-Agent: YourAgent/1.0
```

| Param          | Required    | Validation                                    |
| -------------- | ----------- | --------------------------------------------- |
| `channel`      | conditional | `@handle`, channel URL, or `UC...` ID         |
| `tab`          | no          | `videos` (default), `shorts`, or `streams`     |
| `sort`         | no          | `latest`, `popular`, or `oldest` (omit for the uploads feed) |
| `continuation` | conditional | non-empty (next pages)                        |

Provide exactly one of `channel` or `continuation`, not both. When paginating, pass the same `tab` **and** `sort` on every page.

**Sorting.** Add sort=latest, popular, or oldest to channel/videos to get a channel's videos in the order you want, for example its most-popular uploads first. A sorted page returns about 30 videos (an unsorted page returns about 100), and every page costs the same 1 credit.

When paging, send the same sort on each request.

**Per-item fields by feed:**

| Field | uploads (no `sort`) | `tab=videos` + `sort` | `tab=streams` | `tab=shorts` |
| --- | --- | --- | --- | --- |
| `lengthText` | populated | populated | populated (`LIVE` while live) | `null` |
| `publishedTimeText` | populated | populated | populated (`Streamed 2 years ago`) | `null` |
| `viewCountText` | populated | populated | populated (`null` while live) | populated |
| `channelId` / `channelTitle` / `channelHandle` / `index` | populated | `null` | `null` | `null` |
| `members_only` | always `false` | `true` on membership videos | `true` on membership streams | always `false` |

`members_only` is `true` only when YouTube badges the item "Members only". Such items carry **no `viewCountText`**, because YouTube does not publish view counts for membership content.

**Response:**

```json
{
  "results": [{
    "videoId": "abc123xyz00",
    "title": "Video Title",
    "channelId": "UCsT0YIqwnpJCM-mx7-gSA4Q",
    "channelTitle": "TED",
    "channelHandle": "@TED",
    "lengthText": "15:22",
    "viewCountText": "3.2M views",
    "publishedTimeText": "2 years ago",
    "thumbnails": [...],
    "index": "0",
    "members_only": false
  }],
  "playlist_info": {"title": "Uploads from TED", "numVideos": "5000", "ownerName": "TED"},
  "continuation_token": "4qmFsgKlARIYVVV1...",
  "has_more": true
}
```

Keep calling with `continuation` until `has_more: false`.

## GET /api/v2/youtube/channel/search — 1 credit

Search within a specific channel.

```http
GET https://transcriptapi.com/api/v2/youtube/channel/search?channel=@TED&q=climate+change&limit=30
Authorization: Bearer $TRANSCRIPT_API_KEY
User-Agent: YourAgent/1.0
```

| Param     | Required | Validation                                |
| --------- | -------- | ----------------------------------------- |
| `channel` | yes      | `@handle`, channel URL, or `UC...` ID     |
| `q`       | yes      | 1-200 chars                               |
| `limit`   | no       | 1-50 (default 30)                         |

## GET /api/v2/youtube/channel/info — 1 credit

A channel's profile: title, handle, verified flag, subscriber/video counts, description, tags, thumbnails, banners, and the tabs it exposes.

```http
GET https://transcriptapi.com/api/v2/youtube/channel/info?channel=@TED
Authorization: Bearer $TRANSCRIPT_API_KEY
User-Agent: YourAgent/1.0
```

| Param     | Required | Validation                            |
| --------- | -------- | -------------------------------------- |
| `channel` | yes      | `@handle`, channel URL, or `UC...` ID |

**Response:**

```json
{
  "channelId": "UCAuUUnT6oDeKwE6v1NGQxug",
  "title": "TED",
  "handle": "@TED",
  "verified": true,
  "subscriberCountText": "23.8M subscribers",
  "videoCountText": "4,300 videos",
  "description": "The TED Talks channel features ...",
  "tags": ["TED", "TED Talks"],
  "thumbnails": [...],
  "banners": [...],
  "availableTabs": ["videos", "shorts", "playlists", "community"]
}
```

Counts are display strings and `null` when YouTube hides them — never `0`. Check `availableTabs` before calling `channel/sections` or `channel/videos` with a `tab`.

## GET /api/v2/youtube/channel/playlists — 1 credit/page

List the playlists shown on a channel — useful for finding a playlist ID to feed into `playlist/videos`.

```http
GET https://transcriptapi.com/api/v2/youtube/channel/playlists?channel=@TED
Authorization: Bearer $TRANSCRIPT_API_KEY
User-Agent: YourAgent/1.0
```

| Param          | Required    | Validation                             |
| -------------- | ----------- | --------------------------------------- |
| `channel`      | conditional | `@handle`, channel URL, or `UC...` ID  |
| `continuation` | conditional | non-empty (next pages)                 |

Provide exactly one of `channel` or `continuation`, not both. Returns `results` (`playlistId`, `title`, `url`, `videoCountText`, `thumbnails`), `continuation_token`, `has_more`.

## GET /api/v2/youtube/channel/posts — 1 credit/page

List a channel's community (Posts tab) content — text, publish time, like counts, and any attachment (image, video, playlist, or poll).

```http
GET https://transcriptapi.com/api/v2/youtube/channel/posts?channel=@TED
Authorization: Bearer $TRANSCRIPT_API_KEY
User-Agent: YourAgent/1.0
```

| Param          | Required    | Validation                             |
| -------------- | ----------- | --------------------------------------- |
| `channel`      | conditional | `@handle`, channel URL, or `UC...` ID  |
| `continuation` | conditional | non-empty (next pages)                 |

Provide exactly one of `channel` or `continuation`, not both. Channels with no community tab return an empty `results` list (not an error).

## GET /api/v2/youtube/channel/sections — 1 credit

The curated shelves on a channel's Home page (or its `podcasts`/`releases` pages) — each shelf holds videos, playlists, shorts, or featured channels, in the channel's own order. Not paginated.

```http
GET https://transcriptapi.com/api/v2/youtube/channel/sections?channel=@TED
Authorization: Bearer $TRANSCRIPT_API_KEY
User-Agent: YourAgent/1.0
```

| Param     | Required | Default      | Validation                              |
| --------- | -------- | ------------ | ---------------------------------------- |
| `channel` | yes      | —            | `@handle`, channel URL, or `UC...` ID   |
| `tab`     | no       | `featured`   | `featured` (Home), `podcasts`, `releases` |

`podcasts` and `releases` only exist on channels that have them (empty `results` otherwise — check `availableTabs` from `channel/info` first).

## Typical workflow

```http
# 1. Check latest uploads (free — pass @handle directly)
GET https://transcriptapi.com/api/v2/youtube/channel/latest?channel=@TED
Authorization: Bearer $TRANSCRIPT_API_KEY
User-Agent: YourAgent/1.0

# 2. Get transcript of recent video
GET https://transcriptapi.com/api/v2/youtube/transcript?video_url=VIDEO_ID&format=text&include_timestamp=true&send_metadata=true
Authorization: Bearer $TRANSCRIPT_API_KEY
User-Agent: YourAgent/1.0
```

## Errors

| Code     | Meaning                                                | Action                               |
| -------- | ------------------------------------------------------ | ------------------------------------ |
| 400      | Invalid param combination                              | Both or neither channel/continuation |
| 402      | No credits                                             | transcriptapi.com/billing            |
| 403/1010 | Cloudflare block                                       | Add or fix User-Agent header         |
| 404      | Channel not found                                      | Check handle or URL                  |
| 408      | Timeout                                                | Retry once                           |
| 422      | Invalid channel identifier                             | Check param format                   |

Free tier: 100 credits, 300 req/min. Free endpoints (resolve, latest) require auth but don't consume credits.

## Copy-paste examples

Every request in this file as a ready-to-run one-liner: [references/curl-examples.md](references/curl-examples.md)
