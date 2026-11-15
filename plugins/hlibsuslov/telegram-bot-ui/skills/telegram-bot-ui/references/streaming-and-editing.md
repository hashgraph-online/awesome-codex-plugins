# Streaming, Stop, and editing (engineering)

> Verified 2026-11-12: `sendMessageDraft`, `sendRichMessageDraft`, `MessageGenerationStopped`,
> `editMessageText`. Drafts: Bot API 9.3 (all bots 9.5), rich drafts 10.1, Stop 10.3.
> UX choice of feedback mechanism: `dynamic-feedback-and-streaming.md` (this file does not
> repeat it). Code: `examples/python/tgkit/generation.py` (+ `examples/ts/tgkit.ts`).
> Recipe: [01 AI assistant](../recipes/01-ai-assistant.md).

## Operation state machine

```
STARTED → GENERATING → COMPLETED                      (model finished → final send)
                     → STOP_REQUESTED → STOPPED       (Stop pressed → cancel upstream → policy)
                     → FAILED                         (model/API error → error message + Retry)
                     → TIMED_OUT                      (deadline → cancel upstream → message + Retry)
```
Terminal states never change. Every event (`chunk`, `stage`, `tick`, `stop`, `done`, `error`)
is a no-op after the end: late chunks are dropped (counted), a second Stop does nothing, a Stop
after completion does nothing, a completion after Stop does nothing, a stale timer or deferred
retry can't revive the draft. Cancellation is neither success nor failure.

**One logical finalization** is an application invariant, enforced by the state machine. It is not
a network exactly-once guarantee: a final send that times out has an unknown outcome
(`errors-and-fallbacks.md#unknown-outcome-after-timeout`).

## Stop: can_stop and keep_on_stop

* `can_stop: true` shows the user a Stop button on the draft; pressing it sends the update below.
* `keep_on_stop: true` keeps the draft visible after Stop **for a short time** — it still disappears
  after a while or when the bot sends a message. To keep the partial answer, **send it as a new
  message** (API).
* Pass both on every draft call (the docs don't say they persist between updates; repeating is safe).

Partial-result policy (product choice, decide before streaming):

| Policy | Final message | `keep_on_stop` |
|---|---|---|
| `discard` | "Stopped. Nothing was saved." + Retry | false |
| `keep_marked` | the partial text + footer "stopped — incomplete" + Continue / Retry | true |
| `offer_continue` | "Continue from here or start over?" (partial kept server-side with a TTL) | false |

## Receiving the Stop update

`Update.stopped_message_generation` → `MessageGenerationStopped{chat, message_thread_id?, draft_id}`.
Find the operation by `(chat.id, message_thread_id or 0, draft_id)`; unknown → ignore and log.
Then: cancel the upstream model (stop spending tokens), drop queued chunks, cancel timers.
Subscribe explicitly (`allowed_updates` includes `stopped_message_generation`; it is sticky) and
check the SDK routes it (`sdk-compatibility.md`).

`draft_id`: non-zero, one per operation, never reused for another operation in the same chat/topic.

## Throttling

Flush a draft when (new text ≥ ~40 chars **or** a sentence ended **or** a real stage changed)
**and** ≥ ~1 s since the last draft **and** after any `retry_after`. A finished sentence never
bypasses the interval — coalesce. A 429 on a draft drops that draft (the next one carries newer
text) and pushes the next flush past `retry_after`. Numbers are heuristics, not API limits.

Thinking/progress: `<tg-thinking>` / `{"type":"thinking"}` only in rich drafts, filled from an
**allowlist of real stage labels** (searching, reading, writing) — never the model's reasoning,
prompts, tool arguments or internal ids.

## Finalization

Completed → `sendRichMessage` (no thinking block; same structure as the draft). Validation error
on the rich final → **one** fallback to `sendMessage` with the same text, chat and thread; never a
loop of formats. Failure/timeout → a real message with Retry, never a vanished draft.

## Addressing drafts

Drafts go to **private chats** only: `chat_id` + optional `message_thread_id` (topics). Groups
use a status message + throttled edits or ephemeral progress. Rich drafts can't upload new files
or fetch by URL — upload first, reuse `file_id`. See `topics-and-contexts.md`.

## Editing rich content

`editMessageText(rich_message=…)`: re-send `reply_markup` you want to keep; compare before editing
(`message is not modified`); fall back to a new message when not editable; for inline messages
no new uploads/URL uploads. Forum topics use `message_thread_id`; channel DM topics use
`direct_messages_topic_id` — different fields, don't mix them.
