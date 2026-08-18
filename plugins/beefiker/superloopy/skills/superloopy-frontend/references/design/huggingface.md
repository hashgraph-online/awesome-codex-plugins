# Hugging Face — Design Tokens (loopy-native)
> Category: ai-labs · Signature: sunshine-yellow community warmth with the 🤗 mascot

## Signature & atmosphere
Hugging Face feels like an open-source hackerspace that decided to be cheerful about it. The surface is plain white with honest black text and a single, unmistakable burst of sunflower yellow — the color of the hugging-face emoji that is the literal logo. It reads friendly and un-corporate: emoji in headings, hand-drawn warmth, dense developer content that never tries to look like an enterprise dashboard. The idea to get right is approachable + technical at once: yellow says "welcome," monospace says "real engineering."

## Color (hex · --var · role)
- `#ffffff` `--bg` — page background; `#ffffff` dark-mode flips to `#0b0f19` deep navy-black
- `#1b1b18` `--fg` — text (warm near-black, not pure `#000`)
- `#ffd21e` `--primary` — HF sunflower yellow; the logo color, used for primary fills, highlights, the mascot
- `#ff9d00` `--accent` — amber/orange, the gradient partner to yellow (yellow→orange warm gradient on hero/badges)
- `#6b7280` `--muted` — secondary text (slate gray); `#9ca3af` tertiary
- `#e5e7eb` `--border` — light gray hairline; `#f3f4f6` filled fill/divider
- `#0b0f19` `--card-dark` — the dark-mode surface (navy-tinted, not gray); `#1f2937` raised dark card
- `#ef4444` `--destructive` — red. Contrast: `#ffd21e` is a light yellow — NEVER put text on it lighter than `#1b1b18`; black-on-yellow only (≈ 13:1), yellow-on-white fails as text and must stay decorative/fill.

## Typography
- Stack: UI `"Source Sans 3", "Source Sans Pro", system-ui, sans-serif`; code `"IBM Plex Mono", "Source Code Pro", ui-monospace, monospace`. Source Sans = humanist, friendly; mono is load-bearing for model names, code, metrics.
- Display 48px / 700 / 1.10 / -0.5px · H1 36px / 700 / 1.15 · H2 28px / 600 / 1.20 · H3 20px / 600 / 1.30 · Body 16px / 400 / 1.55 · Mono-label 14px / 500 / 1.40 (model IDs, tags) · Label 13px / 600 / 1.30
- Headings DO go bold (600–700) here — this is the rare ai-labs brand where weight is part of the friendly, confident voice. Emoji are treated as first-class type and sit inline in headings.

## Spacing, radius, depth, motion
- Base 4px; scale 4/8/12/16/24/32/48px — denser than marketing sites, this is a tool.
- Radius scale 6 / 8 / 12px; pill (9999px) for tags and the ubiquitous model/dataset chips.
- Depth strategy: borders over shadows — flat cards with 1px `#e5e7eb`, reserving `rgba(0,0,0,0.05) 0 1px 2px` for menus/popovers only. The Hub aesthetic is functional and flat.
- Motion 120–180ms ease-out; minimal — subtle bg tint on hover, no flourish.

## Components (key)
- Primary CTA: bg `#ffd21e` / text `#1b1b18` (black, never white) / padding 8px 16px / radius 8px / 1px `#1b1b18` optional outline / hover darken to `#f5c211` + translate-y -1px / focus 2px `#ff9d00` ring.
- Model/dataset card (signature): white, 1px `#e5e7eb`, 12px radius; org avatar + mono model ID (`bert-base-uncased`), inline pill tags (`#f3f4f6` fill, mono 13px), small metric row (downloads/likes) in `#6b7280` — dense, scannable, emoji-friendly.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: keep yellow `#ffd21e` paired only with black text; lean on monospace for every model name, tag, and metric; let emoji live inside headings; build flat bordered cards.
- Don't: put white or light text on the yellow — the wrong instinct is "buttons get white text"; yellow demands black. Don't sanitize away the emoji and casual tone to look "enterprise" — the playfulness is the brand. Don't drop heavy shadows or glass blur; the Hub is deliberately flat and bordered. Don't use yellow as body-text or thin-icon color (it fails contrast); it's fills and accents only.

## Example component prompts
- "Hero on `#ffffff`: H1 Source Sans 3 48px / weight 700 / -0.5px with a 🤗 emoji inline; subhead 18px / 400 / 1.55 in `#6b7280`; yellow `#ffd21e` CTA with black `#1b1b18` text, 8px radius."
- "Model card: white, 1px `#e5e7eb`, 12px radius; mono model ID in IBM Plex Mono 14px/500; pill tags `#f3f4f6` fill mono 13px; download/like metrics in `#6b7280`."
- "Tag chip row: pill radius, `#f3f4f6` fill, IBM Plex Mono 13px, `#1b1b18` text."
- "Dark-mode panel: `#0b0f19` navy background, white text, cards `#1f2937` with `#1f2937` borders, yellow accents preserved."
