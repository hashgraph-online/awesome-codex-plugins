# Bot settings from code (Bot API 10.5)

Bot API 10.5 (2026-11-22) moved the bot's own switches into the API: one method writes them,
`getMe` reads them back. Checked against https://core.telegram.org/bots/api#setmysettings and
https://core.telegram.org/bots/api#botfullinfo on **2026-11-22**. Code:
`examples/python/tgkit/settings.py`; recipe [10 Bot settings from code](../recipes/10-bot-settings.md);
request sequence `examples/payloads/r10-bot-settings.json`.

Labels: **[API]** spec; **[Heuristic]** this skill's advice.

## Settings from code: setMySettings

**[API]** `setMySettings` changes only the settings it is given; the others stay as they are.
Returns `True`. Parameters (all optional):

| Parameter | What it switches | Before 10.5 |
|---|---|---|
| `supports_inline_queries` | inline mode on/off | `/setinline` |
| `inline_query_placeholder` | text in the input field after `@bot`; `""` = default | `/setinline` |
| `needs_inline_query_location` | ask for the user's location with every inline query | `/setinlinegeo` |
| `inline_feedback_share_denominator` | receive 1 of N `chosen_inline_result`: 1, 10, 100, 1000; `0` = off | `/setinlinefeedback` |
| `can_join_groups` | can be added to groups | `/setjoingroups` |
| `can_read_all_group_messages` | `true` = privacy mode **off** | `/setprivacy` |
| `can_connect_to_business` | users can connect the bot to their account | BotFather |
| `can_manage_bots` | users can create bots managed by this one | BotFather |
| `supports_guest_queries` | guest queries from chats the bot isn't in | BotFather |
| `supports_join_request_queries` | can be assigned to process join requests | BotFather |
| `has_topics_enabled` | forum topic mode in private chats | BotFather |
| `allows_users_to_create_topics` | users create and delete topics there | BotFather |
| `has_topic_sidebar` | show those topics in a sidebar | new in 10.5 |
| `can_communicate_with_bots` | talk to other bots in groups, private chats, business | BotFather |
| `callback_query_mode` | `default` / `auto` / `inline`, see below | new in 10.5 |

```json
{"inline_query_placeholder": "Search orders…", "has_topics_enabled": true,
 "allows_users_to_create_topics": true, "has_topic_sidebar": true,
 "inline_feedback_share_denominator": 10, "callback_query_mode": "auto"}
```

- **[Heuristic]** Keep the desired settings in the repository, next to the code that depends
  on them (inline handler, topic routing, callback router). A switch flipped by hand in BotFather
  drifts from the code; a reviewed config does not.
- **[Heuristic]** Apply them at start-up or in a deploy step: `getMe`, compare, then **one**
  `setMySettings` with only the differences (`settings.apply`). Nothing differs → no call.
- **[Heuristic]** Validate before sending (`settings.validate`): the denominator must be one of
  0/1/10/100/1000, the mode one of three strings, the rest booleans. Each switch that widens what
  the bot receives — privacy off, location with inline queries, bot-to-bot communication — is a
  product decision: show the human what it changes and wait for a yes.
- **[Heuristic]** BotFather can still change most of these. Pick one owner (the code) and re-apply
  on deploy, or a manual change silently undoes the config.

## Reading settings back: getMe returns BotFullInfo

**[API]** `getMe` returns `BotFullInfo` instead of `User`. The getMe-only flags
(`can_join_groups`, `can_read_all_group_messages`, `supports_inline_queries`,
`can_connect_to_business`, `has_main_web_app`, `has_topics_enabled`,
`allows_users_to_create_topics`, `can_manage_bots`, `supports_guest_queries`,
`supports_join_request_queries`) were removed from `User` and live in `BotFullInfo`, together with
the new `active_usernames`, `inline_query_placeholder` (omitted = default),
`needs_inline_query_location` and `has_topic_sidebar`.

- **[API]** Not readable back: `inline_feedback_share_denominator`, `can_communicate_with_bots`,
  `callback_query_mode`. A diff can't skip them; send them whenever the config names them.
- **[Heuristic]** Typed SDKs that model `getMe` as `User` may drop the new fields or fail
  validation until they ship 10.5 (`sdk-compatibility.md`). Read the raw result when you need them.
- **[Heuristic]** Code that read `from.can_join_groups` (or similar) on an incoming `User` never
  got a value for other users; after 10.5 the field doesn't exist there at all. Read it from getMe.

## Callback query mode

**[API]** `callback_query_mode` decides how callbacks from buttons in messages **sent by the bot**
arrive. Messages sent **via** the bot (inline mode) always come with `inline_message_id`.

| Mode | `CallbackQuery` carries |
|---|---|
| `default` | `message`, an `InaccessibleMessage` (date 0, no content) if the bot can't access it |
| `auto` | `inline_message_id` instead of `message` when the message is inaccessible; `message` can still be inaccessible right after a deletion |
| `inline` | always `inline_message_id`, never `message` |

```json
{"update_id": 900106, "callback_query": {"id": "4382000000000000105",
 "from": {"id": 444444444, "is_bot": false, "first_name": "Dana"},
 "inline_message_id": "BAAAAKx2nwABOWNSENT", "chat_instance": "-7770105", "data": "set:1:topics:on"}}
```

- **[API]** A callback with `inline_message_id` has no `message` and no chat. Edit it with
  `editMessageText` / `editMessageReplyMarkup` and `inline_message_id`; `settings.callback_target`
  returns the right address in every mode, or `None` for an `InaccessibleMessage` (date 0):
  answer the query and send the result in a new message instead of editing.
- **[Heuristic]** With `auto` or `inline`, keep what a handler needs in `callback_data` (it is
  echoed back) or in state keyed by `from.id`; a lookup by `(chat_id, message_id)` finds nothing.
  `ScreenFlow` (`tgkit/flows.py`) keys sessions by message, so it expects `default` (in `auto` it
  answers an inaccessible message with "expired", which is right for it).
- **[Heuristic]** `auto` is the safe upgrade for bots whose menus outlive the bot's access to the
  message (old messages, chats where the bot lost access): buttons keep working through
  `inline_message_id`. Choose `inline` only if every handler is written for it.

## Topics in the private chat and the sidebar

**[API]** `has_topics_enabled` turns on topics in private chats with the bot,
`allows_users_to_create_topics` lets users add and delete them, `has_topic_sidebar` shows them in a
sidebar. `BotFullInfo` reports all three.

- **[Heuristic]** A sidebar fits bots with several long-lived threads per user (orders,
  projects, tickets, one AI conversation per topic). For a single conversation, topics only add
  a step: leave them off.
- **[Heuristic]** Turning topics on changes addressing: every reply carries `message_thread_id`
  (`topics-and-contexts.md#private-chat-topics-and-topic-links`). Ship the routing before the switch.

## Active usernames

**[API]** `BotFullInfo.active_usernames` lists every active username of the bot (10.4 allowed
Premium owners a second one ending in `agent`, `ai`, `app`, `game` or `gay`).

- **[Heuristic]** In groups, `/cmd@name` is for this bot when `name` is **any** active username
  (`settings.addressed_to_me`); a check against `username` alone ignores commands sent to the
  second name.
- **[Heuristic]** Build public links from one chosen username, the same everywhere; don't
  mix both in one product.

## Inline mode settings

**[API]** `supports_inline_queries`, `inline_query_placeholder`, `needs_inline_query_location`
and `inline_feedback_share_denominator` replace `/setinline`, `/setinlinegeo` and
`/setinlinefeedback`; `BotFullInfo` reads back the first three. `InlineQuery.location` and
`ChosenInlineResult.location` are filled only with the location request on.

- **[Heuristic]** The placeholder is a hint, not a label: say what to type
  (`Search orders…`, `City or airport`), under ~30 characters, in the bot's language.
- **[Heuristic]** Ask for location only when results depend on it; users see a prompt with
  every inline query.
- **[Heuristic]** Feedback share: `1` while you need every `chosen_inline_result` (editing the
  sent message, analytics on a small bot); `10`–`1000` for load control on a busy one. Details:
  `inline-mode.md#bot-settings`.

## Owner invites: botinvite links

**[API]** The bot's owner opens `https://t.me/botinvite/<bot_username>` and invites up to 10 users
at once to private chats with the bot. The bot may then message them. Their chat begins with a
`write_access_allowed` service message whose `inviter` is the owner:

```json
{"message_id": 1, "date": 1763800000, "chat": {"id": 444444444, "type": "private", "first_name": "Dana"},
 "from": {"id": 444444444, "is_bot": false, "first_name": "Dana"},
 "write_access_allowed": {"inviter": {"id": 111111111, "is_bot": false, "first_name": "Alex"}}}
```

- **[Heuristic]** Use it for testers, a team's internal bot, a pilot group. Send the link only to
  the owner (`/invite` checks the owner id); it is useless to anyone else.
- **[Heuristic]** Greet an invited user by the inviter's name and give one first action
  (`onboarding-and-first-run.md`): they didn't press Start, so there was no `/start` payload and
  no first-run screen. Tell the owner who accepted.
- **[Heuristic]** "May message them" is not "should broadcast": one welcome, then wait for the user.
