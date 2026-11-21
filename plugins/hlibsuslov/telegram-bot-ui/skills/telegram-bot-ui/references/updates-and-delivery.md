# Update intake and delivery

How updates reach the bot (`getUpdates` vs webhook), what `allowed_updates` really
does, offsets, the secret token, ordering and duplicates, and **every update type**
with when it arrives and what it needs. Checked against Bot API 10.4 on
**2026-11-15**: https://core.telegram.org/bots/api#getting-updates and
https://core.telegram.org/bots/api#update. Every JSON block passes
`scripts/validate_payload.py`; `tests/test_api_catalog_docs.py` fails if a new
`Update` field appears in the snapshot and is missing from the table below.

Labels: **[API]** spec; **[Official]** Telegram docs/FAQ; **[Heuristic]** this skill's advice.

## Two mutually exclusive intake modes

| | `getUpdates` (long polling) | Webhook (`setWebhook`) |
|---|---|---|
| Who connects | your process → Telegram | Telegram → your HTTPS URL |
| Confirmation | next call with `offset = last update_id + 1` | any 2XX response |
| Retries | you re-read unconfirmed updates | Telegram re-sends on non-2XX, gives up "after a reasonable amount of attempts" |
| Parallelism | one poller | up to `max_connections` (1-100, default 40) concurrent requests |
| Good for | development, single process, no public URL | production, horizontal scaling |

- **[API]** The two are mutually exclusive: `getUpdates` does not work while a webhook is
  set. Switch with `deleteWebhook` (optionally `drop_pending_updates: true`).
- **[API]** Undelivered updates are kept on Telegram's side **at most 24 hours**.
- **[API]** `getWebhookInfo` shows `url`, `pending_update_count`, `last_error_date`,
  `last_error_message`, `last_synchronization_error_date`, `max_connections`,
  `allowed_updates`, `ip_address`. Check it first when "the bot receives nothing".
- **[Heuristic]** Two pollers with the same token (a forgotten dev instance) steal each
  other's updates and get 409 Conflict; one token = one consumer.

### Long polling

```json
{"method": "getUpdates", "params": {"offset": 900000401, "limit": 100, "timeout": 50,
  "allowed_updates": ["message", "callback_query", "pre_checkout_query", "my_chat_member"]}}
```

- **[API]** `offset` must be one greater than the highest `update_id` already received; an
  update is confirmed as soon as `getUpdates` is called with a higher offset. A
  negative offset reads `-offset` updates from the end of the queue and forgets all
  earlier ones. Recalculate the offset after each response.
- **[API]** `limit` 1-100 (default 100); `timeout` is the long-poll time in seconds
  (default 0 = short polling, for tests only). Set your HTTP client timeout above it.
- **[Heuristic]** Persist the offset *after* the batch is processed (or after it is
  durably queued). Crashing between "process" and "persist" redelivers — handlers must
  be idempotent.

### Webhook

```json
{"method": "setWebhook", "params": {
  "url": "https://bot.example.com/tg/webhook",
  "secret_token": "h4rd-to-guess_value-from-env",
  "max_connections": 40,
  "allowed_updates": ["message", "edited_message", "callback_query", "inline_query", "chosen_inline_result",
                      "pre_checkout_query", "subscription", "my_chat_member", "chat_member"],
  "drop_pending_updates": false
}}
```

- **[API]** HTTPS only; ports **443, 80, 88, 8443**. A self-signed certificate must be
  uploaded as `certificate` (InputFile, multipart) — a string does not work.
  `ip_address` pins the IP instead of DNS.
- **[API]** `secret_token` (1-256 chars, `A-Za-z0-9_-`) is sent in every request as the
  header `X-Telegram-Bot-Api-Secret-Token`. **Reject requests where it doesn't match**
  (constant-time compare) — the URL alone is not a secret. Load the value from an
  environment variable, never commit it. **[Heuristic]** for the handling.
- **[API]** You may answer the webhook request itself with a method call
  (`{"method": "sendMessage", ...}` as the response body); you cannot learn whether it
  succeeded. Use it only for fire-and-forget replies.
- **[Heuristic]** Return 200 fast and process asynchronously (queue). A slow handler
  causes retries and duplicate deliveries; a handler that returns 500 on a poison
  update gets the same update retried — log it and return 200.
- **[API]** Local Bot API server: HTTP webhook URLs, any local IP, any port,
  `max_connections` up to 100000 (`media-and-files.md#local-bot-api-server`).

## `allowed_updates` is sticky

- **[API]** "If not specified, the previous setting will be used." The list you pass to
  `setWebhook` or `getUpdates` **persists** until you pass another one. Omitting it does
  not reset to "all".
- **[API]** An **empty list** = all update types **except** `chat_member`,
  `message_reaction`, `message_reaction_count` (the default). Those three must be
  requested explicitly.
- **[API]** A change does not affect updates created before the call — unwanted types can
  still arrive briefly.
- **[Heuristic]** Derive the list from the handlers you register (a single source of
  truth) and send it on every start. When you add a handler for a new type
  (`widget_query`, `stopped_message_generation`, `subscription`, …) without updating
  the list, it silently never fires. SDK defaults differ; see `sdk-compatibility.md`.

## Ordering, duplicates, gaps

- **[API]** `update_id`s increase sequentially, which lets you ignore repeats and restore
  order. After a week without updates the next id is chosen randomly — don't assume
  continuity across long idle periods.
- **[API]** At most one optional field is present in an `Update`.
- **[Heuristic]** Dedupe on `update_id` (and on business keys such as
  `telegram_payment_charge_id`, `callback_query.id`). With a webhook and
  `max_connections > 1`, updates from one chat can be processed concurrently and out of
  order: serialize per chat (a per-`chat.id` queue or lock) when order matters
  (forms, edits of the same message).
- **[API]** `message_reaction_count` updates are grouped and can be delayed by up to a
  few minutes; `edited_message` may fire for field changes you don't use.

## Every update type

| `Update` field | Type | Arrives when / conditions |
|---|---|---|
| `message` | `Message` | any new message (private, group, supergroup); in groups subject to privacy mode |
| `edited_message` | `Message` | a known message was edited; may fire for fields you don't use |
| `channel_post` | `Message` | new channel post (bot is a channel admin) |
| `edited_channel_post` | `Message` | channel post edited |
| `business_connection` | `BusinessConnection` | connected / disconnected / rights changed (`business-accounts.md`) |
| `business_message` | `Message` | message in a managed business chat |
| `edited_business_message` | `Message` | edited business message |
| `deleted_business_messages` | `BusinessMessagesDeleted` | business messages deleted |
| `guest_message` | `Message` | guest-mode message in a chat the bot isn't a member of (10.0); answer with `answerGuestQuery` using `Message.guest_query_id` |
| `message_reaction` | `MessageReactionUpdated` | a user changed a reaction; bot must be admin **and request it explicitly**; not sent for reactions by bots |
| `message_reaction_count` | `MessageReactionCountUpdated` | anonymous reaction counts changed; admin + explicit; grouped, delayed |
| `inline_query` | `InlineQuery` | user typed `@bot …` (`/setinline`; `inline-mode.md`) |
| `chosen_inline_result` | `ChosenInlineResult` | user picked a result (`/setinlinefeedback`) |
| `callback_query` | `CallbackQuery` | callback button tapped; always answer with `answerCallbackQuery` |
| `widget_query` | `WidgetQuery` | a widget asked the bot (10.4; `widgets.md`) |
| `shared_widget_query` | `SharedWidgetQuery` | a forwarded shared widget asked the bot (10.4, test server) |
| `shipping_query` | `ShippingQuery` | flexible-price invoice needs shipping options (`payments-and-stars.md`) |
| `pre_checkout_query` | `PreCheckoutQuery` | user confirmed payment; answer within 10 s |
| `purchased_paid_media` | `PaidMediaPurchased` | paid media with a non-empty payload bought in a non-channel chat |
| `poll` | `Poll` | state of a poll the bot sent, or of a manually stopped poll |
| `poll_answer` | `PollAnswer` | vote changed in a non-anonymous poll the bot sent (`polls-checklists-and-reactions.md`) |
| `my_chat_member` | `ChatMemberUpdated` | the bot's own status changed; in private chats only block/unblock |
| `chat_member` | `ChatMemberUpdated` | someone's status changed; admin **and request it explicitly** (`chat-administration.md`) |
| `chat_join_request` | `ChatJoinRequest` | join request; needs `can_invite_users` |
| `chat_boost` | `ChatBoostUpdated` | boost added/changed; bot must be admin |
| `removed_chat_boost` | `ChatBoostRemoved` | boost removed; bot must be admin |
| `managed_bot` | `ManagedBotUpdated` | a managed bot was created, or its token/owner changed (9.6) |
| `subscription` | `BotSubscriptionUpdated` | a user's Stars subscription to the bot was canceled / re-enabled / failed (10.2) |
| `stopped_message_generation` | `MessageGenerationStopped` | user pressed Stop on a draft (10.3; `streaming-and-editing.md`) |

All **[API]** (field descriptions of `Update`), cross-references are this skill's.

### Example: the bot was blocked

```json
{"update_id": 900000402, "my_chat_member": {
  "chat": {"id": 111111111, "type": "private", "first_name": "Olena"},
  "from": {"id": 111111111, "is_bot": false, "first_name": "Olena"},
  "date": 1763190500,
  "old_chat_member": {"status": "member", "user": {"id": 999999999, "is_bot": true, "first_name": "Shop"}},
  "new_chat_member": {"status": "kicked", "user": {"id": 999999999, "is_bot": true, "first_name": "Shop"}, "until_date": 0}
}}
```

Mark the user unreachable and stop scheduled sends; resume on the next
`my_chat_member` with `member`. **[Heuristic]**

## Requests and responses

- **[API]** `https://api.telegram.org/bot<token>/METHOD`, GET or POST; parameters as query
  string, `application/x-www-form-urlencoded`, `application/json` (no uploads) or
  `multipart/form-data` (uploads). Method names are case-insensitive; UTF-8 only.
- **[API]** Response: `{"ok": true, "result": ...}` or `{"ok": false, "error_code",
  "description", "parameters"?}`. `error_code` contents "are subject to change";
  `ResponseParameters` has `retry_after` (flood control) and `migrate_to_chat_id`
  (group became a supergroup — store the new id and retry).
- **[Heuristic]** Never log the request URL (it contains the token).

```json
{"_type": "ResponseParameters", "retry_after": 17}
```

## Common mistakes

| Mistake | Fix |
|---|---|
| New handler never fires | add its type to `allowed_updates` and re-send the list |
| Expecting `chat_member` / reactions by default | request them explicitly; the bot must be admin |
| Webhook without `secret_token` check | verify the header on every request |
| Slow webhook handler | 200 immediately, process from a queue |
| Offset saved before processing | save after; make handlers idempotent |
| Dev poller + prod webhook on one token | one consumer per token; separate test bot |
| Integer overflow on chat ids | ids can exceed 32 bits (≤52 significant bits): use 64-bit ints |

Related: `errors-and-fallbacks.md` (retries, unknown outcomes),
`sdk-compatibility.md#update-delivery-and-new-update-types` (SDK defaults),
`testing-playbook.md` (fixtures).
