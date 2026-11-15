# Business accounts (business bots)

A user connects your bot to their Telegram account (Settings → Telegram Business →
Chatbots). The bot then receives that account's private chats and, within the
rights the user granted, replies, reads, deletes, edits the profile, manages gifts,
Stars and stories **on behalf of the account**. Checked against Bot API 10.4 on
**2026-11-15** (https://core.telegram.org/bots/api#businessconnection and the
methods it links). Every JSON block passes `scripts/validate_payload.py`.

Labels: **[API]** spec; **[Official]** Telegram docs/blog; **[Heuristic]** this skill's advice.

## Preconditions and availability

- **[API]** The bot must have Business Mode enabled in @BotFather;
  `getMe` then returns `can_connect_to_business: true`.
- **[API]** Since **10.0** business bots can manage user accounts **without** the user
  having Telegram Premium (earlier: Premium required). Older SDK docs may still say
  "Premium only".
- **[API]** The user chooses which chats the bot manages and which rights it gets; both can
  change at any time and arrive as a new `business_connection` update.

## Updates

| Update field | Payload | When |
|---|---|---|
| `business_connection` | `BusinessConnection` | connected, disconnected (`is_enabled: false`), or rights edited |
| `business_message` | `Message` with `business_connection_id` | new message in a managed private chat (incoming **and** outgoing by the owner) |
| `edited_business_message` | `Message` | a message in a managed chat was edited |
| `deleted_business_messages` | `BusinessMessagesDeleted` (`business_connection_id`, `chat`, `message_ids`) | messages deleted in a managed chat |

All four are in the default update set; list them explicitly if you pass
`allowed_updates` (`updates-and-delivery.md`). **[API]**

```json
{"update_id": 900000301, "business_connection": {
  "id": "BCxyz", "date": 1763190000, "is_enabled": true, "user_chat_id": 444444444,
  "user": {"id": 444444444, "is_bot": false, "first_name": "Dana", "last_name": "Koval"},
  "rights": {"can_reply": true, "can_read_messages": true, "can_delete_sent_messages": true}
}}
```

```json
{"update_id": 900000302, "business_message": {
  "message_id": 5012, "date": 1763190100, "business_connection_id": "BCxyz",
  "chat": {"id": 555555555, "type": "private", "first_name": "Client"},
  "from": {"id": 555555555, "is_bot": false, "first_name": "Client"},
  "text": "Hi! Are you open on Sunday?"
}}
```

## State the server must keep

Per `business_connection_id`: owner `user` id, `user_chat_id` (your private chat with
the owner), `is_enabled`, the latest `rights`, connection `date`. **[Heuristic]**

- **[API]** A `business_message` chat id belongs to the **business account's** chat, which
  is independent from any bot chat that might share the same id. Key conversation
  state by `(business_connection_id, chat.id)`, never by `chat.id` alone.
- Replace `rights` wholesale on every `business_connection` update; when
  `is_enabled` is false, stop sending immediately and keep data only as long as your
  privacy policy says. **[Heuristic]**
- Messages the owner sends from their own apps also arrive as `business_message`
  (`from` = the owner). Don't auto-reply to the owner's own messages. **[Heuristic]**
- **[API]** `Message.sender_business_bot` marks outgoing messages sent by a bot on behalf of
  the account; `is_from_offline` marks away/greeting/scheduled messages.

## Rights (`BusinessBotRights`)

Absent field = right not granted. **[API]**

| Right | Unlocks |
|---|---|
| `can_reply` | send/edit messages in chats with **incoming messages in the last 24 h** |
| `can_read_messages` | `readBusinessMessage` |
| `can_delete_sent_messages` / `can_delete_all_messages` | `deleteBusinessMessages` (own / any) |
| `can_edit_name`, `can_edit_bio`, `can_edit_username`, `can_edit_profile_photo` | `setBusinessAccountName` / `Bio` / `Username`, `set`/`removeBusinessAccountProfilePhoto` |
| `can_change_gift_settings` | `setBusinessAccountGiftSettings` |
| `can_view_gifts_and_stars` | `getBusinessAccountGifts`, `getBusinessAccountStarBalance` |
| `can_convert_gifts_to_stars` | `convertGiftToStars`, `deleteBusinessAccountGift` (10.4) |
| `can_transfer_and_upgrade_gifts` | `upgradeGift`, `transferGift` |
| `can_transfer_stars` | `transferBusinessAccountStars`; paid upgrades/transfers |
| `can_manage_stories` | `postStory`, `editStory`, `deleteStory`, `repostStory` (`gifts-and-stories.md`) |

Doc inconsistency (as of 2026-11-15): the descriptions of `setBusinessAccountName`,
`setBusinessAccountUsername` and `setBusinessAccountBio` say "requires the
`can_change_name` / `can_change_username` / `can_change_bio` right", while
`BusinessBotRights` defines `can_edit_name`, `can_edit_username`, `can_edit_bio`.
Check the `can_edit_*` fields — they are the ones the connection actually carries.

## Sending and reading on behalf of the account

- **[API]** Pass `business_connection_id` to a send method (52 methods accept it —
  `py -3 scripts/tg_api_lookup.py accepts business_connection_id`). The message is
  sent **as the business account**, in that account's chat.
- **[API]** `can_reply` covers only chats with an incoming message in the last 24 hours;
  `readBusinessMessage` also requires the chat to be active in the last 24 hours.
- **[API]** Editing: business messages **not sent by the bot** and without an inline
  keyboard can only be edited within **48 hours** of sending.
- **[API]** Inline switch buttons (`switch_inline_query*`) are not supported in messages
  sent on behalf of a business account.

```json
{"method": "sendMessage", "params": {
  "business_connection_id": "BCxyz", "chat_id": 555555555,
  "text": "Hi! Yes, on Sunday we are open 10:00–16:00.",
  "reply_parameters": {"message_id": 5012}
}}
```

```json
{"method": "readBusinessMessage", "params": {"business_connection_id": "BCxyz", "chat_id": 555555555, "message_id": 5012}}
```

```json
{"method": "deleteBusinessMessages", "params": {"business_connection_id": "BCxyz", "message_ids": [5013, 5014]}}
```

**[API]** `deleteBusinessMessages`: 1-100 ids, all from the same chat.

## Managing the account profile

```json
{"method": "setBusinessAccountBio", "params": {"business_connection_id": "BCxyz", "bio": "Кав'ярня на Подолі · щодня 8:00–20:00"}}
```

```json
{"method": "setBusinessAccountProfilePhoto", "params": {
  "business_connection_id": "BCxyz",
  "photo": {"type": "static", "photo": "attach://avatar"}
}}
```

- **[API]** Limits: first name 1-64, last name 0-64, username 0-32, bio 0-140 characters.
  `InputProfilePhoto` is `static` (`InputProfilePhotoStatic`) or `animated`
  (`InputProfilePhotoAnimated`, with `main_frame_timestamp`); `is_public` targets the
  public photo shown when the main one is hidden.
- **[Heuristic]** These are **visible to all of the owner's contacts**. Treat every
  profile change as destructive: show the owner the exact new value and require a
  confirmation in your private chat (`user_chat_id`) before calling. Default to
  dry-run in tooling.

## Gifts and Stars of the business account

- `getBusinessAccountGifts` (filters `exclude_*`, `sort_by_price`, cursor
  `offset`/`limit` 1-100) → `OwnedGifts` with `OwnedGiftRegular` / `OwnedGiftUnique`
  entries; each has `owned_gift_id`. **[API]**
- `convertGiftToStars(owned_gift_id)` sells a regular gift for Stars;
  `deleteBusinessAccountGift(owned_gift_id)` (**10.4**) deletes a regular gift **without**
  Stars — only if it isn't limited (`Gift.total_count` omitted) and wasn't refunded.
  Both need `can_convert_gifts_to_stars`. **[API]**
- `upgradeGift(owned_gift_id, keep_original_details, star_count)`: pass `star_count: 0`
  when `prepaid_upgrade_star_count > 0`, otherwise pass `upgrade_star_count` and hold
  `can_transfer_stars`. `transferGift(owned_gift_id, new_owner_chat_id, star_count)`:
  the receiving chat must be active in the last 24 hours. **[API]**
- `getBusinessAccountStarBalance` → `StarAmount`; `transferBusinessAccountStars`
  (1-10000) moves Stars to the **bot's** balance (appears in the bot's ledger as
  `TransactionPartnerUser.transaction_type = "business_account_transfer"`). **[API]**
- `setBusinessAccountGiftSettings(show_gift_button, accepted_gift_types)`. **[API]**

```json
{"method": "getBusinessAccountGifts", "params": {"business_connection_id": "BCxyz", "exclude_unique": true, "limit": 50}}
```

```json
{"method": "deleteBusinessAccountGift", "params": {"business_connection_id": "BCxyz", "owned_gift_id": "og_1182"}}
```

Gift deletion, conversion, upgrade and transfer are **irreversible** and spend or
forgo the owner's Stars. Plan first, show the list, execute only on an explicit
confirmation; the repo's mini-recipe for `deleteBusinessAccountGift` is dry-run by
default (`specialized-updates.md#deletebusinessaccountgift`). **[Heuristic]**

## What the user (and the owner) see

- Customers talk to the business account; messages the bot sends with
  `business_connection_id` are sent **on behalf of** that account. **[API]** Exact
  client rendering of bot-sent business messages is not verified offline.
- So write in the owner's voice and tone, not as "the bot"; no bot-style menus to
  customers unless the owner asked for them. Report actions to the owner in your
  private chat (`user_chat_id`). **[Heuristic]**

## Common mistakes

| Mistake | Fix |
|---|---|
| Replying with `chat_id` but no `business_connection_id` | the message goes to the bot's own chat (or fails) |
| One state table keyed by `chat.id` | key by `(business_connection_id, chat.id)` |
| Auto-replying to the owner's own outgoing messages | skip when `from.id == connection.user.id` |
| Caching rights forever | replace on each `business_connection` update |
| Replying after 24 h of customer silence | `can_reply` won't cover it; ask the owner |
| Still requiring Premium | not since 10.0 |

## Error handling

- Missing right / disabled connection / chat inactive for 24 h → 400 errors; on any
  such error re-fetch `getBusinessConnection` and update your stored rights before
  retrying. **[Heuristic]**
- Never retry destructive calls (`delete*`, `transfer*`, `convert*`) automatically after
  a timeout — the outcome is unknown; reconcile with `getBusinessAccountGifts` /
  `getBusinessAccountStarBalance` first (`errors-and-fallbacks.md#unknown-outcome-after-timeout`).
  **[Heuristic]**
