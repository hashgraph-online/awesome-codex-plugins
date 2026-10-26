---
name: revid-pdf-to-video
description: Turn a PDF (whitepaper, ebook chapter, slide deck export, research paper) into a short summary video. Use when the source is a PDF URL or a PDF the agent can upload to public storage first. Calls the Revid MCP server (render_video → get_project_status).
metadata: {"openclaw":{"requires":{"config":["REVID_API_KEY"]}}}
---

# PDF → summary video

> Calls the **Revid MCP server** (`https://www.revid.ai/api/mcp`). Install once — see [`revid-api-foundations`](../revid-api-foundations/SKILL.md#install-the-revid-mcp-server).

Take a PDF URL and produce a short summary video. Internally this routes
through `article-to-video` once the PDF text has been extracted by Revid's
scraper.

## When to use this skill

- Source is a public PDF URL (whitepaper, paper, ebook, slide export).
- Goal is a 30–90 s summary, not a full reading.
- For HTML articles use [`revid-article-to-short`](../revid-article-to-short/SKILL.md).
- For local PDFs the agent must first upload to public storage (S3, Supabase
  Storage, etc.) so Revid can fetch it.

## Inputs

| Field | Required | Notes |
|---|---|---|
| `url` | yes | Public PDF URL (must be reachable, no auth) |
| `aspectRatio` | no | Default `9:16` |
| `targetDuration` | no | Default 60 (s); raise to 90 s for dense papers |

## Step-by-step

1. Confirm the URL ends in `.pdf` or returns `Content-Type: application/pdf`.
2. Set `source.scrapingPrompt` to bias the summary toward what the user cares
   about ("Focus on the methodology section", "Focus on the executive summary",
   "Pull the 3 biggest takeaways").
3. Call MCP tool `render_video` with the payload below — returns `data.pid`.
   Then poll MCP tool `get_project_status` with that `pid` every 5–8 s until
   `data.status === "ready"`. Optionally call `export_video` for a freshly named mp4.

## `render_video` arguments

```json
{
  "workflow": "article-to-video",
  "source": {
    "url": "{PDF_URL}",
    "scrapingPrompt": "Extract the executive summary and the 3 biggest takeaways. Skip references and appendices."
  },
  "aspectRatio": "9:16",
  "voice":    { "enabled": true, "stability": 0.65, "speed": 0.95, "language": "en-US" },
  "captions": { "enabled": true, "position": "middle", "autoCrop": true },
  "music":    { "enabled": true, "syncWith": "beats" },
  "media": {
    "type": "stock-video",
    "density": "medium",
    "animation": "soft",
    "quality": "pro",
    "imageModel": "good",
    "videoModel": "pro"
  },
  "options": {
    "targetDuration": 60,
    "summarizationPreference": "summarize",
    "soundEffects": true,
    "hasToGenerateCover": true,
    "coverTextType": "title"
  },
  "render": { "resolution": "1080p", "frameRate": 30 }
}
```

## Polling

Call `get_project_status` with the `pid` returned by `render_video`. Stop when
`data.status === "ready"`; fail when `data.status === "failed"`. Cadence:
5 s, then 8 s once `progress > 30`. Full pseudocode:
[`revid-api-foundations` § Polling](../revid-api-foundations/SKILL.md#polling).

## Examples

- [`examples/whitepaper.json`](examples/whitepaper.json) — copy-paste body for
  `render_video` *(also a valid POST body for the direct HTTPS fallback)*.
- [`examples/run.sh`](examples/run.sh) — bash smoke test using the **direct
  HTTPS fallback** (`POST /api/public/v3/render` → `GET /status`). Useful when
  you don't have an MCP client at hand.

## Failure modes

| Symptom | Fix |
|---|---|
| `scrape failed` | PDF behind auth or login wall. Re-host the PDF on public storage. |
| Summary skips the section the user cares about | Tighten `scrapingPrompt` (be specific: section names, page ranges). |
| Visuals are abstract / off-topic | PDFs rarely have crawlable hero images. Pre-render a few key figures as images and pass them in `media.provided`. |
| Voice rushes through technical terms | Lower `voice.speed` to `0.9`. |
| `ok: false`, `error: "insufficient_credits"` | Drop `media.quality` to `"standard"` or `render.resolution` to `"720p"`, or call `buy_credit_pack`. |

## See also

- [`revid-article-to-short`](../revid-article-to-short/SKILL.md) for HTML.
- [`revid-script-with-custom-media`](../revid-script-with-custom-media/SKILL.md)
  for full visual control.
