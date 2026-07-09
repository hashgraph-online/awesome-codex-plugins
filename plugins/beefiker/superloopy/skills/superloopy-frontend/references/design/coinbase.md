# Coinbase — Design Tokens (loopy-native)
> Category: fintech/crypto · Signature: one true blue, fully-pill CTAs, light/dark section binary

## Signature & atmosphere
Coinbase trades on trust through restraint: a near-binary palette of white, near-black, and a single deep blue carries the whole identity. The recognizable idea is the fully rounded CTA — buttons are pills (56px radius, sometimes effectively infinite) that flip to a lighter blue on hover. Sections alternate hard between white and near-black panels, giving a calm, institutional rhythm with no decorative color.

## Color (hex · --var · role)
- `#ffffff` `--bg` — light surface; `#0a0b0d` `--fg` — text + dark-section background (near-black, not pure)
- `#0052ff` `--primary` — brand blue, links, CTA accent/borders (deep, saturated, functional only)
- `#578bfa` `--primary-hover` — button hover fill (lighter blue)
- `#0667d0` `--accent` — secondary link blue
- `#eef0f3` `--muted` / `--card` — cool blue-tinted secondary surface + button bg
- `#282b31` `--card-dark` — dark button/card surface inside dark sections
- `rgba(91,97,110,0.2)` `--border` — hairline card/divider border
- `--destructive` not brand-defined; use a conventional red only for true errors, never decoratively.
- Contrast note: `#0a0b0d` on `#ffffff` is maximal; white text on `#0052ff` clears AA — keep blue functional so contrast pairings stay predictable.

## Typography
- Stack: `CoinbaseDisplay` (hero only), `CoinbaseSans` (UI/headings/nav/buttons), `CoinbaseText` (body reading), `CoinbaseIcons` (icon font). Fallback `system-ui, sans-serif`.
- Display 80/400/1.00 · Display-2 64/400/1.00 · Display-3 52/400/1.00 · H2 36/400/1.11 · Card-title 32/400/1.13 · Feature 18/600/1.33 · Body 18/400/1.56 (CoinbaseText) · Body-sm 16/400/1.50 · Button 16/600/1.20/+0.16px · Caption 14/600-700/1.50 · Small 13/600
- Display weight is 400 — impact comes from size + 1.00 line-height, not bold. Some button labels run lowercase.

## Spacing, radius, depth, motion
- Base 8px; scale 4 · 5 · 6 · 8 · 10 · 12 · 16 · 20 · 24 · 32 · 48.
- Radius: 4-8 (links/small) · 12-16 (cards/menus) · 24-32 (feature) · 40 (XL) · 56 (CTA pill) · effectively-infinite for max-round.
- Depth strategy: borders + section contrast, minimal shadows. Depth is achieved by alternating white vs `#0a0b0d` panels, not elevation.
- Motion: simple color transition on hover (blue→`#578bfa`) ~150ms; focus `2px solid #0a0b0d` outline.

## Components (key)
- Primary CTA: pill, bg `#eef0f3` (light) or `#282b31` (dark) / text matching contrast / radius 56px / `1px solid` matching bg. Hover bg `#578bfa`; focus 2px black outline.
- Blue-bordered button: transparent bg, `1px solid #0052ff`, blue text, 56px radius.
- Section block: full-bleed white or `#0a0b0d`; headings in CoinbaseDisplay on light, white text on dark; blue used only for one accent link.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: keep blue strictly functional — links and CTA accents only.
- Do: round CTAs to 56px+ (full pill); sharp-cornered buttons read off-brand.
- Don't: scatter `#0052ff` as a decorative fill or background tint — the urge to "add brand color everywhere" breaks the trust palette.
- Don't: set hero headlines bold — weight 400 at 1.00 line-height is the move; reaching for 700 is the wrong instinct.
- Don't: blend white→dark sections with gradients — the cut between them should be hard.

## Example component prompts
- "Hero on `#ffffff`: headline 80px CoinbaseDisplay weight 400 line-height 1.00 color `#0a0b0d`; subtitle 18px/400 CoinbaseText; pill CTA bg `#eef0f3` radius 56px padding 12px 24px, hover bg `#578bfa` white text, focus 2px solid `#0a0b0d`."
- "Dark section `#0a0b0d`: 64px CoinbaseDisplay/400 white headline centered; one `#0052ff` accent link 16px/600 CoinbaseSans; dark cards `#282b31` radius 16px, `1px solid rgba(91,97,110,0.2)`."
