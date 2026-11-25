---
summary: "The Mini App design system (TMA profile 1): order of authority, colour roles, type, space, platforms, motion, states, named styles, kit usage; read before designing or restyling a screen."
verified: "2026-11-24"
bot_api: "10.5"
---

# Mini App design system ("TMA profile 1")

## Contents

- [1. Order of authority](#1-order-of-authority)
- [2. Who draws what](#2-who-draws-what)
- [3. Colour roles](#3-colour-roles)
- [4. Type](#4-type)
- [5. Space, shape, touch](#5-space-shape-touch)
- [6. Platforms](#6-platforms)
- [7. Motion and haptics](#7-motion-and-haptics)
- [8. States every screen draws](#8-states-every-screen-draws)
- [9. Styles](#9-styles)
- [10. The kit in use](#10-the-kit-in-use)
- [11. Checklist](#11-checklist)

The one page an agent reads before designing, building or restyling a Mini App screen. It maps Telegram's
theme to the kit's roles, sets type, space, platforms, motion, haptics and states, and defines the named
**styles** a person can ask for ("make it look like a fintech app", "calmer", "denser", "use our brand
colour"). It summarises and links the two source files instead of copying them:

- [telegram-design-guidelines.md](telegram-design-guidelines.md): Telegram's official rules G1-G7 and every
  design-relevant instruction on the Mini Apps page, with a checklist.
- [design-sources.md](design-sources.md) and `data/mini-apps/design-sources.json`: what was taken from
  iOS 27 and the Telegram Mini Apps UI Kit, colour fallbacks, the type scale, shape, Liquid Glass in CSS,
  the dark-fintech direction.

Implementation: `examples/mini-apps/_kit/tma.css` (roles, scales, primitives, style presets) and
`_kit/tma.ts` (theme to `<html>`, version gates, native buttons from a screen stack, haptics, storage).
Labels: **[Official]**, **[Heuristic]**.

## 1. Order of authority

1. The Telegram runtime: `themeParams`, `colorScheme`, safe areas, version, platform.
2. Telegram's Design Guidelines (G1-G7).
3. iOS 27 for proportions, capsules, tab bar, sheets, rows, Liquid Glass.
4. The old Telegram Mini Apps UI Kit for role names, component inventory, iOS/Android pairs, cell slots.
5. Craft and anti-slop rules ([anti-slop.md](anti-slop.md)).
6. The project's brand: accent of illustrations, the colour of one moment per screen, imagery. Never the
   theme's text, surfaces or primary button.

Telegram-native wins over general taste where they disagree ([anti-slop.md](anti-slop.md) §3).

## 2. Who draws what

| Zone | Drawn by | The app controls |
|---|---|---|
| Header: Close / Back, bot title, menu ⋯ | Telegram (Liquid Glass on iOS) | colour (`setHeaderColor`), Back (`BackButton`), Settings item (`SettingsButton`) |
| Bottom bar: MainButton, SecondaryButton | Telegram | text, colour, progress, active state, Secondary `position`, `iconCustomEmojiId` (9.5), bar colour |
| Background behind the page (overscroll) | Telegram | `setBackgroundColor` |
| Everything between | the app | this design system |
| Fullscreen | the app, edge to edge | must pad by `safeAreaInset` + `contentSafeAreaInset` |

Rule **[Heuristic]**: never draw what Telegram draws. The app's own floating controls (tab bar, a side
circle) look like neighbours of Telegram's glass chrome, not like a web navbar.

## 3. Colour roles

Every colour comes from a `--tg-theme-*` variable or a `color-mix()` of one. The kit names them by role;
the `--tma-fb-*` palette (iOS 27 system colours) is only the fallback for keys an older client does not
send and for a plain browser. Full table with fallbacks: `data/mini-apps/theme-params.json`
(`py -3 scripts/webapp_lookup.py theme`).

| Kit variable | Theme key (since) | Use |
|---|---|---|
| `--tma-page` | `secondary_bg_color` (6.1) → `bg_color` | grouped page behind sections |
| `--tma-surface` | `section_bg_color` (7.0) → `bg_color` | cells, cards, inset groups, sheets |
| `--tma-bg` | `bg_color` (6.0) | flat pages (`body.tma-flat`) |
| `--tma-text` / `--tma-hint` | `text_color` / `hint_color` (6.0) | primary / secondary text |
| `--tma-subtitle` | `subtitle_text_color` (7.0) → hint | cell subtitles |
| `--tma-section-header` | `section_header_text_color` (7.0) → hint | section headers |
| `--tma-accent` / `--tma-on-accent` | `button_color` / `button_text_color` (6.0) | the one accent: filled buttons, selection, quick-action circles |
| `--tma-accent-text` | `accent_text_color` (7.0) → link | tonal labels, selected tab, highlighted numbers |
| `--tma-link` | `link_color` (6.0) | links in text |
| `--tma-danger` | `destructive_text_color` (7.0) | destructive actions, errors, losses (with a sign) |
| `--tma-separator` | `section_separator_color` (7.6) | hairlines from the text column |
| `--tma-bottom-bar` | `bottom_bar_bg_color` (7.10) → page | the surface under the native bottom bar |
| `--tma-fill`, `--tma-fill-strong` | text at 8 % / 14 % | segmented track, gray buttons, inputs, steppers |
| `--tma-tonal` | accent at 14 % | tonal buttons, icon tiles, selected chips |
| `--tma-success`, `--tma-success-tint`, `--tma-danger-tint` | iOS green / red fallbacks, tinted | direction of change, outcomes |
| `--tma-brand`, `--tma-on-brand` | a style profile, else the accent | one brand moment per screen (§9.4) |

Rules **[Heuristic]**: one accent per screen; green and red only for direction or outcome and always with a
sign or arrow; surfaces never tinted toward a hue; a user's custom theme must keep working (no brand-blue
button in a green theme, G1).

**One surface level.** The page (`--tma-page`) holds surfaces (`--tma-surface`: a list, a card, a key-value
block); a surface holds content, rows and separators, never another surface. No card in a card, no list or
key-value block inside a card, no tinted box inside a list, no "card-inner". Inside a surface, group with
separators, spacing and type weight; for a second level, push a screen or open a sheet. Fills
(`--tma-fill`, `--tma-tonal`) are for controls (segmented track, steppers, chips, icon tiles), not for
panels. Lint MA35 flags nested surfaces in markup; the rework plan reports `nested-cards` and `stat-cards`.

## 4. Type

System font only (`--tma-font`: `system-ui`, `-apple-system`, Roboto on Android). The iOS 27 scale in `rem`
of a 17 px body, so iOS Dynamic Type can scale it (`font: -apple-system-body` on iOS, check on device);
Android uses a 16 px root with the same ratios. Nothing below 11 px.

| Kit class | Size / line | Weight | Use |
|---|---|---|---|
| `.tma-large-title` | 34/41 | 700 | title of a tab root |
| `.tma-title1` / `.tma-title2` / `.tma-title3` | 28 / 22 / 20 | 600 | sheet title, screen title below a root, section hero |
| body, `.tma-headline` | 17/22 | 400 / 600 | cell titles, text |
| `.tma-callout`, `.tma-subhead` | 16, 15 | 400 | secondary blocks, cell subtitles |
| `.tma-footnote`, `.tma-caption` | 13, 12 | 400 | section footers, legal, meta |
| `.tma-figure` + `.tma-figure__minor` | `--tma-figure-size` (≈ 48-64) | 600 | balances and prices: `tabular-nums`, fraction and currency at 60 % in hint colour |

Figures: one locale format (`Intl.NumberFormat`), tabular figures, a skeleton while loading, "—" on error,
never a fake "0.00". The figure block breathes: label → figure → 12 px → change pill → 20-24 px → the next
block (quick actions or a chart); the kit sets these gaps (`.tma-figure + .tma-delta`).

Every role also exists as a plain utility, regular and emphasized: `.tma-text-large-title`, `-title1`,
`-title2`, `-title3`, `-headline`, `-body`, `-callout`, `-subhead`, `-footnote`, `-caption1`, `-caption2`, plus
`.is-em` for the emphasized weight. Long text (help, terms, articles) goes in `.tma-prose`, which maps
semantic headings onto the scale: h1 → Title 1 bold, h2 → Title 2, h3 → Title 3, h4 → Headline, h5 →
Subheadline semibold, h6 → Footnote semibold in hint colour; lists, code, rules and `.tma-quote` included,
65ch measure. Use real heading levels for structure and the scale for size; never skip levels to get a size.

## 5. Space, shape, touch

| Variable | Default (iOS / Android) | Notes |
|---|---|---|
| `--tma-margin` | 16 | side margin; safe-area insets win in landscape |
| `--tma-s1…s8` | 4 … 32 | every gap on the 4 px step |
| `--tma-gap-section` | 24 | between sections and groups: put them in a `.tma-stack` (or consecutive `.tma-section`s); two surfaces never touch or sit 4-8 px apart |
| `--tma-row` / `--tma-row-2` | 52 / 68 | one-line row / with subtitle |
| `--tma-avatar` | 40 | avatar and icon tile in rows; the separator starts after it |
| `--tma-r-group` | 26 / 16 | inset groups and cards (check on device) |
| `--tma-r-inner` | 14 / 10 | nested surfaces: outer radius minus padding |
| `--tma-r-sheet` | 38 | top corners of a sheet |
| `--tma-target` | 44 / 48 | minimum touch target |
| capsules | radius = half the height | buttons 28 / 34 / 50, chips 34, segmented 32, tab bar 56 |

## 6. Platforms

`tma.ts` mirrors `WebApp.platform` to `<html data-tma-platform>`: `ios`, `android`, `desktop` (`tdesktop`,
`macos`), `web` (`weba`, `webk`). **[Heuristic]**

| | iOS | Android | Desktop / Web |
|---|---|---|---|
| Lists | inset groups, radius 26 | inset groups radius 16, or full width (`.tma-list.is-full`) | inset groups in a ~384-420 px window |
| Targets | 44 | 48 | 44; hover exists but is never the only way |
| Back | edge swipe at the left edge: keep it free | system back = `backButtonClicked` while BackButton is visible | header Back |
| Glass | on floating controls | on floating controls; off on class `LOW` | on, with the solid fallback |

Android performance class (G7): `<html data-tma-perf="low|average|high|unknown">` from the User-Agent. On
`low` the kit removes blur, shortens transitions and stops screen animations; the app also drops parallax,
auto-carousels and animated stickers, and lightens charts.

## 7. Motion and haptics

Motion **[Heuristic]**: 150-250 ms (`--tma-dur`, `--tma-dur-short`), one ease-out curve (`--tma-ease`),
`transform` and `opacity` only. Screens push in from the side (`.tma-screen`), sheets rise (`.tma-sheet`),
dismissal reverses the entrance. `prefers-reduced-motion` turns it all to instant; skeletons stop
shimmering. No idle loops on anything that is not live or loading.

| Moment | Haptic (`tma.haptic`) | API |
|---|---|---|
| Selection in a list, segmented control, toggle, chip, a picker step | `select()` | `selectionChanged()` |
| A small commit (stepper, add to cart, a quick action) | `tap()` | `impactOccurred('light')` |
| Long press opens a menu, a drag lifts / snaps, a limit is hit | `impact('medium' / 'rigid')` | `impactOccurred(...)` |
| The server confirmed / refused / warns | `success()` / `error()` / `warning()` | `notificationOccurred(...)` |
| Scroll, every ordinary tap, typing, timers, decoration | none | — |

The full map (all five impact styles), the rules and the device features next to it (motion sensors,
location, biometrics, fullscreen, QR, sharing): [haptics-and-device.md](haptics-and-device.md).

## 8. States every screen draws

| State | How (kit) |
|---|---|
| Default, pressed | `:active` fill or `scale(.97)`; never hover-only |
| Disabled | `disabled` / `aria-disabled="true"`, 45 % opacity; MainButton `is_active: false` plus the reason in the content |
| Loading | `.tma-skeleton` in the real layout; MainButton `showProgress()` for actions over ~300 ms |
| Empty | `.tma-placeholder`: what is missing, why, one way forward |
| Error | `.tma-placeholder` or `.tma-field__error`: what happened and the recovery; offline text without "check your connection" |
| Success | in place: updated screen, `haptic.success()`, a `.tma-snackbar` if the change is off-screen |

Chrome per screen **[Heuristic]**: header colour = colour at the top of the screen (grouped page →
`secondary_bg_color`, flat → `bg_color`, brand hero → the brand colour, back to the page colour when the
hero scrolls away); background = page; bottom bar = the surface under it. Use the keywords where possible:
`tma.chrome({ header: 'secondary_bg_color', ... })`.

## 9. Styles

A **style** is a named design direction an agent applies when a person asks for a look. It changes shape,
density, type emphasis, glass and which components a screen reaches for. It never replaces the user's
theme colours (G1); brand colour appears on one moment per screen. Data: `data/mini-apps/styles.json`;
tool: `scripts/miniapp_style.py`; CSS: the presets at the end of `_kit/tma.css`.

### 9.1 The presets

| Style | For | Changes | Signature components |
|---|---|---|---|
| `native` (default) | settings, forms, booking, support, no brand brief | nothing: kit defaults | inset groups, chevrons, MainButton |
| `fintech` | wallet, portfolio, points, exchange, one-number analytics | radius 22, rows 64, avatar 44, larger figure | hero figure + delta pill, 2-4 quick-action tiles, asset rows, one line chart, glass tab bar |
| `soft` | shop, food, events, learning, consumer onboarding | radius 30 / 18, rows 56 / 72, avatar 48, section gap 28 | image-led cards and rows, tonal buttons, friendly empty states |
| `dense` | dashboards, editors, admin, trackers, long lists | radius 12 / 8, rows 44 / 56, avatar 32, gap 16, body 16 px, no glass | full-width lists on Android, sticky segmented filters, compact rows |

`py -3 scripts/miniapp_style.py show <style>` prints intent, tokens, components, do and don't.

### 9.2 From a request to a style

| The person says | Style | Also |
|---|---|---|
| "like a bank / wallet / crypto app", "show the balance big", "fintech" | `fintech` | dark first, check light; one chart |
| "friendlier", "warmer", "rounder", "for buyers", "like a shop" | `soft` | real product images with alt |
| "more on one screen", "compact", "for power users", "admin" | `dense` | keep 44 px targets |
| "like Telegram", "classic Telegram", "native", "clean", no direction | `native` | the platform decides the chrome: iOS gets the glass capsule tab bar and 26 px groups, Android 16 px groups and Material sizes (`data-tma-platform`); a whole app redesign: [rework.md](rework.md) |
| "use our brand colour" | current style + `brand` in a profile | brand only on the hero or promo (§9.4) |
| "premium", "nicer" | keep the style; run the craft pass | [anti-slop.md](anti-slop.md) §5 before any token change |

Say which style was chosen and why, in one line, before changing code.

### 9.3 Applying a style

- Preset: `<html data-tma-style="fintech">`. Native: no attribute.
- Custom profile (a brand, rounder, denser, no glass): write `style.json`, check it, compile it, load the CSS
  after `tma.css`:

```json
{"base": "fintech", "radius": "round", "density": "default", "glass": true,
 "brand": {"light": "#1f5fe0", "dark": "#2a63d4", "on": "#ffffff"}}
```

```bash
py -3 scripts/miniapp_style.py check style.json   # ranges, 44 px targets, brand contrast >= 4.5 in both schemes
py -3 scripts/miniapp_style.py css style.json > style.css
```

`radius` (`sharp`/`default`/`round`) and `density` (`compact`/`default`/`roomy`) scale the preset's values and
are clamped to the allowed ranges with a warning; a brand pair under 4.5:1 fails.

### 9.4 Brand colour: one moment per screen

**Where the colour comes from.**
- **An existing project keeps its own palette.** Its main brand colour (the rework plan's brand candidate,
  or the colour the brand guide names) becomes `--tma-brand` through a profile; it is not swapped for a
  palette the skill likes. If it fails 4.5:1 with its text colour in a scheme, darken (light) or lighten
  (dark) that scheme's value until it passes, keeping the hue, and say so.
- **A new project picks a named palette**: Apple's system colours from the Human Interface Guidelines
  (`data/mini-apps/palettes.json`: red, orange, yellow, green, mint, teal, cyan, blue, indigo, purple, pink,
  brown, with their dark and increased-contrast variants). `"brand": "teal"` in `style.json` resolves to a
  pair that passes 4.5:1 in both schemes; `py -3 scripts/miniapp_style.py palettes` lists them, with a
  starting choice per product type. They are the system colours of the iOS 27 kit the rest of this design
  follows, so they sit next to Telegram's chrome without clashing.
- **Gradients.** None of the read sources (the iOS 27 kit, the Telegram Mini Apps kit, Telegram's guidelines)
  ship gradients. The only one allowed is the tonal fade of one brand colour into the page on the hero
  (`.tma-hero`); no multi-hue gradients, no gradient text, no gradient buttons.

Allowed: the hero block at the top of a section root (`.tma-hero`, brand → page fade below its text, header
colour set to the same brand colour and returned to the page colour when it scrolls away), a promo banner,
an illustration, a chart series. Not allowed: the MainButton colour by default, links, text, cell or page
surfaces, the tab bar. The MainButton may take the brand colour only on a screen whose moment is that
button (onboarding sheet) via `setParams({color, text_color})`, contrast-checked. **[Heuristic]**

### 9.5 Restyle workflow (existing Mini App)

1. Inventory: screens, the components each uses, current colours and fonts; run
   `py -3 scripts/miniapp_lint.py <app>` and keep the report.
2. Pick the style from the request (§9.2) and say why.
3. Fix structure before tokens: native buttons instead of own chrome, grouped lists, states (§8).
4. Replace literal colours with kit roles; remove web fonts, gradient text, glows, emoji icons.
5. Apply the preset or a checked profile.
6. Lint again (`--strict`), then the preview matrix: iOS/Android × light/dark × 320/390/430 and
   fullscreen (`scripts/preview_miniapp.py <app> --serve 8790`, `/?view=matrix`).
7. Report what changed, the style chosen, contrast results and what still needs a real device.

### 9.6 Adding a style

A new preset needs a real audience the four do not serve. Add it to `styles.json` (intent, use_for, tokens
within the ranges, components, do, don't) and the same tokens to `tma.css` as
`:root[data-tma-style="name"]`; `miniapp_style.py check-presets` (run by `run_checks.py`) fails when they
drift. Colour tokens are not style tokens.

## 10. The kit in use

```html
<script src="https://telegram.org/js/telegram-web-app.js?65"></script>   <!-- first in <head> -->
<link rel="stylesheet" href="_kit/tma.css">
```

```ts
import { createTma } from '../_kit/tma.ts';             // built to JS by build.mjs, no packages
const tma = createTma();                                // saves launch params, mirrors theme/platform/perf
tma.chrome({ header: 'secondary_bg_color', background: 'secondary_bg_color', bottomBar: 'secondary_bg_color' });
tma.nav.push({ id: 'detail', kind: 'screen', onBack: closeDetail });   // BackButton follows the stack
tma.mainButton({ text: 'Add to order · €4.20', onClick: add });        // progress while it runs
tma.haptic.select();
tma.ready();                                            // after the first useful screen is drawn
```

Primitives: `.tma-page`, `.tma-screen`, `.tma-section` (`__header`, `__footer`), `.tma-list`, `.tma-cell`
(`__body`, `__title`, `__subtitle`, `__after`, `__chevron`, `.is-2`, `.is-button`, `.is-danger`),
`.tma-avatar`, `.tma-icon-tile`, `.tma-badge`, `.tma-btn` (`.is-filled`, `.is-tonal`, `.is-plain`,
`.is-danger`, `.is-sm`, `.is-lg`, `.is-wide`), `.tma-actions` / `.tma-action`, `.tma-figure`, `.tma-delta`,
`.tma-chip`, `.tma-segmented`, `.tma-tabbar`, `.tma-glass`, `.tma-card`, `.tma-banner`, `.tma-hero`,
`.tma-placeholder`, `.tma-field`, `.tma-input`, `.tma-search`, `.tma-switch`, `.tma-check`, `.tma-slider`,
`.tma-stepper`, `.tma-skeleton`, `.tma-spinner`, `.tma-progress`, `.tma-snackbar`, `.tma-coachmark`,
`.tma-scrim` + `.tma-sheet`, `.tma-chart`; text utilities `.tma-text-*`, `.tma-prose`, `.tma-quote`, `.tma-code`;
tables `.tma-table`, `.tma-kv`, `.tma-rank`; settings `.tma-cell__check`, `.tma-pill-select`, `.tma-popup-trigger`;
overlays `.tma-menu`, `.tma-action-sheet`; media `.tma-media`, `.tma-gallery`, `.tma-carousel`, `.tma-dots`,
`.tma-audio`, `.tma-file__icon`, `.tma-avatar-stack`, `.tma-moment`, `.tma-map`, `.tma-qr`; structure
`.tma-accordion`, `.tma-steps`; input `.tma-rating`, `.tma-pin`, `.tma-file-drop`. Icons: `_kit/icons.svg`
(83, mapped to SF Symbols and Material in `data/mini-apps/icons.json`). Anatomy and states:
[components.md](components.md); every element rendered: `examples/mini-apps/gallery`.

## 11. Checklist

- [ ] Every colour is a kit role or a `color-mix()` of one; literals only in the `--tma-fb-*` palette.
- [ ] Light and dark checked, plus one custom theme; text on any glass or brand surface ≥ 4.5:1.
- [ ] No own header, back arrow or fixed bottom CTA; native buttons configured per screen.
- [ ] Safe area + content safe area in fullscreen; nothing under Telegram's controls.
- [ ] Type from the scale, nothing below 11 px, figures in tabular numbers.
- [ ] Radii consistent and nested correctly; targets ≥ 44 (48 on Android).
- [ ] Every list has empty and error states; every load a skeleton; every action feedback.
- [ ] Motion transform/opacity only, reduced motion respected; Android `LOW` gets the light variant.
- [ ] Names, focus, text size, contrast, language and RTL: [accessibility-and-language.md](accessibility-and-language.md) §11.
- [ ] Fields, keyboard, loading, errors per kind, one action once: [forms-and-data.md](forms-and-data.md) §11.
- [ ] One style, named; brand colour on one moment per screen at most.
- [ ] `miniapp_lint.py --strict` clean; preview matrix screenshots taken; real devices listed as checked or not.
