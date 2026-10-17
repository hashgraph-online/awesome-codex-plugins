# The Verge — Design Tokens (loopy-native)
> Category: brand-web-media · Signature: near-black canvas, hazard mint + ultraviolet, Manuka shout, rave-flyer story tiles

## Signature & atmosphere
The Verge feels like a Condé Nast magazine wired to a chiptune soundboard: a near-black page where acid-mint and ultraviolet behave like hazard tape, not brand wash. The recognizable idea is the StoryStream — a vertical feed of rounded, fully-saturated color-block tiles stacked on a timeline rail with mono-uppercase timestamps, topped by a Manuka wordmark at hero scale. There is no light mode; the dark canvas is the product, and color blocks do the work that shadows do elsewhere.

## Color (hex · --var · role)
- `#131313` `--bg` — canvas, warm near-black like a newsprint negative; `#FFFFFF` `--fg` — headlines/display
- `#3CFFD0` `--primary` — Jelly Mint hazard accent: CTA fill, link underlines, active borders, attention tiles
- `#5200FF` `--accent` — Verge Ultraviolet: secondary tiles, promo outlines (often at 0.9 alpha)
- `#949494` `--muted` — bylines, timestamps, credits; `#e9e9e9` muted button text
- `#FFFFFF` `--border` — hairline card outline on dark; `#309875` darker mint border; `#3d00bf` StoryStream rail
- `#2d2d2d` `--card` — secondary slate tile when a story isn't a color block; `#000000` text on mint/yellow/white tiles only
- `#3860be` link-hover (the one place blue appears); `#1eaedb` focus ring
- Note: mint and ultraviolet are hazard accents — never background washes, never gradient fades.

## Typography
- Stack: Manuka (heavy 900 display, 60px+ only) → PolySans (UI/body, 300/500/700) → PolySans Mono (ALL-CAPS labels only) → FK Roman Standard (serif, body/print moments)
- Hero/Display Manuka 107px / 900 / 0.80 / +1.07px · Secondary 90px / 900 / 0.80 · Tertiary 60px / 900 / 0.80
- Large headline PolySans 34px / 700 / 1.00 · Tile headline 24px / 700 / 1.00 · Compact 20px / 700
- Light eyebrow PolySans 19–20px / 300 / 1.20 / +1.9px (the "fashion whisper" against the Manuka shout)
- Body PolySans 16px / 500 / 1.60 · Eyebrow 12px / 400 / +1.8px uppercase
- Mono button label PolySans Mono 12px / 600 / 2.00 / +1.5px uppercase · Mono timestamp 11px / 500–600 / +1.1px uppercase
- Manuka is shout-only (bug below 60px); mono is always uppercase; substitute condensed faces (Anton/Oswald) need +0.10–0.15 line-height.

## Spacing, radius, depth, motion
- Base 8px; scale 2 · 4 · 6 · 8 · 10 · 12 · 16 · 20 · 24px; sections 32–64px, StoryStream items tight at 12–16px gaps
- Radius (eight discrete steps, deliberate): 2px inputs · 3–4px nested images · 20px pill cards/tiles · 24px feature/primary button · 30px promo button · 40px outlined CTA · 50% avatars
- Depth strategy: color-as-elevation. No real shadows — a tile stands out via a mint fill or a 1px hazard-color border. Only "shadow" tokens are 1px inset underlines and a faint `rgba(0,0,0,0.33) 0 0 0 1px` ring on stacked cards.
- Motion: ~150–180ms ease, color-only on hover (no lift, no scale).

## Components (key)
- Primary CTA (Jelly Mint Pill): bg `#3CFFD0` / black text PolySans Mono 12px·600 uppercase +1.5px / radius 24px / padding 10px 24px / hover bg `rgba(255,255,255,0.2)` + 1px `#c2c2c2` ring / focus bg `#1eaedb` white text
- StoryStream tile: `#131313` + 1px white border OR a saturated accent fill; radius 20px (24px feature); ~24–32px padding; mono uppercase timestamp on the left rail; hover shifts headline white → `#3860be` only.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: keep `#131313` everywhere (no light mode); use mint/ultraviolet as hazard buttons, 1px borders, and saturated tile fills.
- Don't: add `box-shadow` for elevation — the instinct to "lift" a card is wrong; use a 1px hazard border or a color-block fill.
- Don't: square the corners or use Manuka below 60px / for UI — it is strictly the display shout.
- Don't: let mint/ultraviolet become a soft background wash or gradient — solid blocks only.

## Example component prompts
- "StoryStream tile on `#131313`: 20px-radius rectangle, 1px solid white border, PolySans Mono 11px/600 uppercase +1.1px timestamp on the left rail, 12px mint uppercase kicker, 24px/700 white headline; hover shifts headline to `#3860be`, no lift."
- "Hero: 107px Manuka 900 headline at 0.80 line-height +1.07px tracking in white, a 20px PolySans weight-300 capitalized kicker +1.9px above it, on `#131313` with 64px vertical padding."
