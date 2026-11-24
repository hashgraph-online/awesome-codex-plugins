# 96 — Profile and settings in a Mini App, with permission to message

Product recipe (no registry row). Verified 2026-11-23 against Bot API 10.5. Components: settings rows in
`references/mini-apps/components.md` §6d. Tags: **[API]**, **[official]**, **[heuristic]**.

1. **Request and visible result.** “Users should manage notifications, language and their plan in the app,
   and get order updates from the bot.” — A settings screen in grouped rows (value, chevron, toggle, date
   pill, pop-up menu, stepper, checkmarks), the Settings item in Telegram's ⋯ menu, a plan screen with a
   clear Cancel, and the first bot message only after the user allowed it.
2. **Why these features.** `SettingsButton` (7.0) puts Settings where Telegram users look for it
   **[official]**; `requestWriteAccess` (6.9) → `write_access_allowed` service message before the bot writes
   first **[API]**; toggles apply at once with `selectionChanged` **[official]/[heuristic]**; preferences in
   `CloudStorage` sync across devices **[official]**; destructive rows confirm with `showConfirm` **[heuristic]**.
3. **Requirements.** 6.9 for write access and CloudStorage, 7.0 for SettingsButton; private chat with the
   bot for messages.
4. **Payload.** `examples/payloads/r96-profile-settings.json`: the message the bot sends after
   `write_access_allowed` (none before it) and the per-user menu button.
5. **Code.** Bot: `r90_99_mini_apps.py::r96`, `bot_side.py` (`on_write_access_allowed`, `notify`). App: the
   kit gallery's Settings group (`examples/mini-apps/gallery`, every trailing type), `tma.settings(cb)`,
   `tma.store()`, `tma.confirm()`; plans: `examples/mini-apps/catalog` → a members-only workout → plans.
6. **Sequence and state.**
   ```mermaid
   sequenceDiagram
     participant A as Mini App
     participant T as Telegram
     participant B as Bot
     A->>T: requestWriteAccess()
     T-->>A: writeAccessRequested {status: allowed}
     T->>B: message.write_access_allowed
     B->>B: remember the user may be messaged
     B->>T: sendMessage("Order notifications are on…")
   ```
7. **Result.** “Order notifications are on. Turn them off in the app's settings.” — sent once, after
   permission.
8. **Typical mistake, limits, alternative.** Messaging users who only opened the app; a gear icon drawn in
   the header area instead of SettingsButton; settings saved only on a “Save” button at the bottom; cancel
   buried in support. Alternative: 3-5 settings as an inline screen in the chat (recipe 24).
9. **Run and verify.** `py -3 examples/python/recipes/r90_99_mini_apps.py r96` ·
   `py -3 -m unittest tests/test_mini_apps_recipes.py` · preview the gallery's Settings group.
10. **Adapt.** Keep: permission before the first message, settings applied at once, the ⋯ menu entry.
    Replace: the preference keys (keep them stable: they are a contract). Related: recipes 10 (bot
    settings), 24 (settings in the chat), 25 (subscriptions).
