---
name: revid-tweet-to-talking-head
description: Turn an X/Twitter/LinkedIn post (URL or pasted thread text) into a talking-head video that delivers the take. Use when a creator wants to repurpose a viral post as a short-form video. Calls the Revid MCP server (render_video → get_project_status).
metadata: {"openclaw":{"requires":{"config":["REVID_API_KEY"]}}}
---

# Tweet / X / LinkedIn post → talking-head video

> Calls the **Revid MCP server** (`https://www.revid.ai/api/mcp`). Install once — see [`revid-api-foundations`](../revid-api-foundations/SKILL.md#install-the-revid-mcp-server).

Take a single post or a thread and produce a 20–45 s talking-head video where
an avatar reads the take.

## When to use this skill

- Source is a tweet URL, X thread URL, LinkedIn post URL, or pasted thread text.
- Output is a **talking-head** delivering the post (avatar + voiceover +
  captions + minimal background motion).
- For an *edited summary with stock visuals* of an article, use
  [`revid-article-to-short`](../revid-article-to-short/SKILL.md) instead.

## Inputs

| Field | Required | Notes |
|---|---|---|
| `text` *or* `url` | yes | Either the pasted thread (preferred — no scraping) or the post URL. |
| `avatar.url` *or* `characterIds[]` | yes | The face. |
| `aspectRatio` | no | Default `9:16` |
| `targetDuration` | no | Default 30 (s) |

## Step-by-step

1. If you have the tweet/thread text, prefer `script-to-video` (no scraping
   risk — many social platforms block bots).
2. If you only have a URL, use `article-to-video` with a tight `scrapingPrompt`.
3. Either way, attach the `avatar` block + a single `characterId`.
4. Call MCP tool `render_video` with the payload below — returns `data.pid`.
5. Then poll MCP tool `get_project_status` with that `pid` every 5–8 s until
   `data.status === "ready"`. Optionally call `export_video` for a freshly
   named mp4.

## `render_video` arguments — pasted thread (preferred)

```json
{
  "workflow": "script-to-video",
  "source": {
    "text": "{TWEET_OR_THREAD_TEXT}"
  },
  "aspectRatio": "9:16",
  "avatar": {
    "enabled": true,
    "url": "{AVATAR_IMAGE_URL}",
    "removeBackground": true
  },
  "voice":    { "enabled": true, "voiceId": "aria-en-us", "stability": 0.65, "speed": 1.05 },
  "captions": { "enabled": true, "position": "middle", "autoCrop": true },
  "music":    { "enabled": false },
  "media": {
    "type": "moving-image",
    "density": "low",
    "animation": "soft",
    "placeAvatarInContext": true
  },
  "options": {
    "targetDuration": 30,
    "summarizationPreference": "no-summarization",
    "hasToGenerateCover": true,
    "coverTextType": "first-line"
  },
  "render": { "resolution": "1080p", "frameRate": 30 }
}
```

`summarizationPreference: "no-summarization"` — for tweets, the original
phrasing IS the value. Don't paraphrase.

## `render_video` arguments — URL (fallback)

```json
{
  "workflow": "article-to-video",
  "source": {
    "url": "{POST_URL}",
    "scrapingPrompt": "Extract only the original post text and the thread author. Ignore replies, reposts, and side panels."
  },
  "aspectRatio": "9:16",
  "avatar": { "enabled": true, "url": "{AVATAR_IMAGE_URL}", "removeBackground": true },
  "voice":   { "enabled": true, "voiceId": "aria-en-us", "stability": 0.65 },
  "captions":{ "enabled": true, "position": "middle" },
  "music":   { "enabled": false },
  "media":   { "type": "moving-image", "density": "low", "animation": "soft" },
  "options": { "targetDuration": 30, "summarizationPreference": "summarizeIfLong" },
  "render":  { "resolution": "1080p" }
}
```

## Polling

Call `get_project_status` with the `pid` returned by `render_video`. Stop when
`data.status === "ready"`; fail when `data.status === "failed"`. Cadence: 5 s,
then 8 s once `progress > 30`. Full pseudocode:
[`revid-api-foundations` § Polling](../revid-api-foundations/SKILL.md#polling).

## Examples

- [`examples/thread-text.json`](examples/thread-text.json) — copy-paste body for
  `render_video` *(also a valid POST body for the direct HTTPS fallback)*.
- [`examples/run.sh`](examples/run.sh) — bash smoke test using the **direct
  HTTPS fallback**.

## Failure modes

| Symptom | Fix |
|---|---|
| `scrape failed` on URL form | Switch to the pasted-thread template — copy the post body into `source.text`. |
| Lip-sync drifts on multi-tweet thread | Lower `targetDuration` to 25 s, or set `summarizationPreference: "summarize"`. |
| Avatar reads in the wrong tone | Set `voice.voiceId` explicitly to a voice that matches the persona; default voice is rarely right for personality-driven content. |
| Tweet contains URLs / @mentions / hashtags | The voice will read them aloud awkwardly. Pre-clean the text: strip raw URLs, replace `@handle` with the person's name, and remove standalone hashtags (or keep one as a sign-off). |
| `ok: false`, `error: "insufficient_credits"` | Drop `media.quality` to `"standard"` or `render.resolution` to `"720p"`, or call `buy_credit_pack`. |

## See also

- [`revid-blog-to-avatar-video`](../revid-blog-to-avatar-video/SKILL.md) — same
  pattern, longer source.
- [`revid-script-to-video`](../revid-script-to-video/SKILL.md).
- [`revid-api-foundations`](../revid-api-foundations/SKILL.md).
