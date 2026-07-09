# Mastercard — Design Tokens (loopy-native)
> Category: fintech/crypto · Signature: warm cream canvas, circle-and-orbit shapes, weight-450 editorial calm

## Signature & atmosphere
Mastercard reads like a premium brand magazine printed on putty-toned stock: the canvas is a warm cream, never white, and everything that matters is shaped like a circle, a stadium, or a full pill. Circular photo portraits sit in asymmetric constellations linked by thin traced-orange arcs, each with a small white satellite arrow docked to its rim. The one idea to land is editorial-institution warmth — sixty-year-old payments authority dressed as a calm, spacious print layout.

## Color (hex · --var · role)
- `#f3f0ee` `--bg` — canvas cream (warm putty, never pure white); `#fcfbfa` `--bg-lifted` — paper-on-paper lifted surface
- `#141413` `--fg` — warm ink-black for headings, body, and footer (the `13` blue pulls toward cream so it never reads jet)
- `#ffffff` `--card` — reserved for nav pill, modals, and satellite-CTA circles
- `#cf4500` `--signal` — burnt signal orange; CONSENT/legal actions only, never marketing CTAs
- `#f37338` `--accent` — light orange; decorative orbital arcs + carousel indicators only
- `#696969` `--muted` — slate-gray secondary text; `#d1cdc7` whisper/disabled on cream
- `#3860be` link blue (inline links). Contrast: ink `#141413` on cream ≈ 14:1; keep whisper `#d1cdc7` for decorative ghost text only, never readable copy.

## Typography
- Stack: `"MarkForMC", "Sofia Sans", Arial, sans-serif` — one geometric sans for everything; Sofia Sans is the open substitute. No second typeface.
- H1-hero 64/500/1.0/-2% · H2 36/500/1.22/-2% · H3-card 24/500/1.2/-2% · Eyebrow 14/700/1.0/+4% UPPERCASE (with accent dot) · Body 16/450/1.4 · Nav/Button 16/500/1.0/-3% · Footer-link 14/450/1.4
- Weight 450 is load-bearing for body — softer than 500, firmer than 400; swapping to 400 flattens the identity. Headlines at 500 with -2% tracking lock the words together.

## Spacing, radius, depth, motion
- Base 8px; scale 8 · 16 · 24 · 32 · 48 · 64 · 96 · 128. Section vertical padding 96–128px desktop.
- Radius: small ≤6 (micro-chips) · 20 (body CTAs — the signature button radius) · 40 (hero stadium frames) · 50% (circular portraits) · 999 (nav/pill/carousel). The 8–12 middle ground is deliberately absent.
- Depth strategy: atmospheric cushioning, not directional light. Nav `rgba(0,0,0,0.04) 0 4px 24px`; elevated media `rgba(0,0,0,0.08) 0 24px 48px` — wide 48px spread at low opacity. Borders preferred over shadow for functional lines.
- Motion: minimal; subtle press-compression on pills; carousel transitions ease. GPU transforms only.

## Components (key)
- Primary CTA (ink pill): bg `#141413` / text `#f3f0ee` (cream, not white) / `1.5px solid #141413` / radius 20px / padding 6px 24px / MarkForMC 16/500/-0.32px. Press = subtle inward shrink.
- Circular portrait + satellite: square photo cropped to 50% circle (260–340px); white 56px circular CTA with ink arrow docked bottom-right, ~40% outside the rim; eyebrow below with `#f37338` dot + uppercase label.
- Floating nav pill: white, radius 999px, padding 16px 40px, shadow `rgba(0,0,0,0.04) 0 4px 24px`, floats ~24px below viewport top.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: use cream `#f3f0ee` as the body background — the instinct to default to white breaks the warm editorial tone.
- Do: set body at weight 450, not 400 — the half-step is the brand's softness.
- Don't: round image frames at 8–16px — Mastercard uses ONLY full-pill (999), 40px, or full-circle; in-between radii look generic.
- Don't: use signal orange `#cf4500` for marketing CTAs — it reads as cookie-consent and dilutes the legal color signal; CTAs are ink pills.
- Don't: place circular portraits on a tidy grid — their identity is asymmetric constellation placement linked by thin orange arcs.

## Example component prompts
- "Circular portrait 300px: square photo cropped to a perfect circle; dock a 56px white satellite button with a dark arrow ~40% outside the bottom-right rim; below, an eyebrow with a `#f37338` dot + uppercase 'SERVICES' in 14px weight 700 +4%, then an H3 24px weight 500 -2% `#141413`."
- "Primary CTA: bg `#141413`, text cream `#f3f0ee`, `1.5px solid #141413`, radius 20px, padding 6px 24px, MarkForMC 16px weight 500 -0.32px. On cream `#f3f0ee` canvas, no drop shadow."
- "Floating nav pill: white, radius 999px, padding 16px 40px, shadow `rgba(0,0,0,0.04) 0 4px 24px`, 24px below viewport top; ink links weight 500 16px with 48px gaps, circular 48px search button right."
