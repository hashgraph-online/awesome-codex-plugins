# Renault — Design Tokens (loopy-native)
> Category: luxury-auto-tooling · Signature: aurora gradients + one diamond-yellow CTA on sharp black/white

## Signature & atmosphere
Renault is a vibrant French showroom that breaks the German-and-Italian monochrome habit: vivid magenta-violet-teal aurora gradients wash behind the vehicles while the interface structure stays disciplined. The recognizable idea is energy-inside-discipline — color lives in the photography and one diamond-yellow CTA, but every button is a zero-radius rectangle and the type runs assertively bold. Light and dark sections alternate in a chessboard rhythm; electrification lives in darkness, tradition in light.

## Color (hex · --var · role)
- `#FFFFFF` `--bg` — light editorial surface; alternating `#000000` dark sections (`is-alternative-mode`)
- `#000000` `--fg` — true-black text on light (Renault uses pure black); `#FFFFFF` on dark
- `#EFDF00` `--primary` — Renault Yellow, super-primary CTA only — a signal, never a surface
- `#1883FD` `--accent` — Renault Blue, the single interaction color, link-hover only
- `#222222` `--surface-dark` — secondary dark surface; `#F2F2F2` `--surface-alt` light differentiation
- `#D9D9D6` `--muted` — warm gray, disabled / tertiary; `#D1D1D1` `--border` — input borders / separators
- Semantic: `#BE6464` error · `#8DC572` success. Gradient `--hero`: photographic magenta→violet→teal (not a CSS surface gradient). Contrast: yellow `#EFDF00` carries black text only (≈ contrast 16:1), never white.

## Typography
- Stack: `"NouvelR", sans-serif` for everything — one proprietary geometric family with a 28° "radical r" matching the diamond logo. No secondary face.
- Hero Title 56px / 700 / 0.95 / 0 (often UPPERCASE model names) · Section 40px / 700 / 0.95 · Card 32px / 700 / 0.95 · Subhead 24px / 700 / 0.95 · Body 14px / 400 / 1.40 · Button 14.4px / 700 / 1.00 / +0.144px · Nav 13px / 700 / 1.50
- Active weights: 400 (body), 700 (everything assertive). Bold-default headings; ultra-tight 0.95 line-height makes display blocks collide into a punchy, urgent texture.

## Spacing, radius, depth, motion
- Base 8px; scale 4 · 8 · 12 · 16 · 20 · 24 · 32 · 40 (button padding fixed at 10px 15px).
- Radius scale 0 · 2 · 3 · 4 · 50px — buttons are 0px (sharp pressed-metal panels); only inputs/chips get the 50px pill.
- Depth strategy: a richer 7-tier shadow set, but most surfaces are flat. Hover lift `rgba(0,0,0,0.2) 0 4px 8px`; floating panels go to `rgba(0,0,0,0.15) 0 40px 80px`. Decorative depth is the photographic hero aurora + card overlay `linear-gradient(rgba(0,0,0,0.6), transparent 40%)`. Motion clean, no blur on UI.

## Components (key)
- Super-primary CTA: bg `#EFDF00` / text `#000000` / radius 0px / padding 10px 15px / 1px `#EFDF00` border / min 46×46px / hover `#F8EB4C`. One per screen — more than one collapses the hierarchy.
- Primary (black): bg `#000000` / text `#FFFFFF` / radius 0px; inverts to white-on-dark with a 1px white border on dark sections.
- PromoCard: full-bleed photo, top overlay `linear-gradient(rgba(0,0,0,0.6), transparent 40%)`, 40px/700 white heading, 0px radius, no border — dark/light cards alternate.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: keep all buttons at 0px radius; reserve `#EFDF00` for exactly one super-primary CTA; set headings at 700 with 0.95 line-height; alternate black/white sections.
- Don't: round the buttons — the reflex to soften CTAs into pills erases the pressed-metal precision that is the structural brand marker (pills are inputs only).
- Don't: use Renault Yellow as a section background or repeat it across CTAs — the instinct to "use the brand color generously" turns a conversion signal into noise and breaks the hierarchy.
- Don't: soften headings to 400/500 for elegance — NouvelR Bold at 0.95 leading is the energetic voice; lighter weights read as off-brand and limp.

## Example component prompts
- "Hero on a full-viewport magenta→violet→teal aurora gradient: centered vehicle render, NouvelR 56px/700/0.95 white headline; a black 0px-radius 'Explore' primary and a transparent white-bordered 0px-radius ghost CTA."
- "PromoCard: full-bleed photo, top overlay `linear-gradient(rgba(0,0,0,0.6), transparent 40%)`, NouvelR 40px/700/0.95 white heading, one inverted white-bg 0px-radius button, 10px 15px padding."
- "Super-primary CTA: `#EFDF00` bg, `#000000` text, NouvelR 14.4px/700/+0.144px, 0px radius, 10px 15px padding, min 46×46px, hover `#F8EB4C` — exactly one per screen."
