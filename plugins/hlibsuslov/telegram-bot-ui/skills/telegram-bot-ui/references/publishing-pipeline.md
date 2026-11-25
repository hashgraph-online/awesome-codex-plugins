---
summary: "Pipeline from source material to a channel post exactly once: content model, rendering, validation, preview, approval, idempotent publish, edits, rate limits, fan-out; read when a bot publishes."
verified: "2026-11-15"
bot_api: "10.4"
---

# Publishing pipeline: from source material to a channel post, exactly once

## Contents

- [1. Content model: structured blocks, never raw HTML](#1-content-model-structured-blocks-never-raw-html)
- [2. Render per format](#2-render-per-format)
- [3. Validate before anything leaves](#3-validate-before-anything-leaves)
- [4. Preview in a private chat](#4-preview-in-a-private-chat)
- [5. Approval step (human in the loop)](#5-approval-step-human-in-the-loop)
- [6. Publish exactly once (idempotency and unknown outcomes)](#6-publish-exactly-once-idempotency-and-unknown-outcomes)
- [7. After publishing: edit, pin, delete, copy, forward](#7-after-publishing-edit-pin-delete-copy-forward)
- [8. Scheduling is the caller's job](#8-scheduling-is-the-callers-job)
- [9. Rate limits and failures](#9-rate-limits-and-failures)
- [10. Mailing to many recipients (FanOut)](#10-mailing-to-many-recipients-fanout)
- [11. Multi-channel and multi-language fan-out](#11-multi-channel-and-multi-language-fan-out)
- [12. Operating checklist for an agent](#12-operating-checklist-for-an-agent)

How an agent operates a bot as a **publisher**: turn source material (a feed item, a CMS
entry, an AI summary) into a channel post and deliver it safely and repeatably. Design of the
post itself: `channel-post-design.md`. Channel rights and updates: `channels-and-broadcasting.md`.

Code: `examples/python/tgkit/publish.py` (model, renderers, validation, `Publisher`,
`FanOut`, `cross_post`), CLI `scripts/tg_post.py`, TypeScript twin
`examples/ts/publishing/publish.ts`, tests `tests/test_publishing.py`. Recipes 30-39.

Tags as in `channel-post-design.md`: **[API]**, **[Guide]**, **[Heuristic]**,
**[Unverified]**; re-read **2026-11-15**, Bot API 10.4 is the newest version on that date.

```
source → content model → render (per format) → validate → preview (private chat)
       → approve (optional) → publish (ledger: pending → sent | unknown)
       → record message_id(s) → edit / pin / unpin / delete / copy / forward
```

## 1. Content model: structured blocks, never raw HTML

Store posts as data (`tgkit.publish.Post`):

```json
{"blocks": [{"type": "heading", "text": "Tram line 4 reopens"},
            {"type": "paragraph", "text": ["Night trams until ", {"bold": "01:00"}, ". ",
                                           {"link": "https://example.com/t4", "text": "Timetable"}]},
            {"type": "table", "header": ["Line", "Until"], "rows": [["4", "01:00"]]}],
 "buttons": [[{"text": "Read the full story", "url": "https://example.com/t4"}]],
 "link_preview": {"url": "https://example.com/t4", "large": true},
 "silent": false, "protect": false}
```

Blocks: `heading`, `paragraph`, `list` (items may be `{"text", "done"}` checklist items),
`quote` (`expandable`, `credit`), `table` (`header`, `rows`, `numeric`, `compact`, `caption`),
`code`, `divider`, `footer`, `document` (rich only). Inline: plain strings, `bold`, `italic`,
`underline`, `strike`, `spoiler`, `code`, `link`. Media: `{"type": "photo"|"video"|"document",
"ref": file_id | https URL | attach://name, "spoiler"}`. Plus `poll`, `stars` (paid media),
`kind` (`auto` by default), `rich_source` (`blocks` | `markdown` | `html`, for rich posts) and
`widget` (an HTML widget used only where the target supports widgets; see
`channel-post-design.md#when-channels-get-widgets`).

Why: one model renders safely to every format; untrusted text (feed titles, user names, model
output) is never parsed as markup **[Heuristic]**; validation runs on data, not on strings.

## 2. Render per format

| Renderer | Output | Use |
|---|---|---|
| `to_entities` | `text` + `entities` (UTF-16 offsets) | **default** for regular posts: no escaping, exact offsets **[API: entities instead of parse_mode]** |
| `to_rich_blocks` | `InputRichBlock[]` | long reads, tables, checklists, documents, embedded buttons **[API]** |
| `to_html` | regular HTML (`parse_mode=HTML`) | compatibility / preview in a CMS; escapes `& < >` and `"` in `href` |
| `to_markdown_v2` | MarkdownV2 | compatibility; escapes all 18 specials; `)` and `\` in URLs |
| `to_rich_html` | `InputRichMessage.html` + `media` | Rich HTML source of the same post (`rich_source: "html"`) |
| `to_rich_markdown` | `InputRichMessage.markdown` + `media` | Rich Markdown source (`rich_source: "markdown"`); HTML tags for features without Markdown syntax |

Every renderer refuses link URLs other than `http(s)://` and `tg://` (no `javascript:`).
`resolve_kind()` chooses text / rich / photo / album / poll / paid media / widget (rules in
`channel-post-design.md#choosing-the-format-per-post-type`).

**Authoring format of a rich post** (`InputRichMessage` takes exactly one of `blocks`,
`html`, `markdown` **[API]**; files referenced as `tg://document?id=…` go in `media` **[API]**):

| Source | Best for in an automated pipeline | Watch out |
|---|---|---|
| `blocks` (default) | posts generated from data, a CMS AST, model output parsed into the content model | verbose JSON; nothing to escape |
| Rich HTML | server templates, CMS exports; every feature has a tag (`<table compact>`, `<blockquote expandable>`, `<tg-button-row>`) | one escaper: `& < >`, plus `"` in attributes |
| Rich Markdown | text people or a model write and review (short diffs) | needs HTML tags for compact tables, expandable quotes, credits, footers, buttons; escaping beyond the documented `\#` follows CommonMark practice **[Unverified]** |

R31 sends the same long read in all three forms.

**Decoration hook.** `plan(..., decorate=fn)` and `Publisher(..., decorate=fn)` accept an
optional `fn(post, context) -> Post` (default: none). It runs before validation and planning,
on a copy of the post. Use it for cross-cutting additions owned elsewhere, e.g. premium custom
emoji from the custom emoji stream (`references/emoji-in-posts.md`) — eligibility is still
enforced by `validate()`. The ledger stores the undecorated source post.

## 3. Validate before anything leaves

`validate(post, context="channel")` returns errors and warnings; `assert_valid()` raises.
Checks: text 4096 / caption 1024 / rich 32768 chars, 500 blocks, 50 media, 20 columns; album
2–10 and type mixing; poll limits and channel-only fields; paid media 1–25000 Stars, ≤ 10
items, payload ≤ 128 bytes; one action per button, `callback_data` 1–64 bytes, URL schemes,
`style` values, buttons illegal in the context (web_app, inline-query switches, pay, game),
custom emoji eligibility; media refs (file_id, URL, `attach://`; local paths are refused);
entity offsets inside the UTF-16 text **[API limits]**. Warnings: first line > 120 chars,
several `primary` buttons, preview requested for a rich post **[Heuristic]**.

CLI: `py -3 scripts/tg_post.py validate post.md`.

## 4. Preview in a private chat

`plan(post, chat_id)` returns the exact request list. Send the same plan to the editor's
private chat (`chat_id` = the editor's user id) — what they see is what the channel gets,
byte for byte (R31, R35). CLI dry run prints the payloads:
`py -3 scripts/tg_post.py preview post.json --chat @your_channel`.

Preview limits: a private chat renders a post the same way as a channel for text, media and
rich messages **[Unverified per client]**; it does not show channel-only things (signature,
view counter, comments button). Rendering on real Android/iOS/Desktop/Web clients is never
proven by JSON (`testing-playbook.md`).

## 5. Approval step (human in the loop)

R35 `ApprovalDesk`: preview + a control message `[Approve and publish] [Edit text] [Reject]`
in the editor's private chat. Rules:

* `callback_data` carries draft id **and version** (`pub:approve:d42:2`): a tap on an old
  preview can't publish outdated text **[Heuristic]**.
* Allow-list editors on the server; answer every callback (`answerCallbackQuery`) **[API]**.
* Approve calls `Publisher.publish()` with key `draft:<id>:v<version>`: a double tap posts once.
* Edit asks for the new text with `force_reply` and re-previews as the next version.
* After publishing, the control message becomes a link `https://t.me/<channel>/<message_id>`.

## 6. Publish exactly once (idempotency and unknown outcomes)

`Publisher.publish(post, chat_id, key)`:

1. Ledger says `sent` → return `already_sent`, **no request**.
2. Ledger says `pending` / `unknown` / `partial` → return `unknown`, **no request**: the
   previous attempt may have been delivered.
3. Otherwise write `pending` **before** the request (write-ahead), send each planned request
   through `call_with_policy`, record every `message_id`, mark `sent`.
4. A timeout or connection reset after the body left (`OutcomeUnknown`) → `unknown`. A send is
   never repeated automatically **[API semantics: send* is not idempotent]**.
5. A Telegram error before anything was posted → `failed` (a later run may retry); after some
   parts were posted → `partial` (finish or delete by hand).

**Key** = a stable id of the logical post per target: feed `guid`, CMS id + version, draft
version, `campaign:recipient`. Never a timestamp.

**Reconcile** (`Publisher.reconcile(key, found_message_ids=…)`): resolve `unknown` with
evidence — an operator looked at the channel, or a `channel_post` update with the post's text
arrived. Found → `sent`; confirmed absent → the record is dropped and publishing may run again.
The Bot API has **no method to search a channel's history** **[API: absence]**; whether a bot
receives `channel_post` updates for its **own** posts is **[Unverified]** (the FAQ says bots
get "all messages from channels where they are a member" **[Guide]**).

Ledger storage: the `Ledger` class is in memory or a JSON file (atomic replace); production
code keeps the same records in its database, keyed uniquely.

**Server-scheduled video**: a returned `message_id` of `0` means the server will post later
(large channels, re-encoding) **[API]**; the record gets `server_scheduled: true`.

## 7. After publishing: edit, pin, delete, copy, forward

| Need | Call | Facts |
|---|---|---|
| Fix text | `editMessageText` (`text`/`entities` or `rich_message`) | rich edits since 10.1 **[API]**; edits keep views, reactions and comments **[Heuristic]** |
| Fix caption | `editMessageCaption` | album: edit the first item's caption **[Heuristic]** |
| Swap media | `editMessageMedia` | albums: same family only (audio→audio, document→document, photo/live photo/video otherwise) **[API]** |
| Buttons only | `editMessageReplyMarkup` | **[API]** |
| Close a poll | `stopPoll` | a sent poll can't be edited otherwise **[API]** |
| Pin / unpin | `pinChatMessage` / `unpinChatMessage` | channel: `can_edit_messages`; no pin notifications in channels **[API]** |
| Delete | `deleteMessage` / `deleteMessages` (1–100 ids) | only < 48 h old; `can_post_messages` deletes own posts, `can_delete_messages` any **[API]** |
| Cross-post identical | `copyMessage` / `copyMessages` | no link to the original; can't copy service, paid media, giveaway, invoice, widget messages; quiz only if `correct_option_ids` known; returns only `MessageId` **[API]** |
| Cross-post with attribution | `forwardMessage(s)` | fails for protected content **[API]** |

`Publisher.edit()` compares a fingerprint of the new post with the stored one and sends
**nothing** when unchanged; when the plan has the same methods it edits only the parts whose
payload changed; when the layout changes (kind, part count) it returns `repost_required`.
`decide_correction()` (R39): unchanged → nothing; same layout → edit; layout change on a
young post (default < 15 min) → delete + repost; otherwise a correction note replying to the
original. Paid and approved suggested posts are never edited **[API]**.

## 8. Scheduling is the caller's job

The Bot API has **no scheduled-send method** for bots **[API: absence, 2026-11-15]**. Run the
publish step from a scheduler (cron, a job queue, a cloud scheduler) and keep the idempotency
key, so a scheduler that fires twice still posts once. Exceptions in the API:
`approveSuggestedPost.send_date` and `SuggestedPostParameters.send_date` (suggested posts in
channel DM chats, ≤ 30 days) **[API]**; `sendPoll.close_date` / `open_period` close a poll on
time **[API]**.

## 9. Rate limits and failures

* Bots FAQ **[Guide]**: in one chat avoid more than 1 message per second; in a group at most 20
  messages per minute; bulk notifications ~30 messages per second. Paid broadcasts
  (`allow_paid_broadcast`, enabled in @BotFather) allow up to 1000/s for 0.1 Star per message
  over the free amount **[API, Guide]**.
* `429` carries `retry_after`: wait at least that long, never retry early, never loop tightly;
  a wait longer than the policy's `max_wait` defers the run instead of sleeping
  (`tgkit.errors.call_with_policy`) **[API + Heuristic]**.
* Multi-part posts to one channel: parts are sequential; later parts are silent.

## 10. Mailing to many recipients (FanOut)

`FanOut(transport, per_second=25).run(campaign, jobs)` (R37):

* throttles below the ~30/s ceiling **[Guide]**; `429` honoured per call;
* one bad recipient never stops the batch: `403` → `blocked` (never retried), `400` →
  `invalid` (fix the payload; retried next run), timeout → `unknown` (not resent), long flood
  wait → `deferred` (reschedule the rest);
* key `campaign:recipient` in the ledger: a re-run skips what already went out;
* personalization through the content model (names as plain text + entities).

## 11. Multi-channel and multi-language fan-out

`cross_post(publisher, post, targets, key)` (R36): one logical post, one key per target
(`key@chat_id`), per-target `changes` (translated blocks, button labels, a different URL).
A failed target is retried by the next run; sent targets are skipped. Identical copies to a
partner channel: `Publisher.copy_to()` (copyMessage with its own `reply_markup`).

## 12. Operating checklist for an agent

1. Confirm the bot is an admin of the channel with `can_post_messages` (and
   `can_edit_messages` to edit/pin, `can_delete_messages` to moderate)
   (`getChatMember(channel, bot_id)`) **[API]**.
2. Build the post as a content model; never paste model output as HTML.
3. `validate` → fix errors; read warnings.
4. Preview to an editor's private chat; wait for approval when the workflow has one.
5. Publish with a stable key; store the returned ids.
6. On `unknown`: stop and reconcile; never "just retry".
7. Later changes go through `edit` (no-op when unchanged) or `decide_correction`.
8. Live runs only with a test bot / test channel first, token from an environment variable
   name, dry run by default (`scripts/tg_post.py publish … --live`).
