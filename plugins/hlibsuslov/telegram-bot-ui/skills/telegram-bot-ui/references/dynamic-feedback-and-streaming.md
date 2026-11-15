# Dynamic feedback: streaming, progress, and loaders

A bot cannot animate arbitrary UI frame by frame. What "animation" actually
means in a Telegram chat is one of these:

- text appearing progressively (`sendMessageDraft`, `sendRichMessageDraft`);
- one message being edited in place (`editMessageText`);
- an updating progress bar inside that message;
- the client's own spinner on a tapped inline button (cleared by
  `answerCallbackQuery`);
- a chat action status ("typing", "uploading photo"…);
- an animated temporary draft;
- a GIF / video / sticker / message effect;
- real animation inside a Mini App.

Pick the mechanism from the **shape of the operation**, not from what looks
impressive.

## Decision table

| Situation | Mechanism |
|---|---|
| AI generates a plain-text answer in a private chat | `sendMessageDraft` (+ `can_stop`, 10.3) |
| AI generates a structured answer (headings, tables, collapsibles) | `sendRichMessageDraft` → `sendRichMessage` |
| Short operation, 2–5 s | `sendChatAction` |
| User tapped an inline button | `answerCallbackQuery` **immediately**, then work |
| Operation has real, nameable stages | `editMessageText` with a stage list / progress bar |
| Progress cannot be measured | Named stages — **never** a fake percentage |
| Operation runs in a group | One status message + rare edits, or per-user ephemeral progress (`ephemeral-and-personal.md`) |
| A card that updates in place in a private chat | HTML widget state edits (`widgets.md`) |
| Genuinely interactive process | Mini App with its own progress UI |
| SDK too old for the new methods | Raw Bot API payload, or fall back to edits |
| Client support unknown | Feature flag + plain-text fallback |

## 1–2. Draft streaming and Stop (UX summary)

`sendMessageDraft` (plain) and `sendRichMessageDraft` (structured, with a `<tg-thinking>` stage
block) show a ~30 s animated preview in **private chats** that must be finalized with a real send.
Since **10.3** a draft can offer **Stop** (`can_stop`) and keep the partial preview briefly
(`keep_on_stop`). UX rules:

* Offer Stop on any answer that can take more than a few seconds; decide up front what Stop means
  (discard / keep marked as incomplete / offer Continue) and say it in the final message.
* The thinking block shows **real stages** from a fixed list, never the model's reasoning.
* Keep the final format equal to the draft's (rich stays rich).
* Fallback ladder: rich draft → plain draft → throttled `editMessageText` → chat action + one send.

State machine, throttling, Stop handling, races and addressing: **`streaming-and-editing.md`**.

## 3. Edit-based streaming and progress bars

The pre-9.3 approach, still correct for anything with **real stages**: send a
message, keep its `message_id`, and edit it as the operation advances.

```
Preparing report ░░░░░░░░░░
Preparing report ███░░░░░░░ 30%
Preparing report ███████░░░ 70%
Done ██████████ 100%
```

**Only show a percentage you actually know.** If the number is invented, show
named stages instead:

```
✓ Sources collected
✓ Data compared
⏳ Building the result
```

**Throttling** — never per token; one update per ~1 s at most, coalescing sentences and stages
(full rule and the 429 handling: `streaming-and-editing.md#throttling`).

Telegram's own FAQ states: *"In a single chat, avoid sending more than one
message per second"*, *"In a group, bots are not be able to send more than 20
messages per minute"*, and about 30 messages/second for bulk broadcasts. Those
sentences are about sending, but edits consume the same budget in practice —
throttle them and always honour `retry_after` on 429
(`errors-and-fallbacks.md`).

**Known costs of edit-based streaming** (design around them; treat as
engineering experience, not documented API behaviour): the message can flicker
on some clients, long-lived edited messages keep their original timestamp, error
paths can produce duplicate messages, intermediate tool/debug text can leak into
the chat, and scroll position can jump. Mitigations: throttle, keep exactly one
`message_id` per operation, never emit intermediate text as *new* messages, and
make finalization idempotent.

**Editing an unchanged message** raises `message is not modified` — compare
before editing.

## 4. The native button loader

Tapping an inline button shows the client's own progress indicator. It clears
only when the bot calls `answerCallbackQuery`. So: **answer first, work after.**

```ts
await answerCallbackQuery(cq.id);                       // clears the spinner
await editMessageText({ text: "Processing…" });         // shows our own state
const result = await performLongOperation();
await editMessageText({ text: render(result), reply_markup: finalKeyboard });
```

- Silent answer (no `text`) is fine and is the common case.
- `text` is **0–200 characters**; a toast, not a place for results.
- `show_alert: true` is a modal — reserve it for consequences and confirmations.
- Keep `cache_time` at 0 for anything state-dependent.
- If the work takes more than a moment, immediately edit the screen to a
  "working" state and **disable the buttons that must not be pressed twice** —
  then re-enable/replace them when finished. Server-side idempotency still
  required; the UI is not a lock.

## 5. Chat actions

`sendChatAction` sets a status for **5 seconds or less**, and clients clear it as
soon as a message arrives from the bot. Telegram: *"We only recommend using this
method when a response from the bot will take a noticeable amount of time to
arrive."* Channel chats are not supported.

Actions: `typing`, `upload_photo`, `record_video`, `upload_video`,
`record_voice`, `upload_voice`, `upload_document`, `choose_sticker`,
`find_location`, `record_video_note`, `upload_video_note`. **Pick the one that
matches what the user will actually receive** — `typing` before a photo is a
small lie the client will contradict.

Waiting ladder:

```
0–1 s     : show nothing
1–5 s     : sendChatAction("typing")
> 5 s     : re-send the action every ~4 s, or switch to a status message
long gen. : sendMessageDraft / sendRichMessageDraft
```

## 6. Mini App progress (boundary)

The Mini App's *internal* UI is ordinary web front-end work and out of this
skill's scope. Its **Telegram-side** controls are in scope:

- `Telegram.WebApp.ready()` — *"informs the Telegram app that the Mini App is
  ready to be displayed… Once this method is called, the loading placeholder is
  hidden"*. Call it as early as the essential UI is up.
- `BottomButton` (the class was renamed from `MainButton` in Bot API 7.10; the
  `Telegram.WebApp.MainButton` accessor remains): `showProgress(leaveActive)` —
  *"A method to show a loading indicator on the button… By default, the button
  is disabled while the action is in progress"* — and `hideProgress()`.
  `iconCustomEmojiId` on the button is Bot API 9.5+.

```js
Telegram.WebApp.MainButton.setText("Building the report").show().showProgress();
// … work …
Telegram.WebApp.MainButton.hideProgress();
```

Leave `leaveActive` unset for form submissions — a re-tappable submit button
during submission is a duplicate-order bug.

## 7. Operation lifecycle (apply to every long action)

1. **Classify** the operation: instant / short / long / streaming / measurable /
   unmeasurable.
2. **Acknowledge instantly** — `answerCallbackQuery`, or a chat action.
3. **Hold one identity for the whole run**: one `draft_id`, one preview
   `message_id`, one internal `operation_id`. Never let a retry create a second
   stream.
4. **Report progress honestly** — real percentages or named stages.
5. **Throttle** updates per the rules above.
6. **Finalize atomically**: persist the result → send the final message →
   close/expire the preview → clear the loader → replace the keyboard with the
   final one → make sure no destructive callback is left armed on a stale
   screen.
7. **Fail visibly**: on error, the last thing the user sees must be a real
   message explaining it plus a way forward — never a stalled spinner or an
   evaporated draft.
8. **Verify SDK support** before using drafts or rich drafts
   (`sdk-compatibility.md`); ship the fallback path if it's missing.
9. **Test on Android, iOS, Desktop, and Web** — draft and edit rendering differs
   between clients (`testing-playbook.md`).

## Checklist

- [ ] Mechanism chosen from the decision table, not by preference.
- [ ] `answerCallbackQuery` called before long work, every time.
- [ ] One `draft_id` / `message_id` / `operation_id` per operation.
- [ ] No per-token edits; throttle thresholds implemented and tuned.
- [ ] No invented percentages.
- [ ] Draft finalized with a real message; failure path also ends in a message.
- [ ] Final format matches the streamed format (rich stays rich).
- [ ] `retry_after` honoured; 429s not retried in a tight loop.
- [ ] Fallback ladder implemented and exercised in tests.
