# Rolex — Design Tokens (loopy-native)
> Category: luxury-auto-tooling · Signature: crown-green on champagne — serif authority, ceremonial whitespace

## Signature & atmosphere
Rolex feels like a watch presented on a velvet tray under a single warm light: a calm green-and-gold world where every element is centered, deliberate, and unhurried. The recognizable idea is ceremony — the bespoke serif and the crown-green band signal permanence and craft, not speed. Nothing is casual; whitespace is reverent, and the green is treated as a seal of authenticity rather than a UI color.

## Color (hex · --var · role)
- `#FFFFFF` `--bg` — primary surface; alternating soft `#F2F1EC` champagne-cream bands for warmth
- `#212121` `--fg` — warm near-black primary text (not pure `#000`)
- `#127749` `--primary` — Rolex Green; brand band, primary CTA, the seal — used as ceremony, not decoration
- `#A37E2C` `--accent` — gold; fine rules, emphasis, premium markers (rationed)
- `#5A5A5A` `--muted` — secondary text; `#8A8A8A` `--muted-2` — tertiary metadata
- `#E3E2DC` `--border` — warm hairline divider; `#127749` for active/selected underlines
- `#0E5C39` `--primary-active` — pressed green. Contrast: green `#127749` on white ≈ 4.9:1 — passes AA for text, comfortable on the CTA.

## Typography
- Stack: serif display `"Rolex Serif", "Garamond", Georgia, "Times New Roman", serif`; UI `"Rolex Sans", Helvetica, Arial, sans-serif`. Serif = authority, sans = wayfinding.
- Display 52px / 400 / 1.20 / 0 · H2 34px / 400 / 1.25 · H3 22px / 500 / 1.30 · Body 16px / 400 / 1.70 (generous editorial leading) · Body-lead 18px / 400 / 1.70 · Label 12px / 600 / 1.20 / +1.2px (UPPERCASE eyebrows, wide tracking)
- Active weights: 400 (serif display + body), 500–600 (sans UI). Display stays at 400 — the serif at scale is the authority, never bold.

## Spacing, radius, depth, motion
- Base 8px; scale 8 · 16 · 24 · 40 · 64 · 96 · 128 (ceremonial, very generous between modules).
- Radius scale 0 · 2 · 4px — essentially square, restrained. Buttons 2px, media 0px.
- Depth strategy: whitespace + thin gold/hairline rules over shadows. Near-flat; one faint elevation `rgba(0,0,0,0.06) 0 4px 16px` on hover cards. Depth is achieved by space and centered composition, not stacking. Motion 280–360ms ease, slow and dignified — opacity/transform only, no scale-pop.

## Components (key)
- Primary CTA: bg `#127749` / text `#FFFFFF` / padding 14px 36px / radius 2px / UPPERCASE 12px/600/+1.2px label / hover darkens to `#0E5C39`, active inset, focus 2px `#A37E2C` gold ring.
- Secondary button: transparent / text `#127749` / 1px `#127749` border / radius 2px / hover fills green with white text.
- Centered editorial block: max-width ~720px, centered, UPPERCASE wide-tracked eyebrow in `#127749`, 52px/400 serif headline, 18px/400/1.70 body — symmetrical, ceremonial whitespace above and below.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: center compositions and lavish ceremonial whitespace (96–128px between modules); set serif display at weight 400; treat green as a seal, gold as a rare rule.
- Don't: left-align everything for "modern web" rhythm — the reflex toward asymmetric SaaS layouts erases the ceremonial symmetry that is the whole register.
- Don't: bold the serif headline — the instinct to add weight for impact removes the engraved-plaque calm; 400 serif at 52px is the authority.
- Don't: scatter green across links, badges, borders, and fills at once — diluting the seal makes it a UI color and kills its authenticity signal; ration it.

## Example component prompts
- "Centered hero on `#FFFFFF`: UPPERCASE 12px/600/+1.2px green `#127749` eyebrow, 52px/400 Rolex Serif headline in `#212121`, line-height 1.20; one green CTA, white UPPERCASE label, 2px radius, 128px whitespace above."
- "Champagne band on `#F2F1EC`: centered 34px/400 serif H2, 18px/400/1.70 body in `#5A5A5A`, thin `#A37E2C` gold rule above the heading."
- "Primary CTA: `#127749` bg, white UPPERCASE 12px/600/+1.2px label, 14px 36px padding, 2px radius; hover `#0E5C39`, focus 2px `#A37E2C` ring in 320ms ease."
