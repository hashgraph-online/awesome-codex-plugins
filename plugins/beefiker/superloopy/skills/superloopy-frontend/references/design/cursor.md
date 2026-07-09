# Cursor — Design Tokens (loopy-native)
> Category: luxury-auto-tooling · Signature: warm cream paper, gothic compression, three typographic voices

## Signature & atmosphere
Cursor reads like a premium print publication that happens to be a code editor's marketing site. The recognizable idea is warmth where you expect cold: the canvas is a cream off-white (`#f2f1ed`), text is a warm yellow-brown near-black (`#26251e`), and even the error state carries warmth rather than clinical red. Borders are mixed in `oklab` space so warm-brown edges stay perceptually even across surfaces. Compressed gothic display type sits against airy margins — dense letters, open layout.

## Color (hex · --var · role)
- `#f2f1ed` `--bg` — warm cream page surface (NOT white — the whole system is warm-shifted); `#26251e` `--fg` — warm near-black text, yellow-brown undertone
- `#e6e5e0` `--surface` — card/secondary surface; surface ramp `#f7f7f4` → `#f2f1ed` → `#ebeae5` → `#e6e5e0` → `#e1e0db` for button tiers
- `#f54e00` `--accent` — Cursor Orange, brand highlight and active links; `#c08532` `--gold` — secondary premium accent
- `#cf2d56` `--error` — warm crimson (also the signature hover-text color); `#1f8a65` `--success` — warm-shifted teal-green
- `rgba(38,37,30,0.55)` `--muted` — 55% warm brown, secondary text; `rgba(38,37,30,0.1)` `--border` — standard edge (true value `oklab(0.263084 -0.00230259 0.0124794 / 0.1)`)
- Timeline accents: `#dfa88f` thinking · `#9fc9a2` grep · `#9fbbe0` read · `#c0a8dd` edit

## Typography
- Stack: `"CursorGothic", system-ui, "Helvetica Neue", Arial` (display/UI), `"jjannon", "Iowan Old Style", Georgia, serif` (editorial body, OpenType `"cswh"` swashes), `"berkeleyMono", ui-monospace, Menlo` (code). Three voices, three jobs.
- Display Hero 72px / 400 / 1.10 / **-2.16px** · Section 36px / 400 / 1.20 / -0.72px · Sub-head 26px / 400 / 1.25 / -0.325px · Title 22px / 400 / 1.30 / -0.11px — tracking relaxes toward 0 as size drops
- Body Serif 19.2px / 500 / 1.50 (jjannon, `"cswh"`) · Body 17.28px / 400 / 1.35 · Button 14px / 400 / 1.00 (CursorGothic, `"ss09"`) · Mono 12px / 400 / 1.67
- CursorGothic stays at weight 400 almost exclusively — hierarchy comes from size and negative tracking, not weight.

## Spacing, radius, depth, motion
- Base 8px with a fine sub-8 ramp: 1.5 · 2 · 2.5 · 3 · 4 · 5 · 6, then 8 · 10 · 12 · 14 · 16 · 24 · 32 · 48 · 64 · 96. The sub-8 increments do icon/text micro-alignment.
- Radius: 4px compact · 8px primary buttons/cards · 10px featured · full-pill (9999px) for tags/filters.
- Depth strategy: oklab borders + diffuse shadows. Edges use 10%/20% warm-brown rings; elevated cards use large-blur low-opacity shadows (`rgba(0,0,0,0.14) 0 28px 70px, rgba(0,0,0,0.1) 0 14px 32px`) so the page seems to open a space rather than float a card. Motion: color 150ms ease, shadow 200ms ease; hover shifts text to `#cf2d56`.

## Components (key)
- Primary button: bg `#ebeae5` (surface-300) / text `#26251e` / padding 10px 12px 10px 14px / radius 8px / no border. Hover text → `#cf2d56`; focus shadow `rgba(0,0,0,0.1) 0 4px 12px`.
- Pill tag: bg `#e6e5e0` / text `rgba(38,37,30,0.6)` / radius 9999px / padding 3px 8px / 14px CursorGothic 400.
- AI timeline: vertical steps each in its semantic color — thinking `#dfa88f`, grep `#9fc9a2`, read `#9fbbe0`, edit `#c0a8dd` — joined by a `rgba(38,37,30,0.1)` connector line.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: use warm tones everywhere — cream `#f2f1ed`, warm-black `#26251e`, never pure white/black for primary surfaces; scale CursorGothic tracking with size (-2.16px at 72px → 0 at 16px); hover text to the warm crimson `#cf2d56`.
- Don't: pick weight 600–700 to make a headline land — the instinct to add weight is wrong here; CursorGothic at 400 with aggressive negative tracking is the impact, and bolding it muddies the compression.
- Don't: drop in a cold-blue focus ring or pure `#fff`/`#000` — the reflex toward neutral cold UI strips the paper-and-ink warmth that is the entire identity.
- Don't: use single-purpose typography — collapsing the three voices into one sans loses the gothic/serif/mono editorial texture.

## Example component prompts
- "Hero on `#f2f1ed`: headline 72px CursorGothic 400, line-height 1.10, letter-spacing -2.16px, `#26251e`; subtitle 17.28px jjannon 400/1.35 in `rgba(38,37,30,0.55)`; primary button `#ebeae5` bg, 8px radius, 10px 14px padding, hover text → `#cf2d56`."
- "Card: `#e6e5e0` bg, 1px solid `rgba(38,37,30,0.1)`, 8px radius; 22px CursorGothic 400 title at -0.11px tracking; body 17.28px jjannon 400 in `rgba(38,37,30,0.55)`; links in `#f54e00`."
- "Pill tag: `#e6e5e0` bg, `rgba(38,37,30,0.6)` text, 9999px radius, 3px 8px padding, 14px CursorGothic 400."
