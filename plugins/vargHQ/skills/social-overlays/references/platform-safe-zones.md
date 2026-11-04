# Platform safe zones and shared motion values (all social overlays)

Every template in this family sits on top of a 9:16 video that a platform will cover with its own UI. These are the published boxes, converted to a 1080×1920 canvas, plus the shared motion and legal rules. All platform names, logos and UI looks are trademarks of their owners (TikTok, Meta/Instagram, Google/YouTube, Snap, Twitch, X, Apple, Trustpilot). Mockups here are for recognisable reference only.

## Safe boxes at 1080×1920 (keep text, faces, buttons and logos inside)

| Platform (source) | Top clear | Bottom clear | Left | Right | Notes |
|---|---|---|---|---|---|
| TikTok In-Feed [1] | 240 px (12.5%) | 660 px (34.4%) | 120 px | 120 px | Official template is 720×1280: 160 top, 440 bottom, 80 sides, plus a 120-px right action rail from y=560 down. ×1.5 → rail is x 780–960 from **y 840** to the bottom |
| Instagram Reels ads [4] | 14% (≈269 px) | 35% (672 px) | 6% (≈65 px) | 6% (≈65 px) | Meta states it as percentages; Meta recommends a 1440×2560 master |
| YouTube Shorts / vertical ads [5] | 288 px | 672 px | 48 px | 192 px | Values printed on Google's own 1080×1920 safe-zone SVG |
| Snapchat Single Image/Video ads [6] | 150 px | 330 px (382 px with Offer Details, ~450 px in Collection ads) | — | — | Snap's help page renders with JS; we read the figures in Snap's indexed text. Check with the Ads Manager safe-zone toggle |

**Universal 9:16 box (post anywhere):** x 120–888, y 288–1248 (11.1%–82.2% of width, 15%–65% of height). Below y 840 (43.75%) also keep x ≤ 780 (72.2%) to clear TikTok's right rail. That leaves a 768×960 box; a CTA or sticker in the lower half of the video lives in x 120–780, y 840–1248.

Platforms publish safe zones for **ads** only; organic UI is similar but changes several times a year [7]. Re-check before a launch.

16:9 and 1:1: no platform publishes overlap boxes for in-feed landscape or square. House default: 5% margin (96 px at 1920×1080, 54 px at 1080×1080), and keep CTAs out of the bottom 15% of 16:9 where player controls and captions sit.

## Shared motion values

| Token | Value | Frames @30 fps | Source |
|---|---|---|---|
| Enter (emphasized decelerate) | `cubic-bezier(0.05, 0.7, 0.1, 1)` | — | Material 3 [26] |
| Exit (emphasized accelerate) | `cubic-bezier(0.3, 0, 0.8, 0.15)` | — | Material 3 [26] |
| Utility move | `cubic-bezier(0.2, 0, 0, 1)` | — | Material 3 [26] |
| Small UI enter | 250–350 ms | 8–11 | Material medium1–3 [26] |
| Card / banner enter | 400–500 ms | 12–15 | Material medium4–long2 [26] |
| Exit | 200–250 ms (~30–40% shorter than enter) | 6–8 | Material short4–medium1 [26] |
| Pop with overshoot | GSAP `back.out(1.7)` (default overshoot 1.70158) | — | GSAP source [27] |
| Springy pop | GSAP `elastic.out(1, 0.3)` (out default period 0.3) | — | GSAP source [27] |
| Remotion spring | default `{mass:1, damping:10, stiffness:100}` bounces; raise damping or set `overshootClamping:true` for no bounce; `durationInFrames` pins length | — | Remotion [30] |

Rule of thumb from Material: duration grows with the distance and area that moves [26]. Everything is driven by timeline time (GSAP paused timeline seeked by HyperFrames, or `useCurrentFrame()` in Remotion). No `Date.now()`, no `setInterval`, no unseeded `Math.random()`.

## Shared legal rules (apply to every preset)

- No fake reviews, testimonials or reviewers, including AI-generated ones; no fake follower/view counts used to look influential for a commercial purpose (FTC rule, 2024) [21].
- Paid creator content: the ad disclosure goes **in the video**, ideally on screen and spoken, next to the endorsement, in plain words such as "ad" or "sponsored"; repeat it during lives [22].
- Instagram: commercials and films that show Instagram's interface need Instagram's permission; never imply partnership [17]. Default to "inspired" generic stickers and cards, not pixel copies.
- Use people's real handles, comments and reviews only with permission; otherwise use clearly fictional names (Apple asks for fictional account data in screen content) [24].
