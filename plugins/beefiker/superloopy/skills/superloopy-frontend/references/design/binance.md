# Binance — Design Tokens (loopy-native)
> Category: fintech/crypto · Signature: gold ingot accent on monochrome, 50px pill CTAs, trading-floor urgency

## Signature & atmosphere
Binance feels like a polished trading floor: stark white surfaces alternate with near-black panels, mirroring the bull/bear duality of markets. The one unmistakable move is Binance Yellow — a warm gold cutting through cold grey text and razor borders like an ingot on a steel desk, and it is the system's only accent. Everything else is monochrome plus data-driven green-up/red-down. Numbers are prominent; trust comes from clarity, not decoration.

## Color (hex · --var · role)
- `#ffffff` `--bg` — light canvas; `#222126` `--card-dark` — dark panels (near-black, faint purple undertone)
- `#1e2026` `--fg` — primary text/ink + text ON yellow buttons; `#32313a` nav/secondary copy
- `#f0b90b` `--primary` — Binance Yellow, the singular accent + CTA fill; `#ffd000` `--accent` — gold pill border/secondary fill; `#d0980b` active/pressed yellow
- `#848e9c` `--muted` — tertiary/metadata grey (the quiet workhorse); `#777e90` muted nav
- `#e6e8ea` `--border` — card/section borders; `#2b2f36` dark card surface; `#f5f5f5` snow surface
- `#0ecb81` positive (up); `#f6465d` `--destructive` / negative (down); `#1eaedb` focus-blue (hover/focus state)
- Contrast note: never yellow-on-yellow; pair `#f0b90b` bg with `#1e2026` text. `#848e9c` on white is borderline small — fine for metadata, not body.

## Typography
- Stack: `BinancePlex, Arial, sans-serif` (tabular numerals by default — built for price columns). System fallback `system-ui, "Segoe UI", Roboto`.
- Display-hero 60/700/1.08 · Display-2 34/700/1.00 · H1 28/500/1.00 · H2 24/700/1.00 · H3 24/600/1.00 · H4 20/600/1.25 · Body-lg 20/500/1.50 · Body 16/500/1.50 · Body-semibold 16/600/1.30 · Button 16/600/1.25/+0.16px · Button-sm 14.4/600/1.60/+0.72px · Caption 14/500/1.43 · Small 12/600/1.0 · Tiny 11/500/1.0
- Weights lean heavy (500-700); tight 1.00-1.25 line-heights on headings echo dashboard density, body opens to 1.50.

## Spacing, radius, depth, motion
- Base 8px; scale 4 · 8 · 12 · 16 · 20 · 24 · 32 · 48 · 64 · 80.
- Radius: 1 · 2 · 6 (non-pill buttons/small cards) · 8 (inputs/data cards) · 10 (nav pills) · 12 (content cards) · 24 (video/hero imagery) · 50 (CTA pills/search).
- Depth strategy: whisper shadows at ~5%. Card `rgba(32,32,37,0.05) 0 3px 5px`; hover `rgba(8,8,8,0.05) 0 3px 5px 5px`; pill CTA `rgb(153,153,153) 0 2px 10px -3px`.
- Motion: background/box-shadow 200ms ease only — financial stability, nothing flashy.

## Components (key)
- Primary CTA (pill): bg `#f0b90b` / text `#1e2026` 16/600 / radius 50px / padding 6px 32px. Hover→`#1eaedb` bg white text; active `#d0980b`; focus blue bg + 2px black outline.
- Secondary (outlined pill): white bg, `#f0b90b` text, `1px solid #f0b90b`, radius 50px, pill shadow.
- Content card: white (or `#2b2f36` on dark), `1px solid #e6e8ea`, radius 12px, 5% shadow; data card radius 8px.
- Price ticker: flat borderless strip, 14/600 ink, `#0ecb81`/`#f6465d` deltas, `#e6e8ea` bottom border.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: keep Binance Yellow as the ONLY brand accent; all other color is data (green up, red down).
- Do: use 50px pills for CTAs and 12px for content cards; alternate white/`#222126` sections in hard cuts.
- Don't: introduce a second brand color or tint cards for semantic state — the instinct to colorize backgrounds breaks the monochrome-plus-gold rule; use text color instead.
- Don't: stack heavy shadows or hover-lift — 5% is the trust ceiling.
- Don't: set headings below weight 500 or round content cards above 12px — lighter/softer reads as un-authoritative here.

## Example component prompts
- "Hero on `#ffffff`: headline 60px BinancePlex weight 700 line-height 1.08 `#1e2026`; subtitle 20px/500 `#848e9c`; yellow pill CTA bg `#f0b90b` text `#1e2026` radius 50px padding 6px 32px, hover bg `#1eaedb` white text."
- "Feature grid 3-col 24px gap: white cards radius 12px, shadow `rgba(32,32,37,0.05) 0 3px 5px`, `#f0b90b` icon, 20px/600 heading, 14px/500 `#848e9c` body. Dark section `#222126` uses `#2b2f36` cards."
