# PostHog — Design Tokens (loopy-native)
> Category: dev-tools · Signature: warm sage-cream wiki energy with a hidden orange that only appears on hover

## Signature & atmosphere
PostHog feels like a scrappy startup's internal wiki that escaped into production — warm, irreverent, deliberately anti-corporate. The background is a sage-tinted cream, not crisp white or a dark void, giving every surface a handmade paper quality, and the palette leans earthy olive-green instead of SaaS blue. The signature move is interaction: brand orange is invisible at rest and flashes into text on hover, a small delight that rewards touching things.

## Color (hex · --var · role)
- `#fdfdf8` `--bg` — warm parchment (never pure white — the sage-cream tint is foundational); `#4d4f46` `--fg` — olive-ink primary text
- `#23251d` `--heading` — deep-olive near-black for headings/links; `#1e1f23` `--primary` — dark CTA fill
- `#F54E00` `--accent` — PostHog orange, HOVER-ONLY text flash; `#F7A501` `--accent-2` — amber-gold hover on dark buttons
- `#eeefe9` `--surface` — input/secondary surface; `#e5e7e0` `--card` — sage button surface; `#d4c9b8` — warm-tan featured
- `#bfc1b7` `--border` — sage-tinted border (warmth runs through every edge); `#9ea096` `--muted` — sage placeholder; `#65675e` — secondary text
- `#3b82f6` `--focus` — the only blue, accessibility focus ring at 50% opacity.
- Contrast: olive-ink `#4d4f46` on parchment passes AA; `#65675e` for secondary, `#9ea096` placeholder-only.

## Typography
- Stack: `IBM Plex Sans Variable` (display + body — technical credibility deployed playfully), `Source Code Pro` / system mono for code.
- Display 30px/800/1.2/-0.75px · Section 36px/700/1.5/0 · Feature 24px/700/1.33/0 · Sub 20px/700/1.4/-0.5px
- Body 16px/400/1.5/0 · Body-relaxed 15px/400/1.71/0 · Nav 15px/600/1.5/0 · Label-uppercase 18px/700/1.5 · Code 14px/500/1.43
- Bold headings dominate (700–800); body line-heights run generous 1.5–1.71 for a content-heavy editorial read. Tracking tightens on display only.

## Spacing, radius, depth, motion
- Base 8px; scale 4 · 8 · 12 · 16 · 24 · 32. Section gaps a compact 32–48px (it's information-dense by design); card padding a tight 4–12px.
- Radius: 4px most UI (buttons/inputs/menus) · 6px larger buttons/cards · 9999px pill badges. Keep corners small and functional.
- Depth = borders + surface-shifts, almost no shadow. Layered surfaces `#fdfdf8 → #eeefe9 → #e5e7e0` create depth; one single dramatic shadow `0 25px 50px -12px rgba(0,0,0,0.25)` reserved for modals/dropdowns only. No gradients, no glassmorphism.
- Motion: opacity-based — dark buttons drop to 0.7 opacity on hover, ~0.8 + slight scale on active.

## Components (key)
- Primary CTA (dark): bg `#1e1f23` / text `#ffffff` / radius 6px / padding 10px 12px. Hover: opacity 0.7 + amber-gold (`#F7A501`) text. Active: 0.8 + slight scale.
- Sage utility button: bg `#e5e7e0` / text `#4d4f46` / radius 4px. Hover: bg `#f4f4f4` + orange (`#F54E00`) text flash.
- Bordered card: `#fdfdf8`/white bg, `1px solid #bfc1b7`, 4–6px radius, no shadow; orange text flash on interactive cards.

## Do / Don't (anti-convention)
- Do: flash `#F54E00` orange (or amber on dark) into text on hover — the hidden accent is the brand's signature interaction.
- Don't: use blue/purple or any conventional tech-SaaS color, and don't use pure white `#ffffff` for the page — the olive/sage warmth is the whole identity.
- Don't: polish it to "premium" — PostHog's charm is scrappy, editorial, hand-drawn; over-refinement kills it.
- Don't: use 12px+ radius or heavy shadows on cards — 4–6px and borders only; one shadow exists, for floating elements.

## Example component prompts
- "Hero on warm parchment `#fdfdf8`: heading 30px IBM Plex Sans weight 800, line-height 1.2, letter-spacing -0.75px, olive-ink `#4d4f46`. Dark CTA `#1e1f23`, 6px radius, white text, hover opacity 0.7 with amber `#F7A501` text."
- "Feature card: `#fdfdf8` bg, `1px solid #bfc1b7`, 4px radius, NO shadow. Heading 20px/700, body 16px/400/1.5 in `#4d4f46`. Interactive cards flash `#F54E00` orange text on hover."
