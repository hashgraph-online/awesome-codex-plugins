# 91 — A minimal Mini App: menu button, startapp, theme, BackButton, MainButton

Product recipe (no registry row). Verified 2026-11-23 against Bot API 10.5 and the Mini Apps page.
References: `references/mini-apps/launch-and-lifecycle.md`, `references/mini-apps/design-system.md`.
Tags: **[API]**, **[official]**, **[heuristic]**.

1. **Request and visible result.** “Give our coffee bot an app for ordering ahead.” — A menu button opens a
   two-tab app (Menu, Order) that looks like Telegram in light and dark, on iOS and Android; a drink opens a
   detail screen with Telegram's Back in the header and “Add to order · €4.20” in the bottom bar; the
   pickup form ends with “Place order · €8.40”; links with `startapp=drink-flat-white` open that drink.
2. **Why these features.** Native chrome: BackButton and MainButton instead of an own arrow and fixed CTA
   **[official: Design Guidelines]**; theme variables instead of colours (G1) **[official]**; `ready()` after
   the first screen hides Telegram's loading screen **[official]**; launch params copied before a router can
   erase the hash **[heuristic]**; closing confirmation only while the form has unsaved input
   **[official]**.
3. **Requirements.** Any client from 6.1 (BackButton, colours); SecondaryButton 7.10, safe areas 8.0,
   custom-emoji MainButton icons 9.5 are gated by the kit **[official]**. Menu button via `setChatMenuButton`
   or @BotFather; Main Mini App and direct links via @BotFather **[API]/[official]**. HTTPS hosting.
4. **Payload.** `examples/payloads/r91-minimal-mini-app.json`: `setChatMenuButton` (`web_app`) and
   `sendMessage` with an inline `web_app` button.
5. **Code.** App: `examples/mini-apps/vanilla/index.html` + `app.ts` on the kit (`_kit/tma.css`,
   `_kit/tma.ts`: `createTma`, `chrome`, `nav`, `mainButton`, `haptic`, `ready`), built by
   `examples/mini-apps/build.mjs` (no packages). Bot: `r90_99_mini_apps.py::r91`, `bot_side.py`
   (`set_menu_button`, `send_open_button`, `link`). React variant: `examples/mini-apps/react`.
6. **Sequence and state.**
   ```mermaid
   stateDiagram-v2
     [*] --> menu: open (menu button / link)
     menu --> drink: tap (BackButton shown, MainButton "Add")
     drink --> menu: Back / Add
     menu --> order: tab
     order --> pickup: Continue (MainButton "Place order")
     pickup --> order: placed (closing confirmation off)
   ```
   State: the cart in memory (persist it in `CloudStorage` or your server for real use); `dirty` turns
   closing confirmation on.
7. **Result.** Mock preview screenshots: `py -3 scripts/preview_miniapp.py examples/mini-apps/vanilla
   --serve 8790` → `/?view=matrix` (iOS/Android × light/dark × 320/390/430, fullscreen, compact).
8. **Typical mistake, limits, alternative.** An own header with a back arrow; a fixed “Order” button at the
   bottom; `100vh`; a white flash in dark mode; `ready()` after data loads; a hash router that drops
   `tgWebAppData`. Limits: `sendData` only from reply-keyboard launches **[official]**. Alternative for 3
   items: a message with buttons.
9. **Run and verify.** `node build.mjs` and `node --test _kit/tma.test.ts` in `examples/mini-apps` ·
   `py -3 scripts/miniapp_lint.py examples/mini-apps --strict` · the preview matrix ·
   `py -3 examples/python/recipes/r90_99_mini_apps.py r91`. Evidence: unit tests, lint, mock preview; real
   clients not checked here.
10. **Adapt.** Keep: the kit's start order (launch params → chrome → first screen → `ready()`), one
    navigation stack, MainButton per screen, tab roots without a MainButton. Replace: the menu data and the
    fake `fetchMenu` with your API (`Authorization: tma <initData>`, recipe 92). Pick a style
    (`references/mini-apps/design-system.md` §9). Related: recipes 93 (checkout), 94 (forms).
