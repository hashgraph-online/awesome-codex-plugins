# 98 — Share a result from a Mini App to a chat

Product recipe (no registry row). Verified 2026-11-23 against Bot API 10.5. References:
`references/mini-apps-bridge.md`, `references/inline-mode.md` (prepared inline messages).
Tags: **[API]**, **[official]**, **[heuristic]**.

1. **Request and visible result.** “Let users send their favourite drink to friends, and post the order to
   the chat they opened the app from.” — “Share” opens Telegram's chat picker with a ready card; an app
   opened from an inline button posts the result into that chat once; “Share to a group” opens Telegram's
   own group picker.
2. **Why these features.** `savePreparedInlineMessage` (bot) → `WebApp.shareMessage(id)` (app, 8.0)
   **[API]/[official]**; `answerWebAppQuery` for apps launched with a `query_id` (inline or menu button),
   once **[API]/[heuristic]**; `savePreparedKeyboardButton` (bot, 9.6) → `WebApp.requestChat(id)` (app) for a
   native chat picker, result as `chat_shared` **[API]/[official]**; `switchInlineQuery` to hand over to
   inline mode **[official]**.
3. **Requirements.** 8.0 for `shareMessage`, 9.6 for `requestChat`; inline mode enabled for
   `switchInlineQuery`; prepared ids expire (`expiration_date`) **[API]**.
4. **Payload.** `examples/payloads/r98-share-result.json`: `savePreparedInlineMessage` (users, groups,
   channels), one `answerWebAppQuery`, `savePreparedKeyboardButton` with `request_chat`.
5. **Code.** Bot: `r90_99_mini_apps.py::r98`, `bot_side.py` (`prepare_share`, `answer_query_once`,
   `prepare_chat_picker`). App: call `shareMessage(id)` / `requestChat(id)` behind `tma.has('8.0')` /
   `tma.has('9.6')`; handle `shareMessageFailed` (`MESSAGE_EXPIRED`: ask the server for a new id).
6. **Sequence and state.**
   ```mermaid
   sequenceDiagram
     participant A as Mini App
     participant S as Server/Bot
     participant T as Telegram
     A->>S: share favourite (initData)
     S->>T: savePreparedInlineMessage
     T-->>S: PreparedInlineMessage {id, expiration_date}
     S-->>A: id
     A->>T: shareMessage(id) → user picks a chat
     T-->>A: shareMessageSent
   ```
7. **Result.** The friend receives “My usual: flat white, oat milk. Try it at Central.” as a message via the
   bot.
8. **Typical mistake, limits, alternative.** Reusing an expired id; answering a query twice; building the
   message text from client input without escaping; sharing from a launch without chat access through
   `answerWebAppQuery` (Main Mini App and direct links have no `query_id`). Alternative: inline mode (recipe
   60).
9. **Run and verify.** `py -3 examples/python/recipes/r90_99_mini_apps.py r98` (2 self-checks) ·
   `py -3 -m unittest tests/test_mini_apps_recipes.py`.
10. **Adapt.** Keep: one prepared id per share, one answer per query, gated calls. Replace: the card text
    and its buttons. Related: recipes 60 (inline mode), 97 (game share).
