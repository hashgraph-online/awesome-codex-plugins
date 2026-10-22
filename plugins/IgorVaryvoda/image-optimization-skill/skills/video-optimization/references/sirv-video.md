# Sirv Video Reference

Sirv-specific video hosting, streaming, and embedding facts. Verify current behavior against the official docs before changing option names or limits:

- `https://sirv.com/help/articles/video-streaming/`
- `https://sirv.com/help/articles/convert-video-to-spin/`
- `https://sirv.com/help/articles/convert-spins-to-videos/`
- `https://sirv.com/help/articles/full-width-background-video/`

## Hosting & Streaming

- Upload any common format: MP4, MOV, WMV, AVI, AVCHD, MKV, WEBM, MPEG-2. Max upload size **512MB** (larger files won't generate streams).
- Sirv transcodes to **HLS adaptive streams** automatically: 1080p, 720p, 480p, 360p by default; 2160p, 1440p, 240p available on request.
- Streams use 2-second segments; the first segment can be preloaded for near-instant playback (~100-500KB).

## Embedding with Sirv Media Viewer

```html
<script src="https://scripts.sirv.com/sirvjs/v3/sirv.js?modules=video"></script>
<div class="Sirv" data-src="https://youraccount.sirv.com/videos/demo.mp4"></div>
```

Use the `?modules=video` module-limited script when the page only needs video. Set explicit dimensions or `aspect-ratio` on the container to prevent CLS.

### Key video options (`data-options` or global `SirvOptions`)

| Option | Purpose |
| --- | --- |
| `video.autoplay: true` | Autoplays muted (browser policy) |
| `video.loop: true` | Loop playback |
| `video.preload: true` | Preload first segment for instant start |
| `video.background: true` | Background mode: muted, looped, no controls |
| `video.controls.speed: true` | Playback speed control |
| `video.controls.quality: true` | Manual resolution selection |
| `video.quality.min / max` | Constrain the adaptive ladder (360-1080) |

### Thumbnails / posters

- Default thumbnail is auto-generated at one-third of duration.
- Pick a frame: `data-options="thumbnail: 11.8"` (seconds) or use a custom image URL: `data-options="thumbnail: https://.../poster.jpg"`.
- Thumbnail as an image URL: `video.mp4?thumbnail=300` (width px), with `&video.thumbPos=34.8` for a specific timestamp.
- For LCP-critical heroes, prefer a static optimized poster image you control.

### Other

- Sirv Media Viewer injects VideoObject JSON-LD for video SEO automatically.
- YouTube/Vimeo URLs can be dropped into SMV galleries as `data-src` items (see `../../sirv-media-viewer/SKILL.md`).
- Fullscreen iframe embed: append `?embed` to the video URL.

## Video ↔ Spin Conversion

**Video to spin** (turn a rotating-product video into an interactive 360 spin):
- UI: right-click the uploaded video → "Convert to spin"; choose duration, JPEG/PNG, and frame count (18/24/36/72/120/180/360 - 36 balances smoothness vs weight).
- API: `POST /v2/files/video2spin` (see `../../sirv-api/SKILL.md`). Hourly conversion limits by plan (e.g. Business 200/h, Enterprise 400/h; Free 0).
- Compress 300-512MB videos under 300MB first.

**Spin to video**: `POST /v2/files/spin2video` renders a spin as MP4 - useful for marketplaces and social that accept video but not spins.

For the spin side of these workflows, use `../../sirv-360-spin/SKILL.md`.
