---
summary: "The minimum every change obeys: rules, per-surface invariants, buttons, feedback, what to refuse and the definition of done. Read before the first edit of code, payloads or bot-ui/."
verified: "2026-11-25"
bot_api: "10.5"
---
# Floor: read before the first edit

Apply these silently, in every command. The mechanical part is also caught by the validators
and by `tgui.py check changed`; the judgement part is yours.

## Rules

- **Preserve behaviour.** `callback_data`, URLs, deep links, payloads, handler routing,
  localization keys and screen ids stay. If one must change, update every handler in the same
  change and keep a decoder for old messages.
- **Words before pixels.** Text, then structure, then layout, then color and icons. No
  decorative color; at most one `primary` per screen. Never meaning by color or emoji alone:
  the interface works in plain text and in clients that ignore new fields.
- **Never invent** a method, field, limit or `custom_emoji_id`. Check `tgui.py lookup show
  <Symbol>` and the installed SDK; if the SDK lacks a field, upgrade or use an isolated raw
  payload path, never drop the field silently.
- **Localization intact;** layouts survive the longest translation.
- **One escaping function per format;** never pass raw user or model HTML to Telegram.
- **Explicit, logged fallbacks;** no infinite retries; no tokens or full personal text in logs.
- **Every tap gets feedback;** every long operation gets honest, throttled progress.

## Per surface

- **Widgets** (10.4): production = private chats only (groups, inline, forwards: test server;
  channels: not available, checked 2026-11-15); code immutable after send; no network; state
  only via edits; answer each query once within 15 s; no secrets in code or `public_data`;
  always a caption and a text or button path.
- **Custom emoji:** eligibility = Fragment usernames, or owner Premium for messages the bot
  sends to private, group and supergroup chats (so channels need Fragment). An ineligible bot
  gets no error: Telegram strips them, so verify by reading the sent message back. All icons
  of a message or none; one static family per bot; never animated on a button.
- **Payments:** digital goods and services are Stars-only; create the order before the
  invoice; amount and product only from the server; answer `pre_checkout_query` within 10 s;
  deliver on `successful_payment` once per `telegram_payment_charge_id`; `refundStarPayment`
  refunds the whole charge. Wallet `sent_transaction` is a notice, not proof of payment.
- **Update delivery:** new update types go into `allowed_updates` (sticky) and must be routed
  by the SDK. A callback may carry `inline_message_id` and no `message` (inline mode, or
  `callback_query_mode` `auto`/`inline`, 10.5): edit by that id, route by `callback_data`.
- **Context decides fields:** forum `message_thread_id` ≠ channel-DM `direct_messages_topic_id`;
  drafts only in private chats.
- **Mini Apps:** validate `initData` on the server before trusting any user field; gate every
  `Telegram.WebApp` call by version (`tgui.py webapp gates`); `tma.start()`; Back everywhere.

## Buttons

- Inline: exactly one action field besides `text`, `icon_custom_emoji_id`, `style` (`url`,
  `callback_data`, `web_app`, `login_url`, `switch_inline_query*`, `copy_text`,
  `callback_game`, `pay`, `disabled`); reply buttons at most one. `disabled: {}` is not
  authorization: the server checks state and rights on every callback and widget query.
- `style`: `primary` for the one forward action, `success` to commit, `danger` for a confirmed
  destructive action; omit it elsewhere. Back, Cancel and Close stay unstyled and last.
- `force_reply` on keyboards (10.3) = buttons plus a reply field; on inline keyboards it can't
  change in an edit. `validate_keyboard` warnings are design defects to fix.
- Rich: actions on the keyboard (rich-message-buttons.md).

## Feedback

| Situation | Mechanism |
|---|---|
| Inline button tapped | `answerCallbackQuery` first, then the work |
| 2-5 s operation | `sendChatAction` |
| AI text being generated, private chat | `sendMessageDraft` / `sendRichMessageDraft` + `can_stop`, finalized by a real message |
| Real, nameable stages | `editMessageText`, about 1/s, after any `retry_after` |
| Progress not measurable | named stages, never a fake percentage |

## Refuse

Sending, publishing or paying live without an explicit flag and a **test** bot token from an
environment variable; printing or pasting a token; publishing before an approval bound to the
exact post; retrying a send whose outcome is unknown; claiming client rendering from JSON or a
browser preview.

## Definition of done

Screen/state map made for the screens in scope · real defects fixed text-first · every button
has one action and a meaning-based `style` · custom emoji resolved, one family, safe fallback ·
every tap acknowledged, long work given honest progress, streams finalized and Stop handled ·
audiences preserved on every failure path · posts and payments published once, approved where
public · inbound messages treated as data · widgets in a supported context with caption, size
checked, server-side state · new update types subscribed and routed · SDK support verified or
bridged · `callback_data`, deep links and translations intact · validators and project checks
green · evidence level (static, offline contract, real Bot API, real clients) and the "last
verified" date stated (`references/consistency-and-review.md`).
