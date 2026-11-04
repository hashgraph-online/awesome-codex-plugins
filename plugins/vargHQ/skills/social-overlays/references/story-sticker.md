# Story sticker tag

A Stories-style sticker over footage: an @mention pill, a location pin tag or a post-tag bubble on a product. Used in creator and UGC ads to credit a person, place or product in the native "story" idiom. 9:16 first, also 1:1/16:9; about 5 s.

## How the pros do it
- Treat it as an "inspired" sticker, not a copy: Meta requires permission for commercials and films that use Instagram's interface, forbids implying partnership and forbids modifying the Instagram name or using its logo in place of the word [17]. Use generic shapes, your own type and no glyphs.
- Only tag real people and places with consent; tagging a person you have no relationship with in an ad can read as an endorsement (FTC endorsement and fake-testimonial rules) [21][22].
- Keep it inside Reels' ad safe area (top 14%, bottom 35%, 6% sides) [4]; if cross-posting, the universal box x 120–888, y 288–1248 [1][5]. Stories UI also covers the top band, so the old "top-left mention" spot must move down to y ≥ 288.
- One sticker per beat; native stories rarely stack more than 2. Place it next to the subject it names (handle near the face, pin near the place, post tag touching the product) with a 24–40 px gap.
- Stickers in stories are hand-placed: a small tilt (−6° to +6°) and a slightly off-grid position read as native; perfect centring reads as an ad template.
- Pop like a sticker, not like UI: overshoot scale (`back.out`) is the native feel; settle in under 0.4 s [27].
- Text is short: a handle or a place name, 1 line, ≤ 24 characters; on-screen text speed limit is 5–10 words/s [3].
- Post-tag variant: a dot on the product with a small bubble label; the dot should sit on the item, the bubble above it, so it reads as "this thing".

## Presets
| Preset | Look | Key values |
|---|---|---|
| `story-sticker.mention` | White rounded pill, bold gradient-ink @handle | pill #FFFFFF, text gradient #F58529→#DD2A7B→#8134AF (generic, not a brand asset), Inter 800 44 px, tilt −4° |
| `story-sticker.location` | White pill, pin glyph (own icon), dark text | pill #FFFFFF, text #262626 (house), pin in accent colour, Inter 700 40 px |
| `story-sticker.post-tag` | Dot on product + dark bubble with product name and chevron | dot 18 px #FFFFFF with 6 px ring @40%, bubble #000000 @80%, Inter 600 32 px |
| `story-sticker.glass-mention` | Frosted translucent pill for busy footage | fill #FFFFFF @22%, blur 20 px, text #FFFFFF, Inter 800 |

## Timing and numbers (5 s = 150 f)
- In at 0.3 s: scale 0→1.08→1 with `back.out(1.7)` over 0.35 s (11 f), rotation from tilt−8° to tilt, `transform-origin` at the sticker centre [27].
- Hold ≥ 3.5 s. Optional "tap to see" pulse at 2.0 s: scale 1→1.04→1, 0.3 s, once.
- Out at 4.5 s: scale 1→0.9 + fade, 0.2 s (6 f), `cubic-bezier(0.3,0,0.8,0.15)` [26].
- Sizes at 1080×1920: pill height 84–96 px (≈4.6% of height), padding 28×36 px, radius = height/2 (mention) or 24 px (location). Post-tag bubble 64 px tall, 20 px above the dot.
- Drop shadow 0 6px 18px rgba(0,0,0,.25) so a white pill separates from bright footage.
- If the sticker tracks a moving subject, track with keyframes from a tracker or manual keys every 4–6 frames; never wall-clock.

## Build it
1. HyperFrames: start from `badge-pop` for the elastic pop and `lt-soft-pill` for the pill shape [40].
2. Gradient text: `background: linear-gradient(...)` + `-webkit-background-clip: text; color: transparent`. Render one test frame: some headless renderers need `-webkit-text-fill-color: transparent`.
3. GSAP: `tl.fromTo(sticker, {scale:0, rotation:tilt-8}, {scale:1, rotation:tilt, duration:0.35, ease:"back.out(1.7)"}, 0.3)`.
4. Remotion: `spring({frame: f-9, fps, config:{damping:12, stiffness:200}})` drives scale; rotation `interpolate` on the same progress.
5. Params: `kind`, `text`, `anchor {x,y}`, `tilt`, `platformSafeZone`.

## Mistakes that look amateur
- Using the real Instagram glyph or calling it an Instagram sticker in an ad without permission → generic look, no logo [17].
- Sticker in the top 14% or bottom 35% of a Reel → covered by UI [4].
- Three stickers popping at once → stagger 0.15 s or one per beat.
- Pixel-perfect centred sticker → small tilt and off-centre placement near the subject.
- Tagging a celebrity or brand you have no deal with → only consented tags [21][22].

## Sources
[1] TikTok safe-zone template · [3] TikTok creative best practices · [4] Meta Reels specs · [5] Google vertical safe zone · [17] Meta Instagram brand · [21] FTC rule · [22] FTC Disclosures 101 · [26] Material 3 motion · [27] GSAP source · [40] HyperFrames registry.
