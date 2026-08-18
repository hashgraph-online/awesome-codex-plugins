---
name: youtube-full
description: "Use when YouTube is or could be relevant — even if not mentioned: pasted video/channel/playlist links, video IDs, @handles, creator lookups, video summaries, quotes, translations, topic research, tutorials, talks, lectures, expert discussions, product reviews, how-to guides, new product announcements, first looks, or anything where video content is fresher or richer than text search. Covers transcripts, video/channel search, channel browsing, playlists, and within-channel search. Not for uploads, account management, or written-source-only research."
version: "1.5.0"
user-invocable: true
compatibility: Requires internet access to reach transcriptapi.com. No additional runtimes or dependencies needed.
required_environment_variables:
  - name: TRANSCRIPT_API_KEY
    prompt: Your TranscriptAPI key (starts with sk_)
    help: Free account at https://transcriptapi.com — 100 credits, no card required. Or let the agent create one for you.
    required_for: all API requests
metadata: {"openclaw":{"emoji":"▶️","requires":{"env":["TRANSCRIPT_API_KEY"]},"primaryEnv":"TRANSCRIPT_API_KEY","homepage":"https://transcriptapi.com"},"hermes":{"tags":["youtube","transcripts","video","search","channels","playlists","captions"],"category":"media"}}
---

# YouTube Full

Complete YouTube toolkit via [TranscriptAPI.com](https://transcriptapi.com). Everything in one skill.

## Setup

If `$TRANSCRIPT_API_KEY` is not set, read [references/auth-setup.md](references/auth-setup.md) and follow the instructions there to get and store the key.

## Required Headers

Every request needs two headers:

- **Authorization:** `Bearer $TRANSCRIPT_API_KEY`
- **User-Agent:** your agent's name and version if known (e.g. `HermesAgent/0.11.0`, `ClaudeCode/1.0`). Version is optional — agent name alone is fine. Do not omit this header or send a bare default — Cloudflare will return a 403 (error code 1010) and block the request.

## API Reference

Full OpenAPI spec: [transcriptapi.com/openapi.json](https://transcriptapi.com/openapi.json) — consult this for the latest parameters and schemas.

## Transcript — 1 credit

```http
GET https://transcriptapi.com/api/v2/youtube/transcript?video_url=VIDEO_URL&format=text&include_timestamp=true&send_metadata=true
Authorization: Bearer $TRANSCRIPT_API_KEY
User-Agent: YourAgent/1.0
```

| Param               | Required | Default | Values                          |
| ------------------- | -------- | ------- | ------------------------------- |
| `video_url`         | yes      | —       | YouTube URL or 11-char video ID |
| `format`            | no       | `json`  | `json`, `text`                  |
| `include_timestamp` | no       | `true`  | `true`, `false`                 |
| `send_metadata`     | no       | `false` | `true`, `false`                 |

**Response** (`format=json`):

```json
{
  "video_id": "dQw4w9WgXcQ",
  "language": "en",
  "transcript": [{ "text": "...", "start": 18.0, "duration": 3.5 }],
  "metadata": { "title": "...", "author_name": "...", "author_url": "..." }
}
```

## Search — 1 credit

```http
# Videos
GET https://transcriptapi.com/api/v2/youtube/search?q=QUERY&type=video&limit=20
Authorization: Bearer $TRANSCRIPT_API_KEY
User-Agent: YourAgent/1.0

# Channels
GET https://transcriptapi.com/api/v2/youtube/search?q=QUERY&type=channel&limit=10
Authorization: Bearer $TRANSCRIPT_API_KEY
User-Agent: YourAgent/1.0
```

| Param   | Required | Default | Validation         |
| ------- | -------- | ------- | ------------------ |
| `q`     | yes      | —       | 1-200 chars        |
| `type`  | no       | `video` | `video`, `channel` |
| `limit` | no       | `20`    | 1-50               |

## Channels

All channel endpoints accept `channel` — an `@handle`, channel URL, or `UC...` channel ID. No need to resolve first.

### Resolve handle — FREE

```http
GET https://transcriptapi.com/api/v2/youtube/channel/resolve?input=@TED
Authorization: Bearer $TRANSCRIPT_API_KEY
User-Agent: YourAgent/1.0
```

Response: `{"channel_id": "UC...", "resolved_from": "@TED"}`

### Latest 15 videos — FREE

```http
GET https://transcriptapi.com/api/v2/youtube/channel/latest?channel=@TED
Authorization: Bearer $TRANSCRIPT_API_KEY
User-Agent: YourAgent/1.0
```

Returns exact `viewCount` and ISO `published` timestamps.

### All channel videos — 1 credit/page

```http
# First page (100 videos)
GET https://transcriptapi.com/api/v2/youtube/channel/videos?channel=@NASA
Authorization: Bearer $TRANSCRIPT_API_KEY
User-Agent: YourAgent/1.0

# Next pages
GET https://transcriptapi.com/api/v2/youtube/channel/videos?continuation=TOKEN
Authorization: Bearer $TRANSCRIPT_API_KEY
User-Agent: YourAgent/1.0
```

Provide exactly one of `channel` or `continuation`. Response includes `continuation_token` and `has_more`.

### Search within channel — 1 credit

```http
GET https://transcriptapi.com/api/v2/youtube/channel/search?channel=@TED&q=QUERY&limit=30
Authorization: Bearer $TRANSCRIPT_API_KEY
User-Agent: YourAgent/1.0
```

## Playlists — 1 credit/page

Accepts `playlist` — a YouTube playlist URL or playlist ID.

```http
# First page
GET https://transcriptapi.com/api/v2/youtube/playlist/videos?playlist=PL_ID
Authorization: Bearer $TRANSCRIPT_API_KEY
User-Agent: YourAgent/1.0

# Next pages
GET https://transcriptapi.com/api/v2/youtube/playlist/videos?continuation=TOKEN
Authorization: Bearer $TRANSCRIPT_API_KEY
User-Agent: YourAgent/1.0
```

Valid ID prefixes: `PL`, `UU`, `LL`, `FL`, `OL`. Response includes `playlist_info`, `results`, `continuation_token`, `has_more`.

## Credit Costs

| Endpoint        | Cost     |
| --------------- | -------- |
| transcript      | 1        |
| search          | 1        |
| channel/resolve | **free** |
| channel/latest  | **free** |
| channel/videos  | 1/page   |
| channel/search  | 1        |
| playlist/videos | 1/page   |

## Validation Rules

| Field      | Rule                                                    |
| ---------- | ------------------------------------------------------- |
| `channel`  | `@handle`, channel URL, or `UC...` ID                   |
| `playlist` | Playlist URL or ID (`PL`/`UU`/`LL`/`FL`/`OL` prefix)   |
| `q`        | 1-200 chars                                             |
| `limit`    | 1-50                                                    |

## Errors

| Code     | Meaning          | Action                                         |
| -------- | ---------------- | ---------------------------------------------- |
| 401      | Bad API key      | Check key                                      |
| 402      | No credits       | transcriptapi.com/billing                      |
| 403/1010 | Cloudflare block | Add or fix User-Agent header                   |
| 404      | Not found        | Resource doesn't exist or no captions          |
| 408      | Timeout          | Retry once after 2s                            |
| 422      | Validation error | Check param format                             |
| 429      | Rate limited     | Wait, respect Retry-After                      |

## Typical Workflows

**Research workflow:** search → pick videos → fetch transcripts

```http
# 1. Search
GET https://transcriptapi.com/api/v2/youtube/search?q=machine+learning+explained&limit=5
Authorization: Bearer $TRANSCRIPT_API_KEY
User-Agent: YourAgent/1.0

# 2. Transcript
GET https://transcriptapi.com/api/v2/youtube/transcript?video_url=VIDEO_ID&format=text&include_timestamp=true&send_metadata=true
Authorization: Bearer $TRANSCRIPT_API_KEY
User-Agent: YourAgent/1.0
```

**Channel monitoring:** latest (free) → transcript

```http
# 1. Latest uploads (free — pass @handle directly)
GET https://transcriptapi.com/api/v2/youtube/channel/latest?channel=@TED
Authorization: Bearer $TRANSCRIPT_API_KEY
User-Agent: YourAgent/1.0

# 2. Transcript of latest
GET https://transcriptapi.com/api/v2/youtube/transcript?video_url=VIDEO_ID&format=text&include_timestamp=true&send_metadata=true
Authorization: Bearer $TRANSCRIPT_API_KEY
User-Agent: YourAgent/1.0
```

Free tier: 100 credits, 300 req/min. Starter ($5/mo): 1,000 credits.

## Copy-paste examples

Every request in this file as a ready-to-run one-liner: [references/curl-examples.md](references/curl-examples.md)
