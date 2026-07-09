# Nike — Design Tokens (loopy-native)
> Category: brand-web-media · Signature: monochrome UI, stadium-scale uppercase type, product is the only color

## Signature & atmosphere
Nike reads like a sports magazine cut with the discipline of Swiss typography: the interface drains itself to black, white, and grey so that one thing — the product photo — carries every drop of color. The recognizable idea is the scoreboard headline: condensed uppercase display crushed to a 0.90 line-height, punching through full-bleed imagery like a chant. Restraint is the trick — the loudest pages on the internet feel minimal because the chrome refuses to compete.

## Color (hex · --var · role)
- `#FFFFFF` `--bg` — page canvas, card surface; `#111111` `--fg` — text and headings (soft-black, never pure `#000`)
- `#111111` `--primary` — primary button fill, nav text; on white this is the maximum-contrast pairing Nike deliberately pushes
- `#707072` `--muted` — secondary copy, prices, metadata, hover text
- `#CACACB` `--border` — input borders, dividers; `#111111` `--border-active` — focused/active border
- `#F5F5F5` `--card` — input fill, image placeholder, loading skeleton; `#FAFAFA` lightest surface tier
- `#D30005` `--destructive` — errors, sale urgency (the only red allowed in chrome)
- accents (functional only): `#007D48` success, `#1151FF` link, `rgba(39,93,197,1)` focus ring
- Note: color in the UI is reserved for semantics. Brand vibrancy comes from merchandise photography, never from interface panels.

## Typography
- Stack: Nike Futura ND (condensed display, uppercase only) → Helvetica Now Display/Text for everything else; fallbacks Helvetica, Arial
- Display 96px / 500 / 0.90 / uppercase — Futura, hero only
- H1 32px / 500 / 1.20 · H2 24px / 500 / 1.20 — Helvetica Now Display
- Body 16px / 400 / 1.75 · Body-emphasis 16px / 500 / 1.75 — generous leading for browsing comfort
- Label / Button 14–16px / 500 / 1.50 · Caption 12px / 500 / 1.50
- Weight 500 is the workhorse for all interactive text — assertive without shouting.

## Spacing, radius, depth, motion
- Base 8px (4px for icon-tight gaps); scale 4 · 8 · 12 · 16 · 24 · 32 · 48 · 64 · 80
- Radius: 0 on imagery (edge-to-edge), 8px form inputs, 20px UI containers, 24px search, 30px buttons/pills, 50% circular
- Depth strategy: tonal-shift only. No card shadows, no hover lift. State lives in grey steps `#F5F5F5 → #E5E5E5 → #CACACB → #707072`. Only "shadow" is a 1px inset divider.
- Motion: 200ms ease on background/opacity (image swap, button color); transform/opacity only.

## Components (key)
- Primary CTA: bg `#111111` / text `#FFFFFF` 16px·500 / padding 12px 24px / radius 30px / no border / hover bg `#707072` / active scale ripple / focus 2px ring `rgba(39,93,197,1)`
- Product card: square image at radius 0, no border, no shadow; title 16px·500 `#111111` and price 14px·500 below with a 12px gap; grid gaps stay tight (4–12px) for an abundant-aisle feel; hover swaps to the secondary photo, no lift.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: keep `#111111` not `#000`; keep the whole interface greyscale and let the shoe be the color.
- Don't: add card shadows or hover-lift — the instinct to "elevate cards" is wrong here; Nike's elevation is flat and works through grey.
- Don't: round product imagery or shrink Futura below 24px — display type is uppercase, huge, or absent.
- Don't: drop interactive text to weight 400 — buttons and links are always 500.

## Example component prompts
- "Hero on `#FFFFFF`: full-bleed edge-to-edge photo at radius 0, dark gradient scrim, a 96px/500 uppercase condensed headline at 0.90 line-height, and a `#111111` pill CTA (radius 30px, 12px 24px) with white 16px/500 label."
- "3-column product grid, square images radius 0, 4px gap, title 16px/500 `#111111`, price 14px/500, secondary text `#707072`, no shadow, hover swaps to side-view image."
