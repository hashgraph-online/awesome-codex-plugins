---
summary: "Start page for Telegram Mini Apps: routing by task, reading order, sources and labels, offline data and tools, what is not covered yet; the agent's route by request is orchestration.md §1."
verified: "2026-11-23"
bot_api: "10.5"
---

# Mini Apps: start here

This folder is the skill's branch for **Telegram Mini Apps** (web apps opened inside Telegram through
`window.Telegram.WebApp`): deciding when to build one, launching it, the client API, a design system that
looks native in both themes and on both platforms, components and screens, anti-slop rules, `initData`
security, performance and testing. Verified against **Bot API 10.5 (2026-11-22)** and
https://core.telegram.org/bots/webapps on **2026-11-23**; the newest Mini App change is Bot API 10.1, the
highest version gate in `telegram-web-app.js` is `9.6`.

The bot side (launch buttons, `web_app_data`, `answerWebAppQuery`, prepared messages and buttons) stays in
[../mini-apps-bridge.md](../mini-apps-bridge.md). Payments from a Mini App: [../payments-and-stars.md](../payments-and-stars.md).
TON wallet: [../wallet-and-ton.md](../wallet-and-ton.md). Widgets inside a message: [../widgets.md](../widgets.md).

## Route by task

| The task | Read | Then |
|---|---|---|
| "Create a Mini App" or "improve / restyle / fix this one": the whole order of work | [orchestration.md](orchestration.md) | the steps link the rest |
| "Should this be a Mini App?" | [decide.md](decide.md) | recipe 90 |
| Open a Mini App from a button, link, menu or profile; `startapp`; hosting | [launch-and-lifecycle.md](launch-and-lifecycle.md) | recipe 91 |
| "Does `Telegram.WebApp` have X, since which version?" | [webapp-api.md](webapp-api.md), `scripts/webapp_lookup.py` | — |
| Verify `initData`, sessions, what to trust | [security.md](security.md) | recipe 92 |
| Take payments: Stars, subscriptions, cards for physical goods, every `invoiceClosed` status | [payments.md](payments.md) | recipes 93, 96 |
| Show Telegram's own things: Stars, grams (formerly Toncoin), gifts and rarity, Premium, boosts; what never to draw | [telegram-elements.md](telegram-elements.md) | gallery group Telegram |
| "How does iOS 27 / Telegram build this?": row, header, button, tab bar, sheet, alert, empty state sizes; how Telegram composes Wallet-, catalogue- and form-like screens | [native-anatomy.md](native-anatomy.md) | `data/mini-apps/design-sources.json` → `ios27.anatomy` |
| Haptics (the Taptic Engine), motion sensors, location, biometrics, fullscreen, orientation, QR, home screen, sharing | [haptics-and-device.md](haptics-and-device.md) | `tma.haptic`, `tma.motion`, `tma.location`; gallery group Device |
| VoiceOver / TalkBack, text size, contrast, touch targets; the user's language, plurals, numbers and dates; right to left | [accessibility-and-language.md](accessibility-and-language.md) | `tma.locale()`, `.tma-sr-only`; stand Language select |
| Forms, fields and the on-screen keyboard; validation, drafts, closing; loading, cache, errors, retries, doing an action once | [forms-and-data.md](forms-and-data.md) | `tma.api()`, `tma.hideKeyboard()`; stand Network select |
| Glass and materials as tokens; "modern" / "trendy" / "new iOS look" requests; new CSS features in Telegram's WebViews; what to do when a platform redesigns | [materials-and-trends.md](materials-and-trends.md) | `--tma-glass-*`, `.tma-glass.is-thin / .is-thick`, `.tma-scroll-edge` |
| Read a Figma file (a kit or the person's own design) through the Figma MCP and turn it into rules, tokens or screens | [figma-workflow.md](figma-workflow.md) | — |
| Make it look like Telegram in light and dark, iOS and Android | [telegram-design-guidelines.md](telegram-design-guidelines.md), [design-sources.md](design-sources.md), [design-system.md](design-system.md) | `examples/mini-apps/_kit` |
| "Make it look like X", "use our brand", "calmer / denser / fintech", restyle an existing app | [design-system.md](design-system.md) §9 styles, `scripts/miniapp_style.py` | `data/mini-apps/styles.json` |
| Build a screen: shop, gym and trainers, bookstore, SaaS dashboard, form, booking, game, editor | [screen-patterns.md](screen-patterns.md), [components.md](components.md) | recipes 93-99 |
| Where the image, title, price, rating go; galleries, filters, booking, plans; review a screen | [layout-rules.md](layout-rules.md), `scripts/miniapp_layout.py` | `examples/mini-apps/catalog` |
| "Rework our Mini App into classic Telegram design", redesign an existing app (any stack) | [rework.md](rework.md), `scripts/miniapp_rework.py plan` | `examples/mini-apps/rework` |
| "It looks generated / web-like / off", "make it premium" | [anti-slop.md](anti-slop.md), `scripts/miniapp_lint.py` | — |
| Speed, weak Android, how to test without a phone | [performance-and-testing.md](performance-and-testing.md), `scripts/preview_miniapp.py` | — |

## Reading order for a new Mini App

1. [decide.md](decide.md): is it a Mini App, which entry point, what the bot says before and after.
2. [launch-and-lifecycle.md](launch-and-lifecycle.md): start sequence, `ready()`, visibility, hosting.
3. [security.md](security.md): the server contract, before any API route exists.
4. [telegram-design-guidelines.md](telegram-design-guidelines.md) G1-G7, then [design-system.md](design-system.md):
   pick a style (§9), use the kit, check [anti-slop.md](anti-slop.md).
5. The closest screen pattern and recipe; then build, lint, preview, test on a device.

## Sources and labels

| Label | Meaning |
|---|---|
| **[Official]** | core.telegram.org/bots/webapps, including its Design Guidelines |
| **[API]** | the Bot API page and changelog |
| **[Heuristic]** | this skill's decision; can change with evidence |
| **[Third-party]** | a library outside Telegram (`@tma.js/*`, TelegramUI): its behaviour is its own, not Telegram's |

Figma sources read for the design files (2026-11-23): Apple iOS and iPadOS 27 and the Telegram Mini Apps UI
Kit (Community). Not read: the Telegram UI community kit, Appetite UI (paid, licence forbids
redistribution). [design-sources.md](design-sources.md) says what was taken from each.

## Offline data and tools

| File | What |
|---|---|
| `data/mini-apps/webapp-catalog.json` | every `Telegram.WebApp` member with version, evidence and anchor URL |
| `data/mini-apps/theme-params.json` | `themeParams` key → CSS variable → role → fallbacks |
| `data/mini-apps/design-sources.json` | iOS 27 colours, type scale, glass, sizes; mapping to theme roles |
| `data/mini-apps/styles.json` | named design styles: intent, tokens, components, do and don't |
| `data/mini-apps/components.json` | 126 elements (structure, navigation, actions, settings, input, display, media, tables, overlays, Telegram's own values) with variants, states, kit class, native replacement and status |
| `data/mini-apps/icons.json` | 83 kit icons mapped to SF Symbol, Material and Lucide names; the open SVG libraries allowed when the kit lacks an icon |
| `data/mini-apps/palettes.json` | named brand palettes for new apps: Apple's system colours (light, dark, increased contrast) from the HIG, a starting choice per product type |
| `scripts/webapp_lookup.py` | `show`, `search`, `since`, `gates`, `theme`, `sync` over the catalog |
| `data/mini-apps/layouts.json` | layout rules L01-L25 and 16 content types (image ratio, card slots, price, primary action, detail order) |
| `scripts/miniapp_layout.py` | `entities`, `show`, `rules`, `review` a screen description (validated against `schema`), `example` |
| `scripts/miniapp_style.py` | `presets`, `palettes`, `show`, `css`, `check` for styles and brand profiles (`"brand": "teal"` or own colours) |
| `scripts/miniapp_lint.py` | 44 rules: security, native controls, theme, motion, labels, slop, payments, Telegram's own marks, rework tells (`--json`, `--strict`) |
| `scripts/fetch_telegram_star.py` | Telegram's original Stars glyph (GPL-3.0, Telegram Web A) into an app that accepts that licence; pinned and hash-checked |
| `scripts/miniapp_rework.py` | `plan` (staged rework plan with replacements, colour map, type map), `colours`, `type` |
| `data/mini-apps/rework-map.json` | every lint rule and 13 web patterns → the Telegram replacement, kit part and reference |
| `scripts/preview_miniapp.py` | local stand with a mock client: platforms, themes, widths, fullscreen, versions, invoice outcomes, haptics log, synthetic motion sensors and location, the user's language (RTL included), the network for the app's own requests (slow, flaky, offline, 500, 401); `--api mock.json` for the app's own server routes |
| `examples/mini-apps/_kit` | `tma.css` (roles, scales, primitives, style presets), `tma.ts` (no-dependency kit), `tg-values.ts` (Stars, grams, gift colours, rarity), `tma-bridge.css` (shadcn / Tailwind tokens → roles), `icons.svg` |
| `examples/mini-apps/gallery` | every kit element on one page: open it in the stand and switch platform, theme, width, style |

## Not covered yet

- **Studio.** The local bot-ui Studio does not model Mini Apps yet. Next step: `web_app` buttons and the menu
  button as nodes of the screen map, and a simulator tap that opens `scripts/preview_miniapp.py` with the
  node's `start_param` and the chat's theme. Until then, preview Mini Apps with the stand directly.
- **The preview stand and the real bridge.** The stand mocks `window.Telegram.WebApp`; apps that talk to
  Telegram only through `@tma.js/sdk` (the React example) build and type-check but need the Telegram test
  environment or a device to show native chrome.
- **Real devices.** Every screenshot in this branch is a mock preview; check iOS, Android and Desktop clients
  before shipping ([performance-and-testing.md](performance-and-testing.md) §5).

Refresh after a Telegram release: `py -3 scripts/webapp_lookup.py sync --fetch` prints the diff;
add `--write` to update the catalog, then re-run the tests.
