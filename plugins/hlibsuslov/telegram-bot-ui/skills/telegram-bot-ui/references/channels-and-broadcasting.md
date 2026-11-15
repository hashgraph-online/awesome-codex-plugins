# Channels, notifications, and broadcasting

Entry point for anything that is **posted or broadcast** rather than replied in a chat:
channel posts, announcements in groups, and mailings to many users. Read next:

* **What a post should look like** and which format per post type →
  `channel-post-design.md` (anatomy, buttons in channels, custom emoji, comments, channel DMs,
  suggested posts, reactions, widgets status).
* **How to publish it safely** (content model → render → validate → preview → approve →
  publish once → edit/pin/delete/copy; scheduling; rate limits; fan-out) →
  `publishing-pipeline.md`.
* Recipes: 30 news autoposter · 31 long-read rich post · 32 album / paid media · 33 poll and
  quiz · 34 pinned daily digest · 35 editorial approval · 36 cross-posting variants · 37
  broadcast mailing · 38 comments and direct messages · 39 correcting a published post
  (`recipes/30-news-autoposter.md` … `recipes/39-correct-published-post.md`).
* Code: `examples/python/tgkit/publish.py`, CLI `scripts/tg_post.py`.

Evidence tags **[API]** / **[Guide]** / **[Heuristic]** / **[Unverified]** as defined in
`channel-post-design.md`; facts re-read on **2026-11-15** (Bot API 10.4, 2026-11-09, is the
newest version on that date).

## Delivery surfaces

| Surface | What changes for formatting and delivery |
|---|---|
| **Channel post** | Bot = admin with `can_post_messages` **[API]**. Regular formatting, media, polls, paid media and Rich Messages (`sendRichMessage` accepts a channel `chat_id`) **[API]**. No widgets **[Guide]**. Buttons: see `channel-post-design.md#buttons-in-a-channel-post`. |
| **Discussion group** (comments) | `linked_chat_id`; posts arrive as `is_automatic_forward` copies; comment by replying to the copy **[API]** (R38). |
| **Channel direct messages** | supergroup with `is_direct_messages`; every send needs `direct_messages_topic_id`; no polls, no ephemeral callback replies; suggested posts **[API]** (R38). |
| **Group announcement** | respect `message_thread_id` in forums; ≤ 20 messages/minute in a group **[Guide]**. |
| **Mailing to users** | one prepared payload per recipient; throttling, `retry_after`, per-recipient outcomes (R37). |
| **Scheduled post** | no native scheduling for bots **[API: absence]**: the caller schedules; the content is validated at compose time and published with an idempotency key. |

## Rights the bot needs in a channel

| Action | Right **[API]** |
|---|---|
| Post, approve suggested posts, see channel statistics | `can_post_messages` |
| Edit others' posts, pin / unpin | `can_edit_messages` |
| Delete any post | `can_delete_messages` (own posts: `can_post_messages`) |
| Manage channel DMs, decline suggested posts, delete in the DM chat | `can_manage_direct_messages` |
| Post / edit / delete stories | `can_post_stories`, `can_edit_stories`, `can_delete_stories` |

Check with `getChatMember(chat_id, bot_id)` or `getChatAdministrators(return_bots=true)` (10.0)
**[API]** before a run; a missing right fails every post with `403`/`400 not enough rights`.

## Updates a publisher listens to

* `channel_post` / `edited_channel_post` — posts in channels where the bot is a member
  **[API]** (whether its own posts come back is **[Unverified]**).
* `message_reaction_count` — anonymous reaction counts (admin bot, opt-in via
  `allowed_updates`) **[API]**.
* `callback_query` — taps on callback buttons under posts; `message.chat` is the channel and
  `from` is the user **[API]**.
* Discussion group `message` updates for comments; DM-chat `message` updates with
  `direct_messages_topic` / `suggested_post_info` **[API]**.
* `poll` — state of polls the bot sent **[API]**.

Remember: `allowed_updates` is sticky; list every type you need (`sdk-compatibility.md`).

## Notification and content controls (summary)

* `disable_notification` — silent: digests, corrections, every part after the first.
* `protect_content` — no forwarding/saving (and no `forwardMessage` cross-posts).
* `link_preview_options` — choose or disable the preview (text messages only; not in
  `sendRichMessage`).
* `has_spoiler`, `show_caption_above_media` — media posts.
* `message_effect_id` — **private chats only** **[API]**: never in channel posts.
* `allow_paid_broadcast` — up to 1000 messages/s for 0.1 Star each over the free limit
  **[API]**.

## Broadcasting in one paragraph

Author the payload once (`plan()`), throttle below ~30 messages/s **[Guide]**, honour
`retry_after`, keep `campaign:recipient` keys so a re-run skips delivered messages, record
`403` as blocked and never retry it, treat timeouts as unknown, and log outcomes without the
token or personal text. Personalize through the content model (names as plain text +
entities). Full pattern: `publishing-pipeline.md#10-mailing-to-many-recipients-fanout`, R37.

## Corrections to earlier guidance in this file

Older versions of this reference said callback buttons "need a chat context, not a bare
channel" and that Web App buttons work in channel posts. Current Bot API pages say otherwise
(checked 2026-11-15): callback buttons have **no channel restriction** (the callback carries the
tapping user), and `web_app` buttons are **private chats only** **[API]**.

## Testing broadcasts and posts

Assert on payloads, never send to real chats from tests (`testing-playbook.md`). Cover:
render per locale; hostile names in every format; preview on/off; silent/protected flags;
split + buttons on the last part; album follow-up; `429` with `retry_after`; `403` per
recipient; a timeout that must not double-post; unchanged edit = no request. All of these are
in `tests/test_publishing.py`.
