---
name: youtube-playlist
description: "Use when a YouTube playlist is involved: pasted playlist links or IDs, requests to list playlist videos, browse playlist contents, or work through a playlist for transcripts or research. Also use when the user wants all videos from a series, course, or collection. Not for creating playlists or account management."
version: "1.5.0"
user-invocable: true
compatibility: Requires internet access to reach transcriptapi.com. No additional runtimes or dependencies needed.
required_environment_variables:
  - name: TRANSCRIPT_API_KEY
    prompt: Your TranscriptAPI key (starts with sk_)
    help: Free account at https://transcriptapi.com — 100 credits, no card required. Or let the agent create one for you.
    required_for: all API requests
metadata: {"openclaw":{"emoji":"▶️","requires":{"env":["TRANSCRIPT_API_KEY"]},"primaryEnv":"TRANSCRIPT_API_KEY","homepage":"https://transcriptapi.com"},"hermes":{"tags":["youtube","playlists","video","transcripts","series"],"category":"media"}}
---

# YouTube Playlist

Browse playlists and fetch transcripts via [TranscriptAPI.com](https://transcriptapi.com).

## Setup

If `$TRANSCRIPT_API_KEY` is not set, read [references/auth-setup.md](references/auth-setup.md) and follow the instructions there to get and store the key.

## Required Headers

Every request needs two headers:

- **Authorization:** `Bearer $TRANSCRIPT_API_KEY`
- **User-Agent:** your agent's name and version if known (e.g. `HermesAgent/0.11.0`, `ClaudeCode/1.0`). Version is optional — agent name alone is fine. Do not omit this header or send a bare default — Cloudflare will return a 403 (error code 1010) and block the request.

## API Reference

Full OpenAPI spec: [transcriptapi.com/openapi.json](https://transcriptapi.com/openapi.json) — consult this for the latest parameters and schemas.

## GET /api/v2/youtube/playlist/videos — 1 credit/page

Paginated playlist video listing (100 per page). Accepts `playlist` — a YouTube playlist URL or playlist ID.

```http
# First page
GET https://transcriptapi.com/api/v2/youtube/playlist/videos?playlist=PL_PLAYLIST_ID
Authorization: Bearer $TRANSCRIPT_API_KEY
User-Agent: YourAgent/1.0

# Next pages
GET https://transcriptapi.com/api/v2/youtube/playlist/videos?continuation=TOKEN
Authorization: Bearer $TRANSCRIPT_API_KEY
User-Agent: YourAgent/1.0
```

| Param          | Required    | Validation                                           |
| -------------- | ----------- | ---------------------------------------------------- |
| `playlist`     | conditional | Playlist URL or ID (`PL`/`UU`/`LL`/`FL`/`OL` prefix) |
| `continuation` | conditional | non-empty string                                     |

Provide exactly one of `playlist` or `continuation`, not both.

**Accepted playlist ID prefixes:**

- `PL` — user-created playlists
- `UU` — channel uploads playlist
- `LL` — liked videos
- `FL` — favorites
- `OL` — other system playlists

**Response:**

```json
{
  "results": [
    {
      "videoId": "abc123xyz00",
      "title": "Playlist Video Title",
      "channelId": "UCuAXFkgsw1L7xaCfnd5JJOw",
      "channelTitle": "Channel Name",
      "channelHandle": "@handle",
      "lengthText": "10:05",
      "viewCountText": "1.5M views",
      "thumbnails": [{ "url": "...", "width": 120, "height": 90 }],
      "index": "0"
    }
  ],
  "playlist_info": {
    "title": "Best Science Talks",
    "numVideos": "47",
    "description": "Top science presentations",
    "ownerName": "TED",
    "viewCount": "5000000"
  },
  "continuation_token": "4qmFsgKlARIYVVV1...",
  "has_more": true
}
```

**Pagination flow:**

1. First request: `?playlist=PLxxx` — returns first 100 videos + `continuation_token`
2. Next request: `?continuation=TOKEN` — returns next 100 + new token
3. Repeat until `has_more: false` or `continuation_token: null`

## Workflow: Playlist → Transcripts

```http
# 1. List playlist videos
GET https://transcriptapi.com/api/v2/youtube/playlist/videos?playlist=PL_PLAYLIST_ID
Authorization: Bearer $TRANSCRIPT_API_KEY
User-Agent: YourAgent/1.0

# 2. Get transcript from a video in the playlist
GET https://transcriptapi.com/api/v2/youtube/transcript?video_url=VIDEO_ID&format=text&include_timestamp=true&send_metadata=true
Authorization: Bearer $TRANSCRIPT_API_KEY
User-Agent: YourAgent/1.0
```

## Extract playlist ID from URL

From `https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf`, the playlist ID is `PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf`. You can also pass the full URL directly to the `playlist` parameter.

## Errors

| Code     | Meaning                 | Action                                           |
| -------- | ----------------------- | ------------------------------------------------ |
| 400      | Both or neither params  | Provide exactly one of playlist or continuation  |
| 402      | No credits              | transcriptapi.com/billing                        |
| 403/1010 | Cloudflare block        | Add or fix User-Agent header                     |
| 404      | Playlist not found      | Check if playlist is public                      |
| 408      | Timeout                 | Retry once                                       |
| 422      | Invalid playlist format | Must be a valid playlist URL or ID               |

1 credit per page. Free tier: 100 credits, 300 req/min.

## Copy-paste examples

Every request in this file as a ready-to-run one-liner: [references/curl-examples.md](references/curl-examples.md)
