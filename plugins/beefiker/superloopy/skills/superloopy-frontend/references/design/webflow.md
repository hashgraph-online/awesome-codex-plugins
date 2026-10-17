# Webflow — Design Tokens (loopy-native)
> Category: brand-web-media · Signature: white canvas, decisive blue, deliberately sharp corners, cascading shadow stacks

## Signature & atmosphere
Webflow looks like a polished marketing site built by people who ship marketing sites — clean white surfaces, a confident brand blue, and a rich secondary palette held in reserve for illustration moments. The recognizable idea is the refusal to over-round: where most builders soften everything, Webflow keeps corners tight (4–8px) and lets precision read as craft. Depth comes from layered, near-invisible shadow cascades rather than one heavy drop shadow, and the custom variable sans gives headlines a sharp, engineered confidence.

## Color (hex · --var · role)
- `#FFFFFF` `--bg` — page canvas; `#080808` `--fg` — near-black primary text
- `#146EF5` `--primary` — Webflow Blue, primary CTA and links; hover `#0055D4`, lighter `#3B89FF`, darker `#006ACC`
- `#5A5A5A` `--muted` — link/secondary text; `#ababab` placeholder/muted; `#222222`/`#363636` darker secondary text
- `#D8D8D8` `--border` — borders and dividers; hover `#898989`
- `#FFFFFF` `--card` — card fill over a 5-layer cascade shadow (see depth)
- secondary palette (illustration/badges only): purple `#7A3DFF`, pink `#ED52CB`, green `#00D722`, orange `#FF6B00`, yellow `#FFAE13`, red `#EE1D36`
- Note: secondary colors decorate sections and badges — they never fill a primary CTA, which stays Webflow Blue.

## Typography
- Stack: WF Visual Sans Variable (display+body, weight 500–600); mono companion Inconsolata; fallback Arial
- Display 80px / 600 / 1.04 / -0.8px · Section heading 56px / 600 / 1.04
- Sub-head 32px / 500 / 1.30 · Feature title 24px / 500–600 / 1.30
- Body 20px / 400–500 / 1.40–1.50 · Body-standard 16px / 400–500 / 1.60 / -0.16px
- Button 16px / 500 / 1.60 / -0.16px · Uppercase label 15px / 500 / 1.30 / +1.5px / uppercase
- Caption 14px / 400–500 · Micro-uppercase 10px / 500–600 / +1px / uppercase
- Display leans 600; uppercase labels get wide positive tracking (0.6–1.5px) as the recognizable eyebrow voice.

## Spacing, radius, depth, motion
- Spacing on a fine fractional scale: 1 · 2.4 · 3.2 · 4 · 5.6 · 6 · 7.2 · 8 · 9.6 · 12 · 16 · 24px
- Radius: 2 · 4 · 8px and 50% only — conservative and sharp; never round functional elements past 8px
- Depth strategy: 5-layer cascading shadow `rgba(0,0,0,0) 0 84px 24px, rgba(0,0,0,0.01) 0 54px 22px, rgba(0,0,0,0.04) 0 30px 18px, rgba(0,0,0,0.08) 0 13px 13px, rgba(0,0,0,0.09) 0 3px 7px` — a soft physically-graded stack, not one hard shadow
- Motion: signature `translate(6px)` shift on button hover; transitions stay quick and GPU-friendly (transform/opacity).

## Components (key)
- Primary CTA: bg `#146EF5` / white label 16px·500 / radius 4px / hover bg `#0055D4` — sharp corner is intentional
- Transparent button: text `#080808`, no fill, `translate(6px)` on hover (the recognizable nudge)
- Card: `1px solid #D8D8D8` border, 4–8px radius, white fill resting on the 5-layer cascade; badge variant uses blue-tint background at ~10% opacity, 4px radius, weight 550.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: keep radius at 4px for functional elements; use the `translate(6px)` hover as the brand's interactive signature.
- Don't: round past 8px on buttons/inputs — the builder-aesthetic instinct to make everything pill-soft is wrong here; sharpness is the point.
- Don't: fill a primary CTA with a secondary color — those hues are for illustration and badges only.
- Don't: replace the layered cascade with a single `0 4px 12px` shadow — the graded multi-layer stack is the depth signature.

## Example component prompts
- "Hero on white: 80px WF Visual Sans heading weight 600, line-height 1.04, -0.8px tracking, near-black `#080808`, with a `#146EF5` CTA at 4px radius and a `translate(6px)` hover."
- "Feature card: white fill, `1px solid #D8D8D8` border, 8px radius, resting on the 5-layer cascade shadow, with a +1.5px-tracked uppercase blue label above a 24px/500 title."
