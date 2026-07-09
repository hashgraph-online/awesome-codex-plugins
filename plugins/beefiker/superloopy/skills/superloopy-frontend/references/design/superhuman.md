# Superhuman — Design Tokens (loopy-native)
> Category: productivity/saas · Signature: white luxury canvas, one cinematic purple gesture

## Signature & atmosphere
Superhuman markets a productivity tool the way a maison markets a watch: a predominantly white, immaculate page with a single dramatic move — a deep twilight-purple gradient hero. The recognizable idea is restraint as confidence; warm cream buttons instead of bright CTAs, one lavender accent, almost no borders or shadows. The typographic voice is unusual on purpose — a variable font sitting at weights between the standard stops, so text feels subtly heavier and more assured than ordinary regular.

## Color (hex · --var · role)
- `#ffffff` `--bg` — dominant page canvas; `#292827` `--fg` — Charcoal Ink, warm near-black (faint brown), never pure black
- `#1b1938` `--hero` — Mysteria Purple; deep blue-purple gradient hero, the one dramatic surface
- `#cbb7fb` `--accent` — Lavender Glow; the *only* accent — emphasis, highlights, badges
- `#714cb6` `--link` — Amethyst; underlined in-content links
- `#e9e5dd` `--button` — Warm Cream; primary button fill (warm, muted, luxurious — not white, not gray)
- `#dcd7d3` `--border` — Parchment border, warm light gray, faint pink undertone
- `rgba(255,255,255,0.95)` `--fg-on-dark` — primary text on the purple hero
- `rgba(255,255,255,0.8)` `--fg-on-dark-2` — secondary text on dark
- No saturated semantic colors on marketing — states ride opacity + underline, not red/green.

## Typography
- Stack: `"Super Sans VF", system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue"` — custom variable font with a non-standard weight axis (460, 540, 600, 700). Intent: between-the-stops weight as a signature texture.
- Display 64/540/0.96/0 · SectionDisplay 48/460/0.96/-1.32px · FeatureTitle 28/540/1.14/-0.63px · BodyHeading 20/460/1.20 · EmphasisBody 18/540/1.50/-0.135px · Body 16/460/1.50 · Button 16/700/1.00 · Nav 16/460/1.20 · Caption 14/500/1.20/-0.315px · Micro 12/700/1.50
- Two rules define the voice: weight 460 is the body default (slightly heavier than regular), and display sits at 0.96 line-height — compressed, architectural — while body opens to 1.50.

## Spacing, radius, depth, motion
- Base 8px; scale 2 · 4 · 6 · 8 · 12 · 16 · 20 · 24 · 32 · 40 · 48 · 56px; section padding 48–80px.
- Radius: **binary system — only 8px (small) and 16px (large)**. No micro 2px, no pill 50px.
- Depth strategy: **borders + color contrast**, not shadows. Card = `1px solid #dcd7d3`; the hero gradient supplies depth via color shift; hero elements use `rgba(255,255,255,0.2)` ghost borders. Shadows are rare and faint.
- Motion: minimal — opacity/brightness shifts on hover, calm over flashy; transform/opacity only.

## Components (key)
- Primary CTA (Warm Cream): bg `#e9e5dd` / text `#292827` / padding ~12px 20px / radius 8px / no border / weight 700. Hover → slight brightness shift only. On the purple hero the cream pops against `#1b1938`.
- Dark primary (light sections): bg `#292827`, white text, 8px radius — inverse for contrast bands.
- Content card: white bg, `1px solid #dcd7d3`, 16px radius, 20px/460 title, 16px/460/1.50 body in `#292827`.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: use Super Sans weight 460 as the default and 540 for display; keep display line-height at 0.96; make primary buttons Warm Cream `#e9e5dd`; cap radius at 8px / 16px.
- Don't: reach for conventional weights 400/500/600 for body/display — the between-stops 460/540 *is* the brand; standard weights flatten it.
- Don't: add bright/saturated CTAs (blue, green, red) — buttons are intentionally muted cream or charcoal, with Lavender `#cbb7fb` as the sole accent. Don't pile on shadows or use pure `#000`/`#fff` text.

## Example component prompts
- "Hero with `#1b1938` purple gradient: H1 Super Sans 64px / weight 540 / line-height 0.96 in `rgba(255,255,255,0.95)`; Warm Cream CTA `#e9e5dd`, `#292827` text, 8px radius, weight 700."
- "Feature card: white bg, `1px solid #dcd7d3`, 16px radius, title 20px/460, body 16px/460/1.50 in `#292827`; emphasis word in Lavender `#cbb7fb`."
- "Section heading 48px Super Sans / weight 460 / 0.96 / -1.32px in `#292827`, single dramatic product screenshot below, all on `#ffffff`."
