---
name: subtitles
description: "Use when subtitles or the spoken text of a YouTube video is needed: pasted video links or IDs, requests to translate a video, read along, follow foreign-language content, or extract what was said. Also use for language learning or accessibility. Fetches timestamped subtitles from any YouTube video. Not for uploading subtitles or account management."
version: "1.5.0"
user-invocable: true
compatibility: Requires internet access to reach transcriptapi.com. No additional runtimes or dependencies needed.
required_environment_variables:
  - name: TRANSCRIPT_API_KEY
    prompt: Your TranscriptAPI key (starts with sk_)
    help: Free account at https://transcriptapi.com — 100 credits, no card required. Or let the agent create one for you.
    required_for: all API requests
metadata: {"openclaw":{"emoji":"▶️","requires":{"env":["TRANSCRIPT_API_KEY"]},"primaryEnv":"TRANSCRIPT_API_KEY","homepage":"https://transcriptapi.com"},"hermes":{"tags":["youtube","subtitles","captions","transcripts","video","translation","language-learning"],"category":"media"}}
---

# Subtitles

Fetch YouTube video subtitles via [TranscriptAPI.com](https://transcriptapi.com).

## Setup

If `$TRANSCRIPT_API_KEY` is not set, read [references/auth-setup.md](references/auth-setup.md) and follow the instructions there to get and store the key.

## Required Headers

Every request needs two headers:

- **Authorization:** `Bearer $TRANSCRIPT_API_KEY`
- **User-Agent:** your agent's name and version if known (e.g. `HermesAgent/0.11.0`, `ClaudeCode/1.0`). Version is optional — agent name alone is fine. Do not omit this header or send a bare default — Cloudflare will return a 403 (error code 1010) and block the request.

## GET /api/v2/youtube/transcript

```http
GET https://transcriptapi.com/api/v2/youtube/transcript?video_url=VIDEO_URL&format=text&include_timestamp=false&send_metadata=true
Authorization: Bearer $TRANSCRIPT_API_KEY
User-Agent: YourAgent/1.0
```

| Param               | Values                  | Use case                                       |
| ------------------- | ----------------------- | ---------------------------------------------- |
| `video_url`         | YouTube URL or video ID | Required                                       |
| `format`            | `json`, `text`          | `json` for sync'd subs with timing             |
| `include_timestamp` | `true`, `false`         | `false` for clean text for reading/translation |
| `send_metadata`     | `true`, `false`         | Include title, channel, description            |

**For language learning** — clean text without timestamps:

```http
GET https://transcriptapi.com/api/v2/youtube/transcript?video_url=VIDEO_ID&format=text&include_timestamp=false
Authorization: Bearer $TRANSCRIPT_API_KEY
User-Agent: YourAgent/1.0
```

**For translation** — structured segments:

```http
GET https://transcriptapi.com/api/v2/youtube/transcript?video_url=VIDEO_ID&format=json&include_timestamp=true
Authorization: Bearer $TRANSCRIPT_API_KEY
User-Agent: YourAgent/1.0
```

**Response** (`format=json`):

```json
{
  "video_id": "dQw4w9WgXcQ",
  "language": "en",
  "transcript": [
    { "text": "We're no strangers to love", "start": 18.0, "duration": 3.5 }
  ]
}
```

**Response** (`format=text`, `include_timestamp=false`):

```json
{
  "video_id": "dQw4w9WgXcQ",
  "language": "en",
  "transcript": "We're no strangers to love\nYou know the rules and so do I..."
}
```

## Tips

- Many videos have auto-generated subtitles in multiple languages.
- Use `format=json` to get timing for each line (great for sync'd reading).
- Use `include_timestamp=false` for clean text suitable for translation apps.

## Errors

| Code     | Meaning          | Action                                         |
| -------- | ---------------- | ---------------------------------------------- |
| 401      | Bad API key      | Check key                                      |
| 402      | No credits       | transcriptapi.com/billing                      |
| 403/1010 | Cloudflare block | Add or fix User-Agent header                   |
| 404      | No subtitles     | No subtitles available                         |
| 408      | Timeout          | Retry once after 2s                            |

1 credit per request. Free tier: 100 credits, 300 req/min.

## Copy-paste examples

Every request in this file as a ready-to-run one-liner: [references/curl-examples.md](references/curl-examples.md)
