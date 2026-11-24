# Mini App bridge (bot side only)

How a bot **launches** Mini Apps and **receives data** from them, and how to trust that
data. The Mini App itself (the `Telegram.WebApp` client API, design system, screens,
security and testing) has its own branch: [mini-apps/README.md](mini-apps/README.md).
HTML widgets inside a message are a different thing (`widgets.md`). Checked on **2026-11-15** against
https://core.telegram.org/bots/webapps and the Bot API 10.4 page. Every JSON block
passes `scripts/validate_payload.py`.

Labels: **[API]** Bot API spec; **[Official]** Mini Apps page; **[Heuristic]** this skill's advice.

## Launch points and what comes back

| Launch point | Bot-side setup | Mini App can… | Bot receives |
|---|---|---|---|
| Reply keyboard `KeyboardButton.web_app` | `sendMessage` with the keyboard (private chats only) | `sendData` (string) | `Message.web_app_data` (`data`, `button_text`) |
| Inline button `InlineKeyboardButton.web_app` | inline keyboard (private chats with the bot only; not business or ephemeral messages) | get `query_id`, ask the bot to post on the user's behalf | your backend call → `answerWebAppQuery` |
| Menu button | `setChatMenuButton` with `MenuButtonWebApp`, or @BotFather | same as inline button | same |
| Main Mini App | @BotFather; link `t.me/<bot>?startapp=<param>` | chat-aware (`chat_type`, `chat_instance`) | your backend; `start_param` |
| Direct link | @BotFather app; `t.me/<bot>/<app>?startapp=<param>` | chat-aware; no chat access | your backend |
| Inline mode | `answerInlineQuery.button.web_app` | `switchInlineQuery` back to results | `inline_query` / `chosen_inline_result` |
| Attachment menu | test server for everyone; production for major advertisers | `query_id` → `answerWebAppQuery` | your backend |
| Chat join request (10.1) | `sendChatJoinRequestWebApp` | verify the applicant | your backend → `answerChatJoinRequestQuery` |

All rows **[Official]**/**[API]**; `mode=compact` on links opens half-height. **[Official]**

```json
{"method": "sendMessage", "params": {
  "chat_id": 111111111, "text": "Pick a delivery slot:",
  "reply_markup": {"keyboard": [[{"text": "Choose time", "web_app": {"url": "https://example.com/slots?lang=uk"}}]],
                   "resize_keyboard": true, "one_time_keyboard": true}
}}
```

```json
{"update_id": 900000701, "message": {
  "message_id": 90, "date": 1763192000,
  "chat": {"id": 111111111, "type": "private", "first_name": "Olena"},
  "from": {"id": 111111111, "is_bot": false, "first_name": "Olena"},
  "web_app_data": {"data": "{\"slot\":\"2026-11-16T10:00\"}", "button_text": "Choose time"}
}}
```

```json
{"method": "setChatMenuButton", "params": {"chat_id": 111111111,
  "menu_button": {"type": "web_app", "text": "Open shop", "web_app": {"url": "https://example.com/shop"}}}}
```

```json
{"method": "answerWebAppQuery", "params": {
  "web_app_query_id": "AAHdF6IQAAAAAN0XohDhrOrc",
  "result": {"type": "article", "id": "ord-8812", "title": "Order #8812",
             "input_message_content": {"message_text": "Order #8812 placed: 2× Margherita"}}
}}
```

## Trusting Mini App data

- **[Official]** `web_app_data` via `sendData` arrives through Telegram as a service
  message — it is authentic, but its **content is user-controlled**: parse and validate
  it like any input (size, JSON schema, allowed values).
- **[Official]** Anything the Mini App sends to **your backend** (`initData`) must be
  verified there: `secret_key = HMAC_SHA256(key="WebAppData", msg=bot_token)`;
  `hash == hex(HMAC_SHA256(key=secret_key, msg=data_check_string))`, where
  `data_check_string` is every field except `hash`, sorted by key, `key=value`, joined
  by `\n`. Also check `auth_date` freshness. Never trust `initDataUnsafe`.
- **[Official]** Third parties without the token verify `signature` (Ed25519, base64url)
  over `"<bot_id>:WebAppData\n" + sorted fields except hash and signature`, with
  Telegram's published public key (different keys for production and test).

```python
import hashlib, hmac, time, urllib.parse

def verify_init_data(init_data: str, bot_token: str, max_age: int = 3600) -> dict:
    """Return the parsed initData fields or raise ValueError. Stdlib only."""
    fields = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
    received = fields.pop("hash", "")
    check = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, received):
        raise ValueError("initData signature mismatch")
    if time.time() - int(fields.get("auth_date", "0")) > max_age:
        raise ValueError("initData too old")
    return fields
```

(The page defines the check string as "all received fields", so only `hash` is
removed and `signature`, when present, stays in. **[Official]** wording; verified
here only for self-consistency, not against a real client's `initData`.) Read `bot_token` from the
environment; never send it to the front-end. **[Heuristic]**

## Mini App ↔ bot helpers in the Bot API

- **[API]** `savePreparedInlineMessage` → `PreparedInlineMessage(id, expiration_date)` for
  `WebApp.shareMessage` (8.0; `inline-mode.md#prepared-inline-messages-mini-apps`).
- **[API]** `savePreparedKeyboardButton(user_id, button: KeyboardButton)` →
  `PreparedKeyboardButton(id)` (9.6): lets a Mini App trigger `request_users`,
  `request_chat` or `request_managed_bot`; results come back as `users_shared`,
  `chat_shared` or `managed_bot_created` service messages.
- **[API]** `WriteAccessAllowed` service message (`from_request`, `web_app_name`,
  `from_attachment_menu`): the user allowed the bot to message them from a Mini App
  (`requestWriteAccess`) — only after this may the bot start the conversation.
- **[API]** Payments from a Mini App: create a link with `createInvoiceLink` and open it
  with `WebApp.openInvoice` (`payments-and-stars.md`).
- **[API]** 10.2 hardened Mini Apps: Mini App methods are refused from origins other than
  the Mini App's own domain — don't load the app inside another site's frame.

```json
{"method": "savePreparedKeyboardButton", "params": {
  "user_id": 111111111,
  "button": {"text": "Choose a group", "request_chat": {"request_id": 7, "chat_is_channel": false, "bot_is_member": true}}
}}
```

## What the user sees

- Reply-keyboard Mini Apps close after `sendData`; the user sees a service message
  with the button text. Inline/menu Mini Apps close after `answerWebAppQuery`, and
  the result appears as a message "via @bot" from the user. **[Official]**
- Answer every `web_app_data` with a visible confirmation in the chat; otherwise the
  user thinks the input was lost. **[Heuristic]**

## Common mistakes

| Mistake | Fix |
|---|---|
| Expecting `sendData` from an inline-button Mini App | only reply-keyboard launches can `sendData` |
| Trusting `initDataUnsafe.user.id` on the server | verify `initData` (HMAC) first |
| Comparing hashes with `==` | constant-time `hmac.compare_digest` |
| `web_app` buttons in groups | private chats only |
| Bot messages a user who only opened the app | wait for `write_access_allowed` or a `/start` |
| Re-using an expired prepared message id | create one per share |
