# Railway — Design Tokens (loopy-native)
> Category: dev-tools · Signature: cosmic charcoal canvas with a magenta-to-violet gradient as the single hero signal

## Signature & atmosphere
Railway feels like deploying into deep space — a near-black charcoal canvas with the faintest cool-violet undertone, where infrastructure is presented as something fluid and alive rather than racked steel. The recognizable idea is the one gradient: a magenta-into-violet sweep that appears exactly once as the brand's energy source (hero glow, primary CTA, the logo mark) and never gets diluted into decoration. Everything else is restrained monochrome with crisp low-opacity borders, so the gradient reads as a single light source in the dark.

## Color (hex · --var · role)
- `#13111c` `--bg` — cosmic charcoal canvas (cool-violet undertone, not neutral black); `#f5f5f7` `--fg` — near-white text (soft, not pure `#ffffff`)
- `#1c1929` `--card` — elevated surface one step up from bg; `#241f33` prominent surface for nested panels
- `#c049ff` `--primary-start` → `#8a3ffc` `--primary-end` — the magenta-to-violet brand gradient (CTA fill, hero glow, logo); text on it `#ffffff`
- `#b794f6` `--accent` — solo violet for links/icons when a gradient would be too loud
- `#9b96ab` `--muted` — secondary/body text (cool gray); `#6c6781` tertiary/placeholder
- `rgba(255,255,255,0.08)` `--border` — low-opacity cool hairline; `rgba(255,255,255,0.12)` emphasized divider
- `#ff5c5c` `--destructive`; `#3ecf8e` success. Contrast: `#9b96ab` on `#13111c` ≈ 5.2:1 (body-ok); keep `#6c6781` for placeholder/metadata only.

## Typography
- Stack: `"Inter", ui-sans-serif, system-ui, sans-serif` (display + body); code `"GeistMono", "JetBrains Mono", ui-monospace, monospace`. Enable `font-feature-settings: "cv11", "ss01"` on Inter for the geometric single-story glyphs.
- Display 64px / 600 / 1.05 / -1.5px · Section 44px / 600 / 1.12 / -1.0px · Card-title 22px / 600 / 1.30 / -0.3px
- Body-lg 18px / 400 / 1.55 · Body 16px / 400 / 1.55 · Button 15px / 500 · Label 13px / 500 / **+0.4px uppercase**
- Code 14px / 400 / 1.55 in GeistMono. Three weights: 400 body, 500 UI, 600 headings — no 700.

## Spacing, radius, depth, motion
- Base 8px; scale 4 / 8 / 12 / 16 / 24 / 32 / 48 / 64 / 96px; section gaps 80–112px on the dark canvas.
- Radius: 6px inputs/tags · 8px buttons · 12px cards · 16px featured panels · 9999px pills/badges.
- Depth blends surface-color steps with soft glow: ground `#13111c` → card `#1c1929` → panel `#241f33`; borders `1px solid rgba(255,255,255,0.08)`. The gradient supplies ambient depth as a blurred radial glow behind the hero (`#8a3ffc` at low opacity); avoid hard drop shadows.
- Motion 160–220ms ease-out; transform/opacity + subtle glow intensification on hover.

## Components (key)
- Primary CTA (gradient pill): `background: linear-gradient(90deg, #c049ff, #8a3ffc)` / text `#ffffff` / padding 10px 20px / radius 8px / hover brightens glow ~6% + lifts; focus `2px solid #b794f6` outline.
- Secondary button: bg `#1c1929` / text `#f5f5f7` / radius 8px / border `1px solid rgba(255,255,255,0.12)` / hover border to `rgba(255,255,255,0.2)`.
- Service card (canvas-graph node): bg `#1c1929`, `1px solid rgba(255,255,255,0.08)`, 12px radius, 16–24px padding; title 22px/600, GeistMono 13px uppercase status label in `#9b96ab`.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: spend the magenta-violet gradient on exactly one role per view (CTA or hero glow) — the instinct to gradient-fill cards and icons everywhere dissolves the single-light-source effect.
- Don't: use neutral `#000`/pure-gray for the dark — the cool-violet undertone (`#13111c`) is what makes it feel cosmic rather than generic-dark-mode.
- Don't: render the brand as a flat solid purple — Railway's identity is the gradient sweep, not a single swatch.
- Don't: cap headings at weight 700 — 600 is the ceiling; tracking and size carry hierarchy.
- Don't: drop hard offset box-shadows on the dark canvas — depth is surface steps plus the blurred gradient glow.

## Example component prompts
- "Hero on `#13111c` with a blurred radial gradient glow (`#8a3ffc` ~18% opacity) behind the headline. H1 64px Inter weight 600, line-height 1.05, letter-spacing -1.5px, color `#f5f5f7`. Gradient pill CTA `linear-gradient(90deg,#c049ff,#8a3ffc)`, white text, 8px radius, 10px 20px."
- "Service card: bg `#1c1929`, `1px solid rgba(255,255,255,0.08)`, 12px radius, 20px padding. Title 22px Inter 600 / -0.3px; body 16px 400 in `#9b96ab`; GeistMono 13px uppercase status label `+0.4px`."
- "Secondary button: bg `#1c1929`, text `#f5f5f7`, 8px radius, border `1px solid rgba(255,255,255,0.12)`, hover border `rgba(255,255,255,0.2)`."
