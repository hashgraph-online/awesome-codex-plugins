---
summary: "One payment pipeline for Stars and Gram: rail choice, states, payload security, refunds, reconciliation, data model, screens and microcopy, and the tgkit.payments runtime."
verified: "2026-11-23"
bot_api: "10.5"
---
# Payments pipeline: product → invoice → payment → delivery → refund → reconciliation

One pipeline for both rails a bot can take money on — **Stars** (`XTR`, invoices) and **Gram**
(the TON wallet inside a widget) — with the states the server keeps, the screens the user sees
and their microcopy in en / ru / uk. API details per rail: `payments-and-stars.md` (Stars,
subscriptions, paid media, provider payments) and `wallet-and-ton.md` (wallet flow, signing).
Runtime for the Stars rail: `examples/python/tgkit/payments.py`, tests in `tests/test_payments.py`.

Checked on **2026-11-23** against the Bot API 10.5 snapshot (`py -3 scripts/tg_api_lookup.py show
<Name>`) and the news of November 2026. Labels: **[API]** Bot API spec · **[Official]** Telegram's
payment guides and terms · **[News]** press and Telegram announcements, not an official spec ·
**[H]** this skill's design rule · **[Unverified]** not confirmed by any source yet.


## Contents

- [1. Pick the rail first](#1-pick-the-rail-first)
- [2. The pipeline, stage by stage](#2-the-pipeline-stage-by-stage)
- [3. States](#3-states)
- [4. Payload and security](#4-payload-and-security)
- [5. Refunds](#5-refunds)
- [6. Reconciliation](#6-reconciliation)
- [7. Data model](#7-data-model)
- [8. Screens and microcopy](#8-screens-and-microcopy)
- [9. Runtime (Stars)](#9-runtime-stars)
- [10. Shipping path (provider invoices)](#10-shipping-path-provider-invoices)
- [11. Ledger audit](#11-ledger-audit)
- [Common mistakes](#common-mistakes)

## 1. Pick the rail first

| | Stars (`XTR`) | Gram (ex-Toncoin, TON network) | Provider (card, fiat) |
|---|---|---|---|
| Allowed for | everything; **the only rail for digital goods and services** [Official] | physical goods, donations and tips, payments between people, suggested posts (`TON`) [H] | physical goods only [Official] |
| How the user pays | invoice: `sendInvoice` / `createInvoiceLink`, `sendPaidMedia`, subscriptions [API] | widget `request(…, {wallet: true})` → bot answers a TON Connect transaction → `wallet.sendTransaction` [API] | invoice with `provider_token` and an ISO 4217 currency [API] |
| Proof of payment | `successful_payment` [Official] | only the on-chain check (sender, recipient, amount, comment, success); `sent_transaction` is a notice [API] | `successful_payment` |
| Units | whole Stars + `nanostar_amount` (10⁻⁹) in transactions [API] | nanograms (10⁻⁹), decimal strings [API] | smallest currency unit (`exp` in currencies.json) [API] |
| Refund | `refundStarPayment`: whole payment only, no amount [API] | Telegram refunds nothing: an outgoing transfer from the bot's wallet, may be partial [H] | at the provider [API] |
| Where it works | private chats, groups, channels, inline, business invoice links [API] | production: private chat with the bot only; groups, inline, forwards are test-server only [Official] | private chats, groups, channels |

**The digital-goods rule.** Digital goods and services sold inside Telegram are paid in Stars;
third-party providers and crypto are not allowed for them [Official]. On **2026-11-17** Telegram
reminded bot and Mini App developers that bot subscriptions, paid tools, access to third-party AI
models and credits or tokens for them are Stars-only and that in-app card payments for digital
services go away; VPN bots in "authoritarian countries" are the stated exception; no effective
date or sanctions were named [News]. Stars can be bought for Gram on Fragment [News].

**Gram.** Toncoin was renamed Gram (announced 2026-06-02); the blockchain stays TON [News]. The
Bot API text says "TON grams" and "nanograms": `SuggestedPostPrice.currency` is `XTR` or `TON`,
`amount` in Stars or nanograms [API]. Gram is **not** an invoice currency: `sendInvoice` takes
`XTR` or ISO 4217 codes only [API].

**Default [H]:** a digital product (credits, AI access, a subscription, a PDF, premium answers,
paid media) is designed in Stars. When someone asks for Gram or a card for it, say so first —
the rule, the 2026-11-17 reminder as news — and give the Stars path. Gram for a digital product
only as the owner's explicit decision, with the warning kept in the design notes. In code:
`check_rail(kind, rail)` in `tgkit/payments.py` returns `ok`, the warning and `suggest: "XTR"`;
subscriptions are refused on any rail but `XTR` because the API has no other (`subscription_period`
requires `XTR`) [API].

## 2. The pipeline, stage by stage

| Stage | Server does | Rule | User sees |
|---|---|---|---|
| Product | catalog row: kind, title per locale, rails allowed, price in integers | price and item come from the server, never from `callback_data` or widget data [H] | product card |
| Order | row **before** the invoice: user, chat, product, amount, `valid_until` | rate-limit order creation per user [H] | — |
| Invoice | Stars: `sendInvoice` / `createInvoiceLink`, `payload = ord:<id>.<tag>`. Gram: transaction request with `valid_until` | payload 1-128 bytes [API], HMAC tag [H]; one `prices` item for Stars [API] | confirmation with terms and `/terms` |
| Pre-checkout (Stars) | order exists, is this user's, not expired, `total_amount` = order amount = current price, stock, per-user limit | answer **within 10 s** [API]; local checks only, slow work after the answer [H] | Telegram's pay sheet, or `error_message` verbatim |
| Payment | Stars: `successful_payment` → payment row, UNIQUE `telegram_payment_charge_id`. Gram: `sent_transaction` → `awaiting`, chain check → `confirmed` | deliver only after proof [Official]; a re-delivered update delivers nothing twice [H] | "Waiting for confirmation…" (Gram), then the receipt |
| Delivery | entitlement row, order `delivered`, one receipt | idempotent: resume `paid → delivered` after a crash, never repeat [H] | receipt + what was unlocked + what next |
| Refund | admin request → confirmation → `refundStarPayment` / outgoing Gram transfer | admin-only, two steps, journal; Stars refund is whole [API] | refund request status, then the result |
| Reconciliation | daily: Stars `getStarTransactions` pages; Gram wallet transactions vs `confirmed` orders | discrepancies to `reconciliation_runs` and the admin [H] | owner's statement and balance |

## 3. States

### Stars

```
draft ─► invoiced ─► pre_checkout ─┬─► declined   (ok=false with a reason)
              │                    └─► paid ─► delivered ─┬─► refund_requested ─► refunded
              └─► expired                                 └─► chargeback (seen only in reconciliation)
subscription: active ─► (renewal) active │ failed │ canceled_by_user │ canceled_by_bot │ refunded
```

- `successful_payment` is the fact: it is recorded even when the order was already expired or
  declined, and an unmatched payment goes to the admin, not to delivery [H].
- A multi-use invoice (group, channel, forward, inline; empty `start_parameter`) is an **offer**
  (`inv:<offer>.<tag>`); every payment becomes its own order at pre-checkout [Official] for
  multi-use, [H] for the order split.
- Subscriptions: one order per subscription; the first `telegram_payment_charge_id` is the
  subscription id [H]; each renewal is a new payment with `is_recurring` [API], kept on the same
  order [H].
  `Update.subscription` (`BotSubscriptionUpdated`) carries only `user`, `invoice_payload` and
  `state` [API]: find the subscription by the payload, check the user. Access by `expires_at`
  (from `subscription_expiration_date`), never by the last update [H].

### Gram

```
invoiced(valid_until) ─► awaiting(msg_hash) ─┬─► confirmed ─► delivered ─► refund_sent ─► refund_confirmed
                                             ├─► mismatch  (amount, recipient or comment differ)
                                             └─► expired   (no transaction by the deadline)
```

A repeated `pay:` inside `valid_until` returns the **same** transaction request; a paid or
awaiting order returns its state, never a new transaction. One `msg_hash` maps to one order. After
`TIMEOUT` the Pay button stays disabled until the check — the money may have left. The Gram price
is fixed in the order until `valid_until`; a new rate means a new order. Details and the signing
flow: `wallet-and-ton.md` [H].

## 4. Payload and security

- `payload = ord:<order_id>.<tag>` or `inv:<offer_id>.<tag>`, `tag` = 8 bytes of HMAC-SHA256
  over `ord:<id>` in hex — about 35 bytes, well under 128 [API] limit. A payload whose tag does
  not verify, an order of another user (a forwarded personal invoice), a changed amount are
  declined at pre-checkout and the owner's order is left untouched [H].
- UNIQUE indexes on `payments.charge_id` (Stars) and `payments.tx_hash` / `msg_hash` (Gram) are the
  idempotency, not an optimisation. Store integers only; never floats [API] for "integer, not
  float".
- **Authenticate updates.** A forged `callback_query` from an admin's id or a forged
  `refunded_payment` is a refund or a revocation. Take updates from `getUpdates`, or from a webhook
  set with `secret_token` whose `X-Telegram-Bot-Api-Secret-Token` header you compare in constant
  time (`webhook_secret_ok()`) before anything is parsed [API] for the header, [H] for the rule.
- Answer `pre_checkout_query` first: run refunds, reconciliation and other slow calls in a worker,
  not in the loop that has to answer within 10 s [H].
- `successful_payment` must match the order it names (payer and amount); a charge that does not —
  or arrives for an order already fulfilled — is recorded unbound, not delivered, and sent to the
  admin [H].
- Refunds only from admin roles, re-checked on the confirmation tap, journaled with who asked and
  who approved. Secrets, full payment records and wallet keys never go into `chat_data`, logs or
  the repo. Gram addresses are linked through the `signData` challenge, not taken from a profile.
- Diffs touching payments get a security review before the PR [H].

```json
{"method": "sendInvoice", "params": {
  "chat_id": 111111111,
  "title": "50 AI credits",
  "description": "Credits for longer answers and image generation. Valid for 12 months.",
  "payload": "ord:3f9a1c0b7d2e.9c41e07a5b3d2f18",
  "currency": "XTR",
  "prices": [{"label": "50 AI credits", "amount": 250}],
  "reply_markup": {"inline_keyboard": [[{"text": "Pay ⭐250", "pay": true}], [{"text": "Terms", "callback_data": "terms"}]]}
}}
```

A price that changed between the invoice and the tap: decline, then send the new invoice — after
the answer, never before it.

```json
{"method": "answerPreCheckoutQuery", "params": {
  "pre_checkout_query_id": "4382bfdwdsb323b2d9", "ok": false,
  "error_message": "The price has changed to ⭐300. A new invoice is below — no Stars were charged."
}}
```

## 5. Refunds

| | Stars | Gram |
|---|---|---|
| Call | `refundStarPayment(user_id, telegram_payment_charge_id)` [API] | outgoing transfer from the bot's wallet [H] |
| Amount | the whole payment; no amount parameter [API] | any amount up to the payment; partial allowed [H] |
| To whom | the payer, by Telegram | the **sender address of the confirmed transaction**, not the profile wallet card [H] |
| Proof | `True` from `refundStarPayment` [API]; the API defines a `refunded_payment` service message (`Message.refunded_payment`) but does not say a refund call produces one [Unverified]: record the refund on `True` | the outgoing transaction confirmed on chain, comment `refund:<order>` [H] |
| Afterwards | revoke access, order `refunded`, user told once | same, order `refund_confirmed` |

- Default: refunds are manual and admin-only; an automatic rule ("within N hours and unused") is an
  option, off by default (`RefundPolicy.auto_within_s` + `is_used`) [H].
- Two steps: the request posts a card to the admin chat ("Refund ⭐250 to user … for «…»? Stars
  refunds are whole-payment only and cannot be undone." + `Refund ⭐250` (`style: danger`) /
  `Keep the payment`); the tap re-checks the role and claims the refund once (a double tap does
  nothing).
- `refundStarPayment` timed out → outcome unknown: do **not** call it again; the refund stays
  `unknown` until reconciliation sees the outgoing transaction with the same id [H]. A 400 →
  `failed`, the order returns to `delivered`; branch on `error_code`, not on `description` [API].
- A partial Stars refund is impossible: offer the whole refund or a goodwill credit instead.
- Refund state lives on the **charge**, not the order: a subscription has one order and a charge
  per period, and each can be refunded once. A refund that wins the race against delivery blocks
  it: delivery re-reads the order and the charge under the same lock that writes the entitlement.
- An `unknown` refund that reconciliation shows never left can be closed by an admin
  (`close_unknown_refund`) and requested again. Stray charges (no matching order) are refundable
  by admins only.

```json
{"method": "sendMessage", "params": {
  "chat_id": 900,
  "text": "Refund ⭐250 to user 111111111 for «50 AI credits» (order 3f9a1c0b7d2e)?\nReason: charged twice\nStars refunds are whole-payment only and cannot be undone.",
  "reply_markup": {"inline_keyboard": [[{"text": "Refund ⭐250", "callback_data": "rf:ok:17", "style": "danger"}], [{"text": "Keep the payment", "callback_data": "rf:no:17"}]]}
}}
```

## 6. Reconciliation

- **Stars, daily.** Page `getStarTransactions` (`offset`, `limit` 1-100, chronological) [API] from
  the previous run's offset. Incoming `TransactionPartnerUser` with `transaction_type:
  "invoice_payment"` matches a payment by `StarTransaction.id` = `telegram_payment_charge_id`
  [API]; compare `amount * 10⁹ + nanostar_amount` with the stored nanostars. An outgoing
  transaction with the same id is a refund [API]; if this bot never refunded it, treat it as a
  **chargeback**: order `chargeback`, access revoked by rule, admin told. The Bot API documents
  that chargebacks debit the balance, not the exact transaction shape — keep this a heuristic and
  look at the raw row [H]. Withdrawals (`fragment`), ads (`telegram_ads`), paid broadcasts
  (`telegram_api`), paid media and the rest are listed separately, not as discrepancies.
- Buckets: matched · missing here (in Telegram, not in our payments) · missing there (ours, not in
  Telegram) · amount mismatch · chargebacks · refunds matched / settled · other. Store each run.
- **Gram.** All `confirmed` orders against the bot wallet's transactions (own node, indexer or
  provider behind `ChainVerifier`); incoming transfers without an order go to an "unidentified"
  list for the admin [H].

```json
{"_type": "StarTransactions", "transactions": [
  {"id": "stxAbCdEf123", "amount": 250, "date": 1763190000,
   "source": {"type": "user", "transaction_type": "invoice_payment", "user": {"id": 111111111, "is_bot": false, "first_name": "Olena"}, "invoice_payload": "ord:3f9a1c0b7d2e.9c41e07a5b3d2f18"}},
  {"id": "stxAbCdEf123", "amount": 250, "date": 1763276400,
   "receiver": {"type": "user", "transaction_type": "invoice_payment", "user": {"id": 111111111, "is_bot": false, "first_name": "Olena"}}},
  {"id": "wd-91", "amount": 1000, "nanostar_amount": 500000000, "date": 1763280000,
   "receiver": {"type": "fragment", "withdrawal_state": {"type": "pending"}}}
]}
```

## 7. Data model

Money columns are integers: Stars, nanostars, nanograms. `tgkit/payments.py` ships the SQLite
version (stdlib); the same shape on Postgres / Supabase:

```sql
create table products (id text primary key, kind text not null check (kind in
  ('digital','physical','subscription','paid_media','donation')), title jsonb not null,
  rails text[] not null, active boolean not null default true);
create table prices (product_id text references products, rail text not null, amount_int bigint not null,
  amount_nano bigint not null default 0, valid_from timestamptz not null, valid_to timestamptz);
create table offers (id text primary key, product_id text not null, chat_id bigint not null,
  amount bigint not null check (amount > 0), payload text not null, valid_until timestamptz not null);
create table orders (id text primary key, user_id bigint, chat_id bigint not null, product_id text not null,
  offer_id text references offers, currency text not null, amount bigint not null check (amount > 0),
  status text not null check (status in ('draft','invoiced','pre_checkout','declined','expired','paid',
  'delivered','refund_requested','refunded','chargeback')), payload text not null,
  valid_until timestamptz not null, decline_reason text, lang text not null default 'en',
  created_at timestamptz not null default now(), updated_at timestamptz not null default now());
create table payments (id bigserial primary key, order_id text references orders, user_id bigint not null,
  currency text not null, amount bigint not null, nano bigint not null default 0,
  charge_id text unique, provider_charge_id text, is_recurring boolean not null default false,
  msg_hash text unique, tx_hash text unique, from_address text, paid_at timestamptz not null);
create table refunds (id bigserial primary key, payment_id bigint not null references payments,
  amount bigint not null, reason text not null check (length(reason) <= 500), requested_by bigint not null,
  approved_by bigint, status text not null check (status in
  ('requested','sending','unknown','done','failed','canceled')), tx_hash text unique,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now());
create unique index refunds_one_active on refunds (payment_id)
  where status in ('requested','sending','unknown','done');
create table subscriptions (id text primary key, user_id bigint not null, product_id text not null,
  order_id text not null unique, state text not null, expires_at timestamptz not null,
  failed_notice_for timestamptz);
create table entitlements (id bigserial primary key, user_id bigint not null, product_id text not null,
  payment_id bigint not null unique references payments, granted_at timestamptz not null,
  expires_at timestamptz, revoked_at timestamptz);
create table ledger (id bigserial primary key, at timestamptz not null, account text not null,
  debit bigint not null default 0, credit bigint not null default 0, ref text not null);
create table events (key text primary key, kind text not null, received_at timestamptz not null);
create table reconciliation_runs (id bigserial primary key, at timestamptz not null, rail text not null,
  period_from timestamptz not null, period_to timestamptz not null, matched int not null,
  missing_here int not null, missing_there int not null, chargebacks int not null,
  diff_nano bigint not null, details jsonb not null);
```

On Supabase: enable RLS on every table and create **no** policies for `anon` or `authenticated`,
so no client can read or write them; only server code with the service role touches payments.
The bot token and wallet keys stay out of the database. Prune `events` older than 24 h (Telegram
keeps an undelivered update at most that long, and `update_id` may restart after a quiet week). Ledger accounts: `user:<id>`, `bot:stars`, `bot:gram`, `fees`,
`refunds`; every event posts a debit and a credit of the same amount.

## 8. Screens and microcopy

Every screen has an empty, loading, error and retry state. `style: success` goes on the Pay
button only; destructive confirmations (`Refund`) use `danger`; navigation stays unstyled. Prices
show the unit: `⭐ 250`, `1.5 Gram ≈ €4.80` (rate fixed until the order's `valid_until`).

| Screen | en | ru | uk |
|---|---|---|---|
| Product card | 50 AI credits · ⭐ 250 · [Buy ⭐250] [Terms] | 50 кредитов · ⭐ 250 · [Купить ⭐250] [Условия] | 50 кредитів · ⭐ 250 · [Купити ⭐250] [Умови] |
| Confirm with terms | You pay ⭐250 for 50 credits. By paying you accept /terms. | Вы платите ⭐250 за 50 кредитов. Оплачивая, вы принимаете /terms. | Ви платите ⭐250 за 50 кредитів. Оплачуючи, ви приймаєте /terms. |
| Waiting (Gram) | Waiting for the payment to confirm… This takes up to a minute. | Ждём подтверждения оплаты… Это до минуты. | Чекаємо підтвердження оплати… Це до хвилини. |
| Success (receipt) | Paid ⭐250. «50 AI credits» is unlocked. Order 3f9a… · /paysupport | Оплачено ⭐250. «50 кредитов» уже доступны. Заказ 3f9a… · /paysupport | Сплачено ⭐250. «50 кредитів» уже доступні. Замовлення 3f9a… · /paysupport |
| Pre-checkout declined | The price has changed to ⭐300. A new invoice is below — no Stars were charged. | Цена изменилась: теперь ⭐300. Новый счёт ниже — звёзды не списаны. | Ціна змінилася: тепер ⭐300. Новий рахунок нижче — зірки не списано. |
| Gram timeout | We are checking the transfer. Don't pay again — we'll message you. | Проверяем перевод. Не оплачивайте повторно — мы напишем. | Перевіряємо переказ. Не сплачуйте повторно — ми напишемо. |
| My purchases (empty) | No purchases yet. [Open the shop] | Покупок пока нет. [Открыть магазин] | Покупок поки немає. [Відкрити магазин] |
| Subscription | Pro · renews on 15 Dec for ⭐300. [Cancel renewal] | Pro · продление 15 дек. за ⭐300. [Отменить продление] | Pro · подовження 15 груд. за ⭐300. [Скасувати подовження] |
| Cancelled | Renewal cancelled. Pro stays on until 15 Dec. [Turn renewal back on] (bot-cancelled only: the tap allows it, the user confirms in Telegram) | Продление отменено. Pro действует до 15 дек. [Вернуть продление] | Подовження скасовано. Pro діє до 15 груд. [Повернути подовження] |
| Renewal failed (once) | The payment for Pro did not go through. Access stays on until 15 Dec, then stops. [Renew ⭐300] | Оплата Pro не прошла. Доступ сохранится до 15 дек., потом отключится. [Продлить ⭐300] | Оплата Pro не пройшла. Доступ збережеться до 15 груд., потім вимкнеться. [Подовжити ⭐300] |
| Refund request | Why do you want a refund? [Charged twice] [Doesn't work] [Other] | Почему вы хотите вернуть деньги? [Списали дважды] [Не работает] [Другое] | Чому ви хочете повернути гроші? [Списали двічі] [Не працює] [Інше] |
| Refund status | Request for order 3f9a… sent. We answer within 24 h. | Запрос по заказу 3f9a… отправлен. Ответим в течение суток. | Запит щодо замовлення 3f9a… надіслано. Відповімо протягом доби. |
| Refund done | ⭐250 returned for «50 AI credits». Access is switched off. | ⭐250 возвращены за «50 кредитов». Доступ отключён. | ⭐250 повернуто за «50 кредитів». Доступ вимкнено. |
| `/paysupport` | Payment problem with order 3f9a…? Describe it in one message — we reply within 24 h. | Проблема с оплатой заказа 3f9a…? Опишите её одним сообщением — ответим за сутки. | Проблема з оплатою замовлення 3f9a…? Опишіть її одним повідомленням — відповімо за добу. |
| Paid media teaser | 3 photos from the shoot · ⭐25 to open | 3 фото со съёмки · ⭐25, чтобы открыть | 3 фото зі зйомки · ⭐25, щоб відкрити |
| Statement and balance | Balance ⭐12 480 · today +⭐1 250, refunds −⭐250. [Statement] | Баланс ⭐12 480 · сегодня +⭐1 250, возвраты −⭐250. [Выписка] | Баланс ⭐12 480 · сьогодні +⭐1 250, повернення −⭐250. [Виписка] |

Obligations [Official]: answer `/paysupport`, offer `/terms` before the purchase and `/support`;
Telegram support does not handle your disputes; test on the test environment with separate
accounts and tokens.

## 9. Runtime (Stars)

```python
from tgkit.payments import ALLOWED_UPDATES, Product, SqliteStore, StarsPayments, webhook_secret_ok

catalog = {"credits50": Product("credits50", "digital", {"en": "50 AI credits"},
                                {"en": "Credits for longer answers."}, 250)}
pay = StarsPayments(transport, SqliteStore("payments.db"), catalog, secret=PAYLOAD_SECRET,
                    admins={ADMIN_ID}, admin_chat_id=ADMIN_ID, on_deliver=add_credits)
pay.invoice(user_id, chat_id, "credits50", lang="uk")      # order + sendInvoice

def webhook(headers, update):                               # setWebhook(..., secret_token=WEBHOOK_SECRET)
    if not webhook_secret_ok(headers, WEBHOOK_SECRET):
        return 403
    if not pay.handle(update):                              # pre-checkout, payment, refund, subscription
        other_handlers(update)
    return 200

pay.reconcile(since=day_start, until=day_end, offset=last_offset)   # daily, in a worker
pay.audit_ledger(offset=last_audit_offset)                          # read-only ledger check (§11)
```

`on_deliver` runs inside the transaction that claims the delivery (the entitlement row, UNIQUE per
charge): write its effects (credits, files) to the same database so they commit or roll back with
the claim; anything external must be idempotent by `payment.charge_id`. Keep it short — it holds
the write lock.

Covered by tests on `FakeTransport`: double delivery of an update, a duplicate arriving mid-
delivery, a crashed delivery and a crashed renewal resumed, forged and foreign payloads, a price
change at pre-checkout, an expired order, stock and per-user limits with live holds, a multi-use
invoice in a group, a stray charge, a refund and a repeated refund, a refund that wins the race
against delivery, per-charge subscription refunds, a lost refund answer, a `failed` subscription
(one message), reconciliation with a chargeback, paging and a re-run, the ledger audit (a missing
refund, a double credit, paging), the webhook secret. Gram runtime (orders, `msg_hash`, `ChainVerifier`, refund transfers) is
the next stage; until then use `tgkit/wallet.py` and `wallet-and-ton.md`.

Physical goods through a provider: no runtime here — the call sequence is §10 and
`payments-and-stars.md#physical-goods-provider-payments`.

## 10. Shipping path (provider invoices)

Shipping exists only on a provider invoice: for Stars, `need_*` and `is_flexible` are ignored [API].

1. `sendInvoice` with `provider_token`, an ISO 4217 `currency`, `need_shipping_address: true` and
   `is_flexible: true`; `prices` may hold several items (only Stars needs exactly one) [API].
2. Telegram sends `Update.shipping_query` (`ShippingQuery`: `id`, `from`, `invoice_payload`,
   `shipping_address`), only for invoices with a flexible price [API].
3. `answerShippingQuery`: `ok: true` with `shipping_options` (`ShippingOption`: `id`, `title`,
   `prices`), or `ok: false` with `error_message`, which Telegram shows the user [API]. Price the
   options from the server's table by `country_code` for the order the payload names [H].
4. `pre_checkout_query` carries the chosen `shipping_option_id` and `order_info` [API]: recompute
   the total as invoice prices plus that option's prices and decline on a mismatch [H].
   `successful_payment` repeats both [API]; store the address with the order, never in logs [H].

```json
{"update_id": 700001, "shipping_query": {
  "id": "sq-7711", "from": {"id": 111111111, "is_bot": false, "first_name": "Olena"},
  "invoice_payload": "ord:5b2e91c4d0aa.3f6c0e9a81d2b7c4",
  "shipping_address": {"country_code": "UA", "state": "", "city": "Kyiv", "street_line1": "Khreshchatyk St 1", "street_line2": "apt 5", "post_code": "01001"}
}}
```

```json
{"method": "answerShippingQuery", "params": {
  "shipping_query_id": "sq-7711", "ok": true,
  "shipping_options": [{"id": "nova", "title": "Nova Poshta branch, 1-2 days", "prices": [{"label": "Delivery", "amount": 350}]},
                       {"id": "courier", "title": "Courier to the door, 1 day", "prices": [{"label": "Courier", "amount": 900}]}]
}}
```

The whole recorded sequence: `examples/python/recipes/api_payments.py` →
`examples/payloads/api-payments.json`.

## 11. Ledger audit

`audit_ledger(offset=…, page_size=100)` checks the ledger itself against the statement and is
read-only: it writes, posts and sends nothing; the admin decides the correction [H].

- Pages `getStarTransactions` from the stored offset (`limit` 1-100) [API] until a page shorter
  than `limit`, and returns `next_offset` for the next run [H].
- **Missing refund.** A refund row reuses the refunded payment's id [API]; an outgoing
  `TransactionPartnerUser` row with `transaction_type: "invoice_payment"` whose id has no
  `refund:<id>` or `chargeback:<id>` posting on `bot:stars` is a refund the ledger lacks — one made
  from another tool, or a `refunded_payment` update that never arrived [H].
- **Double credit.** A charge id is one incoming transaction (`StarTransaction.id` =
  `SuccessfulPayment.telegram_payment_charge_id`) [API]; two income postings under one id are a
  double credit [H]. UNIQUE `payments.charge_id` prevents it inside `tgkit`; the audit catches a
  second writer, an import or a hand edit.
- `reconcile()` (§6) is the run that acts (settles lost refunds, records chargebacks); run the
  audit after it.

## Common mistakes

| Mistake | Fix |
|---|---|
| Gram or a card for credits, AI access, a subscription | Stars; warn about the rule before designing |
| Order created after the payment | order before the invoice; payload names it |
| Payload = bare order id | signed payload; decline forged and foreign ones |
| Heavy work before `answerPreCheckoutQuery` | answer within 10 s, then work |
| Delivery on `pre_checkout_query` or `sent_transaction` | `successful_payment` / on-chain check only |
| "Refund 50 % in Stars" | impossible: whole refund or a goodwill credit |
| Retrying `refundStarPayment` after a timeout | outcome unknown: reconcile first |
| Shipping options on a Stars invoice | shipping exists only on a provider invoice (§10) |
| Income posted per update, not per charge id | one posting per charge; `audit_ledger` finds doubles |
| Access by the last subscription update | access by `expires_at` |
| One message per failed renewal retry | one per period |
| Float money | integers: Stars, nanostars, nanograms |
