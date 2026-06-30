# Porsche — Design Tokens (loopy-native)
> Category: luxury-auto-tooling · Signature: engineered restraint — one heritage red on near-monochrome, square corners

## Signature & atmosphere
Porsche reads like a precision instrument: a near-monochrome canvas of white and graphite where a single inherited red signals only the things that matter. The recognizable idea is heritage-as-discipline — the bespoke Porsche Next typeface carries every word, corners stay essentially square, and the red is rationed so hard it never decorates. It feels less like marketing and more like the dashboard of something that was tuned, not styled.

## Color (hex · --var · role)
- `#FFFFFF` `--bg` — primary content surface; dark photographic heroes use near-black for product framing
- `#0E0E12` `--fg` — graphite near-black primary text (not pure `#000`)
- `#D5001C` `--primary` — Porsche Red (Guards Red lineage); CTA fills, active markers, the one accent — rationed
- `#1A1A1F` `--surface-dark` — dark hero / footer canvas; text inverts to `#FFFFFF`
- `#626669` `--muted` — secondary text / specs metadata; `#969A9D` `--muted-2` — tertiary labels
- `#C8CACB` `--border` — hairline divider on white; `#2A2A30` on dark surfaces
- `#FFFFFF` `--fg-on-dark` — text/links on dark photography. Contrast: `#626669` on `#FFFFFF` ≈ 5.0:1 — body-safe, not for sub-12px.

## Typography
- Stack: `"Porsche Next", "Inter", system-ui, Arial, sans-serif` for everything — one bespoke family, utilitarian fallbacks.
- Display 64px / 600 / 1.10 / -0.5px · H2 40px / 600 / 1.15 · H3 28px / 600 / 1.20 · Body 16px / 400 / 1.55 · Body-lead 18px / 400 / 1.55 · Label 12px / 600 / 1.20 / +0.4px (UPPERCASE eyebrows)
- Active weights: 400 (body), 600 (display + UI emphasis). Bold-by-default headings; the precision comes from the tight -0.5px display tracking, not extra weight.

## Spacing, radius, depth, motion
- Base 8px; scale 4 · 8 · 16 · 24 · 32 · 48 · 64 · 96 (engineered, generous between modules).
- Radius scale 0 · 2 · 4px — effectively square. Cards and buttons read as machined edges; no pills, no 12px+ rounding.
- Depth strategy: borders + dark/light contrast over shadows. One whisper elevation `rgba(0,0,0,0.08) 0 2px 8px` on raised cards; heroes carry weight by full-bleed contrast. Motion 200–280ms ease-out, transform/opacity only — no bounce.

## Components (key)
- Primary CTA: bg `#D5001C` / text `#FFFFFF` / padding 14px 28px / radius 2px / no border / hover darkens to `#B30017` + 2px chevron nudge, active `#950013`, focus 2px `#0E0E12` ring offset 2px.
- Secondary button: transparent / text `#0E0E12` / 1px `#0E0E12` border / radius 2px / hover fills `#0E0E12` with white text.
- Spec block: white surface, UPPERCASE 12px/600/+0.4px label in `#626669` above a 40px/600 figure in `#0E0E12` — dashboard-style number-forward layout.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: keep corners at 0–4px (square is the identity); ration `#D5001C` to one CTA / one marker per view; set display at 600 with tight -0.5px tracking.
- Don't: round buttons into pills — the reflex to soften corners turns an instrument into a consumer app and erases the engineered feel.
- Don't: spread the red across backgrounds, badges, and links at once — the instinct to "use the brand color" dilutes the one signal it exists to send.
- Don't: pick a generic geometric sans for display — Porsche Next's specific letterforms (or a close fallback) carry the heritage; Helvetica reads as anybody.

## Example component prompts
- "Hero on near-black `#1A1A1F`: full-bleed automotive photo, headline 64px Porsche Next weight 600, -0.5px tracking, line-height 1.10, white text; one `#D5001C` CTA, white label, 2px radius."
- "Spec strip on `#FFFFFF`: UPPERCASE 12px/600/+0.4px `#626669` labels over 40px/600 `#0E0E12` figures, 1px `#C8CACB` dividers between columns, 0px radius."
- "Secondary outline button: transparent bg, 1px `#0E0E12` border, 2px radius, 14px 28px padding, hover fills `#0E0E12` with `#FFFFFF` text in 220ms ease-out."
