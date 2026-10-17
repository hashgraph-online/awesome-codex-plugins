# BMW — Design Tokens (loopy-native)
> Category: luxury-auto-tooling · Signature: whispered authority — light 300 display, one engineered blue

## Signature & atmosphere
BMW is German precision rendered as interface: dark photographic heroes alternating with clean white content, paced like a showroom where each car is spotlit against darkness. The recognizable idea is a typographic tension nothing else uses — massive uppercase display set at weight 300 (a whisper, not a shout) against navigation set at weight 900. Every corner is square (0px); every line-height is tight (1.15–1.30). Confidence without raising its voice.

## Color (hex · --var · role)
- `#FFFFFF` `--bg` — primary surface / content sections (`--site-context-theme-color`); dark photographic sections for heroes
- `#262626` `--fg` — near-black primary text on white (not pure `#000`)
- `#1C69D4` `--primary` — BMW Blue, interactive accent ONLY (`--site-context-highlight-color`); never a background or large fill
- `#0653B6` `--focus` — BMW Focus Blue, keyboard-focus and active states (`--site-context-focus-color`)
- `#757575` `--muted` — secondary text / metadata (`--site-context-metainfo-color`); `#BBBBBB` `--muted-2` — tertiary text, footer
- `#FFFFFF` `--fg-on-dark` — links/text on dark hero photography (links hover to white)
- Borders: hairline white bottom-borders on dark surfaces (`1px solid #FFFFFF`); minimal elsewhere — depth comes from dark/light contrast

## Typography
- Stack: `"BMWTypeNextLatin Light", Helvetica, Arial, "Hiragino Sans", Meiryo` for display; `"BMWTypeNextLatin", …` for body/UI. One family, weight extremes.
- Display Hero 60px / 300 / 1.30 / `text-transform: uppercase` — the defining gesture, light-weight monumental type
- Section Heading 32px / 400 / 1.30 · Nav Emphasis 18px / 900 / 1.30 · Body 16px / 400 / 1.15 · Button 16px / 700 / 1.20 · Button-alt 16px / 400 / 1.15
- Active weights are extremes only: 300 (display), 400 (body), 700 (buttons), 900 (nav). No 500–600.

## Spacing, radius, depth, motion
- Base 8px; scale 8 · 12 · 16 · 20 · 24 · 30 · 32 · 40 · 45 · 56 · 60. Showroom pacing: generous padding around dark heroes, compressed line-heights inside content.
- Radius: 0px everywhere — the most angular system here, sharp rectangles by identity.
- Depth strategy: borders + dark/light contrast, effectively no shadows. The contrast between full-bleed dark photography and white content does all the elevation work; focus state is a `#0653B6` ring. Motion: clean, no scale/translate; hover holds color, removes underline.

## Components (key)
- Primary button: 16px BMWTypeNextLatin weight 700, line-height ~1.20, padding-driven height, 0px radius, white bottom-border (`1px solid #FFFFFF`) on dark surfaces. Sharp rectangle.
- Hero: full-bleed dark automotive photography, headline 60px / 300 / uppercase / 1.30 in white, no rounded corners anywhere.
- Content section: white bg, 32px/400/1.30 `#262626` heading, 16px/400/1.15 body — information-dense, nothing breathes.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: set the 60px hero at weight 300 uppercase — light display is the brand voice; keep all corners at 0px; reserve `#1C69D4` for interactive elements only.
- Don't: use weight 600–700 for display — the universal instinct that "big headline = bold" inverts BMW; the whisper at 300 against 900 nav is the whole signature.
- Don't: paint `#1C69D4` onto backgrounds or large surfaces — the reflex to use the brand blue as a hero fill turns precision into a generic blue SaaS page.
- Don't: relax line-heights for "breathing room" — 1.15–1.30 compression is intentional; loosening it dissolves the engineered density.

## Example component prompts
- "Hero: full-width dark automotive photo, headline 60px BMWTypeNextLatin Light weight 300, uppercase, line-height 1.30, white text. Zero border-radius anywhere."
- "Navigation on dark: BMWTypeNextLatin 18px weight 900 links, white text, hover stays white with no underline, sharp rectangular layout, logo 54x54."
- "White content section: 32px/400/1.30 `#262626` heading, 16px/400/1.15 body, `#757575` metadata, `#1C69D4` only on the inline link."
