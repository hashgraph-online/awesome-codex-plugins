# Intercom — Design Tokens (loopy-native)
> Category: productivity/saas · Signature: warm editorial canvas, sharp 4px geometry

## Signature & atmosphere
Intercom feels like a confident magazine spread for an AI-first helpdesk — a warm off-white page with off-black ink and one decisive Fin Orange accent named after the product's agent. Headlines are set in a geometric sans driven to extreme negative tracking with a flat 1.00 line-height, so they compress into billboard-tight blocks that feel engineered. The geometry is the twist: nearly every interactive element sits at a sharp 4px radius, reading industrial against the soft warm surfaces, and buttons physically grow on hover with a `scale(1.1)`.

## Color (hex · --var · role)
- `#faf9f6` `--bg` — warm cream canvas (cards + button surfaces too); not pure white
- `#111111` `--fg` — off-black foreground + dark button bg
- `#ffffff` `--surface` — pure white for specific content surfaces
- `#ff5600` `--accent` — Fin Orange; AI/brand accent ONLY, never decorative
- `#7b7b78` `--muted` — muted text (warm-shifted neutral)
- `#626260` `--muted-2` / `#313130` `--fg-soft` — mid + dark warm neutrals
- `#dedbd6` `--border` — warm oat border (never cool gray)
- `#d3cec6` `--border-2` — lighter warm sand neutral
- Report palette (data viz only): `#65b5ff` blue · `#0bdf50` green · `#c41c1c` red · `#ff2067` pink · `#b3e01c` lime.

## Typography
- Stack: `Saans, ui-sans-serif, system-ui` (primary); `Serrif, ui-serif, Georgia` (serif accents); `SaansMono, ui-monospace` (labels). Substitute Inter / a geometric sans if Saans is unavailable.
- Display 80/400/1.00/-2.4px · H2 54/400/1.00/-1.6px · Sub 40/400/1.00/-1.2px · CardTitle 32/400/1.00/-0.96px
- Feature 24/400/1.00/-0.48px · BodyEmphasis 20/400/0.95/-0.2px · Nav 18/400/1.00/normal · Body 16/400/1.50/normal
- BodyLight 14/300/1.40 · MonoLabel 12/400–500/1.00–1.30/+0.6–1.2px UPPERCASE
- Signature: all headings hold a flat 1.00 line-height with strong negative tracking — the compression is the voice.

## Spacing, radius, depth, motion
- Base 8px; scale 8 · 10 · 12 · 14 · 16 · 20 · 24 · 32 · 40 · 48 · 60 · 64 · 80 · 96.
- Radius: 4px buttons · 6px nav items · 8px cards/containers. Sharp, near-rectangular.
- Depth strategy: **warm borders + surface tints, minimal shadows**. Cards rely on `1px solid #dedbd6` against `#faf9f6`, not drop shadows.
- Motion: button hover `scale(1.1)`, active `scale(0.85)` — a physical grow-then-press; transform only.

## Components (key)
- Primary CTA (dark): bg `#111111` / text `#ffffff` / padding 0 14px / radius 4px. Hover → white bg + dark text + `scale(1.1)`; active → green bg `#2c6415` + `scale(0.85)`.
- Outlined: transparent bg / text `#111111` / `1px solid #111111` / radius 4px / same scale behavior.
- Card: bg `#faf9f6`, `1px solid #dedbd6`, radius 8px, no visible shadow.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: keep all interactive radii at 4px — the sharp geometry against warm surfaces is the identity.
- Don't: round buttons into pills or even 8px+ — softening the corners erases the industrial contrast that makes the warmth read as intentional.
- Don't: scatter Fin Orange as a decorative tint — it marks AI/brand moments only; everywhere else uses warm oat neutrals, never cool gray.

## Example component prompts
- "Hero on `#faf9f6`: headline 80px Saans weight 400, line-height 1.00, letter-spacing -2.4px, `#111111`. Dark CTA `#111111`, 4px radius, 0 14px padding, white text; hover → white bg + dark text + scale(1.1)."
- "Card: `#faf9f6`, `1px solid #dedbd6`, 8px radius, no shadow. Title 24px Saans/400/-0.48px."
- "Mono section label: SaansMono 12px UPPERCASE, letter-spacing +0.6px, `#7b7b78`."
