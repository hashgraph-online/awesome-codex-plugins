# Raycast — Design Tokens (loopy-native)
> Category: luxury-auto-tooling · Signature: obsidian instrument case — macOS-native depth, red as punctuation

## Signature & atmosphere
Raycast feels like the inside of a precision instrument: a near-black blue-tinted void (`#07080a`) that reads as a macOS app, not a web page. The recognizable idea is physical depth on a flat medium — multi-layer shadows with inset highlights make buttons and keycaps look pressed or raised, like glass on a dark desk. Raycast Red punctuates (the hero stripe, an error) rather than pervades, and body type carries unusual positive letter-spacing that keeps the dark surface airy and readable.

## Color (hex · --var · role)
- `#07080a` `--bg` — near-black blue-tinted canvas (NOT pure black — the cold blue tint is the feel); `#f9f9f9` `--fg` — near-white primary text
- `#FF6363` `--accent` — Raycast Red (`hsl(0,100%,69%)`); brand punctuation, danger states, hero stripes — not pervasive
- `#101111` `--surface` — elevated card surface; `#1b1c1e` `--surface-2` — badge/tag fills
- `#9c9c9d` `--muted` — link default / secondary nav; `#cecece` `--fg-soft` — secondary body; `#6a6b6c` `--placeholder` — disabled/placeholder
- `#252829` `--border` — standard card/divider edge (`hsl(195,5%,15%)`); cool grays only, never warm
- Interactive: `hsl(202,100%,67%)` `--info` (~`#55b3ff`, links/focus) · `hsl(151,59%,59%)` success · `hsl(43,100%,60%)` warning
- Keycap gradient `#121212` → `#0d0d0d`; warm glow `rgba(215,201,175,0.05)` behind featured elements

## Typography
- Stack: `Inter, "Inter Fallback", system-ui` everywhere; `"SF Pro Text"` for select macOS-native bits; `GeistMono, ui-monospace, Menlo` for code. OpenType `calt, kern, liga, ss03` enabled globally.
- Display Hero 64px / 600 / 1.10 / 0px (`liga 0, ss02, ss08`) · Section Display 56px / 400 / 1.17 / +0.2px · Section Heading 24px / 500 / +0.2px · Card Heading 22px / 400 / 1.15
- Body 16px / 500 / 1.60 / +0.2px · Button 16px / 600 / 1.15 / +0.3px · Nav 16px / 500 / +0.3px · Caption 14px / 500 / +0.2px · Code 14px GeistMono / 500 / +0.3px
- Body baseline is weight 500 (not 400) and tracking is positive (+0.2 to +0.4px) — both deliberate for dark-mode legibility.

## Spacing, radius, depth, motion
- Base 8px; scale 1 · 2 · 3 · 4 · 8 · 10 · 12 · 16 · 20 · 24 · 32 · 40. Section padding 80–120px vertical; card padding 16–32px; element gaps 8–16px.
- Radius: 6px workhorse (buttons/badges/tags) · 8px inputs · 12px cards/screenshots · 16–20px feature cards · 86px+ pill CTAs · 4–5px keycaps.
- Depth strategy: multi-layer macOS shadows (never single flat ones). Cards use a double-ring (`rgb(27,28,30) 0 0 0 1px` outer + `rgb(7,8,10) 0 0 0 1px inset`); buttons add an inset top highlight `rgba(255,255,255,0.1) 0 1px 0 0 inset`; keycaps stack 5 layers. Motion: hover is **opacity 0.6**, not color swap — the signature interaction.

## Components (key)
- Primary pill CTA: semi-transparent white bg `hsla(0,0%,100%,0.815)` / dark text `#18191a` / pill radius (86px) / inset highlight shadow. Hover → full white. Or transparent + white text variant.
- Feature card: bg `#101111` / `1px solid rgba(255,255,255,0.06)` / 12–16px radius / double-ring shadow. Hover brightens border opacity slightly.
- Keyboard keycap: gradient `#121212`→`#0d0d0d`, 4–6px radius, 5-layer shadow (inset top highlight + bottom dark) for a physical 3D cap; Inter 12px/600.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: keep the background `#07080a` (cold blue tint), use positive +0.2px tracking on body, set body baseline weight to 500, and pair every shadow with an inset companion.
- Don't: use pure black `#000000` for the canvas — the instinct to "go full black for a dark theme" produces a generic dark page; the blue tint is the identity.
- Don't: tighten letter-spacing on body text — the universal dark-UI reflex toward negative/neutral tracking makes Raycast type feel cramped; it deliberately goes airy.
- Don't: ship single-layer flat drop shadows or swap background color on hover — flat shadows lose the macOS-native press, and color-swap hovers break the opacity-0.6 pattern.

## Example component prompts
- "Hero on `#07080a`: 64px Inter 600/1.10 near-white `#f9f9f9` heading; semi-transparent white pill CTA `hsla(0,0%,100%,0.815)`, 86px radius, dark text `#18191a`, hover → full white."
- "Feature card: `#101111` bg, 1px solid `rgba(255,255,255,0.06)`, 16px radius, double-ring shadow (`rgb(27,28,30) 0 0 0 1px`), 22px Inter heading, `#9c9c9d` body, hover opacity 0.6."
- "Keycap row: gradient `#121212`→`#0d0d0d`, 4px radius, 5-layer shadow for physical depth, Inter 12px/600 text."
