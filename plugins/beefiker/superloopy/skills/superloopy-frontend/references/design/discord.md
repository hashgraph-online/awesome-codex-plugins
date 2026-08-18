# Discord — Design Tokens (loopy-native)
> Category: productivity/saas · Signature: blurple on near-black, rounded-playful gaming UI

## Signature & atmosphere
Discord feels like a clubhouse, not an enterprise app — soft, rounded, slightly nocturnal, built for hanging out. The one recognizable idea is Blurple (`#5865f2`) glowing on deep blue-charcoal surfaces; the dark theme is the *default* personality, not an option. Everything is friendly and bubbly: fat radii, chunky buttons, generous padding, and a typeface that reads approachable rather than serious.

## Color (hex · --var · role)
- `#313338` `--bg` — primary app surface (dark theme is canonical); `#dbdee1` `--fg` — foreground text (off-white, never pure white)
- `#1e1f22` `--bg-deep` — deepest layer (server list / sidebar); `#2b2d31` `--bg-mid` — channel column
- `#5865f2` `--primary` — Blurple; CTAs, links, brand fills everywhere
- `#4752c4` `--primary-active` — pressed/darker blurple
- `#23a559` `--success` · `#f0b232` `--warning` · `#da373c` `--destructive` — status hues
- `#949ba4` `--muted` — secondary text on dark (~5.2:1 on `#313338`, AA)
- `#80848e` `--placeholder` — muted/timestamps
- `#3f4147` `--border` — divider on dark surfaces
- Light-mode pairing (less canonical): `#ffffff` `--bg-light` / `#060607` `--fg-light`

## Typography
- Stack: `"gg sans", "Noto Sans", "Helvetica Neue", Helvetica, Arial, sans-serif` — gg sans is rounded-humanist; intent is warm, casual, legible at small sizes in dense chat.
- Display 56/700/1.10/-1px · H1 40/700/1.15/-0.5px · H2 28/600/1.20 · CardTitle 20/600/1.25 · Body 16/400/1.50 · BodySm 14/400/1.43 · Nav 16/500/1.30 · Label 12/700/1.33/+0.4px (uppercase channel headers)
- Display weight tops out at 700; the playfulness comes from radius and color, not from extreme type weight.

## Spacing, radius, depth, motion
- Base 8px (with 4px micro-steps); scale 4 · 8 · 12 · 16 · 20 · 24 · 32 · 40 · 64px.
- Radius: **fat by default** — 8px inputs · 8px buttons · 16px cards · 24px modals/large surfaces · 50% avatars & the squircle→circle server-icon morph.
- Depth strategy: **tonal layering** (stacked grays `#1e1f22` < `#2b2d31` < `#313338` < `#383a40`) does the elevation work; shadows are soft and rare (`0 8px 16px rgba(0,0,0,0.24)` on popovers/modals only).
- Motion 150–250ms ease; the server-icon hover morphs border-radius 50%→16px; transform/opacity only.

## Components (key)
- Primary CTA: bg `#5865f2` / text `#ffffff` / padding 10px 16px / radius 8px / no border / weight 500. Hover → `#4752c4`; active → `#3c45a5` + slight darken; focus → `0 0 0 2px #ffffff` inset-style ring on dark.
- Server icon: 48px square, radius 16px default morphing to 50% circle, hover → 16px squircle + pill indicator `#fff` 4px-wide at left edge.
- Channel list row: 8px 8px padding, 4px radius, muted `#949ba4` text, hover bg `#35373c`, active/selected bg `#404249` with `#f2f3f5` text.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: design dark-first on layered grays (`#1e1f22`/`#2b2d31`/`#313338`) and use Blurple `#5865f2` as the single hero color; keep radii generous (16–24px).
- Don't: default to a white background — Discord's identity *is* the dark theme; a light-first mock reads as the wrong product.
- Don't: tighten radii to 4–6px "professional" corners — the soft, bubbly geometry is the personality. And don't use pure `#000`/`#fff`; the off-tones (`#1e1f22`, `#dbdee1`) keep it from feeling harsh.

## Example component prompts
- "Hero on `#313338`: H1 gg sans 40px / weight 700 / 1.15 / -0.5px in `#dbdee1`; subhead 18px/400/1.50 in `#949ba4`; Blurple CTA `#5865f2`, white text, 8px radius, 10px 16px padding, hover `#4752c4`."
- "Server sidebar on `#1e1f22`: 48px icons, radius 16px morphing to 50% on hover, active pill `#fff` 4px at left; channel column `#2b2d31`, rows 14px/500 in `#949ba4`, selected bg `#404249`."
- "Modal on `#313338`, 24px radius, shadow `0 8px 16px rgba(0,0,0,0.24)`, title 20px/600 in `#f2f3f5`, body 16px/1.50 in `#dbdee1`, Blurple confirm + ghost cancel."
