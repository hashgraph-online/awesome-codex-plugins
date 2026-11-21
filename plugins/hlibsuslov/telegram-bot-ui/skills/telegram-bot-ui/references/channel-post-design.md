# Channel post design

How a channel post should look and which Bot API format carries it. Pipeline (render,
validate, publish once, edit, fan-out): `publishing-pipeline.md`. Channel rights, updates and
mailings: `channels-and-broadcasting.md`. Code: `examples/python/tgkit/publish.py`; recipes
30-39 (`recipes/30-news-autoposter.md` …).

**Evidence tags.** **[API]** = stated on a Bot API page; **[Guide]** = official guide or FAQ;
**[Heuristic]** = this skill's design advice, not a Telegram rule; **[Unverified]** = not stated
in the docs, test on a test channel first. All [API]/[Guide] items re-read on **2026-11-15**
against **Bot API 10.4 (2026-11-09)** — the newest version in the changelog on that date.

## Anatomy of a good post

1. **First line = the headline.** It is what the notification, the chat list and the pinned
   bar show; they cut it short **[Heuristic]** (no documented length — keep it under ~80–120
   characters, `validate()` warns above 120). No greeting, no emoji row, no date-only line.
2. **One idea per post**, 1–3 short paragraphs for news. Longer → a Rich Message long read
   (below), not a split into many messages.
3. **One call to action.** One button (or one link) the reader should take. Several
   equal buttons = no action **[Heuristic]**. At most one `style: "primary"` (`validate()` warns).
4. **Link preview on purpose.** Regular text messages generate a preview from the first link
   unless told otherwise. Set `link_preview_options` **[API]**: `url` (which link to preview),
   `prefer_large_media` / `prefer_small_media`, `show_above_text`, or `is_disabled`. A
   link-heavy digest with a random large card is the most common visual defect **[Heuristic]**.
   `sendRichMessage` has **no** `link_preview_options` parameter **[API]**.
5. **Media placement.** `show_caption_above_media` puts the caption above a photo/video/
   animation (and paid media, copies) **[API]**; `has_spoiler` hides a sensitive photo/video
   **[API]**. Documents ignore both.
6. **Silent vs. loud.** `disable_notification` sends with no sound **[API]** — use it for
   digests, corrections, follow-ups and every part after the first **[Heuristic]**.
   `protect_content` blocks forwarding and saving **[API]** (and therefore `forwardMessage`).
7. **Signature.** `Message.author_signature` carries the post author's signature in channels
   **[API]**; there is **no send parameter** to set it — signing is a channel setting
   **[API: absence]**. What a bot-sent post shows as signature when signing is on is
   **[Unverified]**.
8. **Formatting.** Bold the headline, keep body text plain, italics for metadata. Entities or
   one escaper per format (`security-and-escaping.md`); custom emoji only where eligible (below).

## Choosing the format per post type

| Post type | Method / format | Rules that matter |
|---|---|---|
| Short announcement | `sendMessage` + entities | ≤ 4096 chars **[API]**; headline bold; maybe no preview |
| News with link | `sendMessage` + `link_preview_options.url` | one preview, large media, button "Read the full story" (R30) |
| Long read | `sendRichMessage` (blocks) | ≤ 32768 chars, 500 blocks, 16 levels, 50 media, 20 table columns **[API]**; headings, compact tables (`is_compact` 10.3), expandable quote (10.3), `document` block (10.3), button rows (10.3) (R31) |
| Photo / video | `sendPhoto` / `sendVideo` | caption ≤ 1024 **[API]**; overflow → follow-up text, buttons on the last part (R32) |
| Album | `sendMediaGroup` | 2–10 items; documents/audio only with their own type **[API]**; **no `reply_markup`** → buttons in a silent follow-up; one caption on the first item (R32) |
| Live photo | `sendLivePhoto` / `InputMediaLivePhoto` in albums (10.0) **[API]** | treat as a photo for layout |
| Poll / quiz | `sendPoll` | question 1–300, 1–12 options of 1–100, explanation 0–200 with ≤ 2 line feeds, description 0–1024, `open_period` xor `close_date` **[API]**; `members_only`, `country_codes` are **channel-only** (10.0) **[API]**; media in polls (10.0/10.1) (R33) |
| Checklist | Rich list items with `has_checkbox` / `is_checked` **[API]** | `sendChecklist` is **business-account only** **[API]** — a channel checklist is static text, not tickable |
| Paid media | `sendPaidMedia` | `star_count` 1–25000, ≤ 10 items, `payload` 0–128 bytes **[API]**; in a channel proceeds go to the channel balance **[API]**; `ChatFullInfo.can_send_paid_media` tells if allowed **[API]**; **can't be copied** **[API]** (R32) |
| Giveaway-style post | regular post + poll or button | the Bot API has **no method to create a Telegram giveaway** (only `Giveaway` objects are received) **[API: absence]** |
| Pinned index / digest | one post edited in place + `pinChatMessage` | pin needs `can_edit_messages` in channels; channels never notify about pins **[API]** (R34) |
| Series / thread | each part a post; index post links to `https://t.me/<channel>/<id>` | edit the index as parts appear (R34 pattern) **[Heuristic]** |
| Live card / widget | **not possible in a channel** (see "When channels get widgets") | "Widgets cannot be posted in channels, directly or via the bot" **[Guide, Widgets]**; production widgets go to private chats only **[API]**; users may forward a widget into a channel — **test server only** **[Guide]**; `sendWidget.chat_id` names no channel **[API]** |
| Story | `postStory` (business accounts) | out of scope here |

Decision helper: `tgkit.publish.resolve_kind()` picks `rich` for tables, documents, checklists,
two or more headings, or text over 4096 characters; otherwise a regular text post.

**Video in big channels.** Messages with video sent, copied or forwarded to large groups and
channels may be scheduled by the server until re-encoding; such messages have
`message_id = 0` and can't be used until sent **[API, changelog Dec 2024]**. The publisher
records `server_scheduled` and you wait for the `channel_post` update before editing or pinning.

## Buttons in a channel post

| Button | Channel | Notes |
|---|---|---|
| `url` | yes | `http(s)://` or `tg://` **[API]** |
| `callback_data` | yes **[API: no restriction]** | the tapping user's id arrives in the callback; answer every query; the bot needs an update source (polling/webhook) — likes, "show answer", votes |
| `copy_text` | yes | promo codes, addresses **[API]** |
| `login_url` | yes | domain set in @BotFather; not in ephemeral messages **[API]** |
| `switch_inline_query_chosen_chat` | yes **[API: no channel restriction]** | not in channel DM chats **[API]** |
| `web_app` | **no** | private chats only **[API]** |
| `switch_inline_query_current_chat` | **no** | "Not supported in channels" **[API]** |
| `switch_inline_query` | **avoid** | current page restricts only channel DMs, but the 2017 changelog says these can't be sent to channels **[API, conflicting]** |
| `pay`, `callback_game` | **no** | invoices / games only **[API]** |
| `disabled` (10.3) | yes | a visible "not yet" state; does nothing **[API]** |
| `style` (9.4) | yes | `primary`/`success`/`danger`; rich buttons also `link` (callback only) **[API]** |
| `icon_custom_emoji_id` | **only for bots with Fragment usernames** | the Premium-owner path covers "private, group and supergroup chats" — **not channels** **[API]** |
| Reply keyboards | **no** | nobody types in a channel **[Heuristic]**; `validate_keyboard.py` flags them |

Rich Message buttons (`RichMessageButton`, 10.3) follow the same per-chat rules; their text may
contain only plain text, custom emoji and date-time entities **[API]**.

## Custom emoji in channel text

Custom emoji entities (`tg-emoji`, `![](tg://emoji?id=)`, `custom_emoji` entity) "can only be
used by bots that purchased additional usernames on Fragment or in the messages directly sent
by the bot to private, group and supergroup chats if the owner of the bot has a Telegram
Premium subscription" **[API, formatting options]**. So: in a **channel** only a Fragment-
username bot can use them; always give the fallback emoji **[API]**; never invent ids
(`custom-emoji.md`). `validate(custom_emoji_ok=False)` refuses icons in channel posts.

The button field says the same: `icon_custom_emoji_id` "Can only be used by bots that purchased
additional usernames on Fragment or in the messages directly sent by the bot to private, group
and supergroup chats if the owner of the bot has a Telegram Premium subscription"
**[API, InlineKeyboardButton, re-read 2026-11-15]**. Channels are not in the Premium list, so
for a channel post the only eligible bot is one with Fragment usernames.

Picking packs, ids and fallbacks for posts is owned by the custom emoji stream:
`references/emoji-packs.md`, `references/emoji-in-posts.md`, `examples/python/tgkit/icons.py`,
`scripts/emoji_packs.py`. It plugs into publishing through the decoration hook, with no edits
to `publish.py`:

```python
pub = Publisher(transport, context="channel", custom_emoji_ok=bot_has_fragment_username,
                decorate=lambda post, context: add_premium_emoji(post, context))  # that stream's helper
```

The decorator receives a copy of the post and the target context (`channel`, `channel_dm`,
`group`, `private`) and returns the decorated `Post`. It runs **before** validation, so an
ineligible custom emoji is still refused; the ledger keeps the undecorated source, so
"unchanged" detection does not depend on the decorator.

## When channels get widgets

**Status on 2026-11-15** (sources: `sendWidget` and `sendSharedWidget` method pages, Widgets guide
"Where widgets live" table, Bot API 10.4 changelog):

| Path into a channel | Production | Test server |
|---|---|---|
| `sendWidget` / `sendSharedWidget` by the bot | **not available** — production allows private chats only; `chat_id` names a chat or "the target supergroup", never a channel **[API]** | **not available** — "Widgets cannot be posted in channels, directly or via the bot" **[Guide]** |
| Inline mode | not available | "Any chat except channels" **[Guide]** |
| A user forwards a shared widget into a channel | not available | **test only** **[Guide]** |

So: **not documented as available** for bots in channels. Do not promise HTML widget posts or
widget notifications in channels until the method pages list channels. Rules, size limits and
the runtime of widgets: `references/widgets.md`; examples: `examples/widgets/`.

The pipeline is ready for the change:

* `Post.widget = {"html", "public_data"?, "width"?, "height"?}` is used **only** where
  `widget_supported(context, environment)` is true: today private chats (production, test) and
  groups (test). Everywhere else the post's **blocks** are sent as a regular or Rich Message
  post and `validate()` warns `widget_fallback`.
* A widget post must have blocks: they become the widget **caption** (whole blocks up to 1024
  characters — what notifications, the chat list, search and apps without widgets show) and the
  fallback body.
* The switch is `tgkit.publish.CHANNEL_WIDGETS` (default `False`). Flip it, and add a test, only
  after the `sendWidget` page lists channels.

A channel-safe widget must satisfy (enforced by `validate()` for `context="channel"`):

1. **Read-only / public data only**: no `allow_queries`, so no per-user requests; state lives in
   `public_data` (one state for every viewer), updated by the bot.
2. **No per-user or per-chat state**: no `chat_data`; nothing personal in code or data (the
   widget stream's `check_widget` also refuses secret-looking strings).
3. **Caption first**: the caption alone carries the full meaning; the widget only adds a live
   view of the same facts.
4. Size limits as for any widget: 1–32768 bytes of HTML, ≤ 4096 bytes after zlib level 9,
   `public_data` ≤ 1024 bytes **[API]**.
5. A text/rich fallback always exists (the same blocks), and edits go through
   `editMessageWidgetData` / `editSharedWidgetData` — widget code is immutable **[API]**.

## Comments: the linked discussion group

* `getChat(channel).linked_chat_id` = the discussion group (and vice versa) **[API]**.
* Each channel post is copied into the group as a message with `is_automatic_forward: true`,
  `sender_chat` = the channel and `forward_origin` (`type: "channel"`, `message_id` = the
  channel post) **[API]**. Replies to that copy are the post's comments.
* To comment as the bot: `sendMessage` to the group with
  `reply_parameters.message_id` = the auto-forward's id **[API]**. Moderate with
  `deleteMessage` (bot admin with `can_delete_messages`) **[API]** (R38).
* The bot must be a group member with privacy mode off or admin to see comments
  **[Guide, Bot FAQ]**.
* Reactions on the auto-forward mirror the channel's available reactions **[API]**.

## Channel direct messages and suggested posts

* A channel's direct-messages chat is a **supergroup** with `is_direct_messages: true`;
  `ChatFullInfo.parent_chat` points to the channel **[API]**.
* Every send there needs `direct_messages_topic_id` (one topic per user, see
  `Message.direct_messages_topic`) **[API]** — it is not `message_thread_id`
  (`topics-and-contexts.md`).
* Not available in DM chats: **polls** **[API]**, **ephemeral callback replies** (10.4)
  **[API]**, `switch_inline_query*` buttons **[API]**.
* **Suggested posts** (9.2): users (or the bot, with `suggested_post_parameters`) propose a
  post with optional `price` (`XTR` 5–100000 Stars or `TON`) and `send_date` (300 s–30 days
  ahead) **[API]**. The bot approves with `approveSuggestedPost` (needs `can_post_messages`;
  optional `send_date` ≤ 30 days) or declines with `declineSuggestedPost` (needs
  `can_manage_direct_messages`; `comment` 0–128) **[API]**. Approved/declined suggested
  posts can't be edited; a **paid post** (`is_paid_post`) must not be deleted for 24 hours and
  can't be edited **[API]**.
* `approveSuggestedPost.send_date` is the only "publish at a time" control in the Bot API, and
  only for suggested posts **[API]**.

## Reactions

* Bots can set at most one reaction per message, no paid reactions **[API]**
  (`setMessageReaction`); a custom emoji reaction only if already present or allowed.
* Channel reactions are anonymous: count updates arrive as `message_reaction_count`, only for
  an admin bot that lists it in `allowed_updates` **[API]**. Use them for "most-liked this week"
  digests **[Heuristic]**.

## Accessibility and localization

* Labels make sense without color or emoji; buttons stay readable at the longest translation
  (`localization-and-rtl.md`). RTL rich posts set `is_rtl` **[API]**.
* One language per channel post; cross-post translated variants to per-language channels
  (R36) rather than mixing languages in one post **[Heuristic]**.

## Pre-publish checklist

Headline first and short · one CTA · preview chosen or disabled · format fits the type
(table → rich) · buttons legal for a channel · custom emoji only with a Fragment-username bot ·
captions ≤ 1024, albums 2–10 · silent where it should be · `validate()` has no errors · preview
sent to an editor's private chat (`publishing-pipeline.md`).
