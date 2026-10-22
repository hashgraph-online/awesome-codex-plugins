# Sirv AI Studio REST API Reference

Use the REST API for code integrations: scripts, backends, Zapier/n8n-style automations. For conversational image processing prefer the MCP tools ([mcp-tools.md](mcp-tools.md)).

Base URL: `https://www.sirv.studio/api/zapier`

All requests require: `Authorization: Bearer $SIRV_STUDIO_KEY`. Keys start with `sk_live_`. Read the key from an environment variable; never commit it.

Verified against the service source (July 2026). Credit costs are per model — see [mcp-tools.md](mcp-tools.md) for the cost tables; they apply to both surfaces.

## Table of Contents

1. [Endpoint Overview](#endpoint-overview)
2. [Account](#account)
3. [Background Removal](#background-removal)
4. [Image Upscaling](#image-upscaling)
5. [Background Replacement](#background-replacement)
6. [Image-to-Image Transformation](#image-to-image-transformation)
7. [Image Generation](#image-generation)
8. [Video Generation](#video-generation)
9. [3D Model Generation](#3d-model-generation)
10. [Alt Text Generation](#alt-text-generation)
11. [File Upload](#file-upload)
12. [Batch Operations (Async)](#batch-operations-async)
13. [Rate Limits](#rate-limits)
14. [Code Examples](#code-examples)

## Endpoint Overview

All POST unless noted:

| Endpoint | Purpose |
|----------|---------|
| `GET /me` | Auth test; id, email, credits, tier |
| `/remove-bg` | Background removal |
| `/replace-bg` | Background replacement |
| `/object-removal` | Object removal with mask |
| `/upscale` | Upscaling |
| `/image-to-image` | Prompt-based transformation |
| `/generate` | Text-to-image |
| `/image-translation` | Translate text inside images |
| `/video-generation` | Text/image-to-video |
| `/image-to-3d` | Image to 3D model |
| `/alt-text` | Alt text generation |
| `/product-description` | Marketing copy |
| `/product-lifestyle` | Product in lifestyle scenes |
| `/virtual-try-on` | Garment on person |
| `/depth-map` | Depth map (free) |
| `/image-review` | Marketplace compliance check |
| `/upload` | File upload (multipart, max 10MB, free) |
| `/batch/remove-bg`, `/batch/upscale`, `/batch/alt-text` | Async batch jobs |
| `GET /batch/status/{jobId}` | Poll batch job |
| `/sirv/{file,folder,get-metadata,metadata,search,tags,upload}` | Sirv DAM operations |

## Account

```http
GET /me
```
Returns: `{id, email, credits, tier}`
Cost: FREE

## Background Removal

```http
POST /remove-bg
Content-Type: application/json

{
  "image_url": "https://example.com/product.jpg",
  "model": "birefnet"
}
```
Returns: `{id, image_url, credits_used}`

**Models:** `birefnet` (default), `birefnet-v2`, `bria`
**Also:** `operating_resolution` — `1024x1024` (default), `2048x2048`, `2304x2304`

## Image Upscaling

```http
POST /upscale
Content-Type: application/json

{
  "image_url": "https://example.com/image.jpg",
  "scale": 4,
  "model": "clarity"
}
```
Returns: `{id, image_url, credits_used}`

**Models:** `esrgan` (default, fast), `clarity` (AI-enhanced), `topaz` (premium), `seedvr`
**Scale:** 1-10, default 2 (clamped to each model's max)

## Background Replacement

```http
POST /replace-bg
Content-Type: application/json

{
  "image_url": "https://example.com/product.jpg",
  "prompt": "Modern kitchen counter with marble surface",
  "model": "flux-kontext"
}
```

**Models:** `bria`, `flux-kontext`, `nano-banana`

## Image-to-Image Transformation

```http
POST /image-to-image
Content-Type: application/json

{
  "image_url": "https://example.com/image.jpg",
  "prompt": "Transform to watercolor painting style",
  "strength": 0.7
}
```

**Strength:** 0-1 (how much to transform)

## Image Generation

```http
POST /generate
Content-Type: application/json

{
  "prompt": "Professional product photo of wireless headphones",
  "model": "nano-banana-2",
  "aspect_ratio": "1:1"
}
```
Returns: `{id, image_url, credits_used}`

**Models:** `nano-banana-2` (default), `nano-banana-2-lite`, `flux2`, `zimage`, `gemini`, `gemini-or`, `seedream`, `seedream-or`, `gpt-image-2`
**Aspect ratios:** `1:1`, `16:9`, `9:16`, `4:3`, `3:4`, `21:9`, plus named presets `square_hd`, `square`, `portrait_4_3`, `portrait_16_9`, `landscape_4_3` (default), `landscape_16_9`
**num_images:** 1-4, default 1 (cost multiplies)

## Video Generation

```http
POST /video-generation
Content-Type: application/json

{
  "prompt": "Product rotating on display stand",
  "image_url": "https://example.com/product.jpg",
  "model": "ltx",
  "duration": 5,
  "aspect_ratio": "16:9"
}
```

**Models:** `veo31`, `ltx`, `kling`. Cost is per second of output — see [mcp-tools.md](mcp-tools.md).

## 3D Model Generation

```http
POST /image-to-3d
Content-Type: application/json

{
  "image_url": "https://example.com/product.jpg",
  "model": "meshy",
  "topology": "quad",
  "enable_pbr": true
}
```
Returns: Multiple formats (glb, obj, fbx, usdz)

**Models and costs:** `meshy` 50, `meshy-multi` 25, `seed3d` 50, `trellis` 2, `trellis2` 30, `hunyuan3d` 25

## Alt Text Generation

```http
POST /alt-text
Content-Type: application/json

{
  "image_url": "https://example.com/image.jpg",
  "detail_level": "detailed-caption"
}
```
Cost: 1 credit

**Models:** `florence` (default), `gemini-flash`, `gemini-3-flash`
**Detail levels:** `caption`, `detailed-caption` (default), `more-detailed-caption`

## File Upload

```http
POST /upload
Content-Type: multipart/form-data

file: [binary data, max 10MB]
```
Cost: FREE

## Batch Operations (Async)

Available for remove-bg, upscale, and alt-text only:

```http
POST /batch/remove-bg
POST /batch/upscale
POST /batch/alt-text
Content-Type: application/json

{
  "images": [
    {"id": "1", "image_url": "https://example.com/img1.jpg"},
    {"id": "2", "image_url": "https://example.com/img2.jpg"}
  ],
  "model": "birefnet"
}
```

Batch POSTs are **asynchronous**: the job is queued and the response returns immediately:

```json
{
  "id": "...", "job_id": "...", "status": "queued", "total": 80,
  "estimated_credits": 120, "poll_url": "/api/zapier/batch/status/{jobId}"
}
```

Credits are deducted upfront (refunded if queueing fails). Poll until done:

```http
GET /batch/status/{jobId}
```
Returns `{status, total, completed, failed, pending, credits_used, credits_remaining, results, progress}`.

**Limits:** no fixed per-request cap; the max batch size is your plan's batch limit (Free plan cannot use batch endpoints at all — 403; plan limits in [platform.md](platform.md)). Over-limit requests return 403 `BATCH_LIMIT_EXCEEDED`.

## Rate Limits

Per-hour sliding window on write (processing) requests; reads (`/me`, `/batch/status/*`) have much higher separate limits.

| Plan | Requests/Hour (write) |
|------|---------------|
| Free | 300 |
| Core | 5,000 |
| Growth | 10,000 |
| Enterprise / Volume+ | 30,000 |
| Legacy: Starter 1,000 · Pro 3,000 · Team 5,000 · Business 15,000 · Business+ 20,000 · Scale 30,000 | |

## Code Examples

### JavaScript

```javascript
const SIRV_API = 'https://www.sirv.studio/api/zapier';
const API_KEY = process.env.SIRV_STUDIO_KEY;

async function removeBackground(imageUrl) {
  const response = await fetch(`${SIRV_API}/remove-bg`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      image_url: imageUrl,
      model: 'birefnet'
    })
  });
  return (await response.json()).image_url;
}

async function batchAltText(images) {
  const start = await fetch(`${SIRV_API}/batch/alt-text`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${API_KEY}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ images })
  }).then(r => r.json());

  while (true) {
    const job = await fetch(`${SIRV_API}/batch/status/${start.job_id}`, {
      headers: { 'Authorization': `Bearer ${API_KEY}` }
    }).then(r => r.json());
    if (job.status === 'completed' || job.status === 'failed') return job;
    await new Promise(r => setTimeout(r, 3000));
  }
}
```

### cURL

```bash
# Remove background
curl -X POST https://www.sirv.studio/api/zapier/remove-bg \
  -H "Authorization: Bearer $SIRV_STUDIO_KEY" \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://example.com/product.jpg", "model": "birefnet"}'

# Generate image
curl -X POST https://www.sirv.studio/api/zapier/generate \
  -H "Authorization: Bearer $SIRV_STUDIO_KEY" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Product photo of headphones", "model": "nano-banana-2", "aspect_ratio": "1:1"}'

# Check credits
curl https://www.sirv.studio/api/zapier/me \
  -H "Authorization: Bearer $SIRV_STUDIO_KEY"
```
