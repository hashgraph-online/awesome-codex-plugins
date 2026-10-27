---
name: revid-article-to-short
description: Turn any news article or long-form post URL into a 30–60 second 9:16 short with stock visuals, narration, and captions. Use when the user shares a link and wants an edited summary, not a talking-head. Calls the Revid MCP server (render_video → get_project_status).
metadata: {"openclaw":{"requires":{"config":["REVID_API_KEY"]}}}
---

# Article / news → short

> Calls the **Revid MCP server** (`https://www.revid.ai/api/mcp`). Install once — see [`revid-api-foundations`](../revid-api-foundations/SKILL.md#install-the-revid-mcp-server).

Take any URL with a substantial article body and produce a vertical short with
voiceover + auto-cut stock b-roll + captions.

## When to use this skill

- Source is a news article, long-form blog, press release, or essay.
- Output goal: an **edited summary**, voiceover + visuals, 30–60 s.
- The user does NOT want a talking-head (use
  [`revid-blog-to-avatar-video`](../revid-blog-to-avatar-video/SKILL.md) for that).
- For e-commerce product pages prefer
  [`revid-shopify-product-promo`](../revid-shopify-product-promo/SKILL.md) — same
  workflow but tuned defaults.

## Inputs

| Field | Required | Notes |
|---|---|---|
| `url` | yes | Article URL |
| `aspectRatio` | no | Default `9:16` |
| `targetDuration` | no | Default 45 s |
| `language` | no | Auto-detected; override for non-English |

## Step-by-step

1. Validate the URL.
2. Call MCP tool `render_video` with the payload below — returns `data.pid`.
   Then poll MCP tool `get_project_status` with that `pid` every 5–8 s until
   `data.status === "ready"`. Optionally call `export_video` for a freshly
   named mp4.
3. Return `videoUrl`.

## `render_video` arguments

```json
{
  "workflow": "article-to-video",
  "source": {
    "url": "{ARTICLE_URL}",
    "scrapingPrompt": "Summarize the article body. Skip ads, related links, navigation, and footer."
  },
  "aspectRatio": "9:16",
  "voice":    { "enabled": true, "stability": 0.6, "speed": 1.0, "language": "en-US" },
  "captions": { "enabled": true, "position": "middle", "autoCrop": true },
  "music":    { "enabled": true, "syncWith": "beats" },
  "media": {
    "type": "stock-video",
    "density": "medium",
    "animation": "soft",
    "quality": "pro",
    "videoModel": "pro",
    "imageModel": "good"
  },
  "options": {
    "targetDuration": 45,
    "summarizationPreference": "summarize",
    "soundEffects": true,
    "hasToGenerateCover": true,
    "coverTextType": "headline"
  },
  "render": { "resolution": "1080p", "frameRate": 30 }
}
```

## Examples

- [`examples/article-techreview.json`](examples/article-techreview.json) —
  copy-paste body for `render_video` *(also a valid POST body for the direct
  HTTPS fallback)*.
- [`examples/run.sh`](examples/run.sh) — bash smoke test using the **direct
  HTTPS fallback** (`POST /api/public/v3/render` → `GET /status`). Useful when
  you don't have an MCP client at hand.

## Polling

Call `get_project_status` with the `pid` returned by `render_video`. Stop when
`data.status === "ready"`; fail when `data.status === "failed"`. Cadence: 5 s,
then 8 s once `progress > 30`. Full pseudocode:
[`revid-api-foundations` § Polling](../revid-api-foundations/SKILL.md#polling).

## Failure modes

| Symptom | Fix |
|---|---|
| `scrape failed` | Pre-fetch the article body server-side and switch to [`revid-script-to-video`](../revid-script-to-video/SKILL.md) with the body in `source.text`. |
| Off-topic stock visuals | Pass a tighter `scrapingPrompt` (e.g. *"Focus on the financial markets angle, not the company history"*) and lower `media.density: "low"`. |
| Wrong language detected | Set `voice.language` and `options.language` explicitly. |
| Captions clip subjects | `captions.position: "top"`. |
| `ok: false`, `error: "insufficient_credits"` | Drop `media.quality` to `"standard"` or `render.resolution` to `"720p"`, or call `buy_credit_pack`. |

## See also

- [`revid-shopify-product-promo`](../revid-shopify-product-promo/SKILL.md)
- [`revid-news-to-daily-short`](../revid-news-to-daily-short/SKILL.md) for
  *generating* news from a topic vs summarizing a known URL.
- [`revid-pdf-to-video`](../revid-pdf-to-video/SKILL.md) for PDFs instead of HTML.
