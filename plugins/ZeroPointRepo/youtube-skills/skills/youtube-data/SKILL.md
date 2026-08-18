---
name: youtube-data
description: "Use when structured YouTube data is needed: pasted video/channel/playlist links, transcripts for analysis, video metadata, channel upload history, search results, or playlist contents — without Google API quotas or OAuth. Triggers on YouTube URLs, creator names, topic research, or any request needing YouTube content, even if not mentioned explicitly. Not for uploads, account management, or written-source-only research."
version: "1.5.0"
user-invocable: true
compatibility: Requires internet access to reach transcriptapi.com. No additional runtimes or dependencies needed.
required_environment_variables:
  - name: TRANSCRIPT_API_KEY
    prompt: Your TranscriptAPI key (starts with sk_)
    help: Free account at https://transcriptapi.com — 100 credits, no card required. Or let the agent create one for you.
    required_for: all API requests
metadata: {"openclaw":{"emoji":"▶️","requires":{"env":["TRANSCRIPT_API_KEY"]},"primaryEnv":"TRANSCRIPT_API_KEY","homepage":"https://transcriptapi.com"},"hermes":{"tags":["youtube","transcripts","video","search","channels","playlists","data","metadata"],"category":"media"}}
---

# YouTube Data

YouTube data access via [TranscriptAPI.com](https://transcriptapi.com) — lightweight alternative to Google's YouTube Data API.

## Setup

If `$TRANSCRIPT_API_KEY` is not set, read [references/auth-setup.md](references/auth-setup.md) and follow the instructions there to get and store the key.

## Required Headers

Every request needs two headers:

- **Authorization:** `Bearer $TRANSCRIPT_API_KEY`
- **User-Agent:** your agent's name and version if known (e.g. `HermesAgent/0.11.0`, `ClaudeCode/1.0`). Version is optional — agent name alone is fine. Do not omit this header or send a bare default — Cloudflare will return a 403 (error code 1010) and block the request.

## API Reference

Full OpenAPI spec: [transcriptapi.com/openapi.json](https://transcriptapi.com/openapi.json) — consult this for the latest parameters and schemas.

## Video Data (transcript + metadata) — 1 credit

```http
GET https://transcriptapi.com/api/v2/youtube/transcript?video_url=VIDEO_URL&format=json&include_timestamp=true&send_metadata=true
Authorization: Bearer $TRANSCRIPT_API_KEY
User-Agent: YourAgent/1.0
```

**Response:**

```json
{
  "video_id": "dQw4w9WgXcQ",
  "language": "en",
  "transcript": [
    { "text": "We're no strangers to love", "start": 18.0, "duration": 3.5 }
  ],
  "metadata": {
    "title": "Rick Astley - Never Gonna Give You Up",
    "author_name": "Rick Astley",
    "author_url": "https://www.youtube.com/@RickAstley",
    "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg"
  }
}
```

## Search Data — 1 credit

```http
GET https://transcriptapi.com/api/v2/youtube/search?q=QUERY&type=video&limit=20
Authorization: Bearer $TRANSCRIPT_API_KEY
User-Agent: YourAgent/1.0
```

**Video result fields:** `videoId`, `title`, `channelId`, `channelTitle`, `channelHandle`, `channelVerified`, `lengthText`, `viewCountText`, `publishedTimeText`, `hasCaptions`, `thumbnails`

**Channel result fields** (`type=channel`): `channelId`, `title`, `handle`, `url`, `description`, `subscriberCount`, `verified`, `rssUrl`, `thumbnails`

## Channel Data

Channel endpoints accept `channel` — an `@handle`, channel URL, or `UC...` ID. No need to resolve first.

**Resolve handle to ID (free):**

```http
GET https://transcriptapi.com/api/v2/youtube/channel/resolve?input=@TED
Authorization: Bearer $TRANSCRIPT_API_KEY
User-Agent: YourAgent/1.0
```

Returns: `{"channel_id": "UCsT0YIqwnpJCM-mx7-gSA4Q", "resolved_from": "@TED"}`

**Latest 15 videos with exact stats (free):**

```http
GET https://transcriptapi.com/api/v2/youtube/channel/latest?channel=@TED
Authorization: Bearer $TRANSCRIPT_API_KEY
User-Agent: YourAgent/1.0
```

Returns: `channel` info, `results` array with `videoId`, `title`, `published` (ISO), `viewCount` (exact number), `description`, `thumbnail`

**All channel videos (paginated, 1 credit/page):**

```http
GET https://transcriptapi.com/api/v2/youtube/channel/videos?channel=@NASA
Authorization: Bearer $TRANSCRIPT_API_KEY
User-Agent: YourAgent/1.0
```

Returns 100 videos per page + `continuation_token` for pagination.

**Search within channel (1 credit):**

```http
GET https://transcriptapi.com/api/v2/youtube/channel/search?channel=@TED&q=QUERY&limit=30
Authorization: Bearer $TRANSCRIPT_API_KEY
User-Agent: YourAgent/1.0
```

## Playlist Data — 1 credit/page

Accepts `playlist` — a YouTube playlist URL or playlist ID.

```http
GET https://transcriptapi.com/api/v2/youtube/playlist/videos?playlist=PL_ID
Authorization: Bearer $TRANSCRIPT_API_KEY
User-Agent: YourAgent/1.0
```

Returns: `results` (videos), `playlist_info` (`title`, `numVideos`, `ownerName`, `viewCount`), `continuation_token`, `has_more`

## Credit Costs

| Endpoint        | Cost     | Data returned              |
| --------------- | -------- | -------------------------- |
| transcript      | 1        | Full transcript + metadata |
| search          | 1        | Video/channel details      |
| channel/resolve | **free** | Channel ID mapping         |
| channel/latest  | **free** | 15 videos + exact stats    |
| channel/videos  | 1/page   | 100 videos per page        |
| channel/search  | 1        | Videos matching query      |
| playlist/videos | 1/page   | 100 videos per page        |

## Errors

| Code     | Meaning          | Action                                         |
| -------- | ---------------- | ---------------------------------------------- |
| 401      | Bad API key      | Check key                                      |
| 402      | No credits       | transcriptapi.com/billing                      |
| 403/1010 | Cloudflare block | Add or fix User-Agent header                   |
| 404      | Not found        | Resource doesn't exist                         |
| 408      | Timeout          | Retry once                                     |
| 422      | Validation error | Check param format                             |

Free tier: 100 credits, 300 req/min.

## Copy-paste examples

Every request in this file as a ready-to-run one-liner: [references/curl-examples.md](references/curl-examples.md)
