# The New York Times — Design Tokens (loopy-native)
> Category: brand-web-media · Signature: newsprint-white broadsheet, Cheltenham serif authority, hairline rules, near-zero color

## Signature & atmosphere
The Times reads like the front page made digital: a paper-white field organized by hairline rules and column rhythm, headlines set in its proprietary Cheltenham serif that signals institutional authority before a word is read. The recognizable idea is typographic hierarchy over chrome — story importance is communicated by serif size and rule weight, not by cards, shadows, or color. The palette is near-monochrome by editorial principle, with exactly one link blue lighting up interactive text.

## Color (hex · --var · role)
- `#ffffff` `--bg` — newsprint-white canvas; `#121212` `--fg` — headlines and body (true editorial near-black)
- `#000000` `--primary` — pure ink for the masthead wordmark, section rules, and structural hairlines — the strongest hand on the page
- `#326891` `--accent` — the Times link blue: inline links and hover only, never a fill or background
- `#363636` strong-secondary text; `#666666` `--muted` bylines/timestamps; `#999999` captions/disabled
- `#e2e2e2` `--border` — barely-visible hairline `<hr>`; `#000000` for heavy editorial section rules
- `#f7f7f7` `--card` — the only tinted surface (rare promo/box-out); type sits directly on it
- `#d0021b` reserved for the "LIVE"/breaking dot only — a single editorial alert red, never decorative
- Note: outside grayscale + the link blue (+ the rare breaking red), color is a defect. This is editorial chrome, not a product dashboard — no success/warning palette.

## Typography
- Stack: display serif `"nyt-cheltenham", Georgia, serif` (headlines/authority); body serif `"nyt-imperial", Georgia, serif` (article text); UI/labels `"nyt-franklin", Arial, sans-serif` (kickers, bylines, buttons); kicker mono-ish caps via Franklin
- Hero headline Cheltenham 46px / 700 / 1.05 / -0.4px · Section head Cheltenham 34px / 700 / 1.10 · Story headline 22px / 700 / 1.15
- Article body Imperial 18px / 400 / 1.60 (the reading voice) · Deck/summary Imperial 17px / 400 / 1.45 in `#363636`
- Kicker/section label Franklin 11px / 700 / 1.20 / +0.6px UPPERCASE · Byline Franklin 13px / 500 / 1.30 · Timestamp 12px / 400 `#666666`
- Three faces, three jobs — Cheltenham shouts, Imperial reads, Franklin labels. Headlines are bold serif; never set a headline in the sans, and never set long body in Cheltenham.

## Spacing, radius, depth, motion
- Base 8px; scale 4 · 8 · 12 · 16 · 20 · 24 · 32 · 48px; column gutters 16–24px; sections 24–32px apart, separated by rules not gaps
- Radius: `0` on containers, images, and most buttons — broadsheet corners; `50%` avatars/round icon buttons; small `4px` on the occasional rounded "subscribe" pill only
- Depth strategy: flat, rule-weight only. Tier by stroke — `1px #e2e2e2` quiet hairline → `1px #000000` editorial rule → heavier black section bar. Zero `box-shadow` on editorial content; a faint `rgba(0,0,0,0.12) 0 1px 4px` appears only on true overlays (menus).
- Motion: ~120ms color/background swap; headline hover shifts to the link blue or underlines — no lift, no easing flourish.

## Components (key)
- Subscribe CTA: bg `#326891` / text `#ffffff` / padding 12px 22px / radius 4px / 14px Franklin·700 / hover darkens ~6% — the one place a solid color fill is allowed; most "buttons" are really underlined Franklin text links
- Story package (no card): Cheltenham headline above an Imperial deck and a Franklin uppercase kicker, separated from neighbors by a `1px #e2e2e2` hairline or a `1px #000000` rule; image at radius 0; hover swaps headline `#121212` → `#326891` with underline, image static

## Do / Don't (anti-convention — name the wrong instinct)
- Do: set headlines in bold Cheltenham serif, body in Imperial serif, labels in Franklin sans; separate stories with hairline/black rules; keep the page newsprint-white.
- Don't: add `border-radius` to images, story tiles, or section containers — the instinct to soften corners is the most common Times mistake; broadsheet corners are 0.
- Don't: introduce a second accent color or use color to rank stories — hierarchy is serif size and rule weight, and the only interactive color is `#326891`.
- Don't: drop a `box-shadow` to make a story "pop," or set a headline in the sans — rules and serif weight carry importance; Franklin is for kickers and bylines only.

## Example component prompts
- "Front-page hero on `#ffffff`: Cheltenham headline 46px/700/1.05/-0.4px in `#121212`, Imperial deck 17px/400/1.45 in `#363636`, Franklin 11px/700 UPPERCASE +0.6px kicker `#000000` above; image at radius 0; separated below by a `1px solid #000000` rule."
- "Story tile (no card): 16:9 image at radius 0, Franklin uppercase kicker, Cheltenham 22px/700 headline, Imperial 17px deck `#363636`; divided from the next story by a `1px #e2e2e2` hairline; hover shifts headline to `#326891` with underline."
- "Subscribe module: `#326891` button, white text, 14px Franklin/700, 4px radius, padding 12px 22px; surrounding copy in Imperial 18px/1.60 `#121212`; no shadow, hairline rule above."
