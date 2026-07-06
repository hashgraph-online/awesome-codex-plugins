# Airbnb — Design Tokens (loopy-native)
> Category: consumer · Signature: a travel magazine that happens to be an app — photos breathe, one coral pin

## Signature & atmosphere
The system places near-total faith in content. Photographs run at hero scale with gentle corner rounding, and the chrome retreats to a disciplined grayscale so listings carry the emotion. The single recognizable move is the coral pin (`#ff385c`) used with monastic scarcity — search submit, the active tab, the Reserve button, a wishlist heart — never decoration. Everything else is `#222222` ink on white, separated by hairline borders and whitespace rather than shadow.

## Color (hex · --var · role)
- `#ffffff` `--bg` — canvas; `#f7f7f7` `--surface` — footer/map subsurface tint
- `#222222` `--fg` — near-black ink (not `#000`); carries ~90% of all text
- `#ff385c` `--primary` — Rausch coral, primary CTA + active tab + heart; `#e00b41` `--primary-pressed` — pressed/gradient stop
- `#6a6a6a` `--muted` — secondary labels; `#929292` `--disabled-text`; `#dddddd` `--border` — the workhorse hairline divider
- `#c13515` `--destructive` — form errors; `#428bff` `--link-legal` — the one non-mono link color (terms/privacy)
- Tier accents (rare): `#92174d` Plus, `#460479` Luxe. Contrast: `--fg` on white ≈ 15:1; white on `--primary` ≈ 4.0:1 — keep CTA text ≥ 16px/500.

## Typography
- Stack: `"Airbnb Cereal VF"` (Circular, -apple-system, system-ui fallback). One family, many weights. Substitute: Inter at -0.01em on display sizes.
- Weights are 500 / 600 / 700 — no 400. The body weight is 500, which gives every paragraph confident density.
- Section 28/700/1.43 · Subsection 22/500/1.18/-0.44px · Listing title 20/600/1.20/-0.18px · Subtitle 16/600/1.25 · Body 16/500/1.25 · Button 16/500/1.25 · Caption 14/500/1.29 · Badge 11/600 uppercase (`salt`) · Superscript 8/700/0.32px (the only all-caps)
- Negative tracking on display only (-0.18 to -0.44px); body sits at 0.

## Spacing, radius, depth, motion
- Base 8px; scale 4 · 8 · 12 · 16 · 24 · 32 · 48 · 64; metadata rows stack at 4–8px (intentional density), cards gutter at 24px.
- Radius: tag 4px · button/dropdown 8px · listing photo & container 14px · large image/booking panel 20px · search pill 32px · circle 50% (every icon button, avatar, heart)
- Depth = layered low-opacity shadows, not single drops. Booking-panel signature: `rgba(0,0,0,.02) 0 0 0 1px, rgba(0,0,0,.04) 0 2px 6px, rgba(0,0,0,.1) 0 4px 8px`. Listing cards get zero shadow — they sit on white.
- Motion: press `transform: scale(0.92)`; focus ring `0 0 0 2px #222222`; circular buttons on photos add a `0 0 0 4px #fff` separator ring.

## Components (key)
- Primary CTA ("Reserve"): bg `#ff385c` / text `#ffffff` Cereal 500 16px / padding 14px 24px / radius 8px / no border. Active: scale 0.92 + 2px `#222` ring.
- Listing card: 4:3 photo at 14px radius, no shadow; below it stack three 4px-gap rows — city 16/600 `#222`, type 14/500 `#6a6a6a`, price 16/500 with a 14px "per night" suffix.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: reserve coral for one element per viewport; let photography carry the feeling.
- Don't: use the 400 weight — Cereal's "regular" is 500; 400 reads thin and off-brand.
- Don't: drop-shadow listing cards — separation is whitespace + the photo's own radius.
- Don't: round icon buttons to anything but 50%, or overlay text on photos (captions sit below).

## Example component prompts
- "Reserve button: `#ff385c` bg, white Cereal 500 16px, 14px×24px padding, 8px radius, no shadow; active adds scale(0.92) and a 2px `#222222` ring."
- "Sticky booking panel: white, 14px radius, 1px `#dddddd` border, the 3-layer shadow, 24px padding, 370px wide, pinned 120px below viewport — price headline, date picker, guest dropdown, coral CTA, 12px `#6a6a6a` 'You won't be charged yet'."
- "Listing card: 4:3 photo at 14px radius, no shadow; three 4px-gap rows — 16/600 `#222222` city, 14/500 `#6a6a6a` type, 16/500 price + 14px 'per night'."
