# Ramp — Design Tokens (loopy-native)
> Category: fintech/crypto · Signature: warm sand canvas, signal-yellow accent, monospace-flavored efficiency

## Signature & atmosphere
Ramp feels like a finance tool that values your time: warm off-white paper, dense purposeful type, and a single high-voltage yellow that marks exactly where to act. It reads efficient before it reads pretty — tight grids, real data, a hint of monospace structure. The one idea to land is speed-as-aesthetic: every element looks like it's there to save a minute, never to decorate.

## Color (hex · --var · role)
- `#fcfbf7` `--bg` — warm sand off-white (faint yellow undertone, not pure white); `#ffffff` `--card` — clean white tile lifted off the sand
- `#1c1c1a` `--fg` — warm near-black for headings + body
- `#f1c84b` / `#e8b817` `--primary` — Ramp signal yellow; used as accent + on small CTAs, paired with dark text
- `#1c1c1a` `--cta` — dark primary button fill (yellow is accent, dark does the heavy CTA)
- `#6b6a64` `--muted` — warm slate secondary text; `#9a988f` tertiary
- `#e8e6dd` `--border` — warm hairline; `#d6d3c7` emphasized
- `#c63434` `--destructive` — clay-red; `#0f7a4d` success. Contrast: yellow `#f1c84b` is non-AA for text — only as fill behind dark `#1c1c1a` text or as a 4px accent bar.

## Typography
- Stack: `"Inter", system-ui, sans-serif` display/body; `ui-monospace, "Berkeley Mono", monospace` for figures, labels, and data tables. The mono is the flavor — used more than most fintechs.
- Display 52/600/1.06/-0.02em · H1 38/600/1.12/-0.015em · H2 28/600/1.20 · Card-title 19/600/1.30 · Body-lg 18/400/1.5 · Body 15/400/1.55 · Label-mono 12/500/1.2/+0.02em uppercase · Figure-mono 16/500/1.2 tabular
- Headings at 600, tight tracking; eyebrow labels in uppercase monospace — the signature "terminal" cue.

## Spacing, radius, depth, motion
- Base 4px; scale 4 · 8 · 12 · 16 · 20 · 24 · 32 · 40 · 64 · 88. Section padding 64–88px.
- Radius: 4 (chips/inputs) · 8 (buttons) · 10 (cards) · 14 (panels). Restrained — nothing fully round.
- Depth strategy: hairline borders + one whisper shadow `rgba(28,28,26,0.05) 0 1px 2px`; elevated cards `rgba(28,28,26,0.08) 0 6px 16px`. Borders carry most structure.
- Motion: 120–160ms ease-out; transform/opacity; subtle bg on hover. Snappy, never floaty.

## Components (key)
- Primary CTA: bg `#1c1c1a` / text `#fcfbf7` / padding 10px 18px / radius 8px / no border. Hover lighten ~6%; active translateY(1px); focus `0 0 0 3px rgba(241,200,75,0.45)` yellow ring.
- Accent CTA (sparing): bg `#f1c84b` / text `#1c1c1a` / radius 8px — for one high-intent moment per view.
- Data table row: mono figures tabular-nums, `1px solid #e8e6dd` row divider, 12px label-mono uppercase header `#6b6a64`, hover row bg `#fcfbf7`.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: let dark `#1c1c1a` carry the primary CTA and keep yellow as accent — the instinct to make the brand-yellow the button fails contrast.
- Do: use uppercase monospace for eyebrows/labels and tabular mono for every figure — the "tool, not toy" signal.
- Don't: bleach the canvas to pure white — the warm sand `#fcfbf7` is the texture; white reads generic SaaS.
- Don't: over-round — pills/9999px radius read consumer; Ramp stays at 8–14px.
- Don't: pour yellow across large fills — it's a 4px bar or a single button, never a hero background.

## Example component prompts
- "Expense table on `#fcfbf7`: header labels uppercase monospace 12px weight 500 +0.02em `#6b6a64`; amount cells monospace 16px weight 500 tabular-nums `#1c1c1a`; row divider `1px solid #e8e6dd`, hover bg `#ffffff`."
- "Hero on `#fcfbf7`: H1 Inter 38px weight 600 -0.015em `#1c1c1a`; dark CTA bg `#1c1c1a` text `#fcfbf7` radius 8px, focus yellow ring `0 0 0 3px rgba(241,200,75,0.45)`; a single 4px `#f1c84b` accent bar under the eyebrow."
