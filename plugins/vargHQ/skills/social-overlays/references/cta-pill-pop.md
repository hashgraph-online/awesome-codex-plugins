# CTA pill pop

A follow, shop or watch-next button that pops in over footage near the end of a short-form ad, UGC clip or creator video and tells the viewer the one next step. 9:16 first, also 1:1 and 16:9; 3–5 s on screen (template length 4 s).

## How the pros do it
- Structure the ad as hook → selling points → one clear CTA, and say what to do, think or feel; put the core proposition in the first 3 s, the hook within 6 s [3].
- Make the CTA name the exact action and destination ("Search Lovelee on the App Store", "Link in bio for the 3-pack"), not a vague "download"; an indie dev with 100k views and almost no installs traced it to a CTA viewers could not find [38].
- Write a content-specific CTA tied to the video's topic instead of a generic "learn more" [37]; the platform CTA button already says "Shop now"/"Learn more", so the on-video pill should add the reason [36].
- Test CTAs as a variable: make 2 CTA versions of a few videos, find the best video, then test more CTAs on it [36]. Build the pill so text and colour swap without re-animating.
- An early CTA is fine when the hook carries a deal: low hold rate is not a failure if people click out early [39]. Offer `timing: "early"` (right after the hook, ~3–6 s) and `timing: "end"` presets.
- Keep the pill inside the universal 9:16 box: lower half → x 120–780, y 840–1248 at 1080×1920; never in TikTok's bottom 660 px or right rail [1], Reels' bottom 35% [4] or Shorts' bottom 672 px / right 192 px [5].
- Text on screen at 5–10 words per second at most [3]; a CTA of 2–5 words then needs ≥1.5 s fully readable after the pop settles.
- Speak it and show it at the same moment; FTC notes viewers notice messages made in both audio and video, and some watch muted [22]. Meta and TikTok both push sound-on creative [3][4].
- If the creator is paid, the "ad" disclosure belongs in the video near the endorsement, not only in the caption [22]; reserve a small disclosure tag next to the pill.
- When the CTA is "Download on the App Store", use Apple's unmodified badge: one per video, never animated or angled, ≥40 px tall on screen, clear space ¼ of badge height [24]. Animate the pill around it, not the badge.

## Presets
| Preset | Look | Key values |
|---|---|---|
| `cta-pill-pop.floating-pill` | Solid brand pill, bold label, arrow, back-out pop | 0.35 s pop `back.out(1.7)`, scale 0.6→1, 96 px tall, radius 48 px, Inter 800 40 px |
| `cta-pill-pop.glass-button` | Frosted glass capsule over footage, white label | 0.45 s rise 40 px + fade, `cubic-bezier(0.05,0.7,0.1,1)`, blur 24 px, fill #FFFFFF @18%, 1.5 px white @40% stroke |
| `cta-pill-pop.early-deal` | Pill + small price/offer chip, appears right after the hook | in at 3.0 s, hold 2.5 s, chip staggers +0.12 s |
| `cta-pill-pop.end-tap` | End-card pill with a tap ripple and press | press scale 0.94 for 3 frames at +0.8 s, ripple 0→2.2× in 0.4 s, opacity 0.35→0 |

## Timing and numbers
- Template 4 s = 120 f: in 0–0.35 s (0–11 f), settle, tap/attention beat at 1.2 s (36 f), hold to 3.75 s, exit 0.25 s (8 f) with `cubic-bezier(0.3,0,0.8,0.15)` [26]. Exit is ~30% faster than entry.
- End timing: start the pill 3–4 s before the last frame so it is readable before the loop restarts; early timing: 3–6 s after start [3][39].
- Size at 1080×1920: height 88–104 px (4.6–5.4% of frame height), side padding 40 px, label 36–44 px, min width 360 px, max width 660 px (fits x 120–780). 16:9 at 1920×1080: height 72 px, label 32 px, bottom-right inside 5% margin and above the bottom 15%.
- Position default 9:16: centre x = 450, centre y = 1120 (58% of height).
- Colours: brand colour for fill; label contrast ≥4.5:1 for small text, ≥3:1 for large text (WCAG 1.4.3 [42]). Measured: white on #FE2C55 = 3.68:1, white on #FF0033 = 3.96:1 → only pass as large bold labels (≥40 px at 800 weight); white on #9147FF = 4.62:1 passes. Glass variant needs a 0.25–0.35 black scrim under the text when footage is bright.
- Sound: one short "pop"/"tick" SFX on the frame the scale crosses 1.0 (~frame 7), 6–10 dB under the voice (house default).

## Build it
1. Start from HyperFrames `cta-lockup` (action line + accent capsule + microcopy) or `cta-close`; for a store close use `social-proof-card` / `store-badge-lockup` [40]. For a tap, add `oversized-cursor` or a ripple div.
2. One paused GSAP timeline: `tl.from(pill, {scale:0.6, autoAlpha:0, duration:0.35, ease:"back.out(1.7)"}, t0)`; label `from {y:12, autoAlpha:0, duration:0.25}` at `t0+0.08`; arrow nudge `x:+8` yoyo once at `t0+1.2`.
3. Remotion: `spring({frame: frame - start, fps, config:{damping:14, stiffness:180}, durationInFrames: 12})` for scale; `interpolate` for opacity and exit.
4. Read the safe box from a `platform` param (`tiktok|reels|shorts|universal|landscape`) and clamp the pill rect to it.
5. Expose `label`, `sublabel`, `color`, `timing`, `disclosure` as variables so CTA tests are text swaps [36].

## Mistakes that look amateur
- Pill under TikTok's caption or right rail → clamp to x 120–780, y ≤ 1248 [1].
- "Download now" with no app name or destination → name the store and the search term [38].
- CTA on screen 0.8 s at the very end → ≥1.5 s settled, start 3–4 s before the end [3].
- Bouncing badge from Apple/Google → animate your pill, keep store badges static [24].
- Bouncy elastic on a luxury brand → use the glass preset with decelerate ease, no overshoot.
- Silent CTA in a voice-led ad → say the same words as the pill [22].

## Sources
[1] TikTok In-Feed safe-zone template · [3] TikTok creative best practices · [4] Meta Reels ad specs · [5] Google vertical safe zone · [22] FTC Disclosures 101 · [24] Apple App Store marketing guidelines · [26] Material 3 motion tokens · [27] GSAP source · [36] Barry Hott · [37] Dara Denney · [38] jack friks · [39] Motion creative analytics · [40] HyperFrames registry · [42] W3C WCAG 2.1 contrast minimum. Full entries in `../sources.md`.
