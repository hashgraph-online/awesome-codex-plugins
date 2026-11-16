# Widget design system (Bot API 10.4, widget profile 1)

> Checked 2026-11-15 against the [Widgets guide](https://core.telegram.org/bots/widgets)
> ("Designing widgets", "What widgets support", "Limits", "CSS variables"); Bot API 10.4 is the
> newest version in the changelog on that date. Status of each rule: **API** = Bot API
> requirement, **Guide** = official recommendation or runtime fact from the Widgets guide,
> **Heuristic** = this skill's design advice. Implementation: `examples/widgets/_kit/`
> (inlined by `scripts/build_widget.py`), checked by `scripts/widget_lint.py`.

A widget is part of a message, not a web page. It should read like Telegram drew it: the
chat's palette and text size, the client's own buttons, no frame, no brand chrome, quiet
numbers in tabular figures, one accent at a time. Calm and precise beats decorative.

## 1. The canvas

| Rule | Status |
|---|---|
| The bubble is the canvas: no padding of its own, clipped at the rounded corners. Never set a background on `html`, `body` or the root block: it paints the whole bubble. | Guide |
| The app inserts a default stylesheet under yours: message text colour, size and line height, `body` margin ≈ `8px 12px`, native headings/lists/tables, client buttons. Any rule of yours wins. | Guide |
| Width 200–600 px (phones ≈ 320–430). Height = content, 50–600 px, overflow **clipped**, nothing scrolls. | Guide |
| Keep under ~560 px tall at 320 px width; design for 320 first, check 200 and 600. | Guide (560) / Heuristic (order) |
| No `vh`; `vw`, `vmin`, `%`, `@media (min/max-width)` refer to the **bubble** width. | Guide |
| `width`/`height` in `sendWidget` are only size anchors before load (0 = automatic). Pass `height` only for a widget with a fixed height. | API |

The kit's root block `.k` sets `body{margin:0;padding:0}` and pads itself
`10px 12px` with the bottom padding `max(10px, env(safe-area-inset-bottom),
var(--tg-content-safe-area-inset-bottom))` (Guide: a widget that pads for the time band must zero
the body padding, or it gets two bands).

## 2. Tokens

All colours come from the theme variables the app sets on the root (inline, `!important`; a
widget cannot override them on the root, only redefine on its own elements — Guide). The kit
maps them to short tokens with a fallback that only a plain browser ever sees:

| Token | Theme variable | Use |
|---|---|---|
| `--k-tx` | `--tg-theme-text-color` | body text, chip text |
| `--k-hint` | `--tg-theme-hint-color` | meta, labels, muted values, disabled text |
| `--k-link` | `--tg-theme-link-color` | links |
| `--k-btn` / `--k-btx` | `--tg-theme-button-color` / `--tg-theme-button-text-color` | primary fill / text on it, selected chip, chart stroke |
| `--k-sec` | `--tg-theme-secondary-bg-color` | surfaces on the bubble (cards, chips, tracks) |
| `--k-acc` | `--tg-theme-accent-text-color` | accent text |
| `--k-bad` | `--tg-theme-destructive-text-color` | errors, destructive, thresholds |
| `--k-sep` | `--tg-theme-section-separator-color` | separators |
| `--k-bg` | `--tg-theme-bg-color` | knobs/thumbs that must look cut out of a surface |
| `--k-ok`, `--k-warn` | none: `light-dark(#2e8b3e,#5ec46e)`, `light-dark(#a86400,#f0a73a)` | success / warning status only |

* **Never hard-code a colour without a theme path** (Guide: "never hard-code colors that must
  contrast with the bubble"). The lint allows colour literals only as `var()` fallbacks, inside
  `light-dark()` (resolved to the **chat** scheme — Guide), or as neutral translucent greys
  (`rgba(128,128,128,.2)`), which read the same on light and dark bubbles (Heuristic).
* Success/warning have no theme variable: they are `light-dark()` pairs and are never the only
  signal — pair them with a word or a glyph (▲ ▼ ✓) (Heuristic).
* **Outgoing bubbles** (a widget the user sent via the bot or forwarded) use the user's bubble
  palette; production widgets sit in incoming bubbles today, but test the outgoing palette
  (Guide: "Test every widget in both schemes and in an outgoing bubble").
* `prefers-color-scheme`, `color-scheme` and `light-dark()` follow the chat theme and switch
  live; JS reads `TelegramWidget.colorScheme` and listens to `themeChanged` (Guide).

## 3. Type

| Step | Size | Use |
|---|---|---|
| title | `1.07em`, weight 600 | the widget's name or main fact (`.tt`) |
| body | `1em` (= `--tg-text-font-size`, ≈ 15 px, follows the user's text size) | everything by default |
| meta | `.87em`, `--k-hint` | labels, timestamps, secondary values (`.mt`) |
| small | `.8em` | units, deltas, badges |
| figure | `min(1.33em, 7.4vw)` … `min(1.6em, 9vw)`, weight 600 | KPI numbers: grows with text size, shrinks in a 200 px bubble |

* `em` sizes and system fonts only: `system-ui`, `sans-serif`, `serif`, `monospace`, `ui-*`
  (Guide; named fonts and `@font-face` are removed). Numbers: `font-variant-numeric:
  tabular-nums` (Guide: in the profile) so columns and live counters do not jitter.
* One-line truncation only: `white-space:nowrap;overflow:hidden;text-overflow:ellipsis`
  (`.el`). `-webkit-line-clamp` is out (Guide).
* Test the **largest text size** (Guide): layouts built in `em` grow; check that nothing passes
  600 px. The preview harness has a 20 px text option.

## 4. Spacing, shape, touch

* Spacing scale 4 · 6 · 8 · 10 · 12 px; gaps via flex/grid `gap` (Heuristic).
* Radius: surfaces `10px` (`--k-r`), chips and pills `999px`, tracks `3px` (Heuristic).
* Touch targets: chips ≥ 34 px tall, primary buttons ≥ 36 px (`--tg-button-height` ≈ 36), at
  least 6 px apart (Heuristic, after platform guidance of 44 pt/48 dp scaled to a bubble).
* Primary action: a plain `<button>` — the client draws its own button with pressed and disabled
  states (Guide). Restyle only secondary controls (`.ch` chips).
* Keep controls out of the **leading 20 px** (right edge in RTL): those pixels never take a
  claim, so the back gesture works (Guide). The kit's 12 px side padding plus an inner pad on
  sliders/carousels covers it.

## 5. Layout primitives (kit classes)

| Class | What | Notes |
|---|---|---|
| `.k` | root block | padding + time band, tabular numbers |
| `.hd` | header row | title left, status right, baseline-aligned, mirrors in RTL |
| `.rw` / `.gr` | row / growing cell | `.gr` has `min-width:0` so `.el` can truncate |
| `.sf` | surface card | `--k-sec`, radius 10 |
| `.ls` | separated list | 1 px `--k-sep` between children |
| `.ch` / `.ch.on` | chip button / selected | segmented controls = a `.rw` of `.ch` with `flex:1` |
| `.br > i` | progress track + fill | width transition, reduced-motion aware |
| `.st` | status line | request outcomes; `.e` error, `.ok` success; `min-height` reserves the line |
| `.ic` | 24×24 stroke icon | `currentColor`, inline SVG `<path>` only |
| `.wd` | full-width primary button | |

Grids: two columns down to 200 px for short KPI tiles; one column for anything with text.
Never set a fixed width above 200 px (Heuristic: the narrowest bubble).

## 6. States every widget draws

| State | How | Status |
|---|---|---|
| first paint | synchronously from `chatData`/`publicData`; there is nothing to load | Guide |
| empty (`null` state) | one sentence saying what will appear and who fills it | Heuristic |
| sending | `K.st("Sending…")`, controls `disabled` while `K.busy` | Guide ("show progress and every outcome") |
| error | the code's sentence in `.st.e`; state unchanged | Guide |
| stale | timestamp older than the refresh you promise → "Data may be stale", `--k-warn` | Heuristic |
| disabled | `button[disabled]` (client dims it); text in `--k-hint` | Guide (`[disabled]` is drawn natively) |
| read-only copy | forward or preview: `K.can()` false → buttons disabled, a "Open the bot" hint; forwards of static widgets are snapshots ("as of 19:40") | Guide |
| "offline-looking" | widgets are always offline; what users see is a **bot** that does not answer (`TIMEOUT`, `FAILED`). Say "No answer. Nothing changed" — never "check your connection" | Guide (codes) / Heuristic (wording) |

## 7. Motion

* Transitions and keyframes only for state changes (bar widths, chip fills), 150–300 ms
  (Heuristic). `prefers-reduced-motion` is supported (Guide): the kit turns all transitions and
  animations off under it; games step instead of easing.
* Mute with **colour, not opacity**: at most 16 "heavy" elements (blur shadow, `filter`,
  `backdrop-filter`, `opacity < 1`, or an animation of one) at once, or the widget is stopped
  (Guide). `fill-opacity` in SVG and `rgba()` cost nothing.
* `requestAnimationFrame` stops off-screen; timers fire at most once per second there (Guide).
  Never read layout in every frame.

## 8. Right-to-left

* Set `dir` on the root (the kit sets `rtl` for `ar`, `he`, `fa`, `ur` unless the HTML already
  has `dir`); flex rows and grids mirror themselves (Guide: RTL text is in the profile).
* Logical properties (`margin-inline`, …) are **out** (Guide): where a side matters, write the
  LTR rule and a `[dir=rtl]` override.
* The time badge sits in the **left** corner in an RTL interface:
  `--tg-content-safe-area-corner-left` is then non-zero (Guide).
* Numbers, prices and times come from `Intl` in `navigator.language` (Guide: `Intl` is in the
  profile): `K.nf`, `K.money`, `K.time`.

## 9. Accessibility

Widgets have **no accessibility semantics** in profile 1: `aria-*` is kept but does nothing
(Guide). Therefore:

* The **caption carries the main fact** ("Order #1042 · on the way · ETA 19:40") — it is what
  screen readers, the chat list, notifications, search and apps without widgets get (Guide).
* Every widget ships a **text/button alternative**: an inline keyboard under the widget, or a
  command, that does the main action without the widget (Heuristic, required by this skill).
* Contrast: text on `--k-sec` surfaces uses `--k-tx`; `--k-hint` only for secondary text; never
  convey state by colour alone (Heuristic, WCAG 1.4.1).
* No keyboard and no focus exist in widgets (Guide: `:focus*` is out, `focus()` does nothing), so
  focus styles are not drawn; every action is a tap target with a visible label.
* Drags always have a button alternative (− / + next to a slider, ‹ › next to a carousel)
  (Heuristic).

## 10. Localization inside one document

* **One language per build** (Heuristic): the bot knows `from.language_code` and sends the HTML
  built for that language (`scripts/build_widget.py --lang ru`). Measured on the dashboard:
  English only 3586 compressed bytes, Russian only 3758, all three in one document 4275 — over
  the 4096 limit.
* Shared widgets have one HTML for every viewer (API: code is fixed per shared widget): include
  the languages your audience needs and pick by `navigator.language`.
* Strings that describe **data** (item names, labels, step texts) come from the bot inside the
  state, already localized; the HTML carries only chrome (buttons, statuses, error sentences).
* Cyrillic is 2 bytes per letter in UTF-8 and compresses worse: budget ≈ 170 bytes more per
  language than English (measured on the gallery).
* Budget escape for a **static** widget whose `public_data` is otherwise unused: move the chrome
  strings there as a JSON array and index them (`T[3]`). Field report: 19 short Russian strings
  cost ~410 compressed bytes in the HTML, enough room for a small image once moved (Heuristic).
  Costs: `public_data` travels with forwards and is visible to anyone (fine for UI text, never
  for data), the widget needs a fallback when it is `null`, and it is not available for shared
  widgets, where `public_data` is the live shared state.

## 11. The caption and the fallback mirror the widget

| Widget shows | Caption (≤ 1024 chars) | Fallback keyboard |
|---|---|---|
| dashboard | `api-prod · Operational · p95 182 ms · errors 0.31%` | `24h report` · `7d report` · `Incidents` |
| order tracker | `Order #1042 · On the way · ETA 19:40` | `Track in chat` · `Help` |
| booking | `Haircut · Fri 21 Nov · pick a time` → after booking `Booked: Fri 21 Nov, 14:30` | `Choose a time in chat` |

* Edit the caption when the main fact changes (`editMessageCaption`, API) — a silent
  `editMessageWidgetData` does not update the chat list.
* Use `show_caption_above_media` only when you want the time drawn on the widget (Guide).

## 12. Icons and custom emoji

Telegram custom emoji (`custom_emoji_id`) are **not documented** for widget HTML: the Widgets guide
(checked 2026-11-15) lists colour emoji in text and `data:` PNG/JPEG/GIF/WebP images, and no way to
render a custom emoji inside a widget. Use inline SVG icons (`.ic`, `<symbol>` + `<use>`) or plain
emoji text there. Custom emoji belong to message text, captions and buttons — see `emoji-packs.md`
and `examples/python/tgkit/icons.py` (owned by the emoji stream). The widget's caption is an
ordinary media caption, so it may carry custom emoji entities (API: `caption_entities`).

## 13. Checklist

`py -3 scripts/build_widget.py SRC --strict --lang <each>` (size ≤ 3800 working budget, hard
4096; runtime gaps; lint) → `py -3 scripts/preview_widget.py SRC` (light, dark, outgoing, RTL,
200/320/430/600 px, large text, no caption, forward, preview; a **mock**) → a real Telegram
client in both schemes, largest text, a narrow phone, desktop with a mouse, RTL, an old phone
(Guide "Testing in Telegram"). Report which of these were actually done.
