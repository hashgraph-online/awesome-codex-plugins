# ClickHouse — Design Tokens (loopy-native)
> Category: dev-tools · Signature: acid neon-volt on obsidian black, type heavy enough to feel like mass

## Signature & atmosphere
ClickHouse is a performance cockpit: acid yellow-green slashing across true black like a highlighter on a dark console. It screams speed before you read a word — extra-heavy Inter Black headlines have physical mass, and a single neon accent is the only chroma allowed to interrupt the void. The neon-on-black pairing is one of the highest-contrast in any tech brand, and that's the point: every CTA is impossible to miss.

## Color (hex · --var · role)
- `#000000` `--bg` — pure black (never dark gray as the page); `#ffffff` `--fg` — primary text
- `#141414` `--card` — button/elevated surface; `#faff69` `--primary` — Neon Volt, the sole chromatic accent (CTAs, accent borders, link hovers)
- `#166534` `--accent` — Forest Green secondary CTA (action hierarchy distinct from neon); `#14572f` — dark-forest border variant
- `#f4f692` `--active` — pale-yellow active/pressed text state; `#4f5100` — olive ghost-button border (neon's muted sibling)
- `rgba(65,65,65,0.8)` `--border` — charcoal containment (the workhorse depth mechanism); `#3a3a3a` — button hover bg
- `#a0a0a0` `--muted` — secondary/body text on black.
- Contrast: neon on black is extreme; `#a0a0a0` on black clears AA for body. Neon is never a body-text color.

## Typography
- Stack: `Inter` (display + body), `Basier` (feature-section headings — a subtle product-voice shift), `Inconsolata` (code).
- Display-mega 96px/900/1.0/0 · Hero 72px/700/1.0/0 · Feature 36px/600/1.3/0 (Basier) · Sub 24px/600–700/1.2/0
- Body-lg 18px/400–700/1.56/0 · Body 16px/400/1.5/0 · Uppercase-label 14px/600/1.43/letter-spacing 1.4px · Code 16px/600/1.5 (Inconsolata)
- Weight IS hierarchy: full spectrum 400/500/600/700/900. The 900 Black display weight is the weapon — most sites never touch it.

## Spacing, radius, depth, motion
- Base 8px; scale 6 · 8 · 12 · 16 · 20 · 24 · 32 · 40 · 48 · 64.
- Radius: 4px buttons/badges/code (sharp, database-precise) · 8px cards/containers · 9999px toggles only. Never round past 8px.
- Depth = charcoal borders + inset on press; shadows barely register on black. Card border `1px solid rgba(65,65,65,0.8)`. Inset `rgba(0,0,0,0.14) 0 4px 25px inset` for pressed states (the signature sunk effect). Highest emphasis = a Neon Volt `#faff69` border on featured/selected cards.
- Motion: 120–200ms ease; active text → pale yellow `#f4f692`.

## Components (key)
- Neon CTA: bg `#faff69` / text `#151515` / padding 0 16px / radius 4px / `1px solid #faff69`. Hover bg→dark `rgb(29,29,29)`; active text→`#f4f692`.
- Forest CTA ("Get Started"): bg `#166534` / text `#ffffff` / 12px 16px / 4px radius / `1px solid #141414`. Hover bg→`#3a3a3a`.
- Ghost button: transparent / white text / 0 32px / 4px radius / `1px solid #4f5100` (olive-tinted). Neon-highlighted card: dark card + `1px solid #faff69` border for the featured/selected state.

## Do / Don't (anti-convention)
- Do: stay on pure `#000000` and use Neon Volt strictly as accent/CTA/border — and reach for Inter 900 on the hero, the extreme weight IS the personality.
- Don't: substitute dark gray for the page background — the absolute-black canvas is what makes the neon detonate.
- Don't: fill large areas with neon or drop below weight 700 on display — neon is a slash, not a wash; light weight reads as a different, slower brand.
- Don't: lean on soft diffused shadows (invisible on black) — use charcoal borders and the inset-pressed effect for depth.

## Example component prompts
- "Hero on `#000000`: headline 96px Inter weight 900, line-height 1.0, white. Neon Volt CTA `#faff69` (dark `#151515` text, 4px radius, 0 16px padding) plus ghost button (transparent, `1px solid #4f5100`)."
- "Feature card on black: `1px solid rgba(65,65,65,0.8)`, 8px radius. Title 24px Inter 700, body 16px in `#a0a0a0`. Featured variant gets a `1px solid #faff69` neon border. Uppercase overline 14px/600 letter-spacing 1.4px in `#a0a0a0`."
