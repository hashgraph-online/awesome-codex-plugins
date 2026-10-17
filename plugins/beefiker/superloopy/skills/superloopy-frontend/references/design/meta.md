# Meta — Design Tokens (loopy-native)
> Category: brand-web-media · Signature: gallery-white retail, binary light/dark sections, one decisive blue pill

## Signature & atmosphere
Meta's storefront frames hardware like museum pieces — cinematic product shots floating in wide negative space, broken by a rhythm of pure-white browsing sections alternating with immersive dark showcases. The recognizable idea is the binary surface: white for reading, deep near-black for the product reveal, with a single saturated-blue pill marking every action. The custom Optimistic typeface warms what could be cold tech retail; nothing decorates, everything either sells or navigates.

## Color (hex · --var · role)
- `#FFFFFF` `--bg` — canvas, nav, cards; `#1C2B33` `--fg` — headings/body (warm charcoal, not pure black)
- `#0064E0` `--primary` — every actionable element; hover `#0143B5`, pressed `#004BB9`, on-dark variant `#47A5FA`
- `#5D6C7B` `--muted` — product descriptions, secondary copy
- `#DEE3E9` `--border` — dividers; `#CED0D4` input borders
- `#F1F4F7` `--card` — secondary section surface; `#F7F8FA` flat card fill
- `#C80A28` `--destructive` — store error state; `#007D1E` success
- dark sections: `#1C1E21` standard, `#181A1B` Quest-warm, `#000000` max-contrast
- Note: use Meta Blue `#0064E0`, not legacy Facebook Blue `#1877F2`, for CTAs. Product-line accents (Quest purple `#A121CE`, Ray-Ban red `#D6311F`) stay confined to their own sections.

## Typography
- Stack: Optimistic VF (Dalton Maag) with OpenType `ss01`+`ss02` on display; fallbacks Montserrat, Helvetica, Arial
- Display 64px / 500 / 1.16 · Display-2 48px / 500 / 1.17 — hero, ss01+ss02
- H1 36px / 500 / 1.28 · H2 28px / 300 / 1.21 (the light-weight subhead is signature airiness) · H3 18px / 700 / 1.44
- Body 18px / 400 / 1.44 · Body-compact 16px / 500 / 1.50 / -0.16px (nav, UI labels)
- Caption 14px / 400 / 1.43 / -0.14px · Small 12px / 400 / 1.33
- Negative tracking (-0.14 to -0.16px) tightens small UI; weight is always stated explicitly.

## Spacing, radius, depth, motion
- Base 8px; scale 4 · 8 · 10 · 16 · 24 · 32 · 40 · 48 · 64 · 80 (sections breathe at 64–80)
- Radius: 8px inputs, 20px cards, 24px feature/highlight cards, 100px pill buttons/badges
- Depth strategy: mostly flat via background steps (white → `#F1F4F7` → dark). When elevation is needed, dual-shadow: `0 2px 4px rgba(0,0,0,0.1)` ambient + `0 12px 28px rgba(0,0,0,0.2)` for floating. Nav uses frosted glass `rgba(241,244,247,0.8)` + backdrop-blur.
- Motion: background 200ms ease, transform 150ms; card hover translateY(-2px) with shadow bump.

## Components (key)
- Primary CTA: bg `#0064E0` / white label Optimistic 14px / padding 10px 22px / radius 100px (full pill) / hover `#0143B5` scale(1.1) / pressed `#004BB9` scale(0.9) / focus 3px ring
- Feature card: white or `#F7F8FA` fill, radius 20–24px, edge-to-edge product image clipped to the radius, body 18px/400 `#5D6C7B`, generous internal padding; dark text over photography always gets a `linear-gradient(rgba(0,0,0,0), rgba(0,0,0,0.6))` scrim.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: alternate light and dark full-width sections for a walkthrough cadence; keep buttons fully pill (100px).
- Don't: use sharp corners (<8px) — the default web instinct toward 4–6px radius is wrong; this system is all smooth curves.
- Don't: use weight 300 below 28px — it goes too thin and breaks the airy-subhead trick.
- Don't: stack drop shadows in dark sections — separate by color/border there, not lighting.

## Example component prompts
- "Dark showcase on `#1C1E21`: full-width cinematic image with `linear-gradient(rgba(0,0,0,0), rgba(0,0,0,0.6))` scrim, 48px/500 white headline (ss01+ss02), `#5D6C7B`-on-dark body, and a `#0064E0` pill CTA at radius 100px, padding 10px 22px."
- "3-column product grid: white cards radius 20px, edge-to-edge image at top, body 18px/400 `#5D6C7B`, 24px grid gap, dual-shadow only on hover with translateY(-2px)."
