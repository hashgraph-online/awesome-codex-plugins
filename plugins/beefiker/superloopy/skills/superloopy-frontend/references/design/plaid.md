# Plaid — Design Tokens (loopy-native)
> Category: fintech/crypto · Signature: clean white infrastructure canvas, deep-black type, restrained single-accent

## Signature & atmosphere
Plaid feels like the plumbing behind fintech made presentable: clean white surfaces, confident black headlines, and a quiet sense of connection — dots, nodes, and thin lines implying data flowing between accounts. It is developer-credible and trustworthy rather than flashy. The one idea to land is infrastructure-calm: a near-monochrome, generously-spaced system where structure and one restrained accent signal "reliable rails," not consumer hype.

## Color (hex · --var · role)
- `#ffffff` `--bg` — clean white canvas; `#f4f4f5` `--bg-subtle` — neutral gray section fill (no warm or cool cast)
- `#111111` `--fg` — deep near-black headings + body
- `#000000`/`#1a1a1a` `--cta` — black primary button fill (Plaid's CTA is monochrome)
- `#4b4eff` / `#3a3dd6` `--accent` — Plaid indigo/blue; links, icons, connection-line accents, sparing emphasis
- `#52525b` `--muted` — neutral slate secondary; `#a1a1aa` tertiary/placeholder
- `#e4e4e7` `--border` — neutral hairline; `#d4d4d8` emphasized
- `#fafafa` `--card` — barely-raised card surface
- `#dc2626` `--destructive` — red; `#16a34a` success. Contrast: `#52525b` on white ≈ 7:1 (body-safe); accent `#4b4eff` on white ≈ 5.7:1 (links/icons fine).

## Typography
- Stack: `"Inter", system-ui, -apple-system, sans-serif` everywhere; `ui-monospace, "SF Mono", monospace` for code snippets and API references (developer-facing). Clean, neutral grotesk.
- Display 56/600/1.06/-0.02em · H1 40/600/1.1/-0.015em · H2 30/600/1.2 · Card-title 20/600/1.3 · Body-lg 18/400/1.6 · Body 16/400/1.6 · Label 13/500/1.2/+0.01em · Code 14/450/1.6 mono
- Headings at 600 with tight tracking; body runs a comfortable 1.6 line-height — documentation-readable, generous, never cramped.

## Spacing, radius, depth, motion
- Base 8px; scale 4 · 8 · 12 · 16 · 24 · 32 · 48 · 64 · 96 · 120. Section padding 80–120px (airy).
- Radius: 6 (inputs/chips) · 8 (buttons) · 12 (cards) · 16 (modals). Squared-clean — no pills.
- Depth strategy: hairline borders first; one soft elevation `rgba(17,17,17,0.06) 0 4px 16px` for floating layers. Mostly flat — structure from whitespace and 1px dividers.
- Motion: 150–200ms ease-out; transform/opacity; subtle connection-line draw-in on data-flow diagrams. Calm, deliberate.

## Components (key)
- Primary CTA: bg `#000000` / text `#ffffff` / radius 8px / padding 12px 20px / no border. Hover `#1a1a1a`; active translateY(1px); focus `0 0 0 3px rgba(75,78,255,0.35)` indigo ring.
- Secondary button: bg `#ffffff` / text `#111111` / `1px solid #e4e4e7` / radius 8px; hover bg `#f4f4f5`.
- Connection diagram node: `#fafafa` tile, `1px solid #e4e4e7`, radius 12px; nodes linked by thin `#4b4eff` 1.5px lines (the data-flow motif); icons in indigo.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: keep the primary CTA monochrome black `#000000` — the instinct to make it brand-indigo is wrong; indigo is for links, icons, and connection lines.
- Do: give body a 1.6 line-height and big section gaps — Plaid reads like trustworthy documentation, not a dense dashboard.
- Don't: tint the neutrals warm or cool — keep grays truly neutral; a cast pulls it toward a different brand's identity.
- Don't: over-decorate — no gradients, no heavy shadows; the credibility comes from restraint and clean 1px structure.
- Don't: round to pills — 6–16px squared corners only; full-pill reads consumer-app, not infrastructure.

## Example component prompts
- "Connection diagram on white: three `#fafafa` node tiles, `1px solid #e4e4e7`, radius 12px, indigo icons, linked by thin 1.5px `#4b4eff` lines with a subtle draw-in on scroll; node labels 13px weight 500 `#52525b`."
- "Hero on white: H1 Inter 40px weight 600 -0.015em `#111111`; subhead 18px weight 400 1.6 `#52525b`; black CTA bg `#000000` text white radius 8px padding 12px 20px, hover `#1a1a1a`, focus ring `0 0 0 3px rgba(75,78,255,0.35)`. Hairline borders, no heavy shadow."
