# Together AI — Design Tokens (loopy-native)
> Category: ai-creative · Signature: pastel dreamscape over midnight-blue research

## Signature & atmosphere
Together AI makes GPU clusters feel light and optimistic. The light side is a white canvas blooming with soft pink-blue-lavender gradients and painterly cloud-like illustrations; the dark side drops into a deep midnight blue — not gray-black — where research and technical content live. Against all that softness the typography cuts hard: a geometric modernist display face with aggressive negative tracking, paired with a mono for uppercase technical labels. The recognizable idea is this two-world duality: friendly business messaging in light, serious research in midnight blue.

## Color (hex · --var · role)
- `#ffffff` `--bg` — light-section background, primary text on dark; `#000000` `--fg` — primary text on light
- `#010120` `--bg-dark` — the dark surface: deep midnight blue (distinctly blue, never generic gray-black)
- `#ef2cc1` `--brand-magenta` — gradient/illustration accent only, never UI chrome
- `#fc4c02` `--brand-orange` — second gradient accent only
- `#bdbbff` `--lavender` — soft secondary accent, gentle highlights
- `rgba(0,0,0,0.08)` `--border` — light-surface containment; `rgba(255,255,255,0.12)` `--border-dark` + glass button bg on dark
- `rgba(0,0,0,0.04)` `--surface-subtle` — light badge fills. Contrast: keep magenta/orange off text — they're decorative; rely on `#000`/`#fff` for legibility.

## Typography
- Stack: primary `"The Future", Arial, sans-serif` · labels `"PP Neue Montreal Mono", ui-monospace, monospace`
- Display 64px / 400–500 / 1.00–1.10 / -1.92px · H2 40px / 500 / 1.20 / -0.8px · H3 28px / 500 / 1.15 / -0.42px
- Feature 22px / 500 / 1.15 / -0.22px · Body-lg 18px / 400–500 / 1.30 / -0.18px · Body 16px / 400–500 / 1.28 / -0.16px
- Mono-label 16px / 500 / 1.00 / +0.08px UPPERCASE · Mono-small 11px / 500 / 1.00 / +0.055px UPPERCASE (negative tracking on The Future, positive on the mono — the contrast is the system)

## Spacing, radius, depth, motion
- Base 8px; scale 4·8·12·16·20·24·32·44·48·80·100·120; section gaps 80–120px
- Radius: 4px badges/buttons (the primary), 8px larger cards — sharp geometry deliberately contrasting the soft gradients; no pills
- Depth strategy: a single distinctive shadow tinted with the dark blue — `rgba(1,1,32,0.1) 0 4px 10px` — gives elevated cards a faint blue cast that ties them to dark mode; plus light/dark zone alternation
- Motion: 150–250ms ease-out; gentle paper-hover lift using the blue-tinted shadow

## Components (key)
- Primary CTA: `#010120` bg / `#fff` text / 4px radius / hover lifts with blue-tinted shadow. On dark: glass button `rgba(255,255,255,0.12)` bg, white text, 4px radius. Outlined-light: `1px solid rgba(0,0,0,0.08)`, transparent
- Stats card: a large display number (64px / 500) over a 14px caption, white bg, 8px radius, `rgba(1,1,32,0.1) 0 4px 10px` shadow — the recurring focal anchor

## Do / Don't (anti-convention — name the wrong instinct)
- Do: tint elevation shadows midnight-blue (`rgba(1,1,32,0.1)`), not generic black — it's what makes the depth feel on-brand
- Don't: use a neutral gray-black for dark sections. The wrong instinct is "#111 is close enough"; it must be `#010120` midnight blue or the duality collapses
- Don't: let `#ef2cc1` / `#fc4c02` leak into buttons, text, or borders — they belong in illustrations only
- Don't: round to pills or use positive tracking on The Future — geometry stays sharp (4/8px) and display tracking is always negative

## Example component prompts
- "Hero on white with a soft pink→lavender→blue pastel gradient backdrop; headline `The Future` 64px weight 500 line-height 1.10 letter-spacing -1.92px in `#000`; dark CTA (`#010120` bg, 4px radius)."
- "Stats card: 64px/500 number over a 14px caption, white bg, 8px radius, shadow `rgba(1,1,32,0.1) 0 4px 10px`."
- "Section label: `PP Neue Montreal Mono` 11px weight 500 uppercase letter-spacing +0.055px; black on light, white on dark."
- "Dark research band: `#010120` bg, white text, H2 40px/500 letter-spacing -0.8px, cards bordered `rgba(255,255,255,0.12)`."
