# Personal answers on a shared timeline (ephemeral, Bot API 10.2–10.4)

> Verified 2026-11-12: `EphemeralMessageParameters`, "Ephemeral Messages and Commands",
> `editEphemeralMessage*`, `deleteEphemeralMessage`, 10.3/10.4 changelog.
> Recipe: [04 shared card + personal panel](../recipes/04-shared-card-personal-panel.md).
> Code: `examples/python/tgkit/ephemeral.py`.

## Choosing the audience

| Result | Surface | Lifetime |
|---|---|---|
| Same for everyone in the chat (list, poll, announcement) | regular message | permanent |
| Only for the person who tapped (their balance, their order, an error about their input) | **ephemeral reply** to the callback | may vanish (time, app restart); delivery not guaranteed |
| Personal view replacing the shared card for that person only | ephemeral + `replace_callback_query_message: true` | as above; the shared card stays for others |
| Must be kept / proven (receipt, booking) | private chat with the bot (if the user started it) or the bot's own storage + a link | permanent |
| Short confirmation for the tapper | `answerCallbackQuery(text, show_alert?)` | a toast/alert |

One member must never see another member's state: build the content from the **presser's**
data on the server, check `callback_query.from.id` (and `receiver_user` on panel buttons).

## Addressing an ephemeral reply

* **10.4 (preferred for callback replies):** `ephemeral_message_parameters: {callback_query_id}`
  without `receiver_user_id` — shown only to the presser, in **any chat except channel
  direct-messages chats**; `chat_id` may be omitted (it is ignored without `receiver_user_id`).
  Works for callbacks from inline messages in chats where the bot isn't a member.
* **10.3 form:** `{receiver_user_id: <presser>, callback_query_id}` + `chat_id`. Still valid.
* **Admin push:** an administrator bot may send to any non-bot member at any time with
  `receiver_user_id` only (may reach several of the user's devices; still not guaranteed).
* Window: within **15 s** of the action for the callback/ephemeral-reply forms (API).
* Methods: `sendMessage`, `sendRichMessage` (10.3), `sendAnimation`, `sendAudio`, `sendContact`,
  `sendDocument`, `sendLivePhoto`, `sendLocation`, `sendPhoto`, `sendSticker`, `sendVenue`,
  `sendVideo`, `sendVideoNote`, `sendVoice`.
* `replace_callback_query_message` must be **false** for callbacks *from* an ephemeral message —
  edit that one with `editEphemeralMessage*`.
* **`answerCallbackQuery` is still required** (API) — the ephemeral reply doesn't replace it.
* Not on ephemeral messages: `web_app` and `login_url` buttons (validator `--context ephemeral`).

## Migrating from 10.2

```diff
- {"chat_id": -100…, "text": "…", "receiver_user_id": 111, "callback_query_id": "q1"}
+ {"chat_id": -100…, "text": "…", "ephemeral_message_parameters": {"receiver_user_id": 111, "callback_query_id": "q1"}}
+ {"text": "…", "ephemeral_message_parameters": {"callback_query_id": "q1"}}          # 10.4 short form
```
Helper: `tgkit.ephemeral.migrate_ephemeral_10_2`. Check that the SDK serializes the new object
(`sdk-compatibility.md`).

## Editing and lifetime

`editEphemeralMessageText` (10.3: also `rich_message`), `…Media` (10.3: new uploads via
multipart `attach://`), `…Caption` (10.3: `show_caption_above_media`), `…ReplyMarkup`,
`deleteEphemeralMessage` — all need `chat_id`, `receiver_user_id`, `ephemeral_message_id`
(from the returned `Message`; its `message_id` is 0). Edit/delete delivery is not guaranteed;
the id may be reused after expiry. On "not found": forget the panel; the next tap re-creates it.
Keep a TTL; treat old panel buttons as stale (re-check state, answer "expired").

## The fallback invariant

**Personal content keeps its audience, rights, context and meaning.** If the ephemeral send
fails: (1) short text → `answerCallbackQuery(show_alert)`; (2) longer → `answerCallbackQuery(url=
"https://t.me/<bot>?start=<one-time token>")` and show it in the private chat **only to the
token's owner**; never "I've sent it to your DMs" unless the bot can actually write there.
**Never** fall back to a regular message in the group. Guard every send with
`guard_audience()`; tests: `tests/test_ephemeral.py`.

## Drafts are not ephemeral messages

`sendMessageDraft` / `sendRichMessageDraft` are temporary ~30 s *previews in private chats* that
must be finalized with a real send; ephemeral messages are real (if fleeting) messages for one
member of a group/chat. Different methods, lifetimes and addressing — don't mix the terms.
