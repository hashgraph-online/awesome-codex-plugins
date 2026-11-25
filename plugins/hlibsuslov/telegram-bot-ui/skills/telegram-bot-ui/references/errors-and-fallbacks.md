---
summary: "Degradation ladders for content and interface, failure classification, rules, old clients, the can't-parse-entities response, unknown outcomes; read when designing error handling and fallbacks."
verified: "2026-11-15"
bot_api: "10.5"
---

# Errors, fallbacks, and old clients

## Degradation ladders (adapt to the project — not a universal mandate)

Content:

```
Explicit rich blocks
  → Rich HTML or Rich Markdown
    → Regular HTML or MessageEntity
      → plain text
```

Interface:

```
styled + custom-emoji buttons
  → styled buttons (style only)
    → plain buttons (text + action only)
      → text instructions / commands
```

Feedback:

```
sendRichMessageDraft
  → sendMessageDraft
    → throttled editMessageText
      → sendChatAction + one final message
```

Fall back one step at a time, only for the failure classes that warrant it. The
right ladder depends on the project: some flows should surface an error instead
of degrading (e.g. a payment receipt must not silently become plain text).

## Classify the failure before reacting

| Class | Signal | Reaction |
|---|---|---|
| Validation error (your payload) | 400 `can't parse entities`, bad offset, unclosed tag, malformed blocks, over-limit | Fix the payload; degrade a format step; do **not** retry unchanged |
| Unsupported SDK/API capability | missing type/method, older Bot API | Use a supported format or the adapter (`sdk-compatibility.md`); degrade |
| Telegram 400 (other) | e.g. `message is not modified`, invalid media | Handle specifically (skip edit / fix media); don't blind-retry |
| Telegram 403 | bot blocked / no rights | Stop for that chat; surface; do not retry in a loop |
| Telegram 429 | rate limited, `retry_after` | Back off for `retry_after`, then retry once/limited |
| Unknown outcome | timeout / reset **after** the request was sent | Edits/answers: bounded retry. Sends: **don't** repeat blindly — reconcile (below) |
| Telegram 5xx | server error | Bounded retry with backoff |
| Permissions | can't send type in chat/topic | Surface; adjust or skip |

## Rules

- **Differentiate** the classes above — never treat all failures the same.
- **Some failures are not errors.** Telegram silently drops content a bot may not send —
  custom emoji are the known case. Read the returned object back and compare it with what
  was sent; a clean `try` block is not evidence that anything arrived as intended.
- **No infinite retries.** Bound retries and honor `retry_after`.
- **No silent fallback.** Log that a fallback happened and why (without dumping
  bot token or full personal text).
- **No error suppression.** Swallowing exceptions hides real defects.
- **Never show raw exception text to users.** An HTTP client error raised while downloading a
  Telegram file carries the request URL, and that URL holds the bot token
  (`https://api.telegram.org/file/bot<token>/…`): `f"Error: {e}"` in a reply, caption or widget
  answer sends the token to the user. Map exceptions to your own sentences; if a reason must be
  shown, replace URLs and the token first. `TimeoutError` has an empty `str()`: name it yourself.
  Logs leak the same way: loguru's default `diagnose=True` prints local variables (those URLs)
  in tracebacks, so use `diagnose=False` in production and never log full Bot API URLs.
- On split sends, a failed part must not silently drop the remaining parts.
- Retrying a **validation** error unchanged is pointless — change the payload
  (fix escaping/offsets/limits) or degrade the format.

## UI-specific failure modes

| Symptom | Likely cause | Response |
|---|---|---|
| Buttons render but have no color | SDK dropped `style` before the request, or the client predates 9.4 | Inspect the outgoing payload; see `sdk-compatibility.md` |
| 400 on a button payload | Two action fields on one inline button, or an invalid `style` value | `style` ∈ {`primary`,`success`,`danger`}; exactly one action field |
| 400 mentioning custom emoji | A bogus ID, or a malformed entity offset | Verify the ID with `getCustomEmojiStickers`; recount offsets in UTF-16 |
| Custom emoji missing, **no error at all** | Bot not eligible: Telegram strips the entities and returns `ok: true` (live test, 2026-08-05) | Read the sent `Message` back (`silently_stripped`); degrade explicitly and say why (`custom-emoji.md`) |
| `callback_data` rejected | Over **64 bytes** (bytes, not characters) | Shorten the payload; move state server-side |
| `message is not modified` | Edit with identical text *and* markup | Compare before editing; skip the no-op |
| Spinner never stops on a button | `answerCallbackQuery` not called | Answer first, then work |
| Old message's button acts on stale data | No server-side state re-validation | Re-check state on every callback; disable finished keyboards |
| Streamed draft vanished, nothing left | Draft expired without a final `sendMessage` | Always finalize — including on the error path |

## Old and inconsistent clients

`style` and `icon_custom_emoji_id` are presentation fields. A client that
doesn't know them shows a normal button with the same label and the same action
— which is exactly why the label must carry the full meaning
(`buttons-and-styles.md`). Design for that baseline first, then add the
enhancement.

Assume nothing about rendering parity across Android, iOS, Desktop, and Web —
especially for newer surfaces (rich drafts, thinking blocks, ephemeral message
edits). Where behaviour matters, put it behind a feature flag with a plain-text
fallback and verify on each platform (`testing-playbook.md`).

## `can't parse entities` — first response

Almost always a payload problem: wrong escaping for the chosen parse_mode, an
unclosed/unknown tag, a broken link, or (for entities) a wrong UTF-16 offset.
Fix the payload; don't just retry. See `security-and-escaping.md` and
`testing-playbook.md` regression cases.

## Fallback design

- Build the fallback **once, explicitly**, and test it.
- Keep the fallback path safe (same escaping discipline).
- Preserve keyboards, reply/topic context, and meaning through the fallback.
- A degraded **button** keeps its label and its action — only `style` and the
  icon may be dropped. Never fall back by removing the button.
- Decide per message class whether to **degrade** or **fail loudly**.

## Unknown outcome after timeout

A timeout does not prove the message wasn't delivered; a bounded retry of a send can still create
a duplicate. Per message class: **AI answer / notification** — one logged retry is acceptable
(a rare duplicate beats a lost answer); **order, payment, booking, anything counted** — never
re-send; mark the operation "unknown", show the user the server-side state, and let an idempotent
backend (keyed by operation id) decide. Edits and `answer*` calls are safe to retry
(`message is not modified` = done). 429: wait `retry_after` (or back off ≥ 1 s), bounded attempts,
never a tight loop. Code: `examples/python/tgkit/errors.py` (`call_with_policy`); tests:
`tests/test_errors_and_delivery.py`.

## Audience-preserving fallback

A fallback keeps the **audience, available actions, context and meaning** of the original. A
personal (ephemeral) answer never falls back to a public message; a widget falls back to its caption
plus keyboard, not to a different chat; a rich final falls back once to plain text in the same
chat/thread. A server `ok` doesn't prove the client displayed the feature — keep labels and captions
self-sufficient. Log the fallback class, never tokens or personal text
(`ephemeral-and-personal.md#the-fallback-invariant`).

