---
summary: "The offline Bot API catalog in data/bot-api/ and its three stdlib tools: lookup, payload validation, refresh; read to check a method or type, validate a request or sync a new release."
verified: "2026-11-22"
bot_api: "10.5"
---

# Bot API catalog: offline lookup, payload checks, refresh

## Contents

- [The data](#the-data)
- [Look something up — `scripts/tg_api_lookup.py`](#look-something-up--scriptstg_api_lookuppy)
- [Check a request — `scripts/validate_payload.py`](#check-a-request--scriptsvalidate_payloadpy)
- [The same tools over MCP — `scripts/bot_ui_mcp.py`](#the-same-tools-over-mcp--scriptsbot_ui_mcppy)
- [Refresh when Telegram ships a release — `scripts/sync_bot_api.py`](#refresh-when-telegram-ships-a-release--scriptssync_bot_apipy)
- [Map: API area → reference](#map-api-area--reference)
- [What each release added (9.0 → 10.5)](#what-each-release-added-90--105)

The whole Bot API (every method and type, with fields, required flags, return
types and union members) is committed as JSON in `data/bot-api/`, together with the
full changelog. Three stdlib tools work on it offline. Snapshot: **Bot API 10.5
(released 2026-11-22), fetched 2026-11-22** — 194 methods, 426 types, 29 unions,
82 changelog releases. No version newer than 10.5 existed on 2026-11-22
(checked https://core.telegram.org/bots/api-changelog).

## The data

| File | Content |
|---|---|
| `data/bot-api/catalog.json` | `meta` (version, release date, fetch date, page hashes, counts) + `methods` + `types`. Each parameter/field: `name`, `type` (as printed), `types` (parsed alternatives with array depth), `required`, `description` (official text), `const` for union discriminators, `conditional` when the text says "required if/unless". Methods: `returns` (extracted from prose — a hint), `section`, `url` (anchor) |
| `data/bot-api/changelog.json` | every release: `version`, `date`, `url`, `groups` of items, each item with the `symbols` it links to |
| `data/bot-api/diff.json` | what the last sync changed: added / removed methods and types, per-symbol added/removed/modified fields (type, required, description) |
| `data/bot-api/agent-notes/<domain>.json` | curated agent notes (not generated): purpose, when to use and not, pitfalls with a source label, related symbols, rights, chat types, `since`, reference sections, a checked example. Shape and rules: `scripts/api_notes.py`; a sync sets `"review": true` on notes whose symbol changed |
| `data/bot-api/coverage-floor.json` | which methods, types and WebApp members are not yet explained, shown or carded (maintainers' check, not for answers) |

Descriptions are Telegram's own text; treat `returns` as a convenience and the
description as authoritative.

## Look something up — `scripts/tg_api_lookup.py`

```bash
py -3 scripts/tg_api_lookup.py card sendRichMessage       # agent card (<= 1.5 KB): note + example
py -3 scripts/tg_api_lookup.py show sendPaidMedia          # full card: params, types, returns, URL
py -3 scripts/tg_api_lookup.py search refund                # names, fields and descriptions
py -3 scripts/tg_api_lookup.py accepts reply_markup         # every method taking a parameter
py -3 scripts/tg_api_lookup.py accepts InputMedia           # ...or a type, incl. union members
py -3 scripts/tg_api_lookup.py used-by LabeledPrice         # methods AND types referencing a type
py -3 scripts/tg_api_lookup.py skeleton sendInvoice         # minimal request with required fields
py -3 scripts/tg_api_lookup.py version 10.4                 # what a release changed
py -3 scripts/tg_api_lookup.py since allowed_updates        # changelog history of a symbol or field
py -3 scripts/tg_api_lookup.py versions | diff | meta
```

`card` is the short answer at the moment of a call: purpose, required and conditional
parameters, when to use it and when not, pitfalls labelled API / Official / Observed /
Heuristic / Unverified / Third-party, related symbols, rights, chat types, the reference
section and a checked example. A symbol without a note gets a catalog-only card that says so;
then read `show`. A card marked REVIEW was written before the catalog entry last changed:
the catalog wins.

`--json` on any command gives machine-readable output. Typical questions:
"does `sendMediaGroup` take `reply_markup`?" (`show`), "which methods accept
`business_connection_id` / `message_thread_id` / `rich_message`?" (`accepts`), "when
did `correct_option_ids` replace `correct_option_id`?" (`since`).

## Check a request — `scripts/validate_payload.py`

```bash
py -3 scripts/validate_payload.py examples/payloads/r07-wallet.json      # {"steps": [...]} files
py -3 scripts/validate_payload.py --method sendMessage params.json       # bare params
py -3 scripts/validate_payload.py --type Update examples/fixtures/widget_query_ship.json
```

Checks unknown methods/fields, missing required fields, basic types (Integer,
Float, String, Boolean, `True`, arrays, "X or Y"), nested objects, `null`, and
unions: the discriminator (`type` / `source` / `status`) must select one member and
the object must fit it (`InlineQueryResult` cached vs URL variants share `type` and
are resolved structurally). `{"ok": true, "result": …}` envelopes are unwrapped with
`--type`; keys starting with `_` are treated as annotations.

**It is mostly a structural check**: no general length/byte limits, no prose-only
rules ("required unless …" is printed as a note), no rights, chat types,
production-vs-test availability. A few rules Telegram states in prose are checked,
read from the catalog text itself so a refresh updates them: `setMessageReaction`
(only the `ReactionTypeEmoji` list, one reaction from a bot, no paid reactions) and
`setMyCommands` (name pattern, lengths, at most 100, unique, two-letter language). Run the specialised validators for their areas:
`scripts/validate_keyboard.py` (buttons), `scripts/validate_rich.py` (rich
messages), `scripts/validate_widget.py` (widgets) — the tool prints which apply.

## The same tools over MCP — `scripts/bot_ui_mcp.py`

`py -3 scripts/tgui.py mcp` (or the script itself) is a stdio MCP server, standard library
only: `claude mcp add --transport stdio telegram-bot-ui -- py -3 <skill>/scripts/bot_ui_mcp.py`
(Codex: an `[mcp_servers.telegram-bot-ui]` entry with the same command). Tools:
`telegram_api_lookup` (with "did you mean" for a near miss, never an invented name, and the
agent card when there is a note),
`telegram_api_search`, `webapp_lookup`, `validate_request` (catalog + keyboard rules +
Rich HTML buttons), `check_rich_html`, `knowledge_search` (which reference sections to read),
`map_validate`, `map_render`, `map_simulate` (read-only: they never roll back a pending write),
`map_snapshot` (a single-file Studio page to screenshot; it refuses to replace a file unless
`overwrite: true`), `commands_audit`, `commands_plan`, and three that use the network:
`emoji_library_search`, `emoji_pick_family` (slot coverage, then the brief's tags) and
`emoji_rank_by_tags` (packs by style, colour, mood, topic, bot category, or a style `profile`
whose accent is compared with pack colours; `library_file` reads the offline export instead;
only search words, tag values and pack names are sent; `BOT_UI_EMOJI_RESOLVER=off` turns them
off). Both pick tools return each pack's description and a one-line `why`; every library
answer is checked against the vendored contract (`references/emoji-packs.md`). Arguments are
checked against each tool's input schema.
Nothing sends to Telegram, no tool reads a token. Tested in `tests/test_bot_ui_mcp.py`.

## Refresh when Telegram ships a release — `scripts/sync_bot_api.py`

```bash
py -3 scripts/sync_bot_api.py --check     # fetch, print the diff, write nothing
py -3 scripts/sync_bot_api.py             # fetch, write catalog/changelog/diff
py -3 scripts/tg_api_lookup.py diff       # read what changed
py -3 scripts/tg_api_lookup.py version <new>
```

- One GET per page (`/bots/api`, `/bots/api-changelog`), generic user agent, no
  loops; `robots.txt` on core.telegram.org returned 404 (no restrictions) on
  2026-11-15. Run it per release, not on a schedule.
- **Layout guard**: if the page no longer parses (table headers changed, too few
  methods/types, anchor symbols missing, no version header, >10% symbols lost), it
  exits **2** and writes nothing. Fix the parser (tests in
  `tests/test_api_catalog.py` use the saved excerpts in `tests/fixtures/api/`), then
  re-run. `--api-html` / `--changelog-html` parse saved pages offline.
- After a sync: update `references/official-sources.md`, `references/ui-changelog.md`,
  `recipes/registry.json` for the new rows, and the reference that owns each changed
  area (map below). Run `py -3 scripts/run_checks.py` from the repository root.

## Map: API area → reference

| Area (official section) | Main symbols | Reference |
|---|---|---|
| Getting updates | `getUpdates`, `setWebhook`, `Update`, `WebhookInfo` | `updates-and-delivery.md` |
| Messages, formatting, entities | `sendMessage`, `MessageEntity`, parse modes | `regular-formatting.md`, `format-selection.md`, `security-and-escaping.md` |
| Keyboards and buttons | `InlineKeyboardMarkup`, `ReplyKeyboardMarkup`, `ForceReply` | `inline-keyboards.md`, `reply-keyboards.md`, `buttons-and-styles.md` |
| Callbacks, commands, menu button | `answerCallbackQuery`, `setMyCommands`, `setChatMenuButton` | `navigation-and-flows.md`, `personalization-and-links.md` |
| Editing, streaming, drafts | `editMessage*`, `sendMessageDraft`, `sendRichMessageDraft` | `streaming-and-editing.md`, `dynamic-feedback-and-streaming.md` |
| Rich messages | `sendRichMessage`, `RichBlock*`, `InputRichBlock*` | `telegram-capabilities.md`, `tables.md`, `rich-media.md` |
| Ephemeral messages | `EphemeralMessageParameters`, `editEphemeral*` | `ephemeral-and-personal.md` |
| Widgets, TON wallet | `sendWidget`, `WidgetQuery`, `TonWalletCard` | `widgets.md`, `wallet-and-ton.md` |
| Media and files | `sendPhoto`…`sendLivePhoto`, `sendMediaGroup`, `InputMedia`, `getFile` | `media-and-files.md` |
| Payments, Stars, paid media | `sendInvoice`, `PreCheckoutQuery`, `refundStarPayment`, `sendPaidMedia`, `StarTransaction` | `payments-and-stars.md` |
| Inline mode | `answerInlineQuery`, `InlineQueryResult`, `ChosenInlineResult` | `inline-mode.md` |
| Business accounts | `BusinessConnection`, `BusinessBotRights`, business methods | `business-accounts.md` |
| Chat administration | `ChatMember`, `promoteChatMember`, invite links, join requests | `chat-administration.md` |
| Polls, checklists, reactions | `sendPoll`, `sendChecklist`, `setMessageReaction` | `polls-checklists-and-reactions.md` |
| Gifts and stories | `sendGift`, `getUniqueGift`, `postStory` | `gifts-and-stories.md`, `specialized-updates.md` |
| Mini Apps (bot side) | `WebAppInfo`, `answerWebAppQuery`, `savePrepared*` | `mini-apps-bridge.md` |
| Topics | `createForumTopic`, `message_thread_id` | `topics-and-contexts.md` |
| Bot settings and identity | `setMySettings`, `getMe` (`BotFullInfo`), `setMyCommands` | `bot-settings.md`, `navigation-and-flows.md` |
| Channels and broadcasting | `allow_paid_broadcast`, suggested posts, direct messages | `channels-and-broadcasting.md` |
| Stickers, custom emoji | `getCustomEmojiStickers`, sticker sets | `custom-emoji.md` (sticker-set management: catalog only) |
| Games, Telegram Passport | `sendGame`, `setPassportDataErrors` | catalog only (`tg_api_lookup.py show …`) |
| SDK support of all of the above | — | `sdk-compatibility.md` |

## What each release added (9.0 → 10.5)

Summaries of the official changelog; full text: `py -3 scripts/tg_api_lookup.py
version <v>`. Deep 10.3-10.5 coverage: `bot-api-coverage.md`.

| Version | Date | Added (main items) | Taught in |
|---|---|---|---|
| **10.5** | 2026-11-22 | Bot settings from code (`setMySettings`: inline mode, placeholder, location, feedback share, groups, privacy, business, managed bots, guest/join-request queries, topics + `has_topic_sidebar`, bot-to-bot, `callback_query_mode`); `getMe` returns `BotFullInfo` (getMe-only fields left `User`; `active_usernames`, `inline_query_placeholder`, `needs_inline_query_location`, `has_topic_sidebar`); owner invites `t.me/botinvite/<bot>` + `WriteAccessAllowed.inviter`; expandable quotes hold `blocks` instead of `text` | `bot-settings.md`, `bot-api-coverage.md`, `telegram-capabilities.md` |
| **10.4** | 2026-11-09 | HTML widgets (`sendWidget`, `widget_query`, shared widgets, TON wallet queries); ephemeral callback replies without `receiver_user_id`; quotes from rich messages; TON wallet cards/transfers, `ton_address`/`bank_card_number` entities; chat share themes; `getUniqueGift`, `deleteBusinessAccountGift`; `PaidMessagesWaived`; private-topic links; `AreaPosition` rename | `bot-api-coverage.md`, `widgets.md`, `wallet-and-ton.md`, `gifts-and-stories.md` |
| **10.3** | 2026-08-24 | Rich buttons, compact tables, expandable quotes, document blocks; `EphemeralMessageParameters`; disabled buttons; `force_reply` on keyboards; Stop for drafts (`can_stop`, `stopped_message_generation`); `can_send_welcome_messages`; community joins; gift text | `bot-api-coverage.md`, `buttons-and-styles.md`, `streaming-and-editing.md` |
| **10.2** | 2026-07-14 | Ephemeral messages; rich input blocks (`InputRichBlock*`), `InputMediaVoiceNote`; Communities; `Update.subscription` (`BotSubscriptionUpdated`); Mini App origin hardening | `ephemeral-and-personal.md`, `payments-and-stars.md#subscriptions-bot-features`, `mini-apps-bridge.md` |
| **10.1** | 2026-06-11 | Rich Messages (`sendRichMessage`, `sendRichMessageDraft`, `RichBlock*`); join-request queries (`answerChatJoinRequestQuery`, `sendChatJoinRequestWebApp`); poll link media | `telegram-capabilities.md`, `chat-administration.md#invite-links-and-join-requests` |
| **10.0** | 2026-05-08 | Guest mode (`guest_message`, `answerGuestQuery`); `deleteMessageReaction`, `deleteAllMessageReactions`, `can_react_to_messages`, `getChatAdministrators.return_bots`; poll media, `members_only`, `country_codes`, 1-option polls; live photos (`sendLivePhoto`); business bots without Premium; bot-to-bot messages; managed-bot access settings | `updates-and-delivery.md`, `polls-checklists-and-reactions.md`, `media-and-files.md#live-photos-100`, `business-accounts.md` |
| **9.6** | 2026-04-03 | Managed bots (`request_managed_bot`, `managed_bot` update, token methods); `savePreparedKeyboardButton`; polls: multi-answer quizzes (`correct_option_ids`), revoting, shuffle, added options, `persistent_id`, description | `polls-checklists-and-reactions.md`, `mini-apps-bridge.md`, `specialized-updates.md` |
| **9.5** | 2026-03-01 | `date_time` entity; `sendMessageDraft` for all bots; member tags (`setChatMemberTag`, `can_manage_tags`) | `regular-formatting.md`, `chat-administration.md#tags-95-and-chat-settings` |
| **9.4** | 2026-02-09 | Button `style` and `icon_custom_emoji_id`; custom emoji for Premium owners; topics in private chats; `setMyProfilePhoto`; video qualities; profile audios | `buttons-and-styles.md`, `custom-emoji.md`, `topics-and-contexts.md` |
| **9.3** | 2025-12-31 | Private-chat topics, `sendMessageDraft`; `getUserGifts`, `getChatGifts`, gift colors/backgrounds; `repostStory`; paid media up to 25000 Stars | `streaming-and-editing.md`, `gifts-and-stories.md` |
| **9.2** | 2025-08-15 | Channel direct-messages chats (`direct_messages_topic_id`); suggested posts (`approveSuggestedPost`…); checklist task replies | `channels-and-broadcasting.md`, `polls-checklists-and-reactions.md` |
| **9.1** | 2025-07-03 | Checklists (`sendChecklist`, `editMessageChecklist`); polls up to 12 options; `getMyStarBalance` | `polls-checklists-and-reactions.md#checklists-business-accounts-91`, `payments-and-stars.md` |
| **9.0** | 2025-04-11 | Business account management (`BusinessBotRights`, read/delete, profile, gifts, Stars, stories); unique gifts, `AcceptedGiftTypes`; `giftPremiumSubscription`; `TransactionPartnerUser.transaction_type`; paid messages | `business-accounts.md`, `gifts-and-stories.md`, `payments-and-stars.md` |

Older releases (2015-2024) are in `changelog.json` too: `py -3
scripts/tg_api_lookup.py versions`.
