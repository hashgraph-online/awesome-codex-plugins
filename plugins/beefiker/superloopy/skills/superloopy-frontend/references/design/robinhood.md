# Robinhood — Design Tokens (loopy-native)
> Category: fintech/crypto · Signature: matte-black canvas with neon-green glow, market-data minimalism

## Signature & atmosphere
Robinhood feels like a trading terminal that fits in your pocket: deep matte-black surfaces, a single electric green that glows like a ticker going up, and type stripped to pure data. The mood is dark-mode-native and kinetic — numbers move, lines climb, green means alive. The one idea to land is signal-on-black: a near-monochrome dark UI where one luminous accent carries all the energy.

## Color (hex · --var · role)
- `#0a0a0a` `--bg` — matte near-black canvas; `#16181c` `--card` — charcoal surface lifted off black
- `#ffffff` `--fg` — pure white headings; `#e4e4e7` body on dark
- `#00c805` `--primary` — Robinhood neon green; gains, CTAs, active states, glow accents
- `#00a504` `--primary-hover` — pressed green (darken)
- `#9ca3af` `--muted` — cool gray secondary; `#6b7280` tertiary on dark
- `#26282d` `--border` — low-contrast dark divider; `#33363c` emphasized
- `#ff5000` `--destructive` — loss/down orange-red (the chart's red counterpart to green). Contrast: green `#00c805` on `#0a0a0a` ≈ 9:1, excellent for text and lines; muted `#9ca3af` on `#0a0a0a` ≈ 6:1.

## Typography
- Stack: `"Inter", system-ui, sans-serif` UI; `ui-monospace, "SF Mono", monospace` for prices/percentages with tabular numerals. Capsule-grotesque feel — clean, slightly geometric.
- Display 48/600/1.08/-0.02em · H1 34/600/1.12 · H2 26/600/1.20 · Card-title 18/600/1.30 · Body 16/400/1.5 `#e4e4e7` · Label 12/500/1.2/+0.02em uppercase `#9ca3af` · Price-mono 22/600/1.1 tabular · Delta-mono 14/500 tabular (green up / red down)
- Headings at 600; every price/percentage in tabular monospace so digits never jitter as they update.

## Spacing, radius, depth, motion
- Base 4px; scale 4 · 8 · 12 · 16 · 20 · 24 · 32 · 48 · 72. Section padding 48–72px.
- Radius: 8 (chips) · 12 (buttons/cards) · 16 (sheets) · 9999 (avatar/segmented toggles). Friendly, rounded.
- Depth strategy: NO drop shadows on black — depth from surface lightness steps (`#0a0a0a` → `#16181c` → `#26282d`). Accent glow only: `0 0 24px rgba(0,200,5,0.35)` on hero numbers/CTAs.
- Motion: 200–300ms ease for chart lines and number count-ups; transform/opacity; green glow pulse on positive ticks.

## Components (key)
- Primary CTA: bg `#00c805` / text `#0a0a0a` (dark text on green) / padding 12px 22px / radius 12px / no border. Hover `#00a504` + glow `0 0 20px rgba(0,200,5,0.4)`; active scale(0.98); focus `0 0 0 3px rgba(0,200,5,0.3)`.
- Buy/Sell segmented control: 9999px track `#16181c`, active segment `#00c805` (buy) text dark, divider `#26282d`.
- Ticker card: `#16181c` surface, radius 12px, 20px padding; symbol white 18/600, price mono 22/600 tabular, delta mono 14/500 colored `#00c805`/`#ff5000`.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: design dark-first — `#0a0a0a` canvas is the home surface, not an afterthought theme.
- Do: put DARK text on the green button — green-on-green or white-on-green is the wrong reflex; `#0a0a0a` on `#00c805` is the look.
- Don't: add box-shadows to lift cards on black — they vanish; use surface-lightness steps and the green glow instead.
- Don't: use green for losses or neutral chrome — green is strictly "up/go"; red `#ff5000` is "down". Mixing them destroys the market semantics.
- Don't: render prices in a proportional font — non-tabular digits shimmy on every update; always tabular mono.

## Example component prompts
- "Ticker card on `#16181c`, radius 12px, 20px padding: symbol Inter 18px weight 600 white; price monospace 22px weight 600 tabular-nums white; delta monospace 14px weight 500 `#00c805` for gains / `#ff5000` for losses."
- "Hero on `#0a0a0a`: H1 Inter 34px weight 600 white; green CTA bg `#00c805` text `#0a0a0a` radius 12px padding 12px 22px, hover glow `0 0 20px rgba(0,200,5,0.4)`; muted subhead 16px `#9ca3af`. No drop shadow — depth via `#16181c` surface step."
