# Resend — Design Tokens (loopy-native)
> Category: dev-tools · Signature: pure-black gallery stage where every edge is an icy frost-blue hairline

## Signature & atmosphere
Resend treats email infrastructure like a luxury object displayed in a darkened gallery — the page is pure black and content is lit like an exhibit, nothing competing for the eye. The one idea to copy: borders are not gray, they are a frosted, faintly-blue line that catches light against the void, so containers read as glass panels floating in space. Typography is editorial-grade — a serif masthead sized like a magazine cover sits over precise sans body, and monospace is promoted to a first-class design element.

## Color (hex · --var · role)
- `#000000` `--bg` — page/cards (genuine pure black, the canvas IS the whitespace); `#f0f0f0` `--fg` — primary text (near-white, never `#ffffff` except for max emphasis)
- `#ffffff` — reserved for highest-emphasis text and the solid-white CTA only
- `#a1a4a5` `--muted` — secondary text/descriptions; `#5c5c5c` tertiary/hover detail
- `rgba(214,235,253,0.19)` `--border` — the signature frost-blue hairline at 19% (every divider, button outline, card edge); `rgba(217,237,254,0.145)` lighter variant for list rows
- Accents (one per feature, never mixed in one component): `#ff801f` orange · `#3b9eff` blue · `#11ff99` green (at ~18% for fills) · `#ffc53d` yellow
- `#ff2047` `--destructive` (at 34% for error fills). Contrast: `#a1a4a5` on black ≈ 6:1 (fine for body); accents are vivid enough as text at full opacity, dim them only for backgrounds.

## Typography
- Stack: display serif `"Domaine Display", Georgia, serif` (hero only); display sans `"ABC Favorit", ui-sans-serif, system-ui` (section heads); body/UI `Inter, ui-sans-serif, system-ui`; code `"Commit Mono", ui-monospace, monospace`. Each font has one lane — they never cross.
- Display 96px / 400 / 1.00 / -0.96px (OpenType `"ss01","ss04","ss11"`) · Section 56px / 400 / 1.20 / -2.8px · Sub-head 20px / 400 / 1.30
- Body-lg 18px / 400 / 1.50 · Body 16px / 400 / 1.50 · Nav 14px / 500 / 1.43 / **+0.35px** (the only positive tracking) · Caption 12px / 500 / 1.33
- Code 16px / 400 / 1.50 in Commit Mono — shown prominently, not buried.

## Spacing, radius, depth, motion
- Base 8px; scale 2 / 4 / 6 / 8 / 12 / 16 / 20 / 24 / 32 / 40px; section gaps 80–120px so each block emerges from darkness like a scene.
- Radius: 4px ghost buttons/inputs · 8px tabs · 12–16px cards/images · 24px large panels · 9999px pill CTAs and tags.
- Depth = frost borders, not shadows (a shadow is invisible on pure black). Ring foundation `rgba(176,199,217,0.145) 0 0 0 1px`; explicit edge `1px solid rgba(214,235,253,0.19)`. Focus is a heavy `rgb(0,0,0) 0 0 0 8px` ring.
- Motion 150–200ms ease; transform/opacity only; subtle warm gradient glow may sit behind hero content.

## Components (key)
- Primary CTA (transparent pill): bg `transparent` / text `#f0f0f0` / padding 5px 12px / radius 9999px / border `1px solid rgba(214,235,253,0.19)` / hover bg `rgba(255,255,255,0.28)` / focus 8px black ring.
- Solid CTA (high contrast): bg `#ffffff` / text `#000000` / radius 9999px / padding 5px 12px — for the one "Get started" moment.
- Code preview panel: dark block, Commit Mono 16px, frost-border container at 24px radius, syntax tokens drawn from the accent set (`#ff801f`/`#3b9eff`/`#11ff99`/`#ffc53d`).

## Do / Don't (anti-convention — name the wrong instinct)
- Do: tint every border frost-blue (`rgba(214,235,253,0.19)`) — the instinct to reach for neutral gray borders is exactly what kills the look.
- Don't: lighten the background off `#000000` to a "softer" dark gray — the absolute void is non-negotiable here.
- Don't: use box-shadow for elevation — on black it does nothing; the frost hairline is the depth mechanism.
- Don't: set nav links in negative tracking — nav is the one place that runs **+0.35px**, airy against the compressed headlines.
- Don't: skip the OpenType stylistic sets on Domaine/Favorit — the alternate glyphs are the typographic fingerprint.

## Example component prompts
- "Hero on `#000000`: headline 96px Domaine Display weight 400, line-height 1.00, letter-spacing -0.96px, color `#f0f0f0`, OpenType `'ss01' 'ss04' 'ss11'`. Subtitle 20px ABC Favorit 400/1.30. Two pills: solid white (`#ffffff`/`#000000`) and transparent with frost border `rgba(214,235,253,0.19)`, both 9999px radius."
- "Feature card: transparent bg, NO gray border — use `1px solid rgba(214,235,253,0.19)`, 16px radius. Title 56px ABC Favorit 400 letter-spacing -2.8px; body 16px Inter 400 in `#a1a4a5`."
- "Code block: Commit Mono 16px on black, frost-border container 24px radius, syntax in `#ff801f`/`#3b9eff`/`#11ff99`."
