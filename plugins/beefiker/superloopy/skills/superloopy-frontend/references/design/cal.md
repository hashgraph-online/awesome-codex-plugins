# Cal.com — Design Tokens (loopy-native)
> Category: productivity/saas · Signature: grayscale confidence, ring-shadow depth

## Signature & atmosphere
Cal.com is monochrome on purpose — a black-and-white photograph of a product, where boldness comes from contrast rather than hue. Headlines are set in a custom geometric display face packed extremely tight, so they read as architecture carved into white space; body switches to Inter so the two never blur roles. The depth system is the surprise: no CSS borders at all, just layered shadows where a `0 0 0 1px` ring stands in for the hairline, a soft diffused layer adds ambient lift, and a sharp contact shadow grounds the bottom edge.

## Color (hex · --var · role)
- `#ffffff` `--bg` — page + card surface, the dominant canvas
- `#242424` `--fg` — Charcoal; headings + button bg, a warm near-black (not pure `#000`)
- `#111111` `--fg-deep` — Midnight; high-contrast nav/link text
- `#898989` `--muted` — secondary text + descriptions (~3.5:1, use at ≥18px)
- `#0099ff` `--link` — the only blue, reserved strictly for hyperlinks
- `rgba(34,42,53,0.08)` `--ring` — ring-shadow standing in for a border
- `#f5f5f5` `--surface-2` — barely-there section tint
- Note: brand palette is deliberately colorless; color appears only inside product UI screenshots.

## Typography
- Stack: `"Cal Sans", system-ui` (display only); `Inter, "Inter Placeholder"` (body); `"Roboto Mono"` (code). Substitute a geometric display sans if Cal Sans is unavailable.
- Display 64/600/1.10/0px · H2 48/600/1.10/0px · Feature 24/600/1.30/0px · Sub 20/600/1.20/+0.2px
- BodyLight 18/300/1.30/-0.2px (Cal Sans UI Light) · BodyLightStd 16/300/1.50/-0.2px
- UILabel 16/600/1.00/0px (Inter) · Caption 14/500/1.14 (Inter) · Code 14/600/1.00 (Roboto Mono)
- Signature: Cal Sans cramps below 24px — apply +0.2px tracking under 24px; it is otherwise tight by default.

## Spacing, radius, depth, motion
- Base 8px; scale 4 · 8 · 12 · 16 · 20 · 24 · 28 · 80 · 96 (note the deliberate 28→80 jump for section-level air).
- Radius: 2px inline · 6–8px buttons/inputs · 12px cards · 16px sections · 9999px pills.
- Depth strategy: **ring + diffused + contact shadows, never CSS borders**. Workhorse card `rgba(19,19,22,.7) 0 1px 5px -4px, rgba(34,42,53,.08) 0 0 0 1px, rgba(34,42,53,.05) 0 4px 8px`. Button inner bevel `rgba(255,255,255,.15) 0 2px 0 inset`.
- Motion: hover = opacity → 0.7 on dark buttons; subtle, fast.

## Components (key)
- Primary CTA: bg `#242424` / text `#ffffff` / radius 6–8px. Hover → opacity 0.7. Maximally dark on white is the entire CTA language.
- Ghost/white button: `#ffffff` bg + ring-shadow border + dark text; uses the multi-layer shadow for lift, no `border:`.
- Scheduling card: `#ffffff`, 12px radius, ring+soft+contact shadow stack — feels like a physical card on a table.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: keep the brand grayscale and let contrast carry boldness; use Inter for all body, Cal Sans only for ≥24px headings.
- Don't: add a CSS `border` for containment — the system replaces it with a `0 0 0 1px` ring shadow; a real border breaks the elevation language.
- Don't: introduce a brand accent color — color is reserved for links and in-product UI; a colored button instantly reads off-brand.

## Example component prompts
- "Hero on `#ffffff`: 64px Cal Sans weight 600, line-height 1.10, letter-spacing 0, `#242424`, centered. Dark CTA `#242424`, 8px radius, white text, hover opacity 0.7."
- "Scheduling card: `#ffffff`, 12px radius, no border, shadow `rgba(19,19,22,.7) 0 1px 5px -4px, rgba(34,42,53,.08) 0 0 0 1px, rgba(34,42,53,.05) 0 4px 8px`."
- "Feature body: 16px Inter weight 300, line-height 1.50, `#898989`; 48px Cal Sans/600 heading in `#242424` above it."
