---
summary: "Sending gifts and Premium from Stars, reading owned and unique gifts, gift service messages, stories for business accounts; read when a bot deals with gifts or stories."
verified: "2026-11-15"
bot_api: "10.4"
---

# Gifts and stories

Sending gifts and Telegram Premium paid from the bot's Stars, reading gifts users and
chats own, unique (collectible) gifts, the gift service messages, and posting
stories on behalf of business accounts. Business-account gift management (convert,
upgrade, transfer, the 10.4 delete) is in `business-accounts.md#gifts-and-stars-of-the-business-account`;
the 10.3/10.4 gift deltas also in `specialized-updates.md`. Checked against Bot API
10.4 on **2026-11-15** (https://core.telegram.org/bots/api#sendgift, #gift,
#uniquegift, #poststory). Every JSON block passes `scripts/validate_payload.py`.

Labels: **[API]** spec; **[Heuristic]** this skill's advice.

## Sending gifts

```json
{"method": "getAvailableGifts", "params": {}}
```

```json
{"method": "sendGift", "params": {
  "user_id": 222222222, "gift_id": "5170145012310081615",
  "text": "Дякуємо, що з нами вже рік! 🎉", "pay_for_upgrade": false
}}
```

- **[API]** `getAvailableGifts` → `Gifts` the bot can send now, each with `star_count`,
  optional `upgrade_star_count`, and for limited gifts `total_count` /
  `remaining_count` plus the bot's own `personal_total_count` /
  `personal_remaining_count` (9.3). `is_premium` gifts can be bought only by Premium
  users. Never hard-code gift ids — they rotate; fetch the list. **[Heuristic]**
- **[API]** `sendGift`: `user_id` or `chat_id`, each required when the other is missing (channels by
  `@username`); limited gifts can't go to channels. The Stars come from the **bot's** balance: the
  catalog shows it through `TransactionPartnerUser` (`gift_purchase`), not in `sendGift` itself. The
  receiver **can't convert** a bot-sent gift to Stars. `text` 0-128 chars, entities
  only bold/italic/underline/strikethrough/spoiler/custom_emoji (and `date_time`,
  9.6). `pay_for_upgrade: true` prepays the upgrade for the receiver.
- **[API]** `giftPremiumSubscription(user_id, month_count 3|6|12, star_count
  1000|1500|2500, text?)` — exact pairs only.
- Each gift spends real Stars and is irreversible; confirm amount and receiver
  before calling, and check `getMyStarBalance` first. **[Heuristic]**
- **[API]** The bot's ledger shows these as `TransactionPartnerUser.transaction_type`
  `gift_purchase` / `premium_purchase`, or `TransactionPartnerChat.gift`.

## Reading gifts

- **[API]** `getUserGifts(user_id, …)` (9.3) — gifts owned and hosted by a user;
  `getChatGifts(chat_id, …)` (9.3) — gifts of a chat (saved/unsaved filters are fixed
  unless the bot has `can_post_messages` in the channel). Both: `exclude_*` filters,
  `sort_by_price`, cursor `offset` (string) and `limit` 1-100 → `OwnedGifts`
  (`total_count`, `gifts`, `next_offset`).
- **[API]** `OwnedGift` is `OwnedGiftRegular` (`type: "regular"`) or `OwnedGiftUnique`
  (`type: "unique"`).
- **[API]** `getUniqueGift(name)` (10.4) — a collectible by its unique name → `UniqueGift` (`gift_id`, `base_name`, `name`, `number`,
  `model`, `symbol`, `backdrop`, `colors`, `is_premium`, `is_burned`,
  `is_from_blockchain`, `publisher_chat`…).
- **[API]** `ChatFullInfo.accepted_gift_types` (`AcceptedGiftTypes`: unlimited, limited,
  unique, premium subscription, `gifts_from_channels`) tells you whether a user or
  chat accepts a kind of gift **before** you try to send it.

```json
{"method": "getUniqueGift", "params": {"name": "PlushPepe-1234"}}
```

```json
{"method": "getUserGifts", "params": {"user_id": 222222222, "exclude_unlimited": true, "sort_by_price": true, "limit": 20}}
```

## Gift service messages

| `Message` field | Type | Meaning |
|---|---|---|
| `gift` | `GiftInfo` | a regular gift was sent/received; `owned_gift_id` only for business accounts; `convert_star_count`, `prepaid_upgrade_star_count`, `can_be_upgraded`, `text` + `entities`, `is_private` |
| `unique_gift` | `UniqueGiftInfo` | a unique gift was sent/received/upgraded/transferred/resold; `origin` (`upgrade`, `transfer`, `resale`, `gifted_upgrade`, `offer`), 10.3 `text`, `entities`, `is_private` |
| `gift_upgrade_sent` | `GiftInfo` | an upgrade was paid for a gift sent earlier (9.3) |

All **[API]**. **[API]** `is_private: true` means the sender and text are visible only
to the receiver — never echo them into a group or a public post
(`specialized-updates.md#gift-text-and-privacy`).

## Stories (business accounts, 9.0)

- **[API]** Bots post stories **only on behalf of a managed business account** with the
  `can_manage_stories` right: `postStory`, `editStory`, `deleteStory` (only stories the
  bot posted), `repostStory` (9.3; between two business accounts managed by the same
  bot, source story posted by the bot, right needed on both).
- **[API]** `content` is `InputStoryContentPhoto` (1080×1920, ≤10 MB) or
  `InputStoryContentVideo` (720×1280, streamable H.265 MPEG4 with a key frame every
  second, ≤30 MB); both are **new uploads only**
  (`attach://`), never `file_id`.
- **[API]** `active_period` must be one of 21600, 43200, 86400, 172800 seconds;
  `post_to_chat_page` keeps it on the profile after expiry; caption 0-2048 chars.
- **[API]** `areas`: `StoryArea` = `AreaPosition` (percent-based rectangle; renamed from
  `StoryAreaPosition` in 10.4, same JSON) + `StoryAreaType`: `location`,
  `suggested_reaction`, `link` (≤3 per story), `weather`, `unique_gift`.

```json
{"method": "postStory", "params": {
  "business_connection_id": "BCxyz",
  "content": {"type": "photo", "photo": "attach://story1"},
  "active_period": 86400,
  "caption": "New autumn menu is here 🍂",
  "areas": [{"position": {"x_percentage": 50, "y_percentage": 85, "width_percentage": 60, "height_percentage": 8,
                          "rotation_angle": 0, "corner_radius_percentage": 4},
             "type": {"type": "link", "url": "https://example.com/menu"}}]
}}
```

## What users see

- A gift appears as a service message with the gift sticker and the text; the
  receiver can keep it on their profile. **[Heuristic]** (rendering not verified)
- A story posted via the business account looks like the owner posted it — use the
  owner's voice; never post without the owner's explicit approval of the exact
  media and caption. **[Heuristic]**

## Common mistakes

| Mistake | Fix |
|---|---|
| Hard-coded `gift_id` | fetch `getAvailableGifts` each time |
| Sending a limited gift to a channel | not allowed |
| `giftPremiumSubscription` with 6 months / 1000 Stars | exact pairs: 3/1000, 6/1500, 12/2500 |
| Ignoring `accepted_gift_types` | check before sending; the user may refuse a kind |
| Story photo by `file_id` | stories need a new upload |
| Repeating private gift text publicly | respect `is_private` |
| Using `StoryAreaPosition` in new SDK code | it is `AreaPosition` since 10.4 |
