# Stripe — Design Tokens (loopy-native)
> Category: fintech/crypto · Signature: whisper-weight headlines floating on blue-tinted shadow

## Signature & atmosphere
Stripe reads like a financial institution rebuilt by a type foundry: a bright white field, deep-navy text, and one saturated violet that does all the interactive work. The single most recognizable move is the headline set in weight 300 — light enough to feel ethereal yet so composed it never looks timid. Elevation is the second tell: shadows are tinted blue-gray, not neutral, so even a floating card stays on-brand.

## Color (hex · --var · role)
- `#ffffff` `--bg` — page + card background; `#061b31` `--fg` — foreground, a deep navy, never pure black (warmer, financial-grade)
- `#533afd` `--primary` — CTA fill, links, active state (saturated blue-violet); `#4434d4` `--primary-hover`
- `#665efd` `--accent` — input/range highlight; `#ea2261` / `#f96bee` decorative gradient only (ruby→magenta), never on buttons
- `#64748d` `--muted` — body/secondary text; `#273951` `--label` — form labels
- `#e5edf5` `--border` — default dividers; `#b9b9f9` active/selected border
- `#1c1e54` `--card-dark` — immersive dark sections (deep indigo, not black)
- `#108c3d` text on `rgba(21,190,83,0.2)` — success badge; `--destructive` `#ea2261` reserved, use sparingly
- Contrast note: `#64748d` body on `#ffffff` clears AA for normal text; verify any violet-on-white link at small sizes.

## Typography
- Stack: `sohne-var, "SF Pro Display", sans-serif` display+body; `SourceCodePro, SFMono-Regular, monospace` for code. OpenType `"ss01"` on ALL text (alternate glyphs are the brand); `"tnum"` for tabular figures in data.
- Display 56/300/1.03/-1.4px · Display-2 48/300/1.15/-0.96px · H2 32/300/1.10/-0.64px · H3 22/300/1.10/-0.22px · Body-lg 18/300/1.40/normal · Body 16/300-400/1.40/normal · Button 16/400/1.0/normal · Link 14/400/1.0 · Caption 13/400 · Code 12/500/2.0
- Tracking tightens with size and relaxes to normal at 16px and below.

## Spacing, radius, depth, motion
- Base 8px; dense low end: 4 · 6 · 8 · 10 · 12 · 14 · 16 · 20 (every 2px from 4-12 for data UI).
- Radius: 4 (workhorse) · 5 · 6 (nav) · 8 (featured). No pills.
- Depth strategy: layered blue-tinted shadows. Standard `rgba(50,50,93,0.25) 0 30px 45px -30px, rgba(0,0,0,0.1) 0 18px 36px -18px`; ambient `rgba(23,23,23,0.08) 0 15px 35px`. Focus ring `2px solid #533afd`.
- Motion: short GPU transitions (transform/opacity/box-shadow ~150-200ms ease); shadow intensifies on hover.

## Components (key)
- Primary CTA: bg `#533afd` / text `#ffffff` / padding 8px 16px / radius 4px / no border. Hover bg `#4434d4`; active slightly darker; focus 2px purple ring.
- Card: `#ffffff`, `1px solid #e5edf5`, radius 6px, layered blue shadow above; title 22/300/-0.22px navy, body 16/300 `#64748d`.
- Success badge: `rgba(21,190,83,0.2)` bg, `#108c3d` text, `1px solid rgba(21,190,83,0.4)`, radius 4px, 1px 6px, 10/300.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: set headlines at weight 300 with `"ss01"` on — lightness is the authority here.
- Do: tint every elevation shadow blue (`rgba(50,50,93,...)`) and layer a neutral shadow closer.
- Don't: reach for weight 600-700 on display — the heavy-hero instinct kills the voice; 300 is the voice.
- Don't: use pure black `#000` headings or pill/12px+ radius — navy `#061b31` and 4-8px are deliberate.
- Don't: paint ruby/magenta onto a button or link — those are gradient decoration only.

## Example component prompts
- "Hero on `#ffffff`: headline 48px sohne-var weight 300, line-height 1.15, letter-spacing -0.96px, color `#061b31`, font-feature-settings 'ss01'; subtitle 18px/300 `#64748d`; CTA `#533afd` bg white text radius 4px padding 8px 16px + ghost button transparent `1px solid #b9b9f9` `#533afd` text."
- "Card: white, `1px solid #e5edf5`, radius 6px, shadow `rgba(50,50,93,0.25) 0 30px 45px -30px, rgba(0,0,0,0.1) 0 18px 36px -18px`; title 22px/300 letter-spacing -0.22px `#061b31` 'ss01'; body 16px/300 `#64748d`."
