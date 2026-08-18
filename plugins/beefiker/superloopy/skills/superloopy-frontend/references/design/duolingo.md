# Duolingo — Design Tokens (loopy-native)
> Category: consumer · Signature: candy green, fat rounded type, a 3D button you can press down

## Signature & atmosphere
Duolingo feels like a friendly game console: saturated candy colors, fat rounded everything, and buttons that physically sit on a colored "shelf" you press down into. The one recognizable idea is the bottom-border 3D button — a thick darker edge below the fill that compresses on tap, making the whole UI feel tactile and rewarding. Bright, playful, and confident; the brand owns a loud grassy green and is unafraid of color.

## Color (hex · --var · role)
- `#ffffff` `--bg` — canvas; `#131f23` `--fg` — text (Duo "eel" near-black with a teal undertone, not `#000`)
- `#58cc02` `--primary` — Feather Green; primary CTA fill (the brand color); `#58a700` `--primary-edge` — darker green for the 3D bottom border / pressed
- `#1cb0f6` `--accent` — Macaw Blue; secondary actions, links, info; edge `#1899d6`
- `#777777` `--muted` — secondary text; `#afafaf` tertiary/placeholder
- `#e5e5e5` `--border` — 2px outlines on neutral surfaces; `#f7f7f7` `--card` — quiet panel fill
- `#ff4b4b` `--destructive` — Cardinal red (wrong answer, hearts); `#ffc800` Bee gold (streaks/XP); `#ce82ff` Beetle purple (premium)
- Contrast: `--muted #777` on white ≈ 4.6:1 — body only, not 12px. Color carries meaning: green = correct/go, red = wrong, gold = reward.

## Typography
- Stack: `"din-round", "Feather Bold", "DIN Round Pro", Nunito, sans-serif`; substitute Nunito (heavy weights) — the brand voice is rounded-terminal and chunky.
- Display 32px / 800 / 1.20 · H1 28px / 800 / 1.25 · H2 22px / 700 / 1.30 · Body 17px / 500 / 1.50 · Button 15px / 700 / 1.20 / +0.8px UPPERCASE · Label 13px / 700 / +0.5px
- Signature: weight runs heavy (700–800) across the board and button labels are uppercase with positive tracking — the type is loud on purpose. There is no light weight.

## Spacing, radius, depth, motion
- Base 8px; scale 4 · 8 · 12 · 16 · 24 · 32 · 48; chunky padding inside controls (16px vertical on buttons).
- Radius: 12px cards · 16px buttons/inputs · 16px modals · 50% mascot/avatar — large, soft, no sharp corners anywhere.
- Depth = solid colored bottom border (the 3D shelf), not shadows: button has `border-bottom: 4px solid <edge>`; on `:active` it translates down 2–4px and the bottom border shrinks, simulating a press. Cards use a flat `0 2px 0 #e5e5e5` hard bottom-edge instead of a blur.
- Motion: press translateY 100ms, success bounce / confetti on correct; mascot wiggles. Easing is springy, not linear.

## Components (key)
- Primary CTA (3D button): bg `#58cc02` / text `#fff` / padding 14px 24px / radius 16px / `border-bottom: 4px solid #58a700` / label 15px/700 uppercase +0.8px / `:active` translateY(4px) + bottom border to 0. Hover lightens 4%.
- Lesson tile / answer choice: white card, 2px `#e5e5e5` border, radius 16px, `0 2px 0 #e5e5e5` hard edge; selected state swaps border + edge to `#1cb0f6` / `#84d8ff` and tints fill `#ddf4ff`.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: build buttons with a solid darker bottom-border edge and press them down on active; use heavy 700–800 rounded type; uppercase button labels; lean into saturated color with meaning.
- Don't: use soft blurry box-shadows for depth — the signature is a hard solid bottom edge (`0 2px 0`), not a Gaussian blur. Don't drop weight below 500 or reach for a thin/elegant typeface — chunky is the voice. Don't desaturate the palette into "tasteful" muted tones; the candy brightness is the brand. Don't square the corners.

## Example component prompts
- "Primary Duolingo button: `#58cc02` fill, white uppercase label din-round 15px/700/+0.8px, radius 16px, padding 14px 24px, `border-bottom: 4px solid #58a700`; on :active translateY(4px) and collapse the bottom border to 0."
- "Answer-choice card: white, 2px `#e5e5e5` border, radius 16px, hard edge `0 2px 0 #e5e5e5`; selected → border + edge `#1cb0f6`/`#84d8ff`, fill tint `#ddf4ff`."
- "Streak callout on `#fff`: gold `#ffc800` flame icon, number in 28px/800 `#131f23`, caption 13px/700 `#777`."
