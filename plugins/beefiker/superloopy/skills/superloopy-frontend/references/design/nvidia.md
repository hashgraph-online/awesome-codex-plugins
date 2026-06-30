# NVIDIA — Design Tokens (loopy-native)
> Category: brand-web-media · Signature: black canvas, one lime-shifted green as signal-not-surface, 2px engineered corners

## Signature & atmosphere
NVIDIA feels like GPU silicon rendered as a webpage: a true-black field, white text, and a single lime-shifted green so specific it works as a fingerprint. The recognizable idea is green-as-signal — `#76b900` lives in 2px borders, link underlines, and CTA outlines, but never floods a surface; the moment it becomes a background it stops being NVIDIA. Corners hold a sharp 2px, type leans bold by default, and depth comes from black-against-white material contrast, not soft light.

## Color (hex · --var · role)
- `#000000` `--bg` — true-black dominant canvas; `#ffffff` `--fg` — white text on dark, also light-section background
- `#76b900` `--primary` — NVIDIA Green: borders, underlines, CTA outlines, active state — outline color, not fill
- `#bff230` accent-light — bright lime for highlights/hover; `#3860be` link-hover (blue shift on every link); `#1eaedb` button-hover; `#007fff` button-active
- `#a7a7a7` `--muted` — Gray 300 body on dark; `#898989` Gray 400 metadata; `#757575` Gray 500 footer/placeholder
- `#5e5e5e` `--border` — subtle divider/section border; `#1a1a1a` `--card` — near-black card surface on black pages
- `#e52020` `--destructive` — Red 500; `#3f8500` success (darker than brand green so the two never read as one)
- Note: green is a signal color only. As a large fill or text-on-green block it reads off-brand — keep it to 2px strokes and underlines.

## Typography
- Stack: `"NVIDIA-EMEA", Arial, Helvetica, sans-serif` — industrial, European, no geometric playfulness
- Display hero 36px / 700 / 1.25 / 0 · Section heading 24px / 700 / 1.25 · Card title 20px / 700 / 1.25
- Sub-heading 22px / 400 / 1.75 (the one relaxed line-height) · Body-large 18px / 700 / 1.67
- Body 16px / 400 / 1.50 · Body-small 15px / 400 / 1.67 · Caption 14px / 600 / 1.50
- Button 16px / 700 / 1.25 · Button-compact 14.4px / 700 / 1.00 / +0.144px · Nav link 14px / 700 / 1.43 UPPERCASE
- Bold (700) is the default voice — headings, buttons, links, nav all sit at 700; weight 400 is reserved strictly for body. Tracking is normal everywhere except compact buttons (+0.144px). Nav is uppercase like hardware labels.

## Spacing, radius, depth, motion
- Base 8px; tight technical scale 2 · 4 · 8 · 11 · 13 · 16 · 24 · 32px (note the odd 11/13 button paddings); section padding 48–80px
- Radius: 1px micro spans · `2px` the universal default for buttons/cards/inputs · `50%` avatars — sharp engineered corners are the brand
- Depth strategy: material contrast + one shadow. Single elevation token `rgba(0,0,0,0.3) 0 0 5px` for cards/modals; otherwise depth = black section beside white section, or a green 2px border. No glassmorphism, no blur — clarity over atmosphere.
- Motion: short ~150ms color/background swap on hover; active may `scale(1)` reset, no decorative lift.

## Components (key)
- Primary CTA (green outline): bg `transparent` / text `#000000` (or `#ffffff` on dark) / padding 11px 13px / border `2px solid #76b900` / radius 2px / 16px·700 / hover bg `#1eaedb` + white text / active bg `#007fff` + `1px solid #003eff` / focus outline `#000000` 2px, opacity 0.9 — fill appears only on hover, never at rest
- Product card: bg `#ffffff` or `#1a1a1a` / radius 2px / shadow `rgba(0,0,0,0.3) 0 0 5px` / title 20px·700 with a `border-bottom 2px solid #76b900` green underline accent / bold heading + 15px·400 `#757575` description

## Do / Don't (anti-convention — name the wrong instinct)
- Do: use `#76b900` as a 2px border / underline / outline only; default buttons to transparent-with-green-border; set headings and CTAs at weight 700.
- Don't: fill a surface or button background with green — the instinct to "use the brand color as a background" is exactly wrong; green is a signal, fill is hover-only.
- Don't: round corners past 2px — soft 8–16px radii read as generic SaaS, not engineered hardware.
- Don't: set body in weight 700 or headings in 400 — bold is the chrome, 400 is only for paragraphs; and every link hovers to `#3860be` regardless of its rest color.

## Example component prompts
- "Hero on `#000000`: headline 36px NVIDIA-EMEA / 700 / 1.25 in `#ffffff`; subtitle 18px/400/1.67 in `#a7a7a7`; CTA transparent bg, `2px solid #76b900` border, 2px radius, 11px 13px padding, white text; hover bg `#1eaedb`, text white."
- "Product card: `#ffffff` bg, 2px radius, shadow `rgba(0,0,0,0.3) 0 0 5px`; title 20px/700/1.25 `#000000` with `border-bottom 2px solid #76b900`; body 15px/400/1.67 `#757575`."
- "Nav bar: `#000000`, NVIDIA wordmark left; links 14px/700/1.43 UPPERCASE `#ffffff`, hover `#3860be`; green-outline CTA right-aligned."
