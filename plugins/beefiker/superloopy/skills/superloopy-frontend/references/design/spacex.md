# SpaceX — Design Tokens (loopy-native)
> Category: brand-web-media · Signature: full-viewport photography, spectral-white D-DIN stencil caps, one ghost button, zero chrome

## Signature & atmosphere
SpaceX feels like a film cut into scroll: each section is one full-viewport photograph of a rocket or planet, and the interface disappears behind it. The recognizable idea is text-on-image with no container — uppercase D-DIN type, tracked wide like stenciling on a hull, floats directly on the photo with only a dark gradient for legibility. There are no cards, no shadows, no color beyond black and a faintly blue-violet white; the single barely-visible ghost button is the only thing that looks interactive.

## Color (hex · --var · role)
- `#000000` `--bg` — space black, the void; also the overlay base at 50% alpha
- `#f0f0fa` `--fg` — spectral white: not pure `#fff`, a slight blue-violet tint that mimics starlight (this off-white IS the brand restraint)
- `rgba(240,240,250,0.1)` `--card` / ghost-surface — button fill, ~10% opacity, nearly invisible
- `rgba(240,240,250,0.35)` `--border` — ghost border, spectral at 35% (the only border in the system)
- `rgba(0,0,0,0.5)` `--overlay` — dark gradient laid over photography so text stays legible
- `#f0f0fa` link-hover — full spectral white (links rest slightly dimmed, brighten on hover)
- Note: there is no semantic/status palette and no second hue. Any chromatic color, or pure `#ffffff` instead of `#f0f0fa`, breaks the spectral discipline.

## Typography
- Stack: display `D-DIN-Bold`; body/UI `D-DIN, Arial, Verdana` — industrial DIN-heritage geometric, two weights only (700 / 400)
- Display hero 48px / 700 / 1.00 / +0.96px UPPERCASE · Body 16px / 400 / 1.50–1.70 (the one near-normal-case element, still often tracked)
- Nav-bold 13px / 700 / 0.94 / +1.17px UPPERCASE · Nav 12px / 400 / 2.00 / UPPERCASE
- Caption-bold 13px / 700 / 0.94 / +1.17px UPPERCASE · Caption 12px / 400 / 1.00 UPPERCASE · Micro 10px / 400 / 0.94 / +1px UPPERCASE
- Universal uppercase + positive tracking (0.96–1.17px) is the entire identity — the aerospace stencil voice. Two weights, no medium/semibold. Line-heights compress to 0.94–1.00 — mission-critical, efficient.

## Spacing, radius, depth, motion
- Base 8px; minimal scale 3 · 5 · 12 · 15 · 18 · 20 · 24 · 30px — spacing is not the organizing principle, the photograph is; sections are exactly 100vh
- Radius: 4px on rare utility dividers · `32px` on the ghost button (the only rounded element) — there is effectively no radius scale
- Depth strategy: none simulated. Zero shadows — every surface is already a lit photograph. Layering is purely photo (0) → `rgba(0,0,0,0.5)` legibility overlay (1) → spectral text (2) → ghost button (3).
- Motion: slow cinematic crossfades between full-viewport scenes; button hover brightens the ghost fill, no transform.

## Components (key)
- Ghost button (the only variant): bg `rgba(240,240,250,0.1)` / text `#f0f0fa` / padding 18px / radius 32px / border `1px solid rgba(240,240,250,0.35)` / hover fill brightens, text to full spectral white — a heads-up-display "LEARN MORE" floating over imagery
- Full-viewport scene (in place of any card): `background-size: cover` photo at 100vh, `rgba(0,0,0,0.5)` gradient overlay, a left-aligned text block of 48px D-DIN-Bold uppercase headline + 16px body + ghost button — no panel, no frame, edge to edge

## Do / Don't (anti-convention — name the wrong instinct)
- Do: make each section a full-viewport photograph; set all text UPPERCASE with positive tracking (0.96–1.17px); keep the palette to black + `#f0f0fa` and one ghost button.
- Don't: wrap content in a card, panel, or container — the instinct to "give the text a background box" is the core mistake; text sits directly on the photo with only a gradient.
- Don't: use sentence case or negative letter-spacing — every label is stenciled caps with *positive* tracking.
- Don't: add a `box-shadow`, an icon set, or a second color — shadows are meaningless on a photograph, and any hue or pure-white `#fff` breaks the spectral restraint.

## Example component prompts
- "Full-viewport hero: `background-image` cover at 100vh, dark overlay `rgba(0,0,0,0.5)`; headline 48px D-DIN-Bold UPPERCASE +0.96px in `#f0f0fa`; ghost CTA bg `rgba(240,240,250,0.1)`, `1px solid rgba(240,240,250,0.35)` border, 32px radius, 18px padding."
- "Overlay nav, transparent over photography: links 13px D-DIN/700 UPPERCASE +1.17px in `#f0f0fa`; SpaceX wordmark left-aligned; no background bar."
- "Content scene: 100vh photo with `rgba(0,0,0,0.5)` overlay, left-aligned block — 48px D-DIN-Bold uppercase heading, 16px D-DIN body, ghost button below; no card, no shadow."
