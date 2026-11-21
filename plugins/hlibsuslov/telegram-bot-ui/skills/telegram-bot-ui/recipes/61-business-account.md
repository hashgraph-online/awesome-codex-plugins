# 61 — Business-account bot: auto-replies and quick replies on behalf of a bakery

Product recipe (combines mechanisms; no registry row of its own). Uses `business_connection` /
`business_message` updates, `business_connection_id` on send methods, `readBusinessMessage`,
`InlineKeyboardMarkup.force_reply` (10.3), disabled buttons (10.3), `<tg-time>`. Verified
2026-11-15 against Bot API 10.4 (newest release on that date, 2026-11-09). Index of all product
recipes: `references/use-case-playbooks.md`.
Tags: **[API]** = API requirement, **[official]** = official recommendation, **[heuristic]** =
design heuristic of this skill.

1. **Request and visible result.** “I run a bakery and answer the same questions all day —
   opening hours, the menu. Connect the bot to my Telegram Business account so it answers
   customers for me, and let me add a personal line in one tap.” — The owner connects the bot
   in Settings → Business → Chatbots and immediately gets a message in the bot's chat saying
   what it can and cannot do with the rights they granted. A customer writes “What are your
   hours today?”; the bot answers **from the owner's account** with the opening hours and
   *Menu* / *How to find us* link buttons, and the owner gets a panel in the bot chat with
   *Send: open till 19:00*, *Send: today's special*, *Write my own*, *Pause auto-replies*.
   Turning the connection off stops everything and the owner is told once.
2. **Why these features.**
   - Rights decide behaviour **[API]**: without `can_reply` the bot is **read-only** (the panel
     shows a disabled “Reply access is off” button instead of quick replies);
     `readBusinessMessage` needs `can_read_messages`; replying is possible only in chats with
     incoming messages in the **last 24 hours**. A disabled button never replaces the server
     re-check: the run re-checks rights and window at every tap **[API: disabled “does
     nothing”; the check is yours]**.
   - Messages sent on behalf of a business have **no reply keyboard** (`ReplyKeyboardMarkup` is
     not supported there); inline keyboards work, and `switch_inline_*` and `web_app` buttons are
     not available, so the customer message carries only `url` buttons **[API]**.
   - Quick replies are proposed to the **owner in the bot's private chat** (`user_chat_id` of
     the connection), not to the customer: the owner stays the author **[heuristic]**.
   - *Write my own* uses a message with `InlineKeyboardMarkup.force_reply` (10.3): a *Back*
     button and the reply field open together. The flag is fixed for the message's lifetime, so
     this screen is always a **new** message **[API]**.
   - `style: "primary"` on the first quick reply only (9.4), `disabled: {}` for “window closed”
     (10.3) **[heuristic]**. The deadline is a `<tg-time>` entity that shows in the owner's
     time zone **[API]**.
   - “Manage Bot” opens the bot with `/start bizChat<user_chat_id>` where the id is the managed
     (customer) chat **[official, features page]**.
3. **Requirements.** The **owner** uses Telegram Business; the bot has Secretary Mode enabled
   in @BotFather and the owner adds it in Settings → Business → Chatbots, choosing which
   rights to grant **[official, features page]**. `allowed_updates` must include
   `business_connection`, `business_message` (and `edited_business_message`,
   `deleted_business_messages` if you track them) and `callback_query`. Production. The bot
   must follow the Telegram Business section (5.4) of the Bot Developer ToS **[official]**.
4. **Payload.** Full request sequence: `examples/payloads/r61-business-account.json`. Incoming
   fixtures in `examples/fixtures/`: `usecase_business_connection.json` (rights: `can_reply`
   only), `usecase_business_connection_readonly.json` (rights: `can_read_messages` only),
   `usecase_business_connection_disabled.json` (`is_enabled: false`),
   `usecase_business_message.json` (a customer message).

   | Screen | Message | Buttons (row by row) | Leaves to |
   |---|---|---|---|
   | connected | “Connected: …”, what the bot can / can't do | — | — |
   | customer chat | auto-reply (hours or greeting) **from the owner's account** | `Menu` url · `How to find us` url | — |
   | panel (owner, bot chat) | name, last message, auto-replies on/off, “reply until <time>” | `Send: open till 19:00` primary · `Send: today's special` · `Write my own` · `Pause auto-replies` | quick reply, compose, pause |
   | panel, read-only | name, last message, “Read-only mode” | `Reply access is off` (disabled) | — |
   | panel, window closed | same | `24 h window closed` (disabled) · pause | — |
   | compose | “Reply to this message with your text…” + reply field | `← Back` + force_reply | panel (new message) |
   | disabled | “Connection turned off…” | — | — |

   Key parts:
   ```json
   {"method": "readBusinessMessage", "params": {"business_connection_id": "bizconn_bob", "chat_id": 333333333, "message_id": 5}}
   {"method": "sendMessage", "params": {"business_connection_id": "bizconn_oksana", "chat_id": 222222222,
     "text": "Вітаю, Іван! Ми працюємо з 8:00 до 19:00, з понеділка по суботу.", "parse_mode": "HTML",
     "reply_markup": {"inline_keyboard": [[{"text": "Меню", "url": "https://bakery.example/menu"},
       {"text": "Як нас знайти", "url": "https://bakery.example/map"}]]}}}
   {"method": "sendMessage", "params": {"chat_id": 111111111, "text": "Дайте відповідь на це повідомлення … <b>Іван</b> …",
     "reply_markup": {"inline_keyboard": [[{"text": "← Назад", "callback_data": "bz:4:panel"}]], "force_reply": true}}}
   ```
5. **Code.** `examples/python/recipes/r61_business_account.py` (`BizBot.on_connection`,
   `on_business_message`, `can_send`, `auto_reply`, owner panel screens `panel`/`compose`) on
   top of `examples/python/tgkit/flows.py` (`ScreenFlow`, `OnceStore`, `UpdateDedup`,
   `tg_time`, `I18n`). No TypeScript twin.
6. **Sequence and state.**
   ```mermaid
   stateDiagram-v2
     [*] --> connected: business_connection is_enabled (rights stored, owner told)
     connected --> connected: customer message -> auto-reply (can_reply, 24 h) + owner panel
     connected --> read_only: no can_reply -> panel with disabled button
     connected --> sent: owner taps quick reply (once per message+reply)
     connected --> compose: Write my own (force_reply, new message)
     compose --> sent: owner replies with text (1-4096)
     connected --> disabled: business_connection is_enabled=false
     disabled --> disabled: customer message -> ignored and logged
   ```
   State: `conns[id] = {owner, user_chat_id, rights, enabled, lang}`,
   `chats[(connection, customer chat)] = {name, lang, last_text, last_date, last_msg, auto}`.
   The 24 h window is computed from `last_date` of the customer's latest message. Every send
   goes through `can_send()` (`off` → `no_reply` → `window`), so a button that stayed on screen
   after the situation changed gets a toast, not a failed request. The owner's panel is a
   `ScreenFlow` session of the owner: only the owner can tap it (“belongs to the account
   owner”), a double tap is stale, and a new customer message replaces the panel (old
   buttons stop working). `OnceStore` key `qr:<connection>:<chat>:<customer message>:<reply>`
   survives re-opening the panel through “Manage Bot”: the same quick reply for the same
   customer message is sent once.
7. **Result.** Mock-ups (not client screenshots), Ukrainian owner / English owner:
   ```
   Підключено: Оксана                        Connected: Bob
   Що я можу:                                What I can do:
   • Відповідати за вас протягом 24 год …    • Mark customer messages as read
   Чого я не можу:                           What I can't do:
   • Позначати прочитаними: доступ …         • Reply: access is off, so I work read-only

   Іван                                      Maria
   Останнє повідомлення: «Які години?»       Last message: «Do you have vegan buns?»
   Автовідповіді: увімкнено                  Read-only mode: reply access is off.
   [ Надіслати: до 19:00 ]                   [ Reply access is off ]  (disabled)
   [ Надіслати: меню дня ]
   [ Написати свою ]
   [ Пауза автовідповідей ]
   ```
8. **Typical mistake, limits, alternative.** Mistakes: sending a reply keyboard on behalf of a
   business (not supported); replying outside the 24 h window; assuming rights never change
   (the owner can change them any time: store the latest `business_connection`); answering
   the owner's own messages (they arrive as `business_message` too, the run ignores
   `from.id == owner`); calling `readBusinessMessage` without `can_read_messages`; answering a
   customer for a disabled or unknown connection; a quick-reply button that sends twice; the
   owner's text inserted into HTML unescaped (the run sends `<o_O>` as `&lt;o_O&gt;`).
   Limits **[API]**: text 1-4096 chars, `callback_data` ≤ 64 bytes,
   `readBusinessMessage` needs the chat active in the last 24 hours. Failure paths in the run:
   message for an unknown connection → logged and ignored; for a disabled one → ignored; quick
   reply tapped twice → stale, and from a re-opened panel → “Already sent”; a stranger taps the
   owner's panel → alert “belongs to the account owner”; 5000-character text → error on the
   same step, prompt stays; window closed before the tap → toast; unknown customer chat in
   `bizChat` → explanation. Alternative: when the owner has no Business account, a normal bot chat with a
   “contact the shop” button (recipe 21).
9. **Run and verify.** `py -3 examples/python/recipes/r61_business_account.py` (9 self-checks)
   · `py -3 -m unittest tests/test_usecases.py` (validators with context `business` on every
   message that carries `business_connection_id`: a reply keyboard or `web_app` would fail;
   64-byte callbacks, copy in en/uk, payload drift). Evidence: offline contract; no real
   Business account was connected.
10. **Adapt.** Keep: rights-driven modes, `can_send()` re-check at tap time, inline url buttons
    only on behalf of the business, quick replies proposed to the owner, `OnceStore` per
    (connection, chat, message, reply), ignoring the owner's own messages. Replace: the
    keyword matching (`auto_reply`) with your FAQ or an AI draft that the owner approves, the
    replies and links, the in-memory stores with a database; add `deleted_business_messages`
    handling if you mirror chats. Related: `recipes/21-support-desk.md` (operator handoff),
    `recipes/03-multi-step-form.md` (force_reply steps), `references/specialized-updates.md`,
    `references/buttons-and-styles.md#disabled-buttons`.
