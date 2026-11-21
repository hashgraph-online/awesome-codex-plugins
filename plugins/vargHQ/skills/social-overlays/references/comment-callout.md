# Video comment callout

A viewer comment shown over your footage in a YouTube-style layout: a plain comment, a pinned comment, a creator reply with a heart, or the comment sticker of a reply-to-comment Short. The "you asked, here's the answer" opener for comment-reply videos, FAQs and community proof. 9:16, 1:1, 16:9; about 6 s.

## How the pros do it
- Comment-reply videos are a native format on both big short-form platforms: TikTok shipped "reply to comments with video" in 2020, attaching the comment as a sticker so viewers see what is being answered, and reported 1.8B+ views on #replytocomments [10]. YouTube lets creators reply to comments with a Short; the comment appears as a sticker you can drag and pinch-resize, the commenter is notified and the Short appears under the comment [9].
- So the sticker is the hook: show the question in the first second and answer it right after, which matches TikTok's "proposition in the first 3 s" advice [3].
- Use real comments only, with the author's name blurred or with permission; never write fake comments as social proof in an ad (FTC rule on fake testimonials) [21].
- Layout grammar: avatar circle → handle + time-ago → text → action row (like count, reply). Pinned comments carry a "Pinned by @creator" line above; creator replies show the creator's avatar with a heart badge.
- Typeface: Roboto (OFL) matches the YouTube look closely [41]; colours from YouTube's brand page: Almost Black #212121, White, YouTube Red #FF0033 for the heart/accent [14].
- Size it for phones: comment text ≥ 34 px at 1080 width, max 3 lines (~34 characters/line); trim long comments with an ellipsis, never to change their meaning.
- Place inside the safe box: Shorts top 288 / bottom 672 / right 192 px [5], universal x 120–888, y 288–1248 [1][4]. The classic spot is upper-middle (y ≈ 360–520) so the speaker's face below stays free.
- YouTube's name, logo and UI design belong to YouTube; no logo on the card.

## Presets
| Preset | Look | Key values |
|---|---|---|
| `comment-callout.comment` | White card, avatar, @handle · 2d, text, thumbs-up count | card #FFFFFF, text #212121 (Almost Black), Roboto 500/400 |
| `comment-callout.pinned` | Same + pin icon "Pinned by @creator" line | pinned line 26 px @60% |
| `comment-callout.creator-reply` | Comment + indented creator reply with heart badge | heart #FF0033, reply indent 72 px |
| `comment-callout.reply-sticker` | Compact rounded sticker "Reply to @handle's comment" + text, slight tilt | sticker #FFFFFF radius 28 px, tilt −2°, Roboto 500 |
| `comment-callout.dark` | Dark-mode card for bright footage | card #212121 @92%, text #FFFFFF |

## Timing and numbers (6 s = 180 f)
- 0.00–0.40 s: card scales 0.92→1 + fade, `cubic-bezier(0.05,0.7,0.1,1)` (12 f) [26]; avatar pops 0.25 s `back.out(1.7)` [27].
- 0.30–(0.3 + n/30) s: optional typewriter at 30 chars/s (1 char per frame at 30 fps); otherwise text fades in at 0.35 s. Typewriter only for ≤ 90 characters.
- Like count ticks +1 at the end of typing; heart (creator reply) pops at +0.4 s, scale 0→1.2→1, 0.3 s.
- Hold until 5.6 s (≥ 2.5 s after text completes). Exit 0.25 s, `cubic-bezier(0.3,0,0.8,0.15)`.
- Sizes at 1080×1920: card 840 px wide, radius 32 px, padding 36 px, avatar 80 px, handle 28 px/500 @65%, text 36 px/400 line-height 1.35, action row 26 px. Reply sticker: 760 px wide, text 34 px. At 1920×1080: card 720 px wide, top-left third.
- Shadow 0 10px 30px rgba(0,0,0,.22) on light card over footage.

## Build it
1. HyperFrames: `yt-comment-card` block (avatar pop, username/time, per-character typewriter, likes row, image avatars or initials) [40].
2. Typewriter seek-safe: `text.slice(0, Math.floor((t - t0) * 30))` in an `onUpdate` that reads timeline time, or GSAP TextPlugin on a paused timeline; never `setInterval`.
3. Remotion: `const chars = Math.max(0, Math.floor((frame - 9)))`; slice text; spring for the card.
4. Data: `{handle, avatarUrl|initials, timeAgo, text, likes, pinnedBy?, creatorReply?{handle,text}, permission:true}`; blur handle if `permission` is false.

## Mistakes that look amateur
- Fake comment written by the brand → real comment with permission [21].
- 4-line comment in 22 px → trim to ≤ 3 lines at ≥ 34 px.
- Card covering the speaker's face → upper-middle at y 360–520, face below.
- Typewriter on a 200-character comment → fade the text in instead.
- YouTube logo on the card or "YouTube" in the ad headline → no marks.
- Card under the Shorts right rail → keep right edge ≤ 888 px [5].

## Sources
[1] TikTok safe-zone template · [3] TikTok creative best practices · [4] Meta Reels specs · [5] Google vertical safe zone · [9] YouTube Help: reply to comments with Shorts · [10] TikTok Newsroom: reply with video · [14] YouTube brand colours · [21] FTC rule · [26] Material 3 motion · [27] GSAP source · [40] HyperFrames registry · [41] Google Fonts licences.
