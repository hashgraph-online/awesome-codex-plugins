# Slack — Design Tokens (loopy-native)
> Category: productivity/saas · Signature: aubergine chrome, playful four-color confetti

## Signature & atmosphere
Slack feels like a friendly office that happens to run on software — busy, human, faintly irreverent. The recognizable idea is the deep aubergine sidebar paired with a hand-mixed confetti of warm hues, so the product reads as social before it reads as a tool. Surfaces stay bright and roomy while the chrome goes dark and saturated; the tension between a near-black eggplant frame and a clean white workspace is the whole look.

## Color (hex · --var · role)
- `#ffffff` `--bg` — workspace background; `#1d1c1d` `--fg` — foreground (Slack's near-black, faint warm cast, not pure black)
- `#4a154b` `--primary` — Aubergine; sidebar chrome, top brand fills, primary on dark
- `#611f69` `--primary-hover` — lifted aubergine for hover on dark chrome
- `#36c5f0` `--accent-sky` · `#2eb67d` `--accent-green` · `#ecb22e` `--accent-yellow` · `#e01e5a` `--accent-magenta` — the four confetti hues; use as categorical accents, never as body text
- `#616061` `--muted` — secondary text (~5.7:1 on white, AA)
- `#868686` `--placeholder` — placeholder/disabled
- `#ddd` → `#e0e0e0` `--border` — light hairline divider on white
- `#f8f8f8` `--muted-surface` — alternating band / message hover
- `#007a5a` `--cta` — Slack green CTA fill (white text ≈ 4.6:1, AA); `#1264a3` `--link` — link blue

## Typography
- Stack: `Lato, "Helvetica Neue", Helvetica, Arial, sans-serif` for marketing display; product UI rides system `Slack-Lato`/system-ui. Intent: rounded, warm-humanist, never corporate-cold.
- Display 60/900/1.04/-1.5px · H1 48/900/1.08/-1px · H2 36/800/1.15/-0.5px · CardTitle 22/700/1.25 · Body 18/400/1.50 · BodySm 16/400/1.50 · Nav 15/700/1.33 · Label 13/700/1.3/+0.4px (uppercase eyebrows)
- The signature is black-weight (900) display — Lato Black headlines carry the playful confidence; body stays 400.

## Spacing, radius, depth, motion
- Base 8px; scale 4 · 8 · 12 · 16 · 20 · 24 · 32 · 48 · 64 · 80px; section gaps 64–96px.
- Radius: 4px inputs · 8px buttons · 12px cards · 16px feature media · 9999px avatar/pill.
- Depth strategy: **borders + light single shadows**, not heavy stacks. Card `0 1px 4px rgba(0,0,0,0.08)`; hover lifts to `0 4px 12px rgba(0,0,0,0.12)`. Dark sidebar uses tonal-shift (selected row = `#350d36`), not shadow.
- Motion 120–200ms ease-out; transform/opacity only; hover background-tint on rows.

## Components (key)
- Primary CTA: bg `#007a5a` / text `#ffffff` / padding 12px 16px / radius 8px / border `1px solid transparent` / weight 900. Hover → darken ~6% (`#148567`); active → inset; focus → 4px `rgba(18,100,163,0.3)` ring.
- Aubergine button (on dark): bg `#fff` text `#4a154b`, or ghost = transparent + `1px solid rgba(255,255,255,0.3)`.
- Sidebar row: dark aubergine `#4a154b` base, selected `#350d36`, unread dot in `#36c5f0`, 8px 16px padding, 6px radius — the categorical confetti colors live here as channel/section accents.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: set display weight to 900 (Lato Black) — the heavy headline is the brand's playfulness; use the four confetti hues only as categorical accents.
- Don't: render headlines at a tasteful 500–600 — that flattens Slack into generic SaaS; the black weight is the voice.
- Don't: paint CTAs aubergine — `#4a154b` is *chrome*, the action color is green `#007a5a`. Don't let confetti colors touch body copy or you get a circus.

## Example component prompts
- "Hero on `#ffffff`: H1 Lato 48px / weight 900 / line-height 1.08 / -1px in `#1d1c1d`; subhead 18px/400/1.50 in `#616061`; green CTA `#007a5a`, white text 900 weight, 8px radius, 12px 16px padding, hover `#148567`."
- "Dark sidebar on `#4a154b`: channel rows 15px/700 in `rgba(255,255,255,0.7)`, selected row bg `#350d36` text `#fff`, unread badge `#e01e5a` pill, section eyebrow 13px/700/+0.4px uppercase."
- "Feature card `#ffffff`, `1px solid #e0e0e0`, 12px radius, shadow `0 1px 4px rgba(0,0,0,0.08)`; category dot in one confetti hue (`#2eb67d`); title 22px/700, body 16px/1.50 in `#616061`."
