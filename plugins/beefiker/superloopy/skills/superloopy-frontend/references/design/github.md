# GitHub — Design Tokens (loopy-native)
> Category: dev-tools · Signature: Primer neutrals where a one-step gray canvas separates panels without borders

## Signature & atmosphere
GitHub feels like a workbench that disappears so the code can speak — neutral, legible, and almost aggressively calm. The recognizable move is the canvas/surface split: the page sits on a faint gray (`#f6f8fa`) while cards rise to pure white, so panels read as raised without a single drop-shadow. Color is rationed to functional signals (the merge-green, the danger-red), never decoration; everything else is the Primer gray scale doing quiet structural work.

## Color (hex · --var · role)
- `#ffffff` `--bg` — card/canvas surface; `#0d1117` `--bg-dark` — dark-mode canvas (deep blue-black, not `#000`)
- `#1f2328` `--fg` — primary text (near-black with a blue undertone); `#e6edf3` dark-mode text
- `#0969da` `--primary` — accent blue; link + secondary-button text; on dark `#2f81f7`
- `#1f883d` `--success` — merge/CTA green; hover `#1a7f37`, active `#197935`
- `#cf222e` `--destructive` — danger red; `#9a6700` attention/warn
- `#656d76` `--muted` — secondary text; `#8c959f` tertiary/placeholder
- `#d1d9e0` `--border` — default hairline; `#f6f8fa` `--canvas-subtle` — the gray page behind white cards
- Contrast: muted `#656d76` on white ≈ 5:1 (AA body); reserve `#8c959f` for non-text. Green CTA text is white and passes on `#1f883d`.

## Typography
- Stack: UI `-apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif` (system-native by design — GitHub ships no brand display face); code `ui-monospace, "SFMono-Regular", "SF Mono", Menlo, Consolas, monospace`.
- Display 40px/600/1.25/-0.2px · H1 32px/600/1.25 · H2 24px/600/1.25 · H3 20px/600/1.25 · Body 16px/400/1.5 · Body-sm 14px/400/1.5 (the dominant UI size) · Label 12px/500/1.33
- Two weights carry everything: 400 body, 600 headings/emphasis. There is no light and rarely a 700 — hierarchy comes from size and the gray scale, not boldness.

## Spacing, radius, depth, motion
- Base 8px; scale 4 · 8 · 12 · 16 · 24 · 32 · 40 (Primer's 8-step). Dense list rows at 8/12.
- Radius: 6px buttons/inputs · 6px small cards · 12px large containers · 2em (pill) for Labels/Counters only.
- Depth strategy = borders + canvas-shift, almost never shadows. A panel is white-on-gray with a `1px solid #d1d9e0`. Reserved shadow: dropdowns/overlays only, `rgba(31,35,40,0.12) 0 1px 3px, ... 0 8px 24px`. Focus ring `0 0 0 3px rgba(9,105,218,0.3)`.
- Motion 80–200ms ease-out; hover = background tint shift, not lift.

## Components (key)
- Primary CTA (green): bg `#1f883d` / text `#ffffff` / padding 5px 16px / radius 6px / `1px solid rgba(31,35,40,0.15)` / hover bg `#1a7f37` / active `#197935` / focus `3px rgba(31,35,40,0.3)` ring.
- Default button: bg `#f6f8fa` / text `#24292f` / `1px solid #d1d9e0` / radius 6px / hover bg `#eef1f4`, border `#d1d9e0`.
- Label pill: pill radius (2em), 12px/500, colored 1px border + tinted bg derived from a single hue (e.g. `#0969da` border, `rgba(9,105,218,0.1)` fill).

## Do / Don't (anti-convention — name the wrong instinct)
- Do: build elevation from the canvas-subtle (`#f6f8fa`) gray behind white cards plus a 1px border — separation without shadows.
- Don't: reach for a custom display font or heavy weights — GitHub is deliberately system-font, weight-600 max; a branded heading face breaks the workbench neutrality.
- Don't: use green or red as decoration — they are state signals (merge/danger) only; a green hero band reads as a success message, not a brand color.
- Don't: drop big box-shadows on cards — shadows belong to overlays/menus exclusively.

## Example component prompts
- "Hero on `#f6f8fa`: H1 32px system-ui weight 600, line-height 1.25, `#1f2328`; subhead 16px/400 in `#656d76`. Green CTA `#1f883d` white text, 6px radius, 5px 16px; secondary default button `#f6f8fa` fill, `1px solid #d1d9e0`."
- "Repo card: white bg on the `#f6f8fa` canvas, `1px solid #d1d9e0`, 6px radius, NO shadow. Title 14px/600 `#0969da` (link blue), meta 12px/400 `#656d76`, a pill Label with `rgba(9,105,218,0.1)` fill and `#0969da` 1px border."
