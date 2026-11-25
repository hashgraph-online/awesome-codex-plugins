---
summary: "The order of work to create or rework a Mini App, the file or tool for each step, and a coverage map of every element; read at the start of any Mini App create or rework task."
verified: "2026-11-24"
bot_api: "10.5"
---

# Orchestrating a Mini App: create or rework

The order an agent follows when a person asks to **create** a Mini App or to **improve, restyle or fix**
an existing one, with the file or tool for each step. Every step ends with something checkable. Use it
with the closest recipe (90-99) and the screen pattern for the product type.

## 1. What to load, by request

| Request | Load first | Then |
|---|---|---|
| "Build a Mini App for X" | [decide.md](decide.md), the screen pattern for X, the recipe | [design-system.md](design-system.md), [components.md](components.md) |
| "Make it look like X / use our brand / calmer / denser" | [design-system.md](design-system.md) §9 | `scripts/miniapp_style.py` |
| "Rework / redesign our Mini App like Telegram", "make it native" | [rework.md](rework.md) | `scripts/miniapp_rework.py plan <app>` |
| "It looks generated / web-like / cheap", "make it premium" | [anti-slop.md](anti-slop.md) §5 | `scripts/miniapp_lint.py` |
| Stars, grams, gifts, Premium, verification in the app | [telegram-elements.md](telegram-elements.md) | `_kit/tg-values.ts` |
| "Add vibration / haptics", "use the gyroscope / tilt", "find the user's location", "Face ID" | [haptics-and-device.md](haptics-and-device.md) | `tma.haptic`, `tma.motion`, `tma.location` |
| "Make it accessible", "VoiceOver", "translate the app", "Arabic / RTL", "plural forms" | [accessibility-and-language.md](accessibility-and-language.md) | `tma.locale()`, `.tma-sr-only` |
| "Add a form", "the keyboard covers the field", "handle errors / offline", "it booked twice" | [forms-and-data.md](forms-and-data.md) | `tma.api()`, `idempotencyKey()`, `tma.hideKeyboard()` |
| "Add glassmorphism", "make it look like the new iOS", "modern / trendy", "use view transitions" | [materials-and-trends.md](materials-and-trends.md) | `.tma-glass` levels, glass tokens |
| "Polish it", "make it cleaner", "unslop it" | [anti-slop.md](anti-slop.md) §5 | lint, stand matrix |
| "Build it from our Figma", "match iOS 27" | [figma-workflow.md](figma-workflow.md), [native-anatomy.md](native-anatomy.md) | Figma MCP: `get_metadata`, `get_design_context` |
| "Add a screen / a table / settings / a gallery" | `data/mini-apps/components.json`, [components.md](components.md) | the kit gallery for the markup |
| "Check this screen", "where should the price / photo go", "make the catalogue better" | [layout-rules.md](layout-rules.md) | `scripts/miniapp_layout.py show / review` |
| "What does an app for X look like" (gym, bookstore, SaaS, clinic, events…) | [screen-patterns.md](screen-patterns.md) | the matching example |
| "Verify the user on the server" | [security.md](security.md) | `examples/mini-apps/server` |
| "Does the API have X?" | `scripts/webapp_lookup.py show X` | [webapp-api.md](webapp-api.md) |
| "Open it from the bot / a button / a link" | [launch-and-lifecycle.md](launch-and-lifecycle.md) | [../mini-apps-bridge.md](../mini-apps-bridge.md) |
| "Take payments", "sell for Stars", "subscription in the app", "card payment for goods" | [payments.md](payments.md) | recipes 93, 96; bot side `../payments-pipeline.md` |
| "Make it look like Telegram in light and dark, iOS and Android" | [telegram-design-guidelines.md](telegram-design-guidelines.md), [design-sources.md](design-sources.md) | [design-system.md](design-system.md), `examples/mini-apps/_kit` |
| "It is slow on Android", "how do I test without a phone" | [performance-and-testing.md](performance-and-testing.md) | `scripts/preview_miniapp.py` |

This table is the route the skill's `mini-app` command follows; the "Route by task" table in
[README.md](README.md) maps the same files for people and is kept in step by a test.

## 2. Create

1. **Decide the surface and the entry** ([decide.md](decide.md)): Mini App or not; reply keyboard, inline or
   menu button, Main Mini App, direct link; what the bot says before and after.
2. **Map the screens** from the closest pattern in [screen-patterns.md](screen-patterns.md): tab roots (2-5) and level-2 screens; for each screen its one primary action
   (MainButton or none), its states (loading, empty, error, success), its `startapp` route if any.
3. **Lay out each content type** with [layout-rules.md](layout-rules.md) (`miniapp_layout.py show <entity>`), then **pick the components** from `data/mini-apps/components.json` (status `kit` first, `native` where
   Telegram draws it, never `avoid`). Copy markup from `examples/mini-apps/gallery/index.html`.
4. **Pick the style** (design-system §9.2) and say why in one line; brand colour only as one moment.
5. **Write the server contract first** ([security.md](security.md)): `initData` verification, `auth_date`
   policy, the routes and who may call them.
6. **Build** on the kit: `_kit/tma.css`, `_kit/tma.ts` (`createTma`, `nav`, `mainButton`, `haptic`,
   `store`), icons from `_kit/icons.svg` (names: `data/mini-apps/icons.json`).
7. **Check**: `py -3 scripts/miniapp_lint.py <app> --strict`; unit tests; the preview matrix
   (`scripts/preview_miniapp.py <app> --serve 8790`, `/?view=matrix`, then the Style switch).
8. **Report**: screens, style and why, components used, evidence level (lint, tests, mock preview, test
   server, devices), what is not verified.

## 3. Rework an existing Mini App

The full procedure, translation table, Tailwind / shadcn bridge and acceptance score: [rework.md](rework.md).

1. **Inventory**: screens, entry points, the components each screen uses, how it authenticates.
   `py -3 scripts/miniapp_rework.py plan <app>` gives the lint baseline sorted into stages with the Telegram
   replacement for each finding, plus the colour map and the type map; keep it as the baseline.
2. **Describe each screen** as a screen JSON and run `miniapp_layout.py review`; keep the findings with the lint report.
3. **Rank the defects**: security (MA01-MA02) → broken native behaviour (own header, own back, own bottom
   CTA, missing `ready()`) → missing states → theme (literal colours, `100vh`) → slop → polish.
4. **Fix structure before style**: native buttons, one navigation stack, grouped lists, states.
5. **Replace literals with kit roles**; delete web fonts, gradient text, glows, emoji icons.
6. **Apply the style** the request names (preset or checked profile).
7. **Re-check**: lint `--strict`, preview matrix in every style the app ships, both themes, fullscreen.
8. **Score** with [rework.md](rework.md) §7 (16 items; "classic Telegram" needs chrome, theme and security
   all passing and 14 of 16 overall) and **report** the before/after lint counts, what changed per screen,
   what was left alone and why.

Contracts stay frozen while reworking: API routes, `startapp` values, CloudStorage keys, analytics events.

## 4. Coverage map: every element and where it lives

| Need | Catalogue entry (`components.json`) | Kit | Reference |
|---|---|---|---|
| Text roles, h1-h6, long text | `typography`, `prose`, `quote`, `code` | `.tma-text-*`, `.tma-prose` | design-system §4 |
| Lists, rows, settings | `list`, `cell`, `row-*` (detail, disclosure, button, picker pill, pop-up, stepper, toggle, check) | `.tma-list`, `.tma-cell`, … | components §2, §5 |
| Navigation | `tab-bar`, `segmented`, `chips-row`, `search-field`, `page-dots`; native `back`, `header` | `.tma-tabbar`, … | components §3 |
| Actions | `main-button`, `secondary-button`, `button`, `glass-button`, `quick-actions`, `chip` | `.tma-btn`, … | components §4 |
| Input | `text-field`, `select`, `date-time`, `switch`, `slider`, `stepper`, `pin`, `file-input`, `rating` | `.tma-input`, … | components §5 |
| Display and data | `figure`, `delta`, `chart`, `progress`, `skeleton`, `banner`, `hero`, `coachmark`, `snackbar` | `.tma-figure`, … | components §6 |
| Media | `image`, `video`, `gallery`, `carousel`, `audio`, `file`, `sticker-moment`, `map`, `qr` | `.tma-media`, … | components §6a |
| Tables | `data-table`, `compact-table`, `sortable-table`, `sticky-column-table`, `leaderboard`, `comparison` | `.tma-table`, `.tma-kv` | components §6b |
| Overlays | native `popup`, `qr-scanner`; `sheet`, `action-sheet`, `menu` | `.tma-sheet`, `.tma-menu` | components §7 |
| Icons | 83 ids with SF Symbol and Material equivalents | `_kit/icons.svg` | components §6c |
| Telegram's own values | `stars-amount`, `gram-amount`, `gift-card`, `unique-gift`, `rarity-chip`, `limited-counter`; patterns and `avoid` for Premium, verification | `.tma-amount`, `.tma-gift`, `tg-values.ts` | telegram-elements |
| Framework tokens | shadcn/ui and Tailwind names bridged to the roles | `_kit/tma-bridge.css` | rework §6 |

What is not covered and why: anything the read sources did not show and Telegram does not need (wheel
date pickers: the native input; numbered pagination, breadcrumbs, hamburger menus, bottom toolbars,
floating action buttons, fullscreen modals: replaced, see `avoid` entries). Not read at all: the Telegram UI
community Figma kit and Appetite UI; nothing in the skill comes from them.
