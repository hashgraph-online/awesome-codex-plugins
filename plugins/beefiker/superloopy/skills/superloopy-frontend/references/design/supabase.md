# Supabase — Design Tokens (loopy-native)
> Category: dev-tools · Signature: editor-dark canvas where emerald is an identity stamp, never decoration

## Signature & atmosphere
Supabase feels like a premium code editor that grew a marketing site without losing its terminal soul. The canvas is near-black (never pure), and a single Postgres-green emerald appears only as a signal — in the mark, in links, in an accent border — saying "this is Supabase" rather than dressing anything up. Hero text is crushed to 1.0 line-height, dense as a typed command.

## Color (hex · --var · role)
- `#171717` `--bg` — page canvas (not pure black); `#fafafa` `--fg` — primary text/off-white
- `#0f0f0f` `--card` — deepest surface / primary button fill; `#171717`-and-up for elevated panels
- `#3ecf8e` `--primary` — Supabase emerald (logo, brand accent); `#00c573` `--accent` — interactive green for links
- `rgba(62,207,142,0.3)` `--accent-border` — the green "elevated" border (brand color as depth signal)
- `#b4b4b4` `--muted` — secondary text/links; `#898989` — tertiary/footer; `#4d4d4d` — heavy secondary
- Borders climb: `#242424` (barely visible) → `#2e2e2e` `--border` (standard) → `#363636` → `#393939` (prominent)
- Contrast: `#b4b4b4` on `#171717` clears AA; keep `#898989` for non-essential text.

## Typography
- Stack: `Circular` (geometric sans, rounded terminals — the humanizing element), `Source Code Pro` for uppercase technical labels.
- Display 72px/400/1.0/0 · Section 36px/400/1.25/0 · Card-title 24px/400/1.33/-0.16px · Sub 18px/400/1.56/0
- Body 16px/400/1.5/0 · Nav 14px/500/1.43/0 · Button 14px/500/1.14/0 · Code-label `Source Code Pro` 12px/400/1.33/letter-spacing 1.2px uppercase
- Weight restraint is the rule: 400 for nearly everything, 500 only on nav + buttons. No bold — hierarchy comes from size, not weight.

## Spacing, radius, depth, motion
- Base 8px; scale 4 · 8 · 12 · 16 · 24 · 32 · 48, then dramatic jumps 90 · 96 · 128 for cinematic section gaps.
- Radius: 6px secondary/ghost · 8–16px cards · 9999px primary CTAs and tabs. Nothing between pill and 6px on buttons.
- Depth = border-defined, no shadows. Elevation steps through border color (`#242424 → #2e2e2e → #363636`); the green `rgba(62,207,142,0.3)` border is the highest "elevated" state. Focus only: `rgba(0,0,0,0.1) 0 4px 12px`.
- Motion: 150ms ease; subtle border/opacity transitions.

## Components (key)
- Primary CTA (pill): bg `#0f0f0f` / text `#fafafa` / padding 8px 32px / radius 9999px / `1px solid #fafafa`. Secondary variant: same shape, `1px solid #2e2e2e`, 0.8 opacity.
- Ghost button: transparent / text `#fafafa` / 6px radius / `1px solid transparent`. Tertiary + icon actions.
- Card: dark surface `#171717`, `1px solid #2e2e2e`, 8–16px radius, no shadow, 16–24px internal padding.

## Do / Don't (anti-convention)
- Do: treat emerald as an identity stamp — confine it to logo, links, and accent borders.
- Don't: paint green onto backgrounds or large surfaces — the moment it becomes decoration it stops being a signal.
- Don't: add box-shadows on the dark theme — they're invisible and break the border-hierarchy depth model; step border color instead.
- Don't: reach for bold (700) — 400 carries the system; 500 is the maximum, for interactive text only.

## Example component prompts
- "Hero on `#171717`: headline 72px Circular weight 400, line-height 1.0, `#fafafa`. Sub-text 16px/400/1.5 in `#b4b4b4`. Pill CTA `#0f0f0f` bg, `#fafafa` text, 9999px radius, 8px 32px padding, `1px solid #fafafa` border."
- "Feature card: `#171717` bg, `1px solid #2e2e2e`, 16px radius, NO shadow. Title 24px/400 letter-spacing -0.16px; body 14px/400 `#898989`. Add an emerald variant with `1px solid rgba(62,207,142,0.3)` border."
