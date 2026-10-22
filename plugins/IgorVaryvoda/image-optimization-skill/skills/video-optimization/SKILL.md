---
name: video-optimization
description: Expert guidance on video optimization for web performance. Use when adding, auditing, or improving video on websites - hero/background videos, product demo videos, autoplay loops, GIF-to-video conversion, HLS/adaptive streaming, video posters and thumbnails, lazy loading video, YouTube/Vimeo embed performance, video Core Web Vitals (LCP/CLS/INP), video SEO/schema, or Sirv video hosting and streaming. Covers MP4/WebM/HLS delivery, H.264/VP9/AV1 codec choice, preload strategies, muted autoplay rules, facades for third-party players, and video-to-spin workflows.
---

# Video Optimization Expert

## Default Workflow

1. Identify the role of each video: hero/background ambient loop, product demo, content/tutorial, testimonial, animated-GIF replacement, or third-party embed (YouTube/Vimeo).
2. Choose the delivery mechanism by role and length: short silent loops as progressive MP4/WebM, anything over ~30s or with quality tiers as HLS/adaptive streaming, platform-hosted content behind a click-to-load facade.
3. Fix the highest-impact path first: autoplay video competing with LCP, missing poster, unsized players causing CLS, heavy player JS, eager-loaded below-fold video, or multi-MB GIFs that should be video.
4. Keep source quality high and delivery cheap: upload a high-bitrate master to the host/CDN, let it transcode the ladder; never re-encode an already-compressed download.
5. Verify with evidence: network waterfall (what loads before first paint), poster/LCP element in DevTools, rendered player dimensions, and playback on a throttled mobile profile.

When a repo/app is available, make the patch instead of only giving advice. Prefer local framework conventions over generic snippets.

## Fast Audit Checklist

- **LCP:** Above-fold video has a `poster` (optimized image, not a video frame fetched late); the poster or a sibling image is the LCP candidate, not a spinner or black frame.
- **CLS:** Player/`<video>` has explicit dimensions or CSS `aspect-ratio` before media loads.
- **Autoplay:** Ambient video is `muted autoplay loop playsinline` with no controls; browsers block unmuted autoplay, so never rely on it.
- **Preload:** `preload="none"` + poster for below-fold or click-to-play; `preload="metadata"` for likely-played; only streamed first segments preload for hero video.
- **Weight:** No GIFs over ~500KB (convert to MP4/WebM); silent videos have the audio track stripped; bitrate matches display size.
- **Embeds:** YouTube/Vimeo below the fold load as a facade (thumbnail + play button), not a full iframe at page load.
- **Accessibility:** Content videos have captions/transcripts; ambient video respects `prefers-reduced-motion`; controls are keyboard reachable.
- **SEO:** Meaningful videos have VideoObject JSON-LD (some hosts, including Sirv, inject it automatically).

## Decision Matrix

| Situation | Preferred Action |
| --- | --- |
| Hero/background ambient loop | Short (5-15s) muted MP4 (H.264) + WebM source, `muted autoplay loop playsinline`, poster, `prefers-reduced-motion` fallback to the poster. |
| Animated GIF anywhere | Replace with `<video muted autoplay loop playsinline>` or animated WebP/AVIF for tiny clips; 10-50x smaller. |
| Product demo / content video | HLS via a video host/CDN (Sirv, Mux, Cloudflare Stream, self-hosted hls.js) with poster, controls, `preload="metadata"`. |
| Long-form or variable networks | Adaptive HLS ladder; never a single 1080p progressive MP4. |
| YouTube/Vimeo embed | Facade pattern (thumbnail + play button, swap to iframe on click); saves 0.5-1MB+ of third-party JS per embed. |
| Rotating product video | Consider converting to a 360 spin (`../sirv-360-spin/SKILL.md`) - lighter, interactive, no play button. |
| Existing Sirv account | Upload to Sirv; automatic HLS ladder + Sirv Media Viewer embed. Read [sirv-video.md](references/sirv-video.md). |
| Video is the LCP element | Ensure poster renders instantly (preload it if hero); or stream with a tiny preloaded first segment. |

## Codec & Format Defaults

| Use Case | Default |
| --- | --- |
| Universal compatibility | H.264 (AVC) MP4, High profile, AAC audio |
| Better compression, wide support | VP9 WebM or HEVC (Safari) as a second `<source>` |
| Best compression, modern targets | AV1 (check hardware decode on mobile before committing) |
| Silent loops | Strip audio track entirely (`ffmpeg -an`) - saves weight and enables autoplay reliably |
| Streaming | HLS with 2-4 rung ladder (e.g. 360p/480p/720p/1080p); hosts generate this automatically |

Quality starting points: H.264 CRF 21-25 (lower = better), VP9 CRF 30-34, AV1 CRF 28-34. For ambient background video, go aggressive (CRF 26-28 H.264) - it sits behind content.

## Core Patterns

### Background/ambient hero video

```html
<video class="hero-video" autoplay muted loop playsinline
       poster="hero-poster.jpg" preload="none"
       width="1920" height="1080" aria-hidden="true">
  <source src="hero.webm" type="video/webm">
  <source src="hero.mp4" type="video/mp4">
</video>
```

```css
@media (prefers-reduced-motion: reduce) {
  .hero-video { display: none; }
  .hero { background-image: url(hero-poster.jpg); }
}
```

Preload the poster (it is likely your LCP), not the video.

### GIF replacement

```html
<video autoplay muted loop playsinline width="480" height="270"
       aria-label="Description of the animation">
  <source src="clip.mp4" type="video/mp4">
</video>
```

### Click-to-load YouTube facade

Render a thumbnail (`https://i.ytimg.com/vi/VIDEO_ID/hqdefault.jpg`) with a play button; inject the iframe (with `autoplay=1`) only on click. Use an existing web component like `lite-youtube-embed` rather than hand-rolling when the project allows dependencies.

## When To Read References

- **Web delivery details:** encoding recipes (ffmpeg), HLS setup, lazy loading, embed facades, measurement: [web-video.md](references/web-video.md)
- **Sirv video:** upload formats, automatic HLS ladder, 512MB limit, SMV embed markup and `video.*` options, thumbnails/posters, video-to-spin: [sirv-video.md](references/sirv-video.md)

Sibling skills: `../image-optimization/SKILL.md` for posters/thumbnails as images, `../sirv-media-viewer/SKILL.md` for galleries mixing video with images/spins, `../sirv-360-spin/SKILL.md` for spin conversion, `../sirv-api/SKILL.md` for `video2spin`/`spin2video` jobs.

## Red Flags

- Autoplaying video without `muted` and expecting it to play.
- A hero `<video>` with no poster - users see a black box while segments load and LCP fires late.
- Serving one large progressive MP4 to all devices when the host could stream HLS.
- Full YouTube/Vimeo iframes loading at page load for below-fold embeds.
- Multi-MB animated GIFs.
- Lazy-loading logic that also lazy-loads the poster of an above-fold video.
- Shipping audio tracks in decorative videos.
- Re-encoding an already-lossy download as a "master".

## Verification

- Network waterfall: only the poster (and at most one small first segment) loads before interaction for hero video; nothing video-related loads for below-fold embeds until scroll/click.
- LCP element is the poster or an intentional image, and its time is within budget on throttled mobile.
- No layout shift when the player initializes (compare with DevTools CLS overlay).
- Playback works on iOS Safari (`playsinline`), Android Chrome, and desktop; muted loops actually autoplay.
- `prefers-reduced-motion` shows the static fallback.
- For HLS: quality switches under throttling instead of stalling.
