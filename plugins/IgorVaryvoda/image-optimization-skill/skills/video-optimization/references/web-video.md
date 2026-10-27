# Web Video Delivery Reference

Encoding recipes, streaming setup, lazy loading, embed facades, and measurement for video on the web.

## Table of Contents

1. [Encoding Recipes (ffmpeg)](#encoding-recipes-ffmpeg)
2. [Progressive vs Adaptive Streaming](#progressive-vs-adaptive-streaming)
3. [Preload and Lazy Loading](#preload-and-lazy-loading)
4. [Posters and LCP](#posters-and-lcp)
5. [Third-Party Embed Facades](#third-party-embed-facades)
6. [Accessibility](#accessibility)
7. [Video SEO](#video-seo)
8. [Measurement](#measurement)

## Encoding Recipes (ffmpeg)

### Silent background loop (H.264 + WebM pair)

```bash
# MP4 (universal) - strip audio, aggressive quality, faststart for instant playback
ffmpeg -i master.mov -an -c:v libx264 -crf 26 -preset slow \
  -vf "scale=1920:-2" -movflags +faststart hero.mp4

# WebM (better compression where supported)
ffmpeg -i master.mov -an -c:v libvpx-vp9 -crf 33 -b:v 0 \
  -vf "scale=1920:-2" hero.webm
```

### GIF to video

```bash
ffmpeg -i clip.gif -an -c:v libx264 -crf 23 -preset slow \
  -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" -movflags +faststart clip.mp4
```

(The scale filter forces even dimensions, which H.264 requires.)

### Content video with audio

```bash
ffmpeg -i master.mov -c:v libx264 -crf 22 -preset slow \
  -c:a aac -b:a 128k -movflags +faststart demo.mp4
```

### Poster frame extraction

```bash
ffmpeg -i demo.mp4 -ss 00:00:02 -frames:v 1 -q:v 3 poster.jpg
```

Then optimize the poster like any hero image (resize, WebP/AVIF, preload if above-fold).

### Notes

- `-movflags +faststart` moves the moov atom to the front so playback starts before full download - mandatory for progressive MP4.
- `-an` strips audio; a silent track can add 10-20% weight and complicates autoplay.
- Two-pass encoding (`-b:v` with `-pass 1/2`) beats CRF only when you must hit an exact size budget.
- AV1 (`libaom-av1` or `libsvtav1`): best compression, slow encode; check that target mobile devices hardware-decode AV1 before making it the only source.

## Progressive vs Adaptive Streaming

**Progressive MP4/WebM** - one file, byte-range seeking. Right for clips under ~30s, ambient loops, GIF replacements. Wrong for long content: everyone downloads the same bitrate.

**HLS (adaptive)** - playlist (`.m3u8`) + short segments at multiple resolutions; player picks the rung per connection. Right for demos, tutorials, anything over ~30s, variable networks. Hosts (Sirv, Mux, Cloudflare Stream, Bunny) generate the ladder automatically; self-hosting requires transcoding each rung + packaging.

Browser support: Safari plays HLS natively; Chrome/Firefox/Edge need `hls.js` (attach MediaSource to the `<video>`). Every hosted player does this for you.

A typical ladder: 1080p / 720p / 480p / 360p, 2-second segments. First segment preloaded gives near-instant start at ~100-500KB.

## Preload and Lazy Loading

| Video role | `preload` | Notes |
| --- | --- | --- |
| Hero with autoplay | host-managed / `auto` first segment only | Poster must render first; stream, don't download the file |
| Above-fold click-to-play | `metadata` | Duration/dimensions available, no media data |
| Below-fold anything | `none` + poster | Zero media bytes until interaction or near-viewport |

`<video>` has no native `loading="lazy"`. Lazy-load below-fold video with IntersectionObserver: leave `src`/`<source>` off (or `preload="none"`) until the element nears the viewport, then set sources and `load()`. Never defer the poster of anything above the fold.

Pause off-screen autoplay loops (IntersectionObserver + `video.pause()`) - saves battery/CPU and INP headroom.

## Posters and LCP

- The `poster` image is an LCP candidate; an autoplaying video's first painted frame also counts. A missing poster usually means LCP waits for video data.
- Treat the poster as a hero image: right-sized, WebP/AVIF via CDN, `<link rel="preload" as="image">` when it is the LCP.
- Do not use `?thumbnail`-style dynamically-extracted frames as the hero poster unless they are cached and fast; a static optimized image is safer.
- Black-frame posters: extract from a representative timestamp, not frame 0 (often black/fade-in).

## Third-Party Embed Facades

A YouTube iframe pulls ~0.5-1MB+ of JS/CSS and creates long tasks - per embed, before anyone presses play.

Facade pattern:
1. Render the video thumbnail (`https://i.ytimg.com/vi/VIDEO_ID/hqdefault.jpg`, or `maxresdefault.jpg` when available) with a play button overlay.
2. On click, replace with the real iframe using `?autoplay=1`.
3. Optionally `<link rel="preconnect" href="https://www.youtube-nocookie.com">` on hover/first interaction.

Prefer maintained components (`lite-youtube-embed`, `lite-vimeo-embed`) over hand-rolled facades when dependencies are acceptable. Use `youtube-nocookie.com` for consent-sensitive sites.

## Accessibility

- Content videos: captions (`<track kind="captions">` or host-side), transcripts for tutorials.
- Ambient video: `aria-hidden="true"`, no keyboard trap, and a `prefers-reduced-motion` fallback that hides or pauses it.
- Never remove controls from content videos; only ambient loops go controls-free.
- Autoplaying content with sound is both blocked by browsers and an accessibility failure - do not fight the block.

## Video SEO

Meaningful videos get `VideoObject` JSON-LD: `name`, `description`, `thumbnailUrl`, `uploadDate`, `duration`, `contentUrl`/`embedUrl`. Some hosts (including Sirv Media Viewer) inject this automatically - verify before adding a duplicate by hand. Provide a video sitemap for large libraries.

## Measurement

- **Lighthouse/PageSpeed**: flags GIFs that should be video, offscreen media, and LCP issues.
- **DevTools Performance panel**: check what the video pipeline does before first paint; look for long tasks from player JS.
- **Network panel**: filter Media - verify below-fold videos transfer 0 bytes at load, and HLS starts with one segment, not five.
- **WebPageTest**: filmstrip shows whether the poster or a black box renders; test on 4G profiles.
- **Chrome UX Report / RUM**: watch LCP and INP on pages before/after adding video.
