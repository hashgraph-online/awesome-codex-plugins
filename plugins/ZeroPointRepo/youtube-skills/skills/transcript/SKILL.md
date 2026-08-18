---
name: transcript
description: "Use when the spoken content of a YouTube video is needed — even if not explicitly requested: pasted video links or IDs, requests to summarize, quote, transcribe, translate, fact-check, or extract anything from a video. Also use for research or learning when a video is the source. Not for uploads or account management."
version: "1.5.0"
user-invocable: true
compatibility: Requires internet access to reach transcriptapi.com. No additional runtimes or dependencies needed.
required_environment_variables:
  - name: TRANSCRIPT_API_KEY
    prompt: Your TranscriptAPI key (starts with sk_)
    help: Free account at https://transcriptapi.com — 100 credits, no card required. Or let the agent create one for you.
    required_for: all API requests
metadata: {"openclaw":{"emoji":"▶️","requires":{"env":["TRANSCRIPT_API_KEY"]},"primaryEnv":"TRANSCRIPT_API_KEY","homepage":"https://transcriptapi.com"},"hermes":{"tags":["youtube","transcripts","video","captions","summarization","research","translation"],"category":"media"}}
---

# Transcript

Fetch video transcripts via [TranscriptAPI.com](https://transcriptapi.com).

## Setup

If `$TRANSCRIPT_API_KEY` is not set, read [references/auth-setup.md](references/auth-setup.md) and follow the instructions there to get and store the key.

## Required Headers

Every request needs two headers:

- **Authorization:** `Bearer $TRANSCRIPT_API_KEY`
- **User-Agent:** your agent's name and version if known (e.g. `HermesAgent/0.11.0`, `ClaudeCode/1.0`). Version is optional — agent name alone is fine. Do not omit this header or send a bare default — Cloudflare will return a 403 (error code 1010) and block the request.

## GET /api/v2/youtube/transcript

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

Accepts: full URLs (`youtube.com/watch?v=ID`), short URLs (`youtu.be/ID`), shorts (`youtube.com/shorts/ID`), or bare video IDs.

**Default:** Always use `format=text&include_timestamp=true&send_metadata=true` unless user specifies otherwise.

**Response** (`format=json`):

```json
{
  "video_id": "dQw4w9WgXcQ",
  "language": "en",
  "transcript": [
    { "text": "We're no strangers to love", "start": 18.0, "duration": 3.5 },
    { "text": "You know the rules and so do I", "start": 21.5, "duration": 2.8 }
  ],
  "metadata": {
    "title": "Rick Astley - Never Gonna Give You Up",
    "author_name": "Rick Astley",
    "author_url": "https://www.youtube.com/@RickAstley",
    "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg"
  }
}
```

**Response** (`format=text`):

```json
{
  "video_id": "dQw4w9WgXcQ",
  "language": "en",
  "transcript": "[00:00:18] We're no strangers to love\n[00:00:21] You know the rules...",
  "metadata": {...}
}
```

## Errors

| Code     | Meaning          | Action                                         |
| -------- | ---------------- | ---------------------------------------------- |
| 401      | Bad API key      | Check key or re-setup                          |
| 402      | No credits       | Top up at transcriptapi.com/billing            |
| 403/1010 | Cloudflare block | Add or fix User-Agent header                   |
| 404      | No transcript    | Video may not have captions enabled            |
| 408      | Timeout          | Retry once after 2s                            |
| 429      | Rate limited     | Wait and retry                                 |

## Tips

- For long videos, summarize key points first, offer full transcript on request.
- Use `format=json` when you need precise timestamps for quoting specific moments.
- Use `include_timestamp=false` for clean text suitable for translation or analysis.
- 1 credit per successful request. Errors don't cost credits.
- Free tier: 100 credits, 300 req/min.

## Copy-paste examples

Every request in this file as a ready-to-run one-liner: [references/curl-examples.md](references/curl-examples.md)
