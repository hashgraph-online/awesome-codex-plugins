# WIRED — Design Tokens (loopy-native)
> Category: brand-web-media · Signature: paper-white broadsheet density, custom serif display, mono caps kickers, one ink-blue link

## Signature & atmosphere
WIRED reads like a printed broadsheet plugged into a wall socket: a dense grid held together by hairline rules and typographic weight, never cards or shadows. The recognizable idea is the typographic stack — a brutally large custom serif for the headline, a mono ALL-CAPS kicker tracking-spread like a Geiger tick above every story, and exactly one saturated link blue that lights up like a CRT scanline. Corners are square by religion; the page's confidence comes from refusing to invent a second color.

## Color (hex · --var · role)
- `#FFFFFF` `--bg` — paper-white canvas, treated like uninterrupted newsprint; `#1a1a1a` `--fg` — headlines and body (softened black)
- `#000000` `--primary` — pure ink for ribbons, button borders, structural rules — the strongest hand on the page
- `#057DBC` `--accent` — the single brand color: link hover only, never a fill or background
- `#757575` `--muted` — bylines, timestamps, captions; `#999999` disabled/low-priority
- `#e2e8f0` `--border` — barely-visible `<hr>` hairline tint; `#000000` for structural editorial rules
- `#1a1a1a` `--card` — the only inverted region (footer); paper-white type sits on top
- Note: WIRED intentionally ships no semantic success/error palette — this is editorial chrome, not a dashboard. Color outside grayscale + `#057DBC` is a defect.

## Typography
- Stack: WiredDisplay (custom serif, headlines) → BreveText (humanist serif, body/decks) → Apercu (geometric sans, UI/buttons) → WiredMono (mono, ALL-CAPS kickers/timestamps); fallback helvetica
- Display hero WiredDisplay 64px / regular / 0.93 / -0.5px · Mid 26px / regular / 1.08
- Section heading Apercu 20px / 700 / 1.20 / -0.28px · Subheading 17px / 700 / 1.29
- Article deck BreveText 19px / regular / 1.47 · Body 16px / regular / 1.50
- Button label Apercu 16px / 700 / 1.25 / +0.3px · Inline link Apercu 14px / regular / +0.4px
- Eyebrow/kicker WiredMono 13px / regular / 1.23 / +0.92px uppercase · Section ribbon 12px / 700 / +1.2px · Timestamp 12px / +1.1px uppercase
- Four faces, four fixed jobs — Display shouts, BreveText reads, Apercu clicks, WiredMono labels; mono is always uppercase; substitute serifs (Playfair/Libre Caslon) need +0.10–0.12 line-height.

## Spacing, radius, depth, motion
- Base 8px; scale 1 (hairline) · 4 · 8 · 12 · 16 · 24 · 32 · 40 · 48 · 64px; sections 32–48px apart, gutters 24–32px
- Radius: `0` on every container, image, button, and input — the strictest corner discipline of any editorial site; `50%` icons/avatars only; `1920px` for inline text-span pills ("BREAKING") only
- Depth strategy: flat by religion, rule-weight only. Tier by stroke: 1px `#e2e8f0` quiet `<hr>` → 1px `#000000` editorial rule → 2px `#000000` border (buttons/inputs/ribbons) → solid black ribbon bar → inverted `#1a1a1a` footer. Zero `box-shadow`.
- Motion: ~120–150ms color/background swap only; no easing flourish, no hover lift.

## Components (key)
- Primary CTA (Black Outline): bg `#FFFFFF` / text `#000000` Apercu 16px·700 +0.3px / border `2px solid #000000` / radius 0 / padding ~13px 24px / hover inverts to black bg + white text in 150ms — printerly, not webby
- Story tile (no card): image rectangle at radius 0 above a WiredMono uppercase kicker, WiredDisplay headline, BreveText deck; separated from neighbors by a 1px black hairline rule or whitespace; hover swaps headline `#1a1a1a` → `#057DBC` with underline, image stays static.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: use 2px hard black borders on buttons; put a mono ALL-CAPS kicker above every headline; separate stories with hairline rules.
- Don't: add `border-radius` to anything rectangular — the universal web instinct to soften corners is the single most common WIRED mistake; `0` is law.
- Don't: ship a `box-shadow` to "lift" a tile — use a 2px black border or a hairline rule instead.
- Don't: introduce color outside grayscale + `#057DBC`, or set body in Apercu — BreveText reads, Apercu clicks.

## Example component prompts
- "Editorial story tile: 16:9 image at radius 0, WiredMono uppercase kicker `#1a1a1a` +0.92px above a 26px WiredDisplay headline, separated from the next tile by a 1px solid `#000000` hairline rule — no card, no shadow, no radius."
- "Subscribe button: `2px solid #000000` border, radius 0, white bg, Apercu 16px/700 +0.3px text in `#000000`, hover inverts to black bg + white text in 150ms."
