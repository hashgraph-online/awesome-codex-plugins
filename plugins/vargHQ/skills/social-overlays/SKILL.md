---
name: social-overlays
description: >-
  Eleven conversion overlays for short-form ads, UGC and creator videos, with presets per platform:
  CTA pill, follow tap prompt, story sticker tag, LIVE badge with viewer count, notification drop,
  review proof card, story caption bar, photo wall loop, follower counter and goal bar, comment
  callout (reply-to-comment) and subscribe-and-bell nudge. Presets use one universal 9:16 safe box
  built from TikTok, Meta Reels, YouTube Shorts and Snap specs, CTA timing from creator analysts (ask
  after value, never in the intro), native number formats, contrast and motion tokens, plus the FTC
  rules: reviews, comments and counts come from real data only and paid content is disclosed. Use when
  an ad or creator video needs a call to action, a subscribe or follow ask, a review or comment on
  screen, a LIVE badge or a counter. NOT for fake reviews, fake follower counts or copying a
  platform's logo.
license: MIT
compatibility: >-
  HyperFrames 0.8 (npx hyperframes; brings Chrome, needs Node 22 and ffmpeg) or Remotion 4. No API
  key.
metadata:
  author: vargHQ
  version: "0.1.0"
  varg.cost.typical: "0 credits; renders locally"
  varg.runtime.typical: "minutes per template, mostly render time"
  varg.models: "none"
  varg.outputs: "mp4, webm or mov (alpha) from HyperFrames or Remotion"
  varg.presets: "11 templates, 46 presets"
---

# Social overlays: CTAs, follow prompts, reviews and live badges that convert

Eleven overlays that ask the viewer to do something, placed where no platform UI covers them and timed after the video has earned the ask. Reviews, comments and counts are always the person's real data.

## Gates

- **Real data only.** Reviews, comments, ratings, follower, subscriber and viewer counts must be real and the person's to use. Never generate them; the FTC's 2024 rule bans fake and AI-written reviews and fake social proof.
- **Disclose paid content** on screen and in the voice, near the endorsement.
- **Platform marks.** No platform logos on mockups; badges and buttons are generic look-alikes. Platform names and UI looks are their owners' trademarks.
- **Safe box.** Keep every overlay inside x 120-888, y 288-1248 on 1080x1920, and left of x 780 below y 840.
- **Free fonts only.** Every font in the presets is OFL or Apache. Swap in the person's brand font only if they have a license for video.
- **Seek-safe.** Every value is a function of timeline time; randomness is seeded by frame. No `Date.now()`, `requestAnimationFrame` or unseeded `Math.random()`.
- **No credits here.** These templates render locally for free. Generated footage, voice or music is the varg-ai skill: call `estimate_cost` and wait for the person's approval before any generation.

## Pick a template

11 templates, 46 presets. Each reference file has the same sections: how the pros do it (every rule cited), presets, timing and numbers, how to build it, mistakes that look amateur, sources. Each JSON file holds the same presets as machine-readable values.

Read [`references/platform-safe-zones.md`](references/platform-safe-zones.md) first: it holds the numbers every template here shares.

| Template | Use it for | Presets | Files |
|---|---|---|---|
| **Story caption bar** | Full-width translucent caption strip or big outlined text, Snapchat-story style. | Classic bar, Big text, Classic multi, Light bar | [`caption-bar-overlay.md`](references/caption-bar-overlay.md) · [`json`](assets/presets/caption-bar-overlay.json) |
| **Video comment callout** | A real viewer comment (plain, pinned, creator reply or reply sticker) over footage. | Comment, Pinned, Creator reply, Reply sticker, Dark | [`comment-callout.md`](references/comment-callout.md) · [`json`](assets/presets/comment-callout.json) |
| **CTA pill pop** | A follow / shop / watch-next button that pops in over footage and names one next step. | Floating pill, Glass button, Early deal, End tap | [`cta-pill-pop.md`](references/cta-pill-pop.md) · [`json`](assets/presets/cta-pill-pop.json) |
| **Follow tap prompt** | Creator card whose Follow button gets clicked or tapped and flips to Following. | TikTok-style, Instagram-style, Twitch-style, X-style | [`follow-tap-prompt.md`](references/follow-tap-prompt.md) · [`json`](assets/presets/follow-tap-prompt.json) |
| **LIVE badge and viewer count** | LIVE pill with pulsing dot and ticking viewer count in a corner. | Instagram-style, TikTok-style, Twitch-style, YouTube-style | [`live-badge.md`](references/live-badge.md) · [`json`](assets/presets/live-badge.json) |
| **Notification drop** | System-style notification banner or achievement toast that lands a beat. | iOS-style banner, Dark banner, Android-style, Achievement | [`notification-drop.md`](references/notification-drop.md) · [`json`](assets/presets/notification-drop.json) |
| **Photo wall loop** | Columns of photo cards scrolling at different speeds, seamless loop. | Three column, Opposing, Tilted, Landscape rows | [`photo-wall-loop.md`](references/photo-wall-loop.md) · [`json`](assets/presets/photo-wall-loop.json) |
| **Review proof card** | Real customer review or rating over footage as social proof. | App-store style, Local review style, Review-platform, Marketplace style, Rating badge | [`review-proof-card.md`](references/review-proof-card.md) · [`json`](assets/presets/review-proof-card.json) |
| **Story sticker tag** | Stories-style @mention, location or post-tag sticker over footage. | Mention, Location, Post tag, Glass mention | [`story-sticker.md`](references/story-sticker.md) · [`json`](assets/presets/story-sticker.json) |
| **Subscribe-and-bell nudge** | Cursor clicks Subscribe, then the bell, as a short reminder overlay. | Subscribe, Subscribe and bell, Highlight, Vertical | [`subscribe-nudge.md`](references/subscribe-nudge.md) · [`json`](assets/presets/subscribe-nudge.json) |
| **Follower counter and goal bar** | Subscriber/follower number rolls up to a milestone, or a goal bar fills. | Channel counter, Milestone pop, Goal bar, Stream goal | [`subscriber-counter.md`](references/subscriber-counter.md) · [`json`](assets/presets/subscriber-counter.json) |

## Workflow

1. **Match the request** to a template and one or two presets from the table. Say which and why in one line, and show the person the preset names with their one-line looks before building anything.
2. **Read the reference** for that template, after the shared file, and load its JSON. Take values from the JSON; do not re-guess them.
3. **Build it** the way the reference's "Build it" section says, starting from the named HyperFrames blocks or varg components where it names them. Drive every value from timeline time so any frame renders the same on a re-render.
4. **Fit it to the brand:** swap in the person's colors and fonts only where the reference allows, then re-check contrast and safe zones with the numbers in "Timing and numbers".
5. **Check a draft:** render stills at the key moments (entrance, hold, exit), go through "Mistakes that look amateur", and fix before the final render.


## Rules that hold for every template

1. Universal 9:16 box: x 120–888, y 288–1248 at 1080x1920, and x ≤ 780 below y 840 (TikTok rail). From TikTok's template, Meta Reels (14/35/6%), Google Shorts SVG (288/672/48/192), Snap (150/330).
2. Real data only: reviews, comments, follower/viewer counts are inputs with a permission flag, never generated (FTC 2024 fake-review rule).
3. Disclose paid content in the video, spoken and on screen, near the endorsement.
4. Ask after value: hook ≤6 s, proposition ≤3 s, CTA at the end or right after the payoff; intro subscribe asks hurt retention; early CTA only when the hook carries a deal.
5. Name the exact action, content-specific; test 2 CTA texts per video.
6. Enter cubic-bezier(0.05,0.7,0.1,1) 0.3–0.45 s; exit cubic-bezier(0.3,0,0.8,0.15) 0.2–0.25 s; pops back.out(1.7).
7. ≤5–10 words/s; contrast 4.5:1 (3:1 large bold); white on #FE2C55/#FF0033 only as large bold labels.
8. No platform logos on mockups; App Store badge never animated, ≥40 px; Trustpilot reviews need name + logo + date.
9. Native number formats: 3 significant figures rounded down (12.3K, 1.23M); tabular numerals.
10. One short SFX where the element settles, under the voice.

## Built from

TikTok / Google / Meta / YouTube / Apple primary docs; FTC; Trustpilot; Paddy Galloway (@PaddyG96); Spiegel Research Center; Barry Hott (@binghott); Dara Denney (@DenneyDara); Motion creative analytics; @YouTubeCreators; Nick Nimmin; Cody Wanner; jack friks (@jackfriks).

Every rule in the references cites its source by number. The full list, with links and what was taken from each, is in [`references/sources.md`](references/sources.md). Values marked as house defaults in a reference are our own starting points where no expert published a number.

## Related skills

- [ai-ugc-ad-video](../ai-ugc-ad-video/), [ecommerce-video-ads](../ecommerce-video-ads/): the ads these overlays go on.
- [ai-ad-compliance-check](../ai-ad-compliance-check/): check the finished ad's claims and disclosures.
- HyperFrames registry (`npx hyperframes catalog --query "…"`): about 450 ready-made blocks; the references name the ones to start from.
