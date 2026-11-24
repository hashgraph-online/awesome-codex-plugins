# 90 — Bot or Mini App: deciding the surface and building the hybrid

Product recipe (no registry row). Verified 2026-11-23 against Bot API 10.5 and
https://core.telegram.org/bots/webapps. Decision reference: `references/mini-apps/decide.md`; product
patterns: `references/mini-apps/screen-patterns.md`. Tags: **[API]**, **[official]**, **[heuristic]**.

1. **Request and visible result.** “Our café bot works with buttons, but people want to browse the whole
   menu. Should we build a Mini App?” — A decision per task, not per bot: rating a drink stays a button, the
   live order card is a widget, the catalogue with search becomes a Mini App; the bot keeps notifications
   and opens the app on the exact screen (“Order 1042 is ready” → `startapp=order-1042`).
2. **Why these features.** Mini Apps need hosting, `initData` checks and a second codebase **[heuristic]**,
   so they are used only where the chat cannot work: network data at view time, uploads, long forms, deep
   navigation, dense data, gestures, fullscreen (`decide.md` §2). Notifications stay in the chat because
   users do not open an app to learn their order shipped **[heuristic]**. `startapp` reaches the app as
   `start_param` **[official]**.
3. **Requirements.** Bot API ≥ 6.7 for direct links (`t.me/<bot>/<app>?startapp`), ≥ 7.8 for the Main Mini
   App profile button (enabled in @BotFather) **[official]**. Inline and keyboard `web_app` buttons work in
   private chats only; a `url` button with a `t.me` link works anywhere **[API]**.
4. **Payload.** `examples/payloads/r90-decide-and-hybrid.json`: `sendMessage` with a `url` button to
   `https://t.me/coffee_pickup_bot?startapp=order-1042`, then `setChatMenuButton` with a `web_app` button.
5. **Code.** `examples/python/recipes/r90_99_mini_apps.py::r90` (`choose_surface` follows `decide.md` §4)
   on top of `examples/mini-apps/bot/bot_side.py` (`MiniAppBot.send_alert_with_link`, `set_menu_button`).
   App side: `examples/mini-apps/vanilla` (menu), `examples/mini-apps/catalog` (catalogue patterns).
6. **Sequence and state.**
   ```mermaid
   flowchart LR
     task --> q1{"≤ 3 answers, no network, ≤ 2 levels?"}
     q1 -- yes --> messages
     q1 -- no --> q2{"custom layout, no text input, private chat?"}
     q2 -- yes --> widget
     q2 -- no --> miniapp["Mini App + bot notifications"]
   ```
7. **Result.** Mock-up of the hybrid:
   ```
   Bot: Order 1042 is ready at the counter.   [ Open order ]  -> Mini App opens on order 1042
   Menu button: [ Order coffee ]              -> Mini App opens on the menu
   ```
8. **Typical mistake, limits, alternative.** A Mini App that is only a list of links back into the chat; a
   Mini App for one yes/no; notifications moved into the app; `web_app` buttons in groups (private chats
   only **[API]**). Alternative: a widget for a live card in a private chat (recipe 05), messages for 1-3
   answers (recipe 03).
9. **Run and verify.** `py -3 examples/python/recipes/r90_99_mini_apps.py r90` (2 self-checks) ·
   `py -3 -m unittest tests/test_mini_apps_recipes.py`. Evidence: offline contract.
10. **Adapt.** Keep: one decision per task, notifications in the bot, `startapp` to the exact screen.
    Replace: the routes (`order-<id>`, `tab-<name>`) with your app's, parsed by an allowlist on both sides
    (`parseStartParam` in the kit, `parse_start_param` on the server). Related: recipe 91 (first Mini App),
    `references/mini-apps/launch-and-lifecycle.md`.
