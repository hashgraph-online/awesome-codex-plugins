# HashiCorp — Design Tokens (loopy-native)
> Category: dev-tools · Signature: enterprise black-and-white with whisper shadows and per-product accent colors

## Signature & atmosphere
HashiCorp feels like infrastructure made tangible — austere black-and-white that flips between a clean white informational mode and a dramatic charcoal hero mode (`#15181e`), a literal "build in light, deploy in dark" duality. Restraint is the whole point: shadows are nearly invisible (5% opacity), radii stay tight and structural, and the only chromatic life comes from a per-product accent (Terraform purple, Vault yellow) injected through CSS tokens. Nothing floats, nothing is uncertain — that's the enterprise promise rendered in pixels.

## Color (hex · --var · role)
- `#ffffff` `--bg` — light informational canvas; `#15181e` `--bg-dark` — charcoal hero/product mode; `#0d0e12` deepest dark surface / dark inputs
- `#000000` `--fg` — text on light (brand black); `#efeff1` text on dark; `#3b3d45` secondary text on light
- `#1060ff` `--primary` — action blue on dark; `#2264d6` link blue on light; `#2b89ff` active/bright
- Product accents (use only in their product's context): `#7b42bc` Terraform · `#ffcf25` Vault (needs dark text) · `#14c6cb` Waypoint (hover `#12b6bb`) · `#1868f2` Vagrant
- `#656a76` `--muted` — helper/secondary text; `#d5d7db` light text/button text on dark
- `#f1f2f3` `--surface-light` — subtle light fill; borders `rgba(178,182,189,0.4)` and `rgb(97,104,117)`
- Contrast: white on `#15181e` is strong; Vault yellow `#ffcf25` always pairs with dark text. Each product owns exactly one color — never mix two in one component.

## Typography
- Stack: brand `"HashiCorp Sans", system-ui, sans-serif` (headings/brand text, weight-bearing 600–700); UI/body `system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial`. Brand font carries weight, system font carries words.
- Display 82px/600/1.17/0 · Section 52px/600/1.19 · Feature 42px/700/1.19/-0.42px · Card-title 26px/700/1.19 · Body-lg 20px/400/1.5 (system) · Body 16px/400/1.63 · Nav 15px/500/1.6 · Uppercase-label 13px/600/1.69/+1.3px UPPERCASE
- Tight headings (1.17–1.21) over relaxed body (1.5–1.69) — weight at the top of each section. Enable OpenType `"kern"` on all HashiCorp Sans. Uppercase 13px/600/+1.3px labels are the systematic wayfinding marker.

## Spacing, radius, depth, motion
- Base 8px; scale 2 · 3 · 4 · 6 · 8 · 12 · 16 · 20 · 24 · 32 · 40 · 48 (fine-grained low end). Section gaps 48–80px+.
- Radius: 2px inline · 3px checkboxes/small inputs · 4px secondary buttons · 5px primary buttons/badges/inputs · 8px cards. Nothing pill-shaped.
- Depth strategy = whisper shadows. Default elevation `rgba(97,104,117,0.05) 0 1px 1px, rgba(97,104,117,0.05) 0 2px 2px` — dual-layer at 5%, just enough to signal interactivity. Focus ring `3px solid` color-matched to product context. If a shadow is visible, it's too strong.
- Motion: subtle, ~150–200ms; interaction is signaled by token color shifts, not movement.

## Components (key)
- Primary CTA (dark): bg `#15181e` / text `#d5d7db` / padding 9px 9px 9px 15px (intentionally asymmetric) / radius 5px / `1px solid rgba(178,182,189,0.4)` / shadow whisper-level / focus `3px solid` accent.
- Secondary (light): bg `#ffffff` / text `#3b3d45` / padding 8px 12px / radius 4px / hover surface-tint + whisper lift.
- Product CTA: same structure, fill swapped to the product color (Terraform `#7b42bc`, Vault `#ffcf25` dark text, Waypoint `#14c6cb`) — one product, one color.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: keep the base palette black-and-white and inject color only through the correct product accent; keep shadows at 5% whisper level.
- Don't: raise shadow opacity above ~0.1 or reach for visible drop-shadows — restraint is the enterprise signal, not a missing feature.
- Don't: use pill/rounded buttons — radii stay 2–8px and structural; a 9999px pill reads as consumer-app, not infrastructure.
- Don't: use a product's accent outside its product (no Vault yellow on Terraform content) and don't set HashiCorp Sans below ~17px — it's a 600+ heading face, system-ui does the small UI text.

## Example component prompts
- "Hero on `#15181e`: headline 82px HashiCorp Sans weight 600, line-height 1.17, kern on, white; sub-text 20px system-ui 400/1.5 in `#d5d7db`. Primary button `#15181e` fill, `1px solid rgba(178,182,189,0.4)`, 5px radius, padding 9px 9px 9px 15px; secondary white button `#ffffff`, 4px radius."
- "Section label: 13px HashiCorp Sans weight 600, uppercase, +1.3px tracking, `#656a76`. Below it a card: white bg, 8px radius, whisper shadow `rgba(97,104,117,0.05) 0 1px 1px, rgba(97,104,117,0.05) 0 2px 2px`; title 26px/700, body 16px/400/1.63."
