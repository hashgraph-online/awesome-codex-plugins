# Substack — Design Tokens (loopy-native)
> Category: brand-web-media · Signature: warm paper reading-room, signature orange, generous serif body, post-as-letter

## Signature & atmosphere
Substack feels like opening a personal letter rather than landing on a media site: a warm off-white page, comfortable serif body type at reading width, and a single confident orange that marks every "subscribe." The recognizable idea is the post-as-document — long-form text laid out for sustained reading (~620px column, generous leading), framed by minimal chrome so the writer's voice is the interface. Warmth and legibility do the work that color and decoration do elsewhere.

## Color (hex · --var · role)
- `#ffffff` `--bg` — paper canvas; `#fafaf9` warm off-white for alternating reading bands; `#1a1a1a` `--fg` — softened near-black text (not pure `#000`)
- `#ff6719` `--primary` — Substack orange: subscribe buttons, links-on-hover, brand marks, active rails (the one chromatic signal)
- `#e34c0c` primary-hover (darker orange); `#fff1e7` primary-tint surface behind orange callouts/CTAs
- `#6b6b6b` `--muted` — bylines, timestamps, captions; `#909090` tertiary/placeholder
- `#e7e7e4` `--border` — warm hairline divider/card outline; `#d4d4d0` emphasized rule
- `#fcfcfb` `--card` — card surface a hair off the page; `#1a1a1a` inverted footer/nav region
- Note: this is editorial chrome, not a dashboard — there is no success/error semantic palette. Color outside warm grayscale + the orange (and its tint) is a defect.

## Typography
- Stack: body serif `Georgia, "Times New Roman", serif` (reading voice); UI/headings `-apple-system, "Helvetica Neue", Arial, sans-serif`; the serif/sans split is the identity — serif reads, sans labels and clicks
- Post title (sans) 42px / 700 / 1.15 / -0.4px · Section H2 28px / 700 / 1.25 · Card title 20px / 600 / 1.30
- Body-serif 20px / 400 / 1.60 (the load-bearing reading size, ~620px measure) · Deck/subtitle serif 22px / 400 / 1.45 in `#6b6b6b`
- UI body 16px / 400 / 1.50 · Button label 15px / 600 / 1.20 · Byline 14px / 500 / 1.30 · Caption 13px / 400 / 1.40
- Body sits at serif 20px — larger than most sites on purpose, for sustained reading. Headings are sans 600–700; do not render long-form body in the sans.

## Spacing, radius, depth, motion
- Base 8px; scale 4 · 8 · 12 · 16 · 24 · 32 · 48 · 64px; reading column max ~620px; section rhythm 48–64px (article paragraphs 24–28px apart)
- Radius scale 4 · 6 · 8 · 18px (pill subscribe button) · `50%` avatars — soft but modest, never highly rounded cards
- Depth strategy: hairline borders + faint ring, not drop shadows. Cards use `1px solid #e7e7e4`; an elevated popover gets `rgba(0,0,0,0.08) 0 2px 12px`. Reading bands separate by background tone (`#ffffff` vs `#fafaf9`), not elevation.
- Motion: ~150ms ease-out; opacity/color and a small subscribe-button darken — no scale or lift.

## Components (key)
- Subscribe CTA (orange pill): bg `#ff6719` / text `#ffffff` / padding 10px 20px / radius 18px / no border / 15px·600 / hover bg `#e34c0c` / focus 2px `#ff6719` ring at 40% — the single most repeated component, always the orange
- Post card: bg `#fcfcfb` / `1px solid #e7e7e4` / radius 8px / 20–24px padding / sans title 20px·600 `#1a1a1a`, serif deck 16px/1.5 `#6b6b6b`, 14px byline row with `50%` avatar; hover lifts border to `#d4d4d0`, no shadow

## Do / Don't (anti-convention — name the wrong instinct)
- Do: set long-form body in a serif at 20px/1.60 on a ~620px measure; keep the page warm off-white; use the orange only for subscribe/brand moments.
- Don't: render article body in a sans-serif at 16px — the web-default instinct kills the letter feel; serif at reading size is the voice.
- Don't: spread orange across surfaces or add a second accent — it is a subscribe signal, not a theme color.
- Don't: reach for `box-shadow` to separate cards — warm `1px` hairlines and a tone shift between reading bands do the job; SaaS-style elevation reads wrong here.

## Example component prompts
- "Article layout on `#ffffff`: sans title 42px/700/-0.4px in `#1a1a1a`, serif deck 22px/400/1.45 in `#6b6b6b`, body in Georgia 20px/400/1.60 capped at 620px; orange `#ff6719` subscribe pill (white text, 18px radius, padding 10px 20px) pinned above the fold."
- "Post card: `#fcfcfb` bg, `1px solid #e7e7e4`, 8px radius, 24px padding; sans title 20px/600 `#1a1a1a`, serif deck 16px/1.5 `#6b6b6b`, byline 14px/500 `#6b6b6b` with a 28px `50%` avatar; hover border to `#d4d4d0`, no shadow."
- "Subscribe band on `#fafaf9`: serif headline 28px/400 `#1a1a1a`, body 16px/1.5 `#6b6b6b`, orange pill CTA; full-bleed, separated from the white reading band by tone only."
