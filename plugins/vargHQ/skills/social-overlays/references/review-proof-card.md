# Review proof card

A customer review or rating card over footage (app-store, local-business, review-platform or marketplace style, or a plain star badge) that supplies social proof in an ad or creator video. 9:16, 1:1, 16:9; about 5 s.

## How the pros do it
- **Only real reviews from the business's own customers.** The FTC rule (2024) bans fake reviews and testimonials, reviews by people who don't exist (including AI-generated), misrepresented experience, buying reviews, undisclosed insider reviews and suppressing negative ones; civil penalties apply to knowing violators [21]. Presets therefore take review text, rating, name and date as **inputs**, never placeholders that look real.
- Show the review's own date and star rating beside the quote; offline ads need a date stamp or review count; don't quote out of context; don't present one review's stars as the overall rating; don't show only 5-star reviews without saying so; ask reviewers' permission (Trustpilot's legal brand guidelines) [23].
- Platform marks: Trustpilot requires its name and logo with its reviews, "TrustScore" written next to the number, no altered brand assets and paid-plan eligibility [23]. Apple's App Store badge must not be animated or modified and needs ≥40 px on screen [24]. Use official assets for marks; animate the card, not the mark.
- Credibility is not 5.0: purchase likelihood peaks around 4.0–4.7 stars and drops near 5.0 ("too good to be true"); a verified-buyer label raised purchase odds by 15%; the first 5 reviews matter most (Spiegel Research Center) [25]. Prefer an honest 4.6 with a count over a lone 5-star quote.
- Lead with a specific outcome sentence from the review (what changed, a number, a time) and cut the rest with an ellipsis that keeps meaning [23].
- Readability: ≤ 20 words of quote on screen; at 5–10 words/s the card needs ≥ 2.5 s after it settles [3].
- Place in the universal 9:16 box (x 120–888, y 288–1248) [1][4][5]; the card is wide, so centre it horizontally and keep its bottom edge ≤ y 1248.
- If the person featured was paid or got free product, disclose in the video [22].

## Presets
| Preset | Look | Key values |
|---|---|---|
| `review-proof-card.app-store-style` | Light card, app icon, 5-star row filled to the real rating, title + quote, name · date | card #FFFFFF, stars house gold #FFB400, Inter 700/400, star sweep 0.6 s |
| `review-proof-card.local-review-style` | Avatar initial, name, stars, "x weeks ago", quote | card #FFFFFF, stars house #FBBC04, Roboto 500/400 |
| `review-proof-card.review-platform` | Official review-platform logo + stars asset + "TrustScore 4.6 · 1,203 reviews" | use the platform's official star and logo files unmodified [23] |
| `review-proof-card.marketplace-style` | Stars + "Verified Purchase" + bold headline + body | stars house #FFA41C, verified label house orange #C45500, Inter |
| `review-proof-card.rating-badge` | Compact pill: ★ 4.7 · 2,318 reviews | pill #000000 @70% or #FFFFFF, Inter 800, count-up 0.8 s |

(House colours are generic star golds, not platform assets; sample from official assets when a mark is shown.)

## Timing and numbers (5 s = 150 f)
- 0.00–0.45 s: card rises 56 px + fades, `cubic-bezier(0.05,0.7,0.1,1)` [26].
- 0.35–0.95 s: stars fill left→right over 0.6 s `power2.out`, partial last star preserved (4.6 → last star 60% filled); rating number counts in sync.
- 0.60 s: quote fades/slides in 12 px, 0.3 s; name · date row +0.1 s.
- Hold to 4.7 s (≥ 3 s of full card). Exit 0.25 s down + fade, `cubic-bezier(0.3,0,0.8,0.15)`.
- Sizes at 1080×1920: card 768×(auto, ~360–480) px (the universal safe-box width; ≤660 px if any part sits below y 840), radius 36 px, padding 44 px; stars 44 px with 6 px gap; quote 38–42 px/500, line-height 1.3, max 3 lines, ≤ 34 characters/line; name/date 28 px @60%. Shadow 0 12px 40px rgba(0,0,0,.25).
- 16:9: card 760 px wide at left third, vertical centre; 1:1: 860 px wide, centred, lower half.
- Rating badge: 72 px tall, star 36 px, text 34 px/800.
- Multiple reviews: max 3 in sequence, 1.8–2.5 s each, cross-fade 0.2 s; or a slow vertical marquee (see `photo-wall-loop`).

## Build it
1. HyperFrames: `star-rating-fill` (fractional sweep + synced count), `social-proof-card` (app-store close with stars + proof line + CTA), `store-badge-lockup` for badges [40].
2. Stars: two stacked rows (house grey #D1D1D6 base, gold top) with the top row clipped by `clip-path: inset(0 calc(100% - var(--p)) 0 0)`; tween `--p` from 0 to `rating/5*100%`.
3. Data contract: `{source, rating, count?, title?, quote, author, date, verified?, permission:true}`. Refuse to render if `permission` or `date` is missing (encodes [21][23]).
4. Remotion: `interpolate(frame, [10, 28], [0, rating/5], {extrapolateRight:'clamp', easing: Easing.out(Easing.quad)})` for fill.

## Mistakes that look amateur (or illegal)
- Invented or AI-written "reviews" → real, permissioned reviews only [21].
- Five gold stars on every card → show the real average and count; 4.x reads more believable [25].
- Quote with no date or source → name · date · rating beside the quote [23].
- Animated or recoloured platform logo/badge → official assets, static [23][24].
- 60-word quote in 2 s → trim to ≤ 20 words, hold ≥ 2.5 s [3].
- Star row with whole stars for 4.6 → fractional last star.

## Sources
[1] TikTok safe-zone template · [3] TikTok creative best practices · [4] Meta Reels specs · [5] Google vertical safe zone · [21] FTC fake reviews rule · [22] FTC Disclosures 101 · [23] Trustpilot legal brand guidelines · [24] Apple App Store marketing guidelines · [25] Spiegel Research Center · [26] Material 3 motion · [40] HyperFrames registry.
