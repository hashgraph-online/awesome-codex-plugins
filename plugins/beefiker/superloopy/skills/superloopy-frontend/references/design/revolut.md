# Revolut — Design Tokens (loopy-native)
> Category: fintech/crypto · Signature: stadium-scale medium-weight type, universal pills, zero shadow

## Signature & atmosphere
Revolut feels like fintech printed on a billboard: headlines tower at 100px+ in a geometric grotesque, set at weight 500 with brutal negative tracking so they read at a glance like airport signage. The marketing surface is a disciplined near-black/white binary — the rich semantic palette is held back for the product UI. Every button is a full pill with roomy padding, and there are no shadows at all; depth is pure contrast and whitespace.

## Color (hex · --var · role)
- `#ffffff` `--bg` — light surface; `#191c1f` `--fg` — near-black text + dark surface + primary button
- `#f4f4f4` `--muted` / `--card` — secondary button + subtle surface
- `#494fdf` `--primary` — Revolut blue (`--rui-color-blue`); `#376cd5` `--accent` — link blue
- `#c9c9cd` `--border` — dividers (`--rui-color-grey-tone-20`)
- `#505a63` secondary text; `#8d969e` muted/tertiary text
- `#e23b4a` `--destructive` (danger); `#00a87e` success (teal); `#ec7e00` warning — semantic tokens, product-only
- Contrast note: `#191c1f` on `#ffffff` is near-maximal; reserve `#494fdf`/semantic hues for the product so marketing contrast stays a clean two-color system.

## Typography
- Stack: `"Aeonik Pro", sans-serif` display; `Inter, Arial, sans-serif` body/UI. No `"ss01"`-style features — the geometry carries it.
- Display-mega 136/500/1.00/-2.72px · Display-hero 80/500/1.00/-0.8px · H2 48/500/1.21/-0.48px · H3 40/500/1.20/-0.4px · Card-title 32/500/1.19/-0.32px · Feature 24/400/1.33/normal · Nav 20/500/1.40 · Body-lg 18/400/1.56/-0.09px · Body 16/400/1.50/+0.24px · Body-semibold 16/600/1.50/+0.16px
- Headings are weight 500 (never bold); body Inter carries POSITIVE tracking (+0.16 to +0.24px) — airy reading against compressed display.

## Spacing, radius, depth, motion
- Base 8px; scale 4 · 6 · 8 · 14 · 16 · 20 · 24 · 32 · 40 · 48 · 80 · 88 · 120. Section spacing 80-120px.
- Radius: 12 (nav/small) · 20 (cards) · 9999 (all buttons).
- Depth strategy: NONE. Zero shadows by design — depth from dark/light section contrast and whitespace. Focus ring `0 0 0 0.125rem`.
- Motion: hover = opacity 0.85 on pills; minimal transitions, GPU only.

## Components (key)
- Primary CTA: bg `#191c1f` / text `#ffffff` / padding 14px 32px / radius 9999px. Hover opacity 0.85; focus 0.125rem ring.
- Outlined pill: transparent / text `#191c1f` / `2px solid #191c1f` / 14px 32px / 9999px.
- Ghost-on-dark: `rgba(244,244,244,0.1)` bg / `#f4f4f4` text / `2px solid #f4f4f4` / pill.
- Card: `#f4f4f4` or white, radius 20px, no shadow, separated by generous gap.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: set every heading at weight 500 — authority comes from size + tracking, not bold.
- Do: make every button a full 9999px pill with 14px 32px padding; small tight buttons are wrong here.
- Don't: add shadows — the instinct to "lift" a card breaks the flat identity; use contrast/space instead.
- Don't: pour semantic blues/teals/pinks onto the marketing page — they belong to the product UI only.
- Don't: use bold (700) on Aeonik display — 500 with -2.72px tracking is the look.

## Example component prompts
- "Hero on `#ffffff`: headline 136px Aeonik Pro weight 500 line-height 1.00 letter-spacing -2.72px `#191c1f`; dark pill CTA `#191c1f` white text radius 9999px padding 14px 32px, hover opacity 0.85; outlined pill transparent `2px solid #191c1f`. No shadow."
- "Body block: Inter 16px weight 400 line-height 1.50 letter-spacing +0.24px `#505a63`; card `#f4f4f4` radius 20px, no shadow, 48px gap to next."
