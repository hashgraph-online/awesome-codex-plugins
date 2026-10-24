---
name: revid-shopify-product-promo
description: Turn a Shopify (or any e-commerce) product page URL into a 30–45 second 9:16 promo video ready for TikTok / Reels / Shorts. Use when the user shares a product link and wants a short ad/promo, not a long-form review. Calls the Revid MCP server (render_video → get_project_status).
metadata: {"openclaw":{"requires":{"config":["REVID_API_KEY"]}}}
---

# Shopify product → promo video

> Calls the **Revid MCP server** (`https://www.revid.ai/api/mcp`). Install once — see [`revid-api-foundations`](../revid-api-foundations/SKILL.md#install-the-revid-mcp-server).

Take a product page URL and produce a vertical promo video that pulls the
product image(s), name, key features, and price.

## When to use this skill

- Input is a single product page URL from Shopify, WooCommerce, BigCommerce, or
  any storefront with crawlable HTML (most stores).
- Output goal is a **promo / ad / launch teaser**, 30–45 s, vertical (9:16).
- The user wants Revid to extract the product details automatically. If they
  hand you a script instead, use [`revid-script-to-video`](../revid-script-to-video/SKILL.md).
- For a generic ad written from a product description (no live URL), use
  [`revid-product-description-to-ad`](../revid-product-description-to-ad/SKILL.md).

## Inputs

| Field | Required | Notes |
|---|---|---|
| `url` | yes | Public product page URL |
| `aspectRatio` | no | Defaults to `9:16` |
| `targetDuration` | no | Defaults to 35 (s) |
| `voiceId` | no | Default voice if omitted |
| `webhookUrl` | no | Skip polling if you can receive webhooks |

## Step-by-step

1. **Validate the URL** — must start with `http(s)://`. Reject obvious
   non-product paths (`/cart`, `/blog`, `/collections/all`).
2. **Optional pre-flight** — fetch the URL once with `HEAD` to confirm it
   returns 200. If 4xx, ask the user to confirm the link.
3. **Build the payload** (see template). Defaults are tuned for product promo:
   high `density`, dynamic animation, captions ON, music ON.
4. **Call MCP tool `render_video`** with the payload below — returns `data.pid`.
   Then poll MCP tool `get_project_status` with that `pid` every 5–8 s until
   `data.status === "ready"`. Optionally call `export_video` for a freshly
   named mp4.
5. **Return** `{ pid, status, videoUrl, thumbnailUrl, durationSeconds, creditsUsed }`.

## `render_video` arguments

```json
{
  "workflow": "article-to-video",
  "source": {
    "url": "{PRODUCT_URL}",
    "scrapingPrompt": "Extract the product name, hero image, 3 key features, and price. Ignore reviews, related products, footer, and navigation."
  },
  "aspectRatio": "9:16",
  "voice":    { "enabled": true, "stability": 0.55, "speed": 1.05, "language": "en-US" },
  "captions": { "enabled": true, "position": "middle", "autoCrop": true },
  "music":    { "enabled": true, "syncWith": "beats", "trackName": "uplifting-pop" },
  "media": {
    "type": "stock-video",
    "density": "high",
    "animation": "dynamic",
    "quality": "pro",
    "imageModel": "good",
    "videoModel": "pro",
    "turnImagesIntoVideos": true,
    "applyStyleTransfer": false
  },
  "options": {
    "targetDuration": 35,
    "summarizationPreference": "summarize",
    "hasToGenerateCover": true,
    "coverTextType": "product-name",
    "soundEffects": true,
    "addStickers": false
  },
  "render": { "resolution": "1080p", "frameRate": 30 }
}
```

`scrapingPrompt` is the most important knob — it stops Revid from picking up
header/footer junk. Customize it per storefront if you find a recurring noise
pattern.

## Examples

- [`examples/shopify-aeropods.json`](examples/shopify-aeropods.json) —
  copy-paste body for `render_video` *(also a valid POST body for the direct
  HTTPS fallback)*.
- [`examples/run.sh`](examples/run.sh) — bash smoke test using the **direct
  HTTPS fallback** (`POST /api/public/v3/render` → `GET /status`). Useful when
  you don't have an MCP client at hand.

### Quick test

Call `render_video` with [`examples/shopify-aeropods.json`](examples/shopify-aeropods.json),
with `source.url` set to your product page
(`https://your-shop.myshopify.com/products/your-product`).

## Polling

Call `get_project_status` with the `pid` returned by `render_video`. Stop when
`data.status === "ready"`; fail when `data.status === "failed"`. Cadence: 5 s,
then 8 s once `progress > 30`. Full pseudocode:
[`revid-api-foundations` § Polling](../revid-api-foundations/SKILL.md#polling).

## Failure modes

| Symptom | Fix |
|---|---|
| `scrape failed` / 403 from the URL | Storefront blocks bots. Open the page in a real browser, copy the title + 3 bullet features + price into a script, and switch to [`revid-script-to-video`](../revid-script-to-video/SKILL.md). |
| Video shows wrong product image | Storefront serves SSR via JS only. Pass `media.useOnlyProvided: true` and `media.provided: [{ url: "<hero-image-url>", type: "image" }]` to force the right asset. |
| Voice sounds robotic | Increase `voice.stability` to `0.7` and pick a specific `voice.voiceId`. Default voice varies. |
| Duration overshoots target | Set `options.summarizationPreference: "summarize"` (already in the template) and lower `targetDuration`. |
| Captions cover product | `captions.position: "top"` (or `"bottom"`). |
| `ok: false`, `error: "insufficient_credits"` | Drop `media.quality` to `"standard"` or `render.resolution` to `"720p"`, or call `buy_credit_pack`. |

## See also

- [`revid-product-description-to-ad`](../revid-product-description-to-ad/SKILL.md)
  if you don't have a live URL.
- [`revid-script-with-custom-media`](../revid-script-with-custom-media/SKILL.md)
  if you want to control every visual.
- [`revid-api-foundations`](../revid-api-foundations/SKILL.md) for the contract.
