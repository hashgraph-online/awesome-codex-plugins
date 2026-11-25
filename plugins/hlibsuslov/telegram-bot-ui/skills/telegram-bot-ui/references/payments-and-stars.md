---
summary: "Payments and Telegram Stars: lifecycle and server state, subscriptions, paid media, refunds and the Star ledger, provider payments, rights, errors; read when a bot sells anything."
verified: "2026-11-25"
bot_api: "10.5"
---

# Payments and Telegram Stars

## Contents

- [What it is for](#what-it-is-for)
- [Lifecycle and the state your server must keep](#lifecycle-and-the-state-your-server-must-keep)
- [Subscriptions (bot features)](#subscriptions-bot-features)
- [Paid media](#paid-media)
- [Refunds and the Star ledger](#refunds-and-the-star-ledger)
- [Physical goods (provider payments)](#physical-goods-provider-payments)
- [Rights, availability and obligations](#rights-availability-and-obligations)
- [What the user sees](#what-the-user-sees)
- [Common mistakes](#common-mistakes)
- [Error handling](#error-handling)

Selling digital goods and services (Stars, `XTR`), physical goods (a payment
provider), subscriptions, paid media, refunds and the bot's own Star ledger.
Checked against Bot API 10.5 on **2026-11-25** (10.5 changed nothing in payments; every type and method named
here is in the 10.5 catalog): https://core.telegram.org/bots/api#payments
and https://core.telegram.org/bots/payments-stars. Look up any shape offline with
`py -3 scripts/tg_api_lookup.py show <name>`; every JSON block below passes
`scripts/validate_payload.py`. The whole pipeline across both rails (rail choice, states,
refunds, reconciliation, screens and microcopy, runtime `tgkit/payments.py`):
`payments-pipeline.md`.

Labels: **[API]** = stated in the Bot API spec; **[Official]** = Telegram's payments
guide or terms; **[News]** = press or announcements, not an official spec;
**[Heuristic]** = this skill's design advice; **[API: absence]** = the spec is silent on it;
**[Unverified]** = not confirmed by any source yet.

## What it is for

| Goal | Mechanism |
|---|---|
| One-off digital purchase (credits, a PDF, a premium chat answer) | `sendInvoice` / `createInvoiceLink` with `currency: "XTR"` |
| Monthly access to a bot feature | `createInvoiceLink` with `subscription_period: 2592000` |
| Monthly access to a channel | `createChatSubscriptionInviteLink` (channel admin rights; see `chat-administration.md`) |
| Photos/videos visible after payment | `sendPaidMedia` |
| Physical goods, shipping | `sendInvoice` with `provider_token`, a real currency, `need_shipping_address`, `is_flexible` |
| Money back | `refundStarPayment` |
| Reconcile what was paid | `getStarTransactions`, `getMyStarBalance` |

- **[Official]** Digital goods and services sold inside Telegram apps must be paid in
  Telegram Stars (`XTR`); third-party providers and crypto are not allowed for them
  (app-store rules). Physical goods may use providers and real currencies.
- **[News, 2026-11-17]** Telegram reminded bot and Mini App developers: bot subscriptions,
  paid tools, access to third-party AI models and credits for them are Stars-only; in-app
  card payments for digital services go away. Exception named: VPN bots in "authoritarian
  countries". No effective date or sanctions given. When asked for Gram or a card for a
  digital product, warn first and design the Stars path (`payments-pipeline.md` §1,
  `check_rail()`).
- **[API]** Gram (ex-Toncoin) is not an invoice currency: `currency` is `XTR` or an ISO 4217
  code. Gram payments go through the widget wallet flow (`wallet-and-ton.md`).
- **[API]** For Stars, `provider_token` is an empty string or omitted, and `prices`
  must contain **exactly one** item. `need_*`, `send_*_to_provider` and `is_flexible`
  are ignored for Stars.

## Lifecycle and the state your server must keep

```
sendInvoice / createInvoiceLink ──► user taps Pay ──► Update.pre_checkout_query
     (payload = your order id)                          │ answer within 10 s
                                                        ▼
                                  answerPreCheckoutQuery(ok=true|false, error_message)
                                                        │
                                                        ▼
                              Message.successful_payment  ──► deliver, store charge id
                                                        │
                              (later) refundStarPayment ──► Message.refunded_payment
```

1. **Create an order row before the invoice** (`order_id`, user, item, price, status
   `pending`) and put the `order_id` in `payload` (1-128 bytes, never shown to the
   user). **[API]** for the limit; **[Heuristic]** for the row.
2. **`pre_checkout_query`** — **[API]** the bot must answer within **10 seconds**, or the
   payment is cancelled. Check the order still exists, the price still matches
   `total_amount`, stock/quota is available. Answer `ok: false` with a human
   `error_message` when not. Do slow work *after* answering.
3. **`successful_payment`** — **[Official]** deliver **only** after this message;
   answering the pre-checkout query does not guarantee a payment. Store
   `telegram_payment_charge_id` (needed for refunds and subscription edits) and mark
   the order `paid` **idempotently**: the same charge id must never deliver twice.
4. **Refund** — `refundStarPayment(user_id, telegram_payment_charge_id)` returns `True`: mark the
   order `refunded`, revoke access. The API defines a `refunded_payment` service message, but does not
   say this call produces one **[Unverified]**; treat it as a confirmation if it arrives.
5. **[Official]** A multi-use invoice (sent to a group/channel, forwarded, inline) can be
   paid many times by many users. Your pre-checkout check is the only gate: decide
   per payment whether the order can still be fulfilled.

### Example: a Stars invoice

```json
{"method": "sendInvoice", "params": {
  "chat_id": 111111111,
  "title": "50 AI credits",
  "description": "Credits for longer answers and image generation. Valid for 12 months.",
  "payload": "order:8f2c1e",
  "currency": "XTR",
  "prices": [{"label": "50 credits", "amount": 250}],
  "photo_url": "https://example.com/img/credits-50.png",
  "reply_markup": {"inline_keyboard": [[{"text": "Pay ⭐250", "pay": true}], [{"text": "Terms", "callback_data": "terms"}]]}
}}
```

- **[API]** `amount` is an integer in the smallest units; for `XTR` that is whole Stars.
- **[API]** With a custom `reply_markup`, the **first button must be a Pay button**; empty
  markup shows one "Pay total price" button. Pay buttons are inline-only and must be
  first in the first row (`scripts/validate_keyboard.py` checks this).
- **[API]** `start_parameter` empty → forwarded copies keep a Pay button (multi-chat
  invoice); non-empty → forwards show a deep-link URL button instead.

### Example: the pre-checkout update and its answer

```json
{"update_id": 900000101, "pre_checkout_query": {
  "id": "4382bfdwdsb323b2d9",
  "from": {"id": 111111111, "is_bot": false, "first_name": "Olena", "language_code": "uk"},
  "currency": "XTR",
  "total_amount": 250,
  "invoice_payload": "order:8f2c1e"
}}
```

```json
{"method": "answerPreCheckoutQuery", "params": {"pre_checkout_query_id": "4382bfdwdsb323b2d9", "ok": true}}
```

```json
{"method": "answerPreCheckoutQuery", "params": {
  "pre_checkout_query_id": "4382bfdwdsb323b2d9", "ok": false,
  "error_message": "Цей пакет щойно закінчився. Спробуйте пакет на 100 кредитів."
}}
```

### Example: the successful payment message

```json
{"update_id": 900000102, "message": {
  "message_id": 77, "date": 1763190000,
  "chat": {"id": 111111111, "type": "private", "first_name": "Olena"},
  "from": {"id": 111111111, "is_bot": false, "first_name": "Olena"},
  "successful_payment": {
    "currency": "XTR", "total_amount": 250, "invoice_payload": "order:8f2c1e",
    "telegram_payment_charge_id": "stxAbCdEf123", "provider_payment_charge_id": "stxAbCdEf123"
  }
}}
```

## Subscriptions (bot features)

- **[API]** `createInvoiceLink` with `subscription_period` creates a recurring Stars
  invoice link; the period must currently be **2592000** (30 days), currency `XTR`,
  price at most 10000 Stars. Any number of subscriptions can be active, including
  several from one user. `sendInvoice` has no `subscription_period` — subscriptions
  are links (send the link in a URL button or a Mini App `openInvoice`).
- **[API]** Each renewal produces a `successful_payment` with `is_recurring: true`
  (`is_first_recurring` on the first) and `subscription_expiration_date`.
- **[API]** `Update.subscription` (`BotSubscriptionUpdated`, Bot API 10.2) reports
  `state` = `canceled` (user cancelled), `active` (re-enabled) or `failed` (renewal
  payment failed). It is part of the default update set; when you pass an explicit
  `allowed_updates` list, include `"subscription"` in it.
- **[API]** `editUserStarSubscription(user_id, telegram_payment_charge_id, is_canceled)`:
  `true` stops renewal (access must last to the end of the paid period); `false` only
  **allows the user to re-enable** a subscription the **bot** cancelled: the user turns it back on
  in Telegram, and `Update.subscription` with `state: "active"` confirms it. Until then the
  subscription is still cancelled; never mark it active on the `false` call. A subscription the
  user cancelled in Telegram can be re-enabled only by the user. Remember who cancelled.
- **[API]** `BotSubscriptionUpdated` has only `user`, `invoice_payload` and `state`, no
  charge id. Put the order id in the subscription's payload and find the subscription by it.
- **State**: keep `subscription_id = first telegram_payment_charge_id`, `user_id`,
  `expires_at` (from `subscription_expiration_date`), `state`. Grant access by
  `expires_at`, not by the last update you saw. **[Heuristic]**

```json
{"method": "createInvoiceLink", "params": {
  "title": "Pro plan", "description": "Unlimited answers, priority queue. Renews every 30 days.",
  "payload": "sub:pro:111111111", "currency": "XTR",
  "prices": [{"label": "Pro, 30 days", "amount": 300}],
  "subscription_period": 2592000
}}
```

```json
{"update_id": 900000110, "subscription": {
  "user": {"id": 111111111, "is_bot": false, "first_name": "Olena"},
  "invoice_payload": "sub:pro:111111111", "state": "failed"
}}
```

Interface consequence: when `state` is `failed`, tell the user once, in their
language, what stops working and when (`expires_at`), with one button back to the
plan link. Do not spam on every retry. **[Heuristic]**

## Paid media

- **[API]** `sendPaidMedia(chat_id, star_count 1-25000, media: up to 10 InputPaidMedia)`;
  members: `InputPaidMediaPhoto`, `InputPaidMediaVideo`, `InputPaidMediaLivePhoto`
  (10.0). `payload` 0-128 bytes. In a **channel**, proceeds go to the channel's
  balance; elsewhere to the bot's.
- **[API]** Before payment, receivers see `PaidMediaPreview` (dimensions/duration only);
  after payment `PaidMediaPhoto` / `PaidMediaVideo` / `PaidMediaLivePhoto`.
- **[API]** `Update.purchased_paid_media` (`PaidMediaPurchased`: `from`,
  `paid_media_payload`) arrives only for media with a **non-empty payload** sent by
  the bot in a **non-channel** chat. Channel purchases are visible in
  `getStarTransactions` only.

```json
{"method": "sendPaidMedia", "params": {
  "chat_id": 111111111, "star_count": 25, "payload": "album:kyiv-night",
  "media": [{"type": "photo", "media": "attach://p1"}, {"type": "video", "media": "attach://v1", "supports_streaming": true}],
  "caption": "Kyiv at night — 2 photos, 1 video"
}}
```

(The `attach://` names refer to multipart parts — see `media-and-files.md#uploading`.)

## Refunds and the Star ledger

```json
{"method": "refundStarPayment", "params": {"user_id": 111111111, "telegram_payment_charge_id": "stxAbCdEf123"}}
```

```json
{"method": "getStarTransactions", "params": {"offset": 0, "limit": 100}}
```

- **[API]** `getStarTransactions` returns transactions in chronological order, 1-100 per
  page; page with `offset`. `StarTransaction.id` equals
  `SuccessfulPayment.telegram_payment_charge_id` for incoming user payments and equals
  the original id for refunds. Use it to reconcile; do not rely on updates alone.
- **[API]** `source` (incoming) / `receiver` (outgoing) is a `TransactionPartner`:
  `user` (with `transaction_type`: `invoice_payment`, `paid_media_payment`,
  `gift_purchase`, `premium_purchase`, `business_account_transfer`), `chat`,
  `affiliate_program`, `fragment` (withdrawals, with `RevenueWithdrawalState`),
  `telegram_ads`, `telegram_api` (paid broadcasting: `request_count` billed requests),
  `other`.
- **[API]** Amounts can have a fractional part: `StarAmount` / `StarTransaction` carry
  `nanostar_amount` (1/10⁹ Star). Store both integers; never floats.
- **[API]** `refundStarPayment` takes only `user_id` and `telegram_payment_charge_id`: a Stars
  refund is always the **whole** payment. "Refund half" is impossible; offer the whole
  refund or a goodwill credit. Gram refunds are outgoing transfers instead (`wallet-and-ton.md`).
- **[API]** For `invoice_payment` transactions `TransactionPartnerUser` can carry
  `invoice_payload` (and `subscription_period`), a second key to match against orders.
- **[API]** Chargebacks at Apple/Google/provider level can debit your balance later; this
  is outside Telegram's control. Reconcile periodically. **[API: absence]** The exact shape of
  a chargeback transaction is not documented on the Bot API or Stars pages; this skill treats an outgoing transaction
  with a known charge id the bot never refunded as a chargeback **[Heuristic]**
  (`payments-pipeline.md` §6).
- `getMyStarBalance` (9.1) returns the bot's `StarAmount`.

## Physical goods (provider payments)

- `provider_token` from @BotFather, a real ISO 4217 `currency`, several `prices`
  allowed, tips via `max_tip_amount` / `suggested_tip_amounts` (≤4, strictly
  increasing, ≤ max). **[API]**
- `is_flexible: true` + `need_shipping_address: true` → `Update.shipping_query`;
  answer with `answerShippingQuery` (`ok`, `shipping_options` required when ok,
  `error_message` when not). **[API]**
- Provider payments, refunds and chargebacks happen at the provider;
  `refundStarPayment` is Stars-only. **[API]**

```json
{"method": "answerShippingQuery", "params": {
  "shipping_query_id": "sq-1", "ok": true,
  "shipping_options": [{"id": "nova", "title": "Nova Poshta, 1-2 days", "prices": [{"label": "Delivery", "amount": 9000}]}]
}}
```

## Rights, availability and obligations

- No special bot setting is needed to sell for Stars; provider payments need a
  provider connected in @BotFather. **[Official]**
- **[Official]** The bot must answer **`/paysupport`** (payment problems) and offer terms
  (`/terms` or equivalent) and support. Telegram's support does not handle your
  disputes.
- **[Official]** Test Stars payments on Telegram's **test environment** (separate
  accounts and bot tokens); production invoices charge real Stars.
- Invoices work in private chats, groups and channels; inline invoices via
  `InputInvoiceMessageContent` (see `inline-mode.md`). Business-account invoice links:
  `createInvoiceLink.business_connection_id` (Stars only). **[API]**
- Paid broadcasts: `allow_paid_broadcast` on send methods lifts the 30 msg/s limit up
  to 1000 msg/s for 0.1 Star per message above the free rate; it is enabled in @BotFather and
  needs at least 100,000 Stars on the bot's balance and at least 100,000 monthly active users
  **[Official, Bots FAQ, checked 2026-11-25]**. (broadcast design itself:
  `channels-and-broadcasting.md`).

## What the user sees

- An invoice is a message with photo, title, description and a Pay button; in the
  bot's private chat it turns into a **receipt** after payment. **[Official]**
- `error_message` from a rejected pre-checkout is shown verbatim — write it like UI
  copy: what happened + what to do (`microcopy-and-labels.md`). **[Heuristic]**
- After `successful_payment`, confirm in one message what was unlocked, and edit or
  remove the "Buy" keyboard on the earlier screen so it can't be tapped again.
  **[Heuristic]**

## Common mistakes

| Mistake | Fix |
|---|---|
| Delivering on `pre_checkout_query` | Deliver on `successful_payment` only |
| Slow DB/HTTP work before answering pre-checkout | Answer within 10 s; work afterwards |
| Two `prices` items for `XTR` | Exactly one item for Stars |
| `amount: 2.5` | Integers in smallest units |
| Losing `telegram_payment_charge_id` | Persist it with the order; refunds need it |
| Delivering twice on a retried update | Idempotency key = charge id |
| Passing `allowed_updates` without `pre_checkout_query` / `subscription` | List every type you handle (`updates-and-delivery.md`) |
| Treating every `successful_payment` of a subscription as new | Check `is_recurring` / `is_first_recurring` |

## Error handling

- An answer after the 10-second window cannot save the payment: Telegram has already
  cancelled it. Expect the late call to fail and tell the user to try again.
  **[Heuristic]** (exact error text not verified offline).
- Check your own order state before `refundStarPayment`; a second refund of the same
  charge is rejected. After a timeout the outcome is unknown: do not call it again;
  reconcile (`payments-pipeline.md` §5). Branch on `ok`/`error_code`, never on the `description` text,
  which Telegram may change. **[API]** for "contents of error_code are subject to
  change"; the rest **[Heuristic]**.
- Flood control (429) carries `parameters.retry_after`; see
  `errors-and-fallbacks.md`.

Related: `gifts-and-stories.md` (gifts and Premium paid in Stars),
`business-accounts.md` (Star balance of a business account), `inline-mode.md`
(inline invoices), `mini-apps-bridge.md` (`openInvoice` from a Mini App).
