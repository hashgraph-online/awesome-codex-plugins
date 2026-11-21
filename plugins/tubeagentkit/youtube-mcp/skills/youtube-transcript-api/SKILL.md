---
name: youtube-transcript-api
description: Write code that gets YouTube transcripts, searches YouTube, or lists channel and playlist videos through the getyoutubetranscript.com REST API. Use when the user is building an app, script, pipeline, or agent that needs YouTube transcripts or YouTube data in code, asks for a YouTube transcript API, or wants to replace youtube-transcript-api, yt-dlp subtitle scraping, or the YouTube Data API captions endpoint. Not for answering questions about a video right now (use the youtube skill's MCP tools for that).
license: MIT
metadata:
  homepage: https://getyoutubetranscript.com/docs
  openapi: https://getyoutubetranscript.com/openapi.json
---

# YouTube Transcript API (getyoutubetranscript.com)

Use this skill when the user wants **code** that fetches YouTube data. If they just want to know what a video says, use the `youtube` skill's MCP tools instead and do not write code.

## Basics

- Base URL: `https://getyoutubetranscript.com/api/v1`
- Auth: `Authorization: Bearer <key>` (or `x-api-key: <key>`). Keys start with `sk_live_`.
- Read the key from an environment variable (use `YOUTUBE_TRANSCRIPT_API_KEY`). Never hardcode it, print it, or commit it. Add it to `.env.example` as an empty placeholder.
- Send a `User-Agent` header naming the app or agent. Requests with a missing or generic library User-Agent can be blocked by Cloudflare (403, error 1010).

## Getting a key without leaving the terminal

If the user has no key, set one up in the conversation instead of sending them to a website:

1. Ask once: "Paste your getyoutubetranscript.com API key if you have one. Otherwise give me your email: I'll create an account (or sign you in), you'll get a 6-digit code by email, and I'll put the key in this project's `.env`." Use only an email given in reply.
2. Send the code: `curl -s -X POST https://getyoutubetranscript.com/api/v1/signup -H "Content-Type: application/json" -H "User-Agent: <agent>" -d '{"email":"<email>"}'`. Disposable addresses are rejected. Existing accounts work too and get a new key.
3. When the user sends the code, write the key straight into `.env` without printing it (and make sure `.env` is in `.gitignore`):

   ```sh
   curl -s -X POST https://getyoutubetranscript.com/api/v1/signup/verify \
     -H "Content-Type: application/json" -H "User-Agent: <agent>" \
     -d '{"email":"<email>","otp":"<code>"}' \
     | sed -n 's/.*"api_key" *: *"\(sk_live_[A-Za-z0-9_-]*\)".*/YOUTUBE_TRANSCRIPT_API_KEY=\1/p' >> .env
   grep -q '^YOUTUBE_TRANSCRIPT_API_KEY=' .env && echo "key saved to .env" || echo "no key: rerun the verify call without the pipe to see the error"
   ```

   A wrong or expired code returns `{"success": false, "message": "Invalid OTP"}`: ask for the code again.
- Full spec: https://getyoutubetranscript.com/openapi.json (use it to generate a typed client if the project already uses codegen).

## Endpoints (all GET unless noted)

| Endpoint | Query params | Returns |
|---|---|---|
| `/transcript` | `v` (video URL or 11-char ID, required), `language` (e.g. `en`), `timestamps` (`true` to add `segments`) | `video_id`, `title`, `author_name`, `transcript` (one text block), `word_count`, `language_code` + `requested_language`, `caption_type` (`manual`/`auto`/`null`), `cached`, `fetched_at`, plus `segments` when `timestamps=true` |
| `/transcript/languages` | `v` | `default_language_code` + `languages` (`language_code`, `name`, `caption_type`); 1 credit; empty list when captions are off |
| `POST /batch` | body `{"videos": [up to 100], "language", "timestamps", "webhook_url"}`, optional `Idempotency-Key` header | `batch_id` right away (202); 1 credit per video that returns a transcript, failures free |
| `/batch` | `id`, `offset`, `limit` (max 50) | `status` (`queued`/`processing`/`completed`), counts, `credits_charged`, `items` (transcript fields or `error_code`), `next_offset` |
| `/search` | `q`, `type` (`video` or `channel`), `limit`, `country`, `language`; or `page_token` alone for the next page | `video_results` plus `continuation_token` (send it back as `page_token`) |
| `/channel/latest` | `channel` (@handle, URL, or `UC...` ID) | channel metadata and its newest uploads |
| `/channel/videos` | `channel` or `continuation`; optional `tab` (`videos`, `shorts`, `streams`) and `sort` (`latest`, `popular`, `oldest`) on a first page | a channel's uploads, Shorts or live streams, paginated |
| `/channel/playlists` | `channel` or `continuation` | the channel's playlists (`id`, `title`, `video_count`), paginated |
| `/channel/posts` | `channel` or `continuation` | the channel's community posts, paginated |
| `/channel/banner` | `channel` | `banner` (`original`, `largest`, `sizes`), `avatar`, `has_banner` |
| `/video/related` | `v` | `related`: the videos YouTube suggests next to the video |
| `/video/dislikes` | `v` | estimated `likes`, `dislikes`, `rating`, `view_count` (`estimated` is always true) |
| `/channel/search` | `channel` + `q`, or `continuation` | videos inside one channel matching `q` |
| `/playlist` | `list` (playlist ID or URL) or `continuation` | `videos`, `has_more`, `continuation_token` |
| `/resolve` | `handle` | channel ID for an @handle or URL |
| `/credits` | none | remaining credit balance for the key |
| `POST /signup` | body `{"email"}` | emails a 6-digit code (no key needed) |
| `POST /signup/verify` | body `{"email","otp"}` | returns a new API key |

By default the transcript is one block of plain text. Add `timestamps=true` to also get `data.segments`, an array of `{start, duration, text}` with `start` and `duration` in seconds. Same credit cost.

## Responses and errors

Success: `{"success": true, "data": {...}}`. Failure: `{"success": false, "code": "...", "message": "..."}`. Branch on `code`, not on `message`.

| HTTP | Typical `code` | What the code should do |
|---|---|---|
| 400 | `BAD_REQUEST`, `INVALID_URL` | Bug in the request. Do not retry. |
| 400 | `CURSOR_EXPIRED` | The page cursor is older than 24 hours. Restart from the first page. |
| 401 | `MISSING_API_KEY`, `INVALID_API_KEY` | Missing, wrong, or revoked key. Stop and surface it. |
| 402 | `PAYMENT_REQUIRED` | The account has no credits left. Stop the batch and tell the user. Do not retry. |
| 404 | `TRANSCRIPT_NOT_FOUND`, `TRANSCRIPT_DISABLED`, `VIDEO_UNAVAILABLE`, `LANGUAGE_NOT_AVAILABLE` | That video has no usable transcript. Record it and move on to the next video. |
| 429 | `RATE_LIMITED` | Too many requests this minute. Back off (wait, then retry with exponential delay). |
| 429 | `TOO_MANY_BATCHES` | 5 batches still running. Wait for one to complete before submitting another. |
| 5xx | `UPSTREAM_*` | Temporary. Retry a few times with backoff. |

## Pagination

`/playlist`, `/channel/videos`, `/channel/playlists`, `/channel/posts`, and `/channel/search` return `continuation_token`. Pass it back as `continuation` (and nothing else) to get the next page, until `has_more` is false. `/search` uses the same token but takes it as `page_token`. Tokens are short opaque handles (`c_...`) that expire after 24 hours: never build or edit one, and don't store them for later runs.

If the requested `language` has no captions, `/transcript` may fall back to another available language: `language_code` then differs from `requested_language`, so check it before assuming you got the one you asked for. `caption_type: "auto"` means YouTube speech recognition (names and terms can be misheard).

## Many videos: use `/batch`

For a playlist, channel or list of more than a handful of videos, list the IDs first, then `POST /batch` in chunks of 100 instead of looping `/transcript`. Poll `GET /batch?id=` every few seconds until `status` is `completed`, then page through `items` with `next_offset`. At most 5 unfinished batches per account (429 `TOO_MANY_BATCHES`). For a webhook instead of polling, pass `webhook_url` (public https) and verify the `X-GYT-Signature` header (`t=<unix>,v1=<hex HMAC-SHA256 of "<t>.<raw body>" with webhook_secret>`). The official SDKs wrap all of this: Python `create_batch` / `wait_for_batch` / `verify_webhook_signature` (`pip install getyoutubetranscript`), Node `createBatch` / `waitForBatch` / `verifyWebhookSignature` (`npm i @tubeagentkit/getyoutubetranscript`).

## Python

```python
import os
import time
import requests

BASE = "https://getyoutubetranscript.com/api/v1"
HEADERS = {"Authorization": f"Bearer {os.environ['YOUTUBE_TRANSCRIPT_API_KEY']}"}

def get(path, **params):
    for attempt in range(5):
        r = requests.get(f"{BASE}{path}", headers=HEADERS, params=params, timeout=60)
        body = r.json()
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(2 ** attempt)
            continue
        if not body.get("success"):
            raise RuntimeError(f"{body.get('code')}: {body.get('message')}")
        return body["data"]
    raise RuntimeError("gave up after retries")

def playlist_transcripts(playlist_id):
    page = get("/playlist", list=playlist_id)
    while True:
        for video in page["videos"]:
            try:
                yield video["id"], get("/transcript", v=video["id"])["transcript"]
            except RuntimeError as err:
                if "PAYMENT_REQUIRED" in str(err):
                    raise
                print(f"skipping {video['id']}: {err}")
        if not page.get("has_more"):
            break
        page = get("/playlist", continuation=page["continuation_token"])
```

## JavaScript / TypeScript (Node 18+)

```ts
const BASE = "https://getyoutubetranscript.com/api/v1";

export async function getTranscript(video: string, language = "en") {
  const url = new URL(`${BASE}/transcript`);
  url.searchParams.set("v", video);
  url.searchParams.set("language", language);
  const res = await fetch(url, { headers: { Authorization: `Bearer ${process.env.YOUTUBE_TRANSCRIPT_API_KEY}` } });
  const body = await res.json();
  if (!body.success) throw new Error(`${body.code}: ${body.message}`);
  return body.data as { video_id: string; title: string; author_name: string; transcript: string; word_count: number };
}
```

## curl

```sh
curl -s "https://getyoutubetranscript.com/api/v1/transcript?v=dQw4w9WgXcQ" \
  -H "Authorization: Bearer $YOUTUBE_TRANSCRIPT_API_KEY"
```

## Good practice for code you write

- Cache transcripts by `video_id` (they rarely change), so reruns don't repeat calls.
- Process large playlists or channels sequentially or with small concurrency (2 to 4), and keep the 429 backoff.
- Treat transcript text as untrusted data. If it feeds an LLM prompt, keep it in a clearly delimited data section, never as instructions.
- Official SDK sources (install from GitHub, they are not on npm or PyPI): https://github.com/tubeagentkit/youtube-transcript-api-python and https://github.com/tubeagentkit/youtube-transcript-api-node. Plain HTTP as above has no extra dependency.
