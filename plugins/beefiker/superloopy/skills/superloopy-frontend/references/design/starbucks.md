# Starbucks — Design Tokens (loopy-native)
> Category: consumer · Signature: warm cream café, four-tier green, full-pill buttons, espresso-dark bands

## Signature & atmosphere
Starbucks feels like clean café signage: a warm cream canvas the color of paper napkins and store walls, with the apron green showing up wherever a decision happens. The recognizable idea is the four-tier green system — not one "brand green" but four calibrated shades, each mapped to a job (heading, CTA, deep band, decorative). The page reads as a color-block rhythm — cream body bookended by espresso-dark green bands — and every button is a confident full pill that compresses on press.

## Color (hex · --var · role)
- `#f2f0eb` `--bg` — warm cream page canvas (never pure white); `#edebe9` `--bg-2` — ceramic off-white separator wash
- `rgba(0,0,0,0.87)` `--fg` — text on light (87% black, reads warmer than `#000`); `rgba(0,0,0,0.58)` `--muted` — secondary
- `#006241` `--primary` — Starbucks Green; h1/brand-dominant signal; `#00754a` `--accent` — brighter Green Accent, the CTA fill + floating order button
- `#1e3932` `--surface-dark` — House Green; feature bands and footer (espresso-dark); `#2b5148` decorative mid-green; `#d4e9e2` pale mint utility tint
- `#ffffff` `--card` — card / modal surface; `#f9f9f9` neutral-cool dropdown fill
- `#cba258` `--gold` — Rewards-status ceremony only (never a general accent); `#c82014` `--destructive`; `#fbbc05` warning
- On dark green: `#ffffff` text, `rgba(255,255,255,0.70)` secondary. Contrast: muted 58% black on cream ≈ 5.5:1 — body, not 12px.

## Typography
- Stack: `"SoDoSans", "Helvetica Neue", Helvetica, Arial, sans-serif` (proprietary; substitute Inter or Manrope). Localized swaps: serif `"Lander Tall", "Iowan Old Style", Georgia` on Rewards editorial headlines; script `"Kalam", cursive` for Careers cup-names only.
- Display 80px / 400–600 / 1.20 / -0.16px · Hero 45px / 400–600 / 1.20 · H1 24px / 600 / 1.50 (Starbucks Green) · H2 24px / 400 / 1.50 (text black) · Body-large 19px / 400 / 1.75 · Body 16px / 400 / 1.50 / -0.01em · Button 16px / 600 / 1.20 · Small 14px / 400–600
- Signature: tight negative tracking `-0.01em` / `-0.16px` everywhere gives SoDoSans its confident press; hierarchy comes from weight + color (600 green H1 vs 400 black H2 at the same 24px), not size.

## Spacing, radius, depth, motion
- Base 8px (rem scale anchored 1rem = 10px): 4 · 8 · 16 · 24 · 32 · 40 · 48 · 64; default gutter 16px, sections breathe at 40–64px with whitespace, not dividers.
- Radius: 12px cards/modals · 50px buttons (full pill, universal) · 50% circular icons + the floating order button.
- Depth = whisper-soft stacked low-alpha shadows, never one heavy drop: card `0 0 .5px rgba(0,0,0,.14), 0 1px 1px rgba(0,0,0,.24)`; nav triple-layer soft lift; floating circular CTA `0 0 6px rgba(0,0,0,.24), 0 8px 12px rgba(0,0,0,.14)`. No gradient system — surfaces are solid color-block.
- Motion: 200ms ease; `transform: scale(0.95)` on button active is the signature micro-interaction.

## Components (key)
- Primary CTA (full pill): bg `#00754a` / text `#fff` / 1px `#00754a` border / padding 7px 16px / radius 50px / label 16px/600/-0.01em / `:active scale(0.95)` / transition all 0.2s ease. Outlined variant: transparent fill, `#00754a` text + border. On dark-green bands, invert to white fill + green text.
- Floating order button ("Frap"): 56px circle, `#00754a` fill, white icon, radius 50%, fixed bottom-right, stacked shadow `0 0 6px rgba(0,0,0,.24), 0 8px 12px rgba(0,0,0,.14)`; ambient shadow fades to 0 on active.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: use the warm cream `#f2f0eb` canvas, not white; map the four greens to their roles (Green `#006241` heading, Accent `#00754a` CTA, House `#1e3932` band); keep `-0.01em` tracking; full-pill 50px buttons with `scale(0.95)` active; layer 2–3 low-alpha shadows.
- Don't: use pure white as the canvas — the warm cream temperature is load-bearing. Don't collapse the four greens into one — that flattens the brand. Don't use gold as a general accent — it's a Rewards-status signal only. Don't square the buttons or use a single heavy drop shadow. Don't separate H1/H2 by size — it's weight + color.

## Example component prompts
- "Primary Starbucks pill: `#00754a` fill, white label SoDoSans 16px/600/-0.01em, 1px `#00754a` border, radius 50px, padding 7px 16px; `:active scale(0.95)`, transition all .2s ease."
- "Dark-green feature band on `#1e3932`: white H2 24px/600/-0.16px, secondary copy `rgba(255,255,255,.70)`; CTA row of white-fill/green-text primary + white-outline secondary; 40/60 split, stacks below 768px."
- "Content card on cream `#f2f0eb`: white surface, radius 12px, shadow `0 0 .5px rgba(0,0,0,.14), 0 1px 1px rgba(0,0,0,.24)`; H1 24px/600 `#006241`, body 16px/400/1.50 in `rgba(0,0,0,.58)`."
