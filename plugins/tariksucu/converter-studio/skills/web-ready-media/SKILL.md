---
name: web-ready-media
description: Prepare images and videos for a website or app - convert photos to WebP or AVIF, resize them to sensible widths with responsive variants, strip camera and location data, and turn videos into small streaming-friendly MP4 (H.264, faststart) or WebM with a poster image. Use when the user wants faster pages, smaller images, "optimize images", a hero or background video, or media for a web project.
---

# Media for the web

Keep the originals. Write results next to them or into the folder the project serves assets from (`public/`, `static/`, `assets/`), and show the size before and after.

## Images

Defaults that suit most sites: longest side at most 2560 px, WebP at quality 80, no metadata. Transparency is kept by WebP and AVIF.

| Goal                       | Command                                                                                       |
| -------------------------- | --------------------------------------------------------------------------------------------- |
| One WebP, max 2560 px wide | `cwebp -q 80 -resize 2560 0 -metadata none in.jpg -o out.webp` (only when the image is wider) |
| WebP with ImageMagick      | `magick in.png -auto-orient -resize '2560x2560>' -strip -quality 80 out.webp`                 |
| AVIF (smaller, slower)     | `magick in.jpg -resize '2560x2560>' -strip -quality 55 out.avif`                              |
| Responsive widths          | repeat with `-resize 640x`, `1280x`, `1920x` → `name-640.webp`, `name-1280.webp`, …           |
| Remove location data only  | `magick in.jpg -strip out.jpg`                                                                |

Check what is installed first: `command -v cwebp magick avifenc`. For HEIC sources or when no tool is available, convert with the Converter Studio MCP tools (`convert` with `to: "webp"` or `"avif"`) and resize locally afterwards, or at https://converter.studio.

For responsive images, give the user the markup:

```html
<picture>
  <source
    type="image/avif"
    srcset="hero-640.avif 640w, hero-1280.avif 1280w, hero-1920.avif 1920w"
  />
  <img
    src="hero-1280.webp"
    srcset="hero-640.webp 640w, hero-1280.webp 1280w, hero-1920.webp 1920w"
    sizes="100vw"
    width="1920"
    height="1080"
    alt="…"
    loading="lazy"
    decoding="async"
  />
</picture>
```

Set `width` and `height` to the real aspect ratio. Use `loading="lazy"` for images below the fold only, not for the main image at the top of the page.

## Video

| Goal                                     | Command                                                                                                                                             |
| ---------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| MP4 that starts playing at once (≤1080p) | `ffmpeg -i in.mov -vf "scale='min(1920,iw)':-2" -c:v libx264 -crf 24 -preset slow -pix_fmt yuv420p -c:a aac -b:a 128k -movflags +faststart out.mp4` |
| Silent loop for a landscape hero         | `ffmpeg -i in.mov -an -vf "scale='min(1280,iw)':-2,fps=30" -c:v libx264 -crf 26 -preset slow -pix_fmt yuv420p -movflags +faststart hero.mp4`        |
| WebM alternative (VP9)                   | `ffmpeg -i in.mp4 -c:v libvpx-vp9 -crf 34 -b:v 0 -row-mt 1 -c:a libopus -b:a 96k out.webm`                                                          |
| Poster image (first second)              | `ffmpeg -ss 1 -i out.mp4 -frames:v 1 -q:v 3 poster.jpg`                                                                                             |

Markup for a background video:

```html
<video autoplay muted loop playsinline preload="metadata" poster="poster.jpg">
  <source src="hero.webm" type="video/webm" />
  <source src="hero.mp4" type="video/mp4" />
</video>
```

Without ffmpeg, the Converter Studio MCP tools convert to MP4 or WebM (`convert` with `to: "mp4"`); video is priced by its length, its frame size and the format made (WebM costs several times more than MP4), so say so before a long video and give the price the conversion shows.

## Report

List each output with its dimensions and size, and the saving in percent. Point out files that got bigger (rare, usually already-compressed small images) and keep the original for those.
