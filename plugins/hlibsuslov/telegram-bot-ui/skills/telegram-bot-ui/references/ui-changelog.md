# UI-relevant Bot API history and version gates

Only the entries that change what a bot's **interface** can do. Every line below
was read from the official changelog
(https://core.telegram.org/bots/api-changelog) and the object pages on
2026-08-05 (≤ 10.2), 2026-11-12 (10.3, 10.4) and 2026-11-22 (10.5). Verification dates and quotes: `official-sources.md`.

Re-checked 2026-11-22: 10.5 is the newest release. The non-UI history of
every release from 9.0 (business accounts, payments, polls, gifts, chat management)
is in `api-catalog.md#what-each-release-added-90--105`; any symbol's history:
`py -3 scripts/tg_api_lookup.py since <name>`.

**Before using anything here, confirm two things:** (1) Telegram hasn't shipped a
newer version — re-read the changelog; (2) the project's SDK actually exposes
the field (`sdk-compatibility.md`). A feature existing in the Bot API is not the
same as a feature you can call.

## The current UI toolbox by version

| Version | Date | UI-relevant additions |
|---|---|---|
| **10.5** | 2026-11-22 | **Bot settings from code**: `setMySettings` (inline mode + `inline_query_placeholder`, location, feedback share, groups, privacy, topics in private chats + **`has_topic_sidebar`**, `callback_query_mode`, …); `getMe` → `BotFullInfo` (`active_usernames`, `inline_query_placeholder`, `needs_inline_query_location`, `has_topic_sidebar`; getMe-only flags removed from `User`). Callbacks from the bot's own messages may carry `inline_message_id` instead of `message`. **Expandable quotes in Rich Messages hold `blocks`** (lists, tables, code) instead of `text` — breaking for 10.3/10.4 payloads. Owner invites `t.me/botinvite/<bot>` (up to 10 users) and `WriteAccessAllowed.inviter`. Details: `bot-settings.md`. |
| **10.4** | 2026-11-09 | **HTML widgets** (`sendWidget`, `sendSharedWidget`, `widget_query`, `shared_widget_query`, `answerWidgetQuery`, `editMessageWidgetData`, `editSharedWidgetData`; production: private chats only) with TON wallet requests. Ephemeral callback replies without `receiver_user_id` in any chat except channel DMs; `chat_id` optional. Quotes from rich messages (`TextQuote.rich_texts`, `ReplyParameters.quote_rich_texts`). TON wallet cards/transfers, `ton_address` / `bank_card_number` entities, `RichTextTonAddress`. Chat share themes. Private-chat topic links `t.me/<bot>/<thread>`. `AreaPosition` rename. Full list: `bot-api-coverage.md`. |
| **10.3** | 2026-08-24 | **Disabled inline buttons** (`disabled: {}`), **`force_reply` on inline and reply keyboards**, **Stop for drafts** (`can_stop`, `keep_on_stop`, `stopped_message_generation`). Rich buttons (`RichMessageButton`, `RichTextButton`, `<tg-button-row>`), compact tables, expandable quotations, document blocks, `tg://document`. `EphemeralMessageParameters` (replaces 10.2 top-level params), `replace_callback_query_message`, ephemeral media upload / rich edit, `can_send_welcome_messages`. Community join and gift-text service fields. |
| **10.2** | 2026-07-14 | **Ephemeral messages** (group messages visible only to one user + the bot): `sendMessage`/media `receiver_user_id` & `callback_query_id`, `editEphemeralMessageText/Media/Caption/ReplyMarkup`, `deleteEphemeralMessage`, `ReplyParameters.ephemeral_message_id`, `BotCommand.is_ephemeral`, `Message.receiver_user`. **Rich message input blocks** (`InputRichBlock*`, incl. `InputRichBlockTable`), `InputRichMessage.blocks`, `InputRichMessageMedia`, `InputMediaVoiceNote`. Communities. |
| **10.1** | 2026-06-11 | **Rich Messages**: `sendRichMessage`, `sendRichMessageDraft`, `InputRichMessage`, `RichBlock*`/`RichText*`, `editMessageText` `rich_message`, `InputRichMessageContent` usable as inline-result content. Join-request queries (`answerChatJoinRequestQuery`, `sendChatJoinRequestWebApp`). Poll media links. |
| **10.0** | 2026-05-08 | Guest mode (`answerGuestQuery`, `Update.guest_message`). Reaction management (`deleteMessageReaction`, `deleteAllMessageReactions`, `can_react_to_messages`). Poll media (`sendPoll` `media`, option media), live photos. |
| **9.6** | 2026-04-03 | `PreparedKeyboardButton` + `savePreparedKeyboardButton` (Mini App can trigger `request_users` / `request_chat` / `request_managed_bot`), `KeyboardButton.request_managed_bot`, `WebApp.requestChat`. Poll UX: multi-answer quizzes, `shuffle_options`, `allows_revoting`, `allow_adding_options`, `hide_results_until_closes`, poll `description`. |
| **9.5** | 2026-03-01 | **`date_time` `MessageEntity`** (client-side localized dates/times), `sendMessageDraft` opened to all bots, member tags, `BottomButton.iconCustomEmojiId` (Mini App side). |
| **9.4** | **2026-02-09** | **`style` on `KeyboardButton` and `InlineKeyboardButton`** (colored buttons). **`icon_custom_emoji_id` on both button classes.** **Custom emoji allowed in messages sent directly by the bot to private/group/supergroup chats when the bot owner has Telegram Premium.** Topics in private chats (`createForumTopic`, `User.allows_users_to_create_topics`). `setMyProfilePhoto` / `removeMyProfilePhoto`. |
| **9.3** | 2025-12-31 | `sendMessageDraft` (streamed partial messages), topics in private chats (`message_thread_id` in private chats, `User.has_topics_enabled` — `BotFullInfo` since 10.5). |
| **6.2** | 2022-08-12 | Custom emoji foundation: `MessageEntity` type `custom_emoji`, `MessageEntity.custom_emoji_id`, `getCustomEmojiStickers`, `Sticker.type` + `Sticker.custom_emoji_id`. |

Older, still-load-bearing UI primitives (unchanged): `InlineKeyboardMarkup`,
`ReplyKeyboardMarkup`, `ForceReply`, `ReplyKeyboardRemove`, `setMyCommands` with
scopes and `language_code`, `setChatMenuButton`, `answerCallbackQuery`,
`editMessageReplyMarkup`, `CopyTextButton`, `web_app` buttons, deep links.

## What 9.4 actually changed for UI work

Two presentation-only fields on **both** button classes:

```json
{
  "text": "Finish the test",
  "icon_custom_emoji_id": "5368324170671202286",
  "style": "success",
  "callback_data": "finish_test"
}
```

- `style` — *"Must be one of 'danger' (red), 'success' (green) or 'primary'
  (blue). If omitted, then an app-specific style is used."* No other values,
  no custom colors. Semantics: `buttons-and-styles.md`.
- `icon_custom_emoji_id` — the custom emoji shown **before** the button text.
  Eligibility (Fragment usernames / owner Premium) and how to obtain a real ID:
  `custom-emoji.md`.
- Neither field counts toward the "exactly one action field" rule — the Bot API
  wording explicitly excludes `text`, `icon_custom_emoji_id`, and `style`.
- The third 9.4 UI change is easy to miss: **custom emoji in message text** are
  no longer Fragment-only — an owner's Premium subscription unlocks them for
  messages the bot sends directly to private/group/supergroup chats.

## What the 9.3 → 10.2 run changed for AI-bot interfaces

The single biggest shift after colored buttons is that **waiting became a
first-class UI surface**:

- `sendMessageDraft` (9.3, all bots since 9.5) — a ~30-second animated preview
  of a message being generated; same `draft_id` animates, empty `text` shows a
  native *"Thinking…"* placeholder, and the result must still be persisted with
  `sendMessage`. Private chats only.
- `sendRichMessageDraft` (10.1) — the same idea for structured answers, plus
  `RichBlockThinking` / `InputRichBlockThinking` (`<tg-thinking>`), which is
  **only** valid inside a rich draft. The docs recommend the
  `https://t.me/addemoji/AIActions` custom emoji set for it.
- `editMessageText` + `editMessageReplyMarkup` remain the fallback for staged
  progress and are the only option in groups.
- `date_time` entities (9.5) let deadlines and ETAs render in the reader's own
  locale instead of a server-formatted string.
- Ephemeral messages (10.2) make per-user progress inside a group possible
  without spamming the chat.

Design rules for all of it: `dynamic-feedback-and-streaming.md`.

## Version gates to check before designing

| You want to use | Minimum Bot API | Also verify |
|---|---|---|
| Colored buttons (`style`) | 9.4 | SDK exposes the field; client behaviour when unknown |
| Custom emoji on buttons | 9.4 | Eligibility route; ID obtained, not invented |
| Custom emoji in text via owner Premium | 9.4 | Owner's Premium is current; chat type is private/group/supergroup |
| Custom emoji in text via Fragment usernames | 6.2 | Fragment purchase exists |
| Localized dates in text (`date_time`) | 9.5 | MarkdownV2/entities path (HTML cannot express it) |
| Streaming a reply before it's final | 9.3 (all bots 9.5) | Private chats only; final `sendMessage` still required |
| Streaming a *structured* reply / `<tg-thinking>` | 10.1 | Thinking block is draft-only; final send must stay rich |
| Per-user menus inside a group (ephemeral) | 10.2 | Edit delivery is not guaranteed |
| Tables / headings / collapsible blocks in the body | 10.1 (+10.2 blocks) | `tables.md`, `telegram-capabilities.md` |
| Mini App triggering a `request_*` button | 9.6 | Private-chat-only constraints |
| Disabled button / keyboard + reply field | 10.3 | `disabled` is the only action; inline `force_reply` immutable on edit |
| Stop button on a streamed answer | 10.3 | subscribe to `stopped_message_generation`; SDK routes it |
| Ephemeral reply without receiver / chat_id | 10.4 | not in channel DM chats; `answerCallbackQuery` still required |
| Widget in a message | 10.4 | production: private chats only; SDK must deliver `widget_query` |

## Keeping this file honest

When Telegram ships a new version: read the changelog, add a row here **only**
for entries that change the interface, update `official-sources.md` with the new
verification date, and leave the historical rows intact — projects on older SDKs
still need them.
