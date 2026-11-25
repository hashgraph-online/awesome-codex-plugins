---
summary: "Native polls and quizzes (9.6, 10.0), business checklists, message reactions and reactions as quiet status feedback; read for polls, checklists, reactions or acknowledging work."
verified: "2026-11-25"
bot_api: "10.5"
---

# Polls, checklists and reactions

Native polls and quizzes (with the 9.6 and 10.0 extensions: multiple correct answers,
revoting, added options, media, members-only, country limits), checklists (business
accounts), and message reactions (setting, reading counts, deleting). Checked
against Bot API 10.5 on **2026-11-25** (https://core.telegram.org/bots/api#sendpoll,
#poll, #sendchecklist, #setmessagereaction). Every JSON block passes
`scripts/validate_payload.py`.

Labels: **[API]** spec; **[Heuristic]** this skill's advice.

## Contents

- [Polls and quizzes](#polls-and-quizzes)
  - [Sending](#sending)
  - [Receiving results](#receiving-results)
- [Checklists (business accounts, 9.1)](#checklists-business-accounts-91)
- [Reactions](#reactions)
  - [Setting](#setting)
  - [Reading](#reading)
  - [Reactions as interface feedback (event-driven UI)](#reactions-as-interface-feedback-event-driven-ui)
  - [Deleting others' reactions (10.0, moderation)](#deleting-others-reactions-100-moderation)
- [What users see](#what-users-see)
- [Common mistakes](#common-mistakes)

## Polls and quizzes

### Sending

```json
{"method": "sendPoll", "params": {
  "chat_id": -1001234567890,
  "question": "Where do we meet on Friday?",
  "options": [{"text": "Podil"}, {"text": "Pechersk"}, {"text": "Online"}],
  "is_anonymous": false,
  "allows_multiple_answers": true,
  "allow_adding_options": true,
  "close_date": 1763450000,
  "description": "Vote by Thursday 18:00. You can change your vote."
}}
```

```json
{"method": "sendPoll", "params": {
  "chat_id": 111111111,
  "question": "Which of these are prime?",
  "options": [{"text": "2"}, {"text": "9"}, {"text": "11"}, {"text": "15"}],
  "type": "quiz",
  "allows_multiple_answers": true,
  "correct_option_ids": [0, 2],
  "explanation": "9 = 3×3 and 15 = 3×5.",
  "shuffle_options": true
}}
```

Limits and rules **[API]**:

- `question` 1-300 chars (only custom-emoji entities); `options` **1-12** (minimum
  lowered from 2 to 1 in 10.0; max 12 since 9.1), option text 1-100 chars.
- Quiz: `correct_option_ids` (9.6, **replaced** `correct_option_id`) — increasing
  0-based ids, required for quizzes; quizzes may allow multiple answers since 9.6.
  `explanation` 0-200 chars, ≤2 line feeds; `explanation_media` (10.0).
- `allows_revoting` defaults to false for quizzes, true for regular polls.
  `allow_adding_options` is not supported for anonymous polls and quizzes.
  `hide_results_until_closes`, `shuffle_options` (9.6).
- `open_period` / `close_date` 5-2628000 s, mutually exclusive; `is_closed: true`
  sends a closed preview.
- `description` 0-1024 chars and `media` (10.0) describe the poll; options can carry
  `media` (`InputPollOptionMedia`: animation, link (10.1), live photo, location,
  photo, sticker, venue, video). `media` on the poll is an `InputPollMedia`
  (animation, audio, document, live photo, location, photo, venue, video).
- `members_only` (voters who have been members >24 h) and `country_codes` (0-12
  ISO 3166-1 alpha-2) — 10.0, **channel chats only**: a group poll with either field fails.
- Polls can't be sent to channel direct-messages chats.

### Receiving results

- **[API]** `poll` updates: new state of polls **sent by the bot** and of manually stopped
  polls. `poll_answer` updates: a user changed their vote in a **non-anonymous** poll
  sent by the bot (`option_ids`, and since 9.6 `option_persistent_ids`; `user` or
  `voter_chat`). An empty `option_ids` = vote retracted.
- **[API]** `PollOption.persistent_id` (9.6) stays stable when options are added; store
  votes against it, not against the array index. Options added by users carry
  `added_by_user` / `added_by_chat` and `addition_date`; service messages
  `poll_option_added` / `poll_option_deleted` appear in the chat.
- **[API]** `stopPoll(chat_id, message_id, reply_markup?)` closes a poll **sent by the bot**
  and returns the final `Poll`. Not available for inline messages.
- **[API]** Replies can target one option: `ReplyParameters.poll_option_id`,
  `Message.reply_to_poll_option_id` (9.6).

```json
{"update_id": 900000601, "poll_answer": {
  "poll_id": "5432109876",
  "user": {"id": 222222222, "is_bot": false, "first_name": "Taras"},
  "option_ids": [0, 2],
  "option_persistent_ids": ["opt-podil", "opt-online"]
}}
```

State: map `poll_id → (chat_id, message_id, purpose)` when sending; tally from
`poll_answer` keyed by `(poll_id, user.id)` with last-write-wins (revotes replace).
For anonymous polls only `poll` totals exist — you can't know who voted. **[Heuristic]**

## Checklists (business accounts, 9.1)

- **[API]** `sendChecklist` and `editMessageChecklist` work **only on behalf of a connected
  business account** (`business_connection_id` required) to a private chat.
- **[API]** `InputChecklist`: `title` 1-255, `tasks` 1-30 `InputChecklistTask` (`id`
  positive and unique, `text` 1-100), `others_can_add_tasks`,
  `others_can_mark_tasks_as_done`. Title/task entities: formatting and (9.6)
  `date_time` only.
- **[API]** Incoming: `Message.checklist` (`Checklist` with `ChecklistTask`s:
  `completed_by_user` / `completed_by_chat` (9.3), `completion_date`), service
  messages `checklist_tasks_done` (`marked_as_done_task_ids`,
  `marked_as_not_done_task_ids`) and `checklist_tasks_added`. Reply to one task with
  `ReplyParameters.checklist_task_id` (9.2).

```json
{"method": "sendChecklist", "params": {
  "business_connection_id": "BCxyz", "chat_id": 555555555,
  "checklist": {"title": "Before your appointment", "others_can_mark_tasks_as_done": true,
                "tasks": [{"id": 1, "text": "Bring your passport"}, {"id": 2, "text": "Arrive 10 minutes early"}]}
}}
```

Edit by sending the **whole** new checklist with the same task ids for unchanged
tasks; new ids for new tasks. **[Heuristic]** (the method replaces the checklist)

## Reactions

### Setting

```json
{"method": "setMessageReaction", "params": {"chat_id": 111111111, "message_id": 4021, "reaction": [{"type": "emoji", "emoji": "👍"}]}}
```

- **[API]** Bots can set **one reaction per message** (non-Premium rules); a custom-emoji
  reaction only if already present on the message or allowed by admins; **paid
  reactions can't be used by bots**. Clearing the bot's reaction with `reaction: []`
  (or by omitting it) is not stated in the method text **[Unverified]**. The `emoji` value must be one of the fixed list in `ReactionTypeEmoji`
  (`tg_api_lookup.py show ReactionTypeEmoji`).
- **[Heuristic]** A reaction is a cheap acknowledgement ("👀 seen", "👍 done") that adds
  no message to the chat — use it instead of "OK, received" replies in groups.

### Reading

- **[API]** `message_reaction` (`MessageReactionUpdated`: `user` or `actor_chat`,
  `old_reaction`, `new_reaction`) — per user, non-anonymous; bot must be **admin** and
  request the type **explicitly**; never sent for reactions set by bots.
- **[API]** `message_reaction_count` (`MessageReactionCountUpdated`: `reactions` with
  `ReactionCount`) — anonymous totals, grouped, delayed up to a few minutes; admin +
  explicit.
- **[API]** `ChatFullInfo.available_reactions` lists allowed reactions;
  `ChatPermissions.can_react_to_messages` (10.0) controls who may react.

```json
{"update_id": 900000602, "message_reaction": {
  "chat": {"id": -1001234567890, "type": "supergroup", "title": "Foodies of Kyiv"},
  "message_id": 812, "date": 1763191200,
  "user": {"id": 222222222, "is_bot": false, "first_name": "Taras"},
  "old_reaction": [], "new_reaction": [{"type": "emoji", "emoji": "🔥"}]
}}
```

### Reactions as interface feedback (event-driven UI)

A reaction changes the message it is on and sends no new message, so it is the quietest
acknowledgement a bot has. **[Heuristic]** unless marked.

| Moment | Do | Instead of |
|---|---|---|
| A request arrives and work starts | react 👀 on the user's message | "Got it, working on it…" |
| A long job runs | keep one status card and edit it (`dynamic-feedback-and-streaming.md`); reactions don't show progress | a reaction per step |
| Done, the result is a new message anyway | replace 👀 with 👍 (or 👌) on the request, then send the result | a "Done!" message before the result |
| Done, nothing else to say (saved a note, logged an expense) | 👍 or ✍ on the user's message and nothing else | "Saved ✅" |
| Failed | remove the reaction (`reaction: []`) and reply with what failed and what to do | 👎 or 🤬 alone: a reaction cannot carry a next step |
| Rating an AI answer | an inline 👍/👎 pair, or read users' reactions where the bot receives them | asking "Was this helpful?" in a new message |

Rules: one state per message, the newest wins (a bot holds one reaction: setting a new one
replaces it, **[API]**); only the emoji in `ReactionTypeEmoji` (✅ ❌ ⏳ are **not** reaction emoji,
**[API]**; `validate_payload.py` rejects them); pick a fixed meaning per emoji for the whole bot and
write it down in the style profile; never react to messages the bot did not need to touch.
A reaction is not proof the work finished: when the result matters later, the message or card
carries the state, and the reaction only mirrors it.

Errors: `setMessageReaction` fails on some service messages and when reactions are restricted in
the chat (`ChatFullInfo.available_reactions`, `can_react_to_messages`); treat the failure as
cosmetic, log it, never retry in a loop, and never let it block the real reply. Rate limits apply
like any other call.

Reading users' reactions: groups and channels need the bot to be an administrator and
`message_reaction` / `message_reaction_count` listed in `allowed_updates` (**[API]**); anonymous
reactions arrive only as counts, late and grouped. Private chats: the docs state no exception, and
whether a bot receives `message_reaction` there is **Unverified** in this skill; check it with a
test bot before building on it, and keep a button as the fallback. App notifications, a bot's own
toast (`answerCallbackQuery`) and Telegram's system notifications are three different things: a
bot controls only the first two (`disable_notification` on its own messages, toasts on presses).

### Deleting others' reactions (10.0, moderation)

- **[API]** `deleteMessageReaction(chat_id, message_id, user_id | actor_chat_id)` removes
  one user's/chat's reaction; `deleteAllMessageReactions(chat_id, user_id |
  actor_chat_id)` removes up to 10000 recent reactions by them. Groups/supergroups
  only; needs `can_delete_messages`.

```json
{"method": "deleteAllMessageReactions", "params": {"chat_id": -1001234567890, "user_id": 666666666}}
```

## What users see

- Non-anonymous polls show voter avatars; quizzes show the explanation on a wrong
  answer or the lamp icon. **[API]** (explanation behaviour)
- A bot reaction appears like any user's reaction with the bot's avatar. **[Heuristic]**
  (rendering not verified offline)

## Common mistakes

| Mistake | Fix |
|---|---|
| `correct_option_id` (singular) | removed in 9.6 → `correct_option_ids` |
| Counting votes by option index after users add options | use `persistent_id` |
| Expecting `poll_answer` for anonymous polls | only `poll` totals |
| `allow_adding_options` on a quiz / anonymous poll | not supported |
| `sendChecklist` without a business connection | business accounts only |
| Waiting for `message_reaction` with default `allowed_updates` | request it explicitly, be admin |
| Two reactions from the bot | one per message |
