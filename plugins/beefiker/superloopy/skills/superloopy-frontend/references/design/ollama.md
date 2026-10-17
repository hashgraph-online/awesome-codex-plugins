# Ollama — Design Tokens (loopy-native)
> Category: ai-creative · Signature: warm grayscale minimalism with softened edges

## Signature & atmosphere
Ollama strips away until only the tool remains — a pure-white void with zero chromatic color, where content floats without shadow or decoration. The absence of design is the design. What keeps it warm rather than clinical is the pairing of a rounded system display font with an exclusively pill-shaped geometry: rounded letterforms plus rounded buttons plus rounded containers make a developer CLI feel approachable. This is minimalism with literally softened edges, not cold Swiss-grid austerity.

## Color (hex · --var · role)
- `#ffffff` `--bg` — pure white page background and secondary button surface (never off-white or cream); `#000000` `--fg` — primary headlines and links
- `#262626` `--fg-2` — button text on light, secondary headline weight; `#090909` `--surface-darkest` — footer/dark container
- `#fafafa` `--surface` — the subtlest section background, one notch off white
- `#e5e5e5` `--border` — the workhorse: button backgrounds, borders, primary containment; `#d4d4d4` `--border-2` — white-button outline
- `#737373` `--muted` — secondary body text, footer links; `#525252` `--muted-strong` — emphasized secondary; `#a3a3a3` `--faint` — placeholders, tertiary
- `#404040` `--btn-text` — text on white-surface buttons
- `rgba(59,130,246,0.5)` `--ring` — the ONLY non-gray value in the system, focus ring only. Strictly grayscale otherwise.

## Typography
- Stack: display `"SF Pro Rounded", system-ui, -apple-system, sans-serif` · body `ui-sans-serif, system-ui, sans-serif` · code `ui-monospace, SFMono-Regular, Menlo, monospace`
- Display 48px / 500 / 1.00 / normal · H2 36px / 500 / 1.11 / normal · H3 30px / 400–500 / 1.20 / normal
- Card-title 24px / 400 / 1.33 · Body-lg 18px / 400–500 / 1.56 · Body 16px / 400–500 / 1.50
- Caption 14px / 400 / 1.43 · Small 12px / 400 / 1.33 · Code 16px / 400 / 1.50 (only two weights matter: 400 body, 500 headings)

## Spacing, radius, depth, motion
- Base 8px; scale 4·6·8·10·12·14·16·20·24·32·40·48·88·112; section gaps very generous (88–112px)
- Radius: binary — `12px` for containers (cards, code blocks, panels) and `9999px` for everything interactive (buttons, tabs, inputs, tags). Nothing in between
- Depth strategy: zero shadows, ever. Separation comes only from `1px solid #e5e5e5` borders and `#fafafa` background shifts — paper-flat by intent
- Motion: minimal; interactions feel instant. Subtle background/border shifts over decorative transitions

## Components (key)
- Primary CTA: black pill — `#000000` bg / `#ffffff` text / 10px 24px / 9999px radius. Gray pill: `#e5e5e5` bg, `#262626` text, `1px solid #e5e5e5`. White pill: `#fff` bg, `#404040` text, `1px solid #d4d4d4`. All buttons share 10px 24px padding — consistency is absolute
- Terminal command block: `ollama run …` in `ui-monospace`, inside a 12px-radius `1px solid #e5e5e5` container on white, integrated copy button, no shadow

## Do / Don't (anti-convention — name the wrong instinct)
- Do: keep the palette strictly grayscale — the only color anywhere is the blue focus ring
- Don't: add a brand accent hue. The wrong instinct is "every AI product needs a signature color"; Ollama's refusal to color the interface IS its position
- Don't: use a radius between 12px and pill. The system is binary — container (12px) or interactive (9999px), never 4px/8px
- Don't: add shadows or weights above 500 — flat borders carry depth, and 400/500 carry the whole type ramp

## Example component prompts
- "Hero on `#ffffff`: black-line illustration centered above a headline `SF Pro Rounded` 48px weight 500 line-height 1.0 in `#000`; a black pill CTA (`#000` bg, `#fff` text, 9999px, 10px 24px) beside a gray pill (`#e5e5e5` bg, `#262626` text)."
- "Code block: 12px radius, `1px solid #e5e5e5` border on white, `ui-monospace` 16px command, no shadow."
- "Pill tab bar: active tab `#e5e5e5` bg + `#262626` text, inactive transparent + `#737373` text, all 9999px."
- "Integration grid: 4 columns of 12px-radius cards, `1px solid #e5e5e5`, icon + name, pure white surface."
