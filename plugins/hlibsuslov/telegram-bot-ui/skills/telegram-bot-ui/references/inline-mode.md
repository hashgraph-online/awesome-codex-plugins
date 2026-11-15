# Inline mode

Users type `@yourbot query` in **any** chat and pick a result; the message is sent
by the user "via @yourbot". Also covers the switch buttons that open inline mode,
`chosen_inline_result`, editing inline messages by `inline_message_id`, and prepared
inline messages for Mini Apps. Checked against Bot API 10.4 on **2026-11-15**:
https://core.telegram.org/bots/api#inline-mode, https://core.telegram.org/bots/inline.
Every JSON block passes `scripts/validate_payload.py`.

Labels: **[API]** spec; **[Official]** Telegram's guides; **[Heuristic]** this skill's advice.

## Bot settings (BotFather)

| Command | Effect |
|---|---|
| `/setinline` | turns inline mode on and sets the input placeholder **[Official]** |
| `/setinlinegeo` | the client asks the user for location; `InlineQuery.location` filled **[Official]** |
| `/setinlinefeedback` | enables `chosen_inline_result`; a sampling probability (1/10, 1/100, 1/1000) limits load **[Official]** |

Without `/setinline` nobody can invoke the bot inline; without feedback there are no
`chosen_inline_result` updates at all.

## Flow and state

```
user types "@bot pizza"  ──► Update.inline_query {id, query, offset, chat_type}
                                  │ answerInlineQuery(results ≤ 50, cache_time, next_offset)
user scrolls to the end   ──► inline_query again with offset = your next_offset
user taps a result        ──► message sent by the user, "via @bot"
                              ──► Update.chosen_inline_result (only with feedback on)
user taps a callback button on that message ──► callback_query with inline_message_id
                                                (no message, no chat)
```

- **[API]** `query` is up to 256 characters; an empty query is normal — return default or
  trending results.
- **[API]** At most **50 results** per answer; `id` of each result 1-64 bytes, unique within
  the answer. `next_offset` ≤ 64 bytes; empty string = no more pages.
- **[API]** `cache_time` defaults to **300 s**; results are cached on Telegram's servers per
  query text for everyone unless `is_personal: true` (then per user). Personalised or
  permission-dependent results must be `is_personal` with a short `cache_time`.
- **[API]** `chat_type`: `sender` (private chat with the inline sender), `private`,
  `group`, `supergroup`, `channel`; may be missing for some clients/secret chats.
- **[Heuristic]** Keep no per-query server state other than a short cache keyed by
  `(query, offset, user if personal)`. Encode pagination in `next_offset` (e.g. a
  cursor), not in memory. Answer fast: inline queries are typed letter by letter, so
  debounce expensive search and return something within ~1 s.

### Example: answer with an article and a "connect account" button

```json
{"method": "answerInlineQuery", "params": {
  "inline_query_id": "AAEC12345",
  "results": [
    {"type": "article", "id": "pz-margherita", "title": "Margherita — 9.50 €",
     "description": "Tomato, mozzarella, basil",
     "input_message_content": {"message_text": "<b>Margherita</b> — 9.50 €\nTomato, mozzarella, basil", "parse_mode": "HTML"},
     "reply_markup": {"inline_keyboard": [[{"text": "Order", "callback_data": "ord:pz-margherita"}]]},
     "thumbnail_url": "https://example.com/t/margherita.jpg"}
  ],
  "cache_time": 30, "is_personal": true, "next_offset": "c:20",
  "button": {"text": "Connect your account", "start_parameter": "inline_connect"}
}}
```

- **[API]** `InlineQueryResultsButton` shows above the results; exactly one of
  `web_app` or `start_parameter` (1-64 chars, `A-Za-z0-9_-`). `start_parameter` opens the
  private chat with `/start inline_connect`; after setup, send the user back with a
  `switch_inline_query` button. **[Official]** pattern ("Switch to PM").

### Result types

- **[API]** `InlineQueryResult` is one of 20 types: `article`, `photo`, `gif`,
  `mpeg4_gif`, `video`, `audio`, `voice`, `document`, `location`, `venue`, `contact`,
  `game`, plus `InlineQueryResultCached*` variants (`photo`, `gif`, `mpeg4_gif`,
  `sticker`, `document`, `video`, `voice`, `audio`) that take a `*_file_id` instead
  of a URL. Cached and URL variants share the same `type` value — the presence of
  `photo_file_id` vs `photo_url` decides. `py -3 scripts/tg_api_lookup.py show
  InlineQueryResult` lists them; `validate_payload.py` resolves the ambiguity.
- **[API]** Any result can carry `input_message_content` to send something other than the
  media itself: `InputTextMessageContent`, `InputRichMessageContent` (10.1),
  `InputLocationMessageContent`, `InputVenueMessageContent`,
  `InputContactMessageContent`, `InputInvoiceMessageContent` (Stars invoices — see
  `payments-and-stars.md`), `InputWidgetMessageContent` and
  `InputSharedWidgetMessageContent` (10.4, test server only today — `widgets.md`).

```json
{"method": "answerInlineQuery", "params": {
  "inline_query_id": "AAEC12346",
  "results": [
    {"type": "photo", "id": "p1", "photo_file_id": "AgACAgIAAxkBAAIB"},
    {"type": "photo", "id": "p2", "photo_url": "https://example.com/p2.jpg", "thumbnail_url": "https://example.com/p2s.jpg", "caption": "Kyiv, 2026"}
  ],
  "cache_time": 300
}}
```

## `chosen_inline_result`

```json
{"update_id": 900000201, "chosen_inline_result": {
  "result_id": "pz-margherita",
  "from": {"id": 222222222, "is_bot": false, "first_name": "Taras"},
  "query": "pizza",
  "inline_message_id": "BAAAAJw0AAA8e2Kx"
}}
```

- **[API]** `inline_message_id` is present **only if the result had an inline keyboard**.
  Without a keyboard you can never edit that message. If you need to edit it later
  (live status, votes), attach at least one button.
- **[Official]** With caching, you may get more chosen results than queries; use sampling
  for popular bots. Do not use it as an exact usage counter. **[Heuristic]**

## Editing inline messages

The bot is not a member of the chat where the inline message lives; it has no
`chat_id`/`message_id`. Edit by `inline_message_id` instead:

```json
{"method": "editMessageText", "params": {
  "inline_message_id": "BAAAAJw0AAA8e2Kx",
  "text": "<b>Margherita</b> — ordered by Taras ✅",
  "parse_mode": "HTML",
  "reply_markup": {"inline_keyboard": [[{"text": "Track", "callback_data": "trk:8812"}]]}
}}
```

- **[API]** `editMessageText`, `editMessageCaption`, `editMessageMedia`,
  `editMessageReplyMarkup`, `editMessageLiveLocation`, `stopMessageLiveLocation`,
  `setGameScore`, `getGameHighScores` and `editMessageWidgetData` (10.4) accept
  `inline_message_id` (use it **instead of** `chat_id` +
  `message_id`) and return **`True`**, not a `Message`, for inline messages.
- **[API]** `editMessageMedia` on an inline message cannot upload a new file — use a
  `file_id` or URL.
- **[API]** Not available for inline messages: `deleteMessage`, `stopPoll`,
  `editMessageChecklist`, `pinChatMessage`. Plan "remove" as "edit to a closed state".
- **[API]** `CallbackQuery` from an inline message has `inline_message_id` and **no**
  `message`; `chat_instance` identifies the chat without revealing it.
- Ephemeral replies to such callbacks work without `chat_id` since 10.4
  (`ephemeral-and-personal.md#addressing-an-ephemeral-reply`).

## Switch buttons (opening inline mode from a keyboard)

| Field on `InlineKeyboardButton` | What the tap does | Not supported |
|---|---|---|
| `switch_inline_query` | pick any chat, insert `@bot <query>` | channel DM chats, business messages |
| `switch_inline_query_current_chat` | insert `@bot <query>` here | channels, channel DM chats, business messages |
| `switch_inline_query_chosen_chat` | pick a chat of allowed types (`allow_user_chats`, `allow_bot_chats`, `allow_group_chats`, `allow_channel_chats`) | channel DM chats, business messages |

All **[API]**. Use `switch_inline_query_current_chat` for "choose from a long list"
pickers inside the same chat; use `switch_inline_query_chosen_chat` for "Share
with a friend" with only private chats allowed. **[Heuristic]**

```json
{"method": "sendMessage", "params": {
  "chat_id": 222222222,
  "text": "Your order is ready to share.",
  "reply_markup": {"inline_keyboard": [[{"text": "Share with a friend", "switch_inline_query_chosen_chat": {"query": "order 8812", "allow_user_chats": true}}]]}
}}
```

## Prepared inline messages (Mini Apps)

- **[API]** `savePreparedInlineMessage(user_id, result, allow_*_chats)` stores one
  `InlineQueryResult` the user can send from a Mini App (`WebApp.shareMessage`);
  returns `PreparedInlineMessage` with `id` and `expiration_date`. Expired ids are
  unusable — create one per share action. See `mini-apps-bridge.md`.
- **[API]** `answerWebAppQuery(web_app_query_id, result)` sends a message on behalf of the
  user from an inline-mode Mini App; returns `SentWebAppMessage` (with
  `inline_message_id` only when the result has an inline keyboard).

```json
{"method": "savePreparedInlineMessage", "params": {
  "user_id": 222222222,
  "result": {"type": "article", "id": "share-8812", "title": "My order", "input_message_content": {"message_text": "I ordered a Margherita 🍕"}},
  "allow_user_chats": true, "allow_group_chats": true
}}
```

## What the user sees

- Results appear as a vertical list (articles, documents) or a horizontal/grid strip
  (photos, GIFs, stickers) above the keyboard; the tap sends immediately, no
  confirmation. **[Official]** So results must be complete and correct before the
  tap — never "click to finish" in the result itself. **[Heuristic]**
- The sent message shows "via @yourbot" next to the sender; tapping it re-inserts the
  mention (viral loop). **[Official]**
- `title` and `description` are the only text visible before sending; front-load the
  distinguishing word. **[Heuristic]**

## Common mistakes

| Mistake | Fix |
|---|---|
| Personal results cached for everyone | `is_personal: true`, short `cache_time` |
| No keyboard on a result you want to edit later | attach ≥1 button, else no `inline_message_id` |
| Editing with `chat_id` from `chosen_inline_result` | there is none; use `inline_message_id` |
| Expecting a `Message` back from an inline edit | the result is `True` |
| Duplicate result `id`s | unique, 1-64 bytes |
| 51+ results | ≤50 and paginate with `next_offset` |
| Handling `chosen_inline_result` but feedback is off / not in `allowed_updates` | `/setinlinefeedback` and list it (`updates-and-delivery.md`) |

## Error handling

- `answerInlineQuery` for an old query fails (the query expired while you were
  searching). Drop it; the user has typed something newer. **[Heuristic]**
- An invalid result in the array fails the whole answer. Validate offline with
  `py -3 scripts/validate_payload.py` and keep one bad record from breaking the list.
  **[Heuristic]**
