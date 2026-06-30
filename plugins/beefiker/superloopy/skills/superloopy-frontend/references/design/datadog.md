# Datadog — Design Tokens (loopy-native)
> Category: dev-tools · Signature: the purple of a thousand dashboards — dense data-dark UI with a single magenta-purple brand

## Signature & atmosphere
Datadog feels like a monitoring wall at 3am: an information-dense interface tuned to surface signal fast, anchored by one unmistakable purple (`#632ca6`) that doubles as both logo and primary action. The recognizable idea is high-density legibility — tight rows, small text that stays sharp, and a calm slate-gray chrome that lets the colored time-series data and status dots do the talking. Marketing surfaces go bright and friendly; the product itself is a dark, focused observability cockpit.

## Color (hex · --var · role)
- `#ffffff` `--bg` — light/marketing canvas; `#1c1c26` `--bg-dark` — product dashboard canvas (blue-slate, not `#000`); `#26263a` panel surface on dark
- `#3b3b54` `--fg` heading on light / `#11111a` body text; `#e6e6ef` text on dark
- `#632ca6` `--primary` — Datadog purple; logo + primary CTA fill; hover `#52248a`, active `#46206f`
- `#7c3aed` `--accent` — brighter violet for highlights/links; `#774aa4` muted purple variant
- `#774aa4`→data hues: `#3399ff` blue · `#00b16a` green (healthy) · `#ffb800` warn · `#e3303e` error/critical — the status palette
- `#6c6c7c` `--muted` — secondary text; `#9b9bab` tertiary/placeholder
- `#d4d4e0` `--border` — hairline on light; `#3a3a52` border on dark
- Contrast: muted `#6c6c7c` on white ≈ 4.7:1 (AA body). Status colors are semantic — green/red mean healthy/critical, never decoration.

## Typography
- Stack: UI `"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif` (clean grotesque tuned for dense numeric UI); code `"Roboto Mono", ui-monospace, monospace` for metrics/queries.
- Display 56px/700/1.1/-1px · H1 36px/700/1.2 · H2 28px/600/1.25 · H3 20px/600/1.3 · Body 16px/400/1.5 · Body-sm 14px/400/1.43 · Data 13px/500/1.3 (dense table/metric size) · Label 11px/600/1.2/+0.4px UPPERCASE
- Marketing leans heavier (700 display) than most dev-tools; the product UI lives at 13–14px with 500 weight for scannable metric density. Tabular numerals (`"tnum"`) on all metric/timeseries text.

## Spacing, radius, depth, motion
- Base 4px (denser than the usual 8 — this is a data product); scale 4 · 8 · 12 · 16 · 20 · 24 · 32 · 48. Table rows on 4/8.
- Radius: 4px inputs/chips · 6px buttons · 8px cards/widgets · 12px modals · pill for status badges.
- Depth strategy = borders on dark, soft shadows on light. Dashboard widgets separate by `1px solid #3a3a52` on the dark canvas. Light cards lift with `rgba(28,28,38,0.08) 0 1px 3px, ... 0 4px 12px`. Focus ring `0 0 0 2px rgba(99,44,166,0.4)`.
- Motion 100–200ms ease-out; data refresh transitions are fast and non-distracting (opacity/transform only).

## Components (key)
- Primary CTA: bg `#632ca6` / text `#ffffff` / padding 8px 16px / radius 6px / no border / hover bg `#52248a` / focus `2px rgba(99,44,166,0.4)` ring.
- Secondary button: bg `#ffffff` / text `#632ca6` / `1px solid #d4d4e0` / radius 6px / hover bg `#f5f3fa`.
- Status badge/dot: pill, 11px/600 uppercase, color from the semantic set — `#00b16a` OK · `#ffb800` warn · `#e3303e` critical — paired with a leading dot of the same hue.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: design on a 4px base for genuine data density and let the purple be the only brand color while green/yellow/red stay strictly semantic status.
- Don't: loosen the rows to a roomy 8/16 marketing rhythm in the product UI — Datadog's value is information density; airy spacing wastes the dashboard.
- Don't: use the status green/red as decorative accents — they read as health signals; a green button next to metrics implies "healthy," not "click me."
- Don't: pick a warm or neutral brand color — the magenta-leaning purple (`#632ca6`) is the entire brand recall; a generic blue erases it.

## Example component prompts
- "Marketing hero on `#ffffff`: H1 56px Inter weight 700, line-height 1.1, letter-spacing -1px, `#11111a`; subhead 18px/400 `#6c6c7c`. Purple CTA `#632ca6` white text, 6px radius, 8px 16px, hover `#52248a`; secondary `1px solid #d4d4e0`, `#632ca6` text."
- "Dashboard widget on `#1c1c26`: panel `#26263a`, `1px solid #3a3a52`, 8px radius. Title 13px Inter 600 uppercase `#9b9bab` +0.4px tracking; metric 28px/600 tabular-nums `#e6e6ef`; status dot + pill `#00b16a` for OK, `#e3303e` for critical."
