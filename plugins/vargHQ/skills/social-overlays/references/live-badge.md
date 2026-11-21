# LIVE badge and viewer count

A "LIVE" pill with a pulsing dot and a ticking viewer count in a corner, styled after Instagram Live, TikTok LIVE, Twitch or YouTube Live. Used for stream recaps, "we went live" promos, launch-day energy and stream clips cut for shorts. 9:16, 1:1, 16:9; about 6 s.

## How the pros do it
- Colour is the identity, so take it from the owner: YouTube Red #FF0033 with Almost Black #212121 and white are YouTube's primary brand colours [14]; Twitch tokens give live red #EB0400 and purple #9147FF [15]; TikTok's brand red is #FE2C55 (third-party token files) [16]. We found no published hex for Instagram's live pill; the preset uses a generic magenta→orange gradient and says so.
- The badge text must stay legible: white on #EB0400 measures 4.62:1 and passes for any size; white on #FF0033 (3.96:1) and #FE2C55 (3.68:1) pass only as large text (≥24 px, or ≥18.5 px bold) [42]. Keep the "LIVE" label ≥ 28 px bold at 1080 wide.
- The viewer count must not be fake when the video is an ad: buying or faking views/followers to look influential for a commercial purpose is banned by the FTC rule [21]. Use the real peak count, a round illustrative number with "example" in the brief, or no count.
- Abbreviate like the platforms: above 1,000 YouTube shows 3 significant figures, rounded down (12,345 → 12.3K) [13]. Use the same rule for viewer counts so numbers look native.
- Corner placement must respect the target feed: a vertical clip re-posted to TikTok loses the top 240 px [1], Shorts the top 288 px [5], Reels the top 14% [4]. Put the badge at y ≥ 300 in 9:16 even though real live apps place it higher. In 16:9 stream recaps, top-left with a 48 px margin.
- During a sponsored live, the ad disclosure must repeat periodically [22]; leave room for a small "Ad"/"Paid partnership" chip under the badge if the source stream was sponsored.
- Trademarks: the words and layouts are recognisable platform UI; do not add the platform logos and do not imply a partnership [17].

## Presets
| Preset | Look | Key values |
|---|---|---|
| `live-badge.instagram-style` | Gradient pill "LIVE" + eye icon count chip on dark glass | gradient #DD2A7B→#F58529 (generic), chip #000000 @45%, Inter 800 |
| `live-badge.tiktok-style` | Red/pink pill "LIVE" + count chip | pill #FE2C55, text #FFFFFF, TikTok Sans 700, chip #000000 @40% |
| `live-badge.twitch-style` | Square-cornered red "LIVE" + red-dot viewer count in white | pill #EB0400 radius 4 px, count #FFFFFF with dot #EB0400, Inter 700 |
| `live-badge.youtube-style` | Red rounded "LIVE" + "watching" count | pill #FF0033, text #FFFFFF, Roboto 500/700, count chip #212121 @80% |

## Timing and numbers (6 s = 180 f)
- In at 0.2 s: pill slides from x−24 px + fade, 0.3 s (9 f), `cubic-bezier(0.05,0.7,0.1,1)` [26]; count chip follows +0.1 s.
- Dot pulse: scale 1→1.35→1 and opacity 1→0.55→1, period 1.0 s, `sine.inOut`, driven by timeline time (`repeat` on the paused timeline, which HyperFrames seeks) [28].
- Count ticks: every 0.9–1.4 s (seeded pseudo-random from a fixed seed), +0.3%–2% per tick, digits roll 8 px up in 0.2 s with `power2.out`; use `font-variant-numeric: tabular-nums` so the chip does not jitter.
- Abbreviation: <1,000 exact; ≥1,000 → 3 significant figures rounded down (1.23K, 12.3K, 123K, 1.23M) [13].
- Out at 5.7 s: 0.2 s fade + x−16 px, `cubic-bezier(0.3,0,0.8,0.15)`.
- Sizes at 1080×1920: pill 52–60 px tall, padding 12×20 px, label 30 px/800 tracking +4%, dot 14 px; count chip same height. Position x = 120, y = 312 (9:16 safe). At 1920×1080: pill 44 px tall at (48, 48).

## Build it
1. HyperFrames: `badge-pop` for the entrance, `count-up` for number easing (switch to tick steps) [40].
2. Seeded tick list: precompute `ticks = [{t, value}]` from a seed (e.g. mulberry32(42)) at build time; render the value for the current time by finding the last tick with `t ≤ time`. Seek-safe by design.
3. Dot pulse: a sub-timeline `gsap.timeline({repeat: 5}).to(dot, {scale:1.35, opacity:0.55, duration:0.5, ease:"sine.inOut", yoyo:true, repeat:1})` nested in the main paused timeline.
4. Remotion: `const phase = (frame % 30) / 30; scale = 1 + 0.35*Math.sin(Math.PI*phase)`.
5. Params: `platform`, `viewers` (start value) or `viewerSeries`, `label`, `corner`, `safeZone`, `showCount`.

## Mistakes that look amateur
- Count ticking up in perfectly even steps or every frame → seeded irregular ticks every ~1 s.
- Proportional digits making the chip width wobble → tabular numerals.
- "1,234,567 watching" in a phone-native look → platforms abbreviate (1.23M) [13].
- Badge under TikTok's top bar after reposting → y ≥ 300 in 9:16 [1].
- Fake "84.2K watching" on an ad for a stream that never had it → real or clearly illustrative numbers [21].
- Dot pulse on wall clock (CSS animation without seek) → timeline-driven pulse.

## Sources
[1] TikTok safe-zone template · [4] Meta Reels specs · [5] Google vertical safe zone · [13] Rival IQ (YouTube rounding) · [14] YouTube brand colour · [15] Twitch tokens · [16] TikTok tokens · [17] Meta Instagram brand · [21] FTC rule · [22] FTC Disclosures 101 · [26] Material 3 motion · [28] GSAP eases · [40] HyperFrames registry · [42] WCAG 2.1 contrast.
