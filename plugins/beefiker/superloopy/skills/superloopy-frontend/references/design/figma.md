# Figma — Design Tokens (loopy-native)
> Category: productivity/saas · Signature: colorless gallery chrome, color is the product

## Signature & atmosphere
Figma's marketing surface is a white gallery wall — the interface itself uses only black and white, so the vivid product gradients hung against it become the art. The other half of the signature is typographic: a variable display sans driven at unusual weight stops (320, 330, 340, 450, 480, 540) so hierarchy emerges from micro weight shifts rather than the blunt regular-vs-bold jump. Geometry is rounded to pill and circle, and focus rings are dashed — a quiet nod to the selection handles inside the editor.

## Color (hex · --var · role)
- `#ffffff` `--bg` — every background and white button surface
- `#000000` `--fg` — every text, solid button, and border; the sole interface "color"
- `rgba(0,0,0,0.08)` `--glass-dark` — subtle overlay for secondary buttons on light surfaces
- `rgba(255,255,255,0.16)` `--glass-light` — frosted overlay for buttons on dark/colored surfaces
- `--hero-gradient` — multi-stop electric green → bright yellow → deep purple → hot pink; lives ONLY in hero + product showcases, never in chrome
- Contrast note: black-on-white is ~21:1; the entire chrome is maximal contrast by construction.

## Typography
- Stack: `"figmaSans", "SF Pro Display", system-ui, helvetica` (display/body); `"figmaMono", "SF Mono", menlo` (labels). Substitute Inter / a variable sans if figmaSans is unavailable.
- Display 86/400/1.00/-1.72px · H2 64/400/1.10/-0.96px · Sub 26/540/1.35/-0.26px · SubLight 26/340/1.35/-0.26px
- FeatureTitle 24/700/1.45/normal · BodyLg 20/330–450/1.30–1.40/-0.14px · Body 16/330–400/1.40/-0.14px · BodyLight 18/320/1.45/-0.26px
- MonoLabel 18/400/1.30/+0.54px UPPERCASE · MonoSmall 12/400/1.00/+0.6px UPPERCASE
- OpenType `"kern"` enabled globally. Body tracking is always negative; mono labels always positive.

## Spacing, radius, depth, motion
- Base 8px; scale 4 · 8 · 12 · 16 · 18 · 24 · 32 · 40 · 48 · 50.
- Radius: 6px small containers · 8px cards/images/dialogs · 50px pill (tabs, CTAs) · 50% circle (icon buttons).
- Depth strategy: **contrast, not shadow**. White content sitting on a gradient/dark section is the elevation; product screenshots carry their own dimensionality. Shadows used sparingly and softly.
- Motion: short ease transitions on color/opacity; focus = dashed 2px outline (the signature).

## Components (key)
- Primary CTA (white pill): bg `#ffffff` / text `#000000` / padding 8px 18px 10px (asymmetric vertical) / radius 50px. Focus → dashed 2px outline. Used on dark/colored surfaces.
- Icon button: bg `rgba(0,0,0,0.08)` (light) or `rgba(255,255,255,0.16)` (dark) / radius 50% / dashed focus.
- Product tab bar: horizontal pill tabs (50px radius), active = black bg + white text, inactive = transparent + black text, figmaSans 20/480.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: keep chrome strictly black + white and let color enter only through product content/gradients.
- Don't: pick standard weights 400/500/600/700 for display — the identity is the variable stops (320–540); a flat 700 headline loses the airy precision.
- Don't: use solid focus rings or sharp button corners — dashed outlines and pill/circle geometry are load-bearing brand cues.

## Example component prompts
- "Hero on a vivid green→yellow→purple→pink gradient. Headline 86px figmaSans weight 400, line-height 1.00, letter-spacing -1.72px, white. White pill CTA, 50px radius, 8px 18px 10px padding, black text, dashed 2px focus."
- "Section label: figmaMono 18px UPPERCASE, letter-spacing +0.54px, black, kern on."
- "Body copy 20px figmaSans weight 330, line-height 1.40, letter-spacing -0.14px, black on white."
