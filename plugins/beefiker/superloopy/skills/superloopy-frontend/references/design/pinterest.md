# Pinterest — Design Tokens (loopy-native)
> Category: consumer · Signature: warm craft canvas — olive-sand neutrals, one bold red, masonry density

## Signature & atmosphere
A warm, inspiration-driven canvas that treats visual discovery like a lifestyle magazine. The recognizable idea is temperature: where most tech leans cool steel, Pinterest's neutrals tilt olive/sand and its ink is a plum-tinted near-black — the whole surface feels handcrafted and cozy rather than clinical. One bold red (`#e60023`) is the singular accent, always confident, never subtle. Generous rounding and a dense masonry grid make the photography the value proposition.

## Color (hex · --var · role)
- `#ffffff` `--bg` — warm-white canvas; `#f6f6f3` `--surface` — fog light surface; `#33332e` `--bg-dark` — dark footer/sections
- `#211922` `--fg` — plum black, primary text (warmer than `#000`); `#000000` `--fg-2` — button text/secondary
- `#e60023` `--primary` — Pinterest Red, primary CTA + brand, singular
- `#62625b` `--muted` — secondary copy; `#91918c` `--muted-2`/`--border` — warm silver, input borders, disabled
- `#e5e5e0` `--secondary` — sand-gray secondary button bg; `#e0e0d9` `--circle` — circular action bg; `hsla(60,20%,98%,.5)` `--badge-wash` — warm badge tint
- `#435ee5` `--ring` — focus blue; `#2b48d4` `--link`; `#9e0a0a` `--destructive`
- Contrast: `--fg` on white ≈ 16:1. Note: primary red uses **black** text (≈ 4.3:1) by brand convention — keep label ≥ 12px/bold.

## Typography
- Stack: `"Pin Sans"` (single family, everything) with a global fallback chain incl. CJK. Substitute: -apple-system / Inter.
- Display hero 70/600 · Section heading 28/700/-1.2px (negative tracking = cozy, intimate titles) · Body 16/400/1.40 · Caption-bold 14/700 · Caption 12/400-500/1.50 · Button 12/400
- Compact scale (12–70px) with a dramatic jump — most functional text is 12–16px, app-dense. No ultra-light weights; type always feels substantial (400 minimum).

## Spacing, radius, depth, motion
- Base 8px; scale 4 · 6 · 7 · 8 · 10 · 12 · 16 · 18 · 20 · 24 · 32, then big jumps 80 · 100 for section breaks.
- Radius: small card 12px · button/input 16px (rounded, NOT pill) · feature card 20px · large 28px · panel/tab 32px · hero container 40px · circle 50%
- Depth = essentially flat. Masonry relies on photography for interest, not elevation; minimal token shadows only on overlays/dropdowns. Warmth of surface color + generous rounding does the depth work.
- Motion: subtle; focus uses `#435ee5` outer ring via semantic tokens.

## Components (key)
- Primary CTA: bg `#e60023` / text `#000000` / padding 6px 14px / radius 16px / 2px transparent border. Secondary: `#e5e5e0` sand bg, black text, same shape.
- Circular action: bg `#e0e0d9` / icon `#211922` / radius 50% — pin save/nav controls.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: use warm olive/sand neutrals (`#e5e5e0`, `#e0e0d9`, `#91918c`) everywhere — the warm tone is the identity.
- Don't: reach for cool steel grays because they feel "modern" — Pinterest's grays must lean warm/olive.
- Don't: pill-shape buttons — the brand is 16px-rounded, distinctly not a 999px capsule; and use plum `#211922`, not `#000000`, for primary text.
- Don't: add heavy shadows or extra brand colors — it's flat by design, depth comes from content; red + warm neutrals is the whole palette.

## Example component prompts
- "Hero on white: 70px/600 Pin Sans headline in `#211922`; red CTA (`#e60023` bg, black text, 16px radius, 6px 14px padding) beside a sand secondary (`#e5e5e0`, 16px radius)."
- "Pin card: white bg, 16px radius, no shadow; photography fills the top, 16px/400 `#62625b` description below."
- "Circular action button: `#e0e0d9` bg, 50% radius, `#211922` icon; input field white bg, 1px `#91918c` border, 16px radius, 11px 15px padding, focus blue `#435ee5` outline."
