# Brex — Design Tokens (loopy-native)
> Category: fintech/crypto · Signature: pure-black enterprise canvas, orange spark accent, tight grotesk authority

## Signature & atmosphere
Brex feels like the corporate-card brand that grew up: confident pure-black surfaces, crisp white grids, and a single warm orange that sparks like a metal card catching light. It is enterprise-serious but not cold — the orange keeps it human against the black. The one idea to land is premium-restraint: a near-monochrome system where one warm accent and tight grotesk type carry all the personality.

## Color (hex · --var · role)
- `#ffffff` `--bg` — light marketing canvas; `#0e0e0e` `--bg-dark` — pure-black alternating sections + footer
- `#0e0e0e` `--fg` — near-black text on light; `#ffffff` `--fg-invert` — white text on dark sections
- `#f46b28` / `#ff5a1f` `--primary` — Brex orange/coral; accent, links, and accent CTAs (paired with dark or white text per surface)
- `#f5f5f4` `--card` — faint warm-gray light surface; `#1a1a1a` `--card-dark` raised tile on black
- `#6b6b6b` `--muted` — gray secondary on light; `#a1a1a1` muted on dark
- `#e5e5e3` `--border` — light hairline; `#262626` `--border-dark` divider on black
- `#d23b2e` `--destructive` — red. Contrast: orange `#f46b28` on white ≈ 3.1:1 — use as fill/accent or large text only, not 14px body.

## Typography
- Stack: `"Inter", "Söhne", system-ui, sans-serif` display/body — a tight neo-grotesk; `ui-monospace, monospace` for figures. Geometric, confident, no serif.
- Display 60/600/1.04/-0.025em · H1 42/600/1.08/-0.02em · H2 30/600/1.18/-0.015em · Card-title 20/600/1.3 · Body-lg 18/400/1.5 · Body 16/400/1.55 · Label 13/500/1.2/+0.01em · Figure-mono 16/500 tabular
- Headings at 600 with notably tight negative tracking (-2% to -2.5%) — words pack together for a premium, locked-up feel. Never light, never 700+ on display.

## Spacing, radius, depth, motion
- Base 4px; scale 4 · 8 · 12 · 16 · 24 · 32 · 48 · 64 · 96 · 120. Section padding 80–120px.
- Radius: 6 (chips/inputs) · 8 (buttons) · 12 (cards) · 16 (panels). Tight, squared-modern — no big pills.
- Depth strategy: borders + light/dark section alternation do the work. One soft shadow for floats: `rgba(0,0,0,0.08) 0 8px 24px`. On black, depth via `#1a1a1a` surface step, never shadow.
- Motion: 150–200ms ease-out; transform/opacity; subtle bg and border transitions. Crisp, not bouncy.

## Components (key)
- Primary CTA (light surface): bg `#0e0e0e` / text `#ffffff` / radius 8px / padding 12px 22px. Hover lighten ~8%; active translateY(1px); focus `0 0 0 3px rgba(244,107,40,0.4)` orange ring.
- Accent CTA: bg `#f46b28` / text `#0e0e0e` / radius 8px — one high-intent action; on dark sections becomes the white-text orange pill.
- Dark feature band: `#0e0e0e` bg, white H2 30/600, body `#a1a1a1`, tiles `#1a1a1a` with `1px solid #262626`, orange `#f46b28` accent line or icon.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: alternate pure-black `#0e0e0e` and white sections for rhythm — black is a primary surface, not just a footer.
- Do: keep the primary CTA dark/black and use orange as the accent or single high-intent button — flooding orange cheapens the premium tone.
- Don't: over-round — pills/9999px read consumer-friendly; Brex stays 6–16px squared-modern.
- Don't: set orange as small body text — it fails contrast on white; it's a fill, large display, or accent line.
- Don't: loosen the heading tracking — the locked-up -2% negative tracking IS the authority; default tracking reads generic.

## Example component prompts
- "Dark feature band on `#0e0e0e`: H2 Inter 30px weight 600 -0.015em white; body 16px weight 400 1.55 `#a1a1a1`; tile `#1a1a1a` `1px solid #262626` radius 12px with a 2px `#f46b28` accent line; orange CTA bg `#f46b28` text `#0e0e0e` radius 8px."
- "Hero on white: H1 Inter 42px weight 600 -0.02em `#0e0e0e`; dark CTA bg `#0e0e0e` text white radius 8px padding 12px 22px, focus ring `0 0 0 3px rgba(244,107,40,0.4)`; subhead 18px 1.5 `#6b6b6b`."
