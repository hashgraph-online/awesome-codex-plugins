---
summary: "Payments inside a Mini App: which rail, the Stars purchase flow, invoiceClosed statuses, subscriptions, card payments, the Serverless variant; read for the app side of taking money."
verified: "2026-11-24"
bot_api: "10.5"
---

# Payments inside a Mini App

## Contents

- [1. Which rail](#1-which-rail)
- [2. The flow (one-off Stars purchase)](#2-the-flow-one-off-stars-purchase)
- [3. Each status on screen](#3-each-status-on-screen)
- [4. Before and around the button](#4-before-and-around-the-button)
- [5. Subscriptions: the "My plan" screen](#5-subscriptions-the-my-plan-screen)
- [6. Card payments for physical goods](#6-card-payments-for-physical-goods)
- [7. Telegram Serverless variant](#7-telegram-serverless-variant)
- [8. Checklist](#8-checklist)
- [9. The paywall: P1-P12](#9-the-paywall-p1-p12)

How a Mini App takes money: which rail for which goods, the end-to-end flow from cart to receipt, what each
`invoiceClosed` status means on screen, subscriptions, card payments for physical goods, and where TON
fits. This page is the **app side**. The server pipeline (order states, signed payload, pre-checkout within
10 seconds, idempotent delivery, refunds, reconciliation) lives in [../payments-and-stars.md](../payments-and-stars.md)
and the payments pipeline reference; this page links to it and never re-implements it.

Checked on **2026-11-24** against Bot API 10.5 (no payment changes; last ones: 10.4 TON wallet in widgets,
10.2 `BotSubscriptionUpdated`), https://core.telegram.org/bots/payments-stars,
https://core.telegram.org/bots/payments and https://core.telegram.org/bots/webapps. Labels: **[API]**,
**[Official]**, **[News]** (announcements, not specification), **[Heuristic]**.

## 1. Which rail

| Goods | Rail | In the Mini App | Proof of payment | Refund |
|---|---|---|---|---|
| Digital goods and services: credits, AI access, files, premium features | **Telegram Stars only**, currency `XTR` **[Official]**; cards or crypto for digital goods risk the app being hidden on mobile **[Official, Stars FAQ]** | server `createInvoiceLink` (`XTR`, empty `provider_token`, exactly one price) → `WebApp.openInvoice(link, cb)` (6.1) **[API]** | `successful_payment` to the bot **[Official]** | `refundStarPayment`, whole payment **[API]** |
| A monthly feature | **Stars subscription**: `createInvoiceLink` with `subscription_period` 2592000 (30 days) **[API]** | `openInvoice`; Mini Apps support paid subscriptions **[Official]** | first `successful_payment` with `is_first_recurring`, renewals with `is_recurring` and `subscription_expiration_date` **[API]** | per period charge; renewal switched with `editUserStarSubscription` **[API]** |
| Physical goods and services (coffee, books on paper, delivery) | **Payment provider** (card, Apple Pay, Google Pay through the provider sheet) **[Official]** | server `createInvoiceLink` with `provider_token`, ISO 4217 currency, several price parts **[API]** | `successful_payment` | at the provider |
| Photos or videos for Stars | **Paid media** is a chat message (`sendPaidMedia`), not a Mini App rail **[API]** | a "Open in chat" button; the bot sends the media | `purchased_paid_media` | — |
| TON | **No wallet in `Telegram.WebApp`** (the catalog has none); the 10.4 wallet flow works in message widgets only **[API]** | out of scope here: TON Connect is a third-party SDK; verify transfers on chain ([../wallet-and-ton.md](../wallet-and-ton.md)) | on-chain check **[Heuristic]** | outgoing transfer |

- One invoice cannot mix `XTR` and a fiat currency **[API]**: a cart with an e-book and a paper book becomes
  two orders and two invoices in a row, and the screen shows both groups **[Heuristic]**.
- Stars for **physical** goods are not addressed by the official pages; this skill uses a provider for
  physical goods and Stars for digital ones **[Heuristic]**.
- 2026-11-17: Telegram reminded developers that subscriptions, paid tools, AI access and credits must be paid
  in Stars **[News]**; no deadline was given.

## 2. The flow (one-off Stars purchase)

```
App ──cart {ids, qty} + initData──► Server ──createInvoiceLink──► Telegram
App ◄──{order_id, link}──────────── Server
App ──openInvoice(link)───────────────────────────────────────► Telegram payment sheet
                                    Server ◄── pre_checkout_query (answer ≤ 10 s)
                                    Server ◄── successful_payment → deliver once, receipt in the chat
App ◄── invoiceClosed {status} (a hint) ── App ── GET /orders/<id> ──► Server (the truth)
```

1. **Who pays.** Every request carries `Authorization: tma <initData>`; the server verifies it and uses
   the verified `user.id` ([security.md](security.md) §2-5; at most 1 hour old for a session that spends
   money). On Telegram Serverless the platform verifies it **[Official]**.
2. **What it costs.** The client sends item ids, variants and quantities. The server prices them from the
   rail's own price list (whole Stars for Stars, minor units for a provider), never by converting a fiat
   price at a fixed rate, and checks stock and limits **[Heuristic]**.
3. **Order before invoice.** An order row with the user, the lines, the amount and `valid_until`; the
   invoice payload carries a signed order reference (`ord:<id>.<hmac>`, ≤ 128 bytes **[API]**). Checking
   out the same cart again before `valid_until` returns the **same** open order and link (double taps).
4. **The link.** `createInvoiceLink`: `title` 1-32, `description` 1-255 characters **[API]**. A Stars
   invoice has one price, so the lines are shown in the app and in the receipt, not on the sheet.
5. **Open it** from a tap: `openInvoice(link, cb)` behind `isVersionAtLeast('6.1')`; the MainButton shows
   progress and stays inactive while the sheet is open (kit: `tma.pay(link)`).
6. **`invoiceClosed` is a hint** **[Official]**: on any status the app asks the server for the order
   (`GET /orders/<id>`, own orders only) and draws that state (§3).
7. **Pre-checkout** (server, ≤ 10 s **[API]**): the payload signature is valid, `from.id` is the order's
   owner (a leaked link paid by someone else is refused), the order has not expired, `total_amount` equals
   the order, stock still holds. `error_message` is shown to the user verbatim: write it as UI text.
8. **`successful_payment` is the only fact of payment** **[Official]**: unique by
   `telegram_payment_charge_id`, delivery in the same transaction as the right it grants, a repeated update
   delivers nothing twice.
9. **Receipt** in the chat: amount, what was unlocked, order number, `/paysupport` **[Official for
   /paysupport]**. If the app was opened from a Main Mini App or a direct link and the user never started the
   bot, ask `requestWriteAccess` before paying, so the receipt can reach them **[Heuristic]**.
10. **Refunds and reconciliation** are server work: a "Request a refund" screen files a request; an admin
    approves; `refundStarPayment` refunds the whole payment **[API]**; `getStarTransactions` reconciles
    daily. The app shows "Refunded" from the order state.

```json
{"method": "createInvoiceLink", "params": {
  "title": "Order 1042", "description": "AI credits pack · 500 credits",
  "payload": "ord:1042.3f9a1c22b7", "currency": "XTR", "provider_token": "",
  "prices": [{"label": "Order 1042", "amount": 250}]}}
```

## 3. Each status on screen

| `invoiceClosed` status | Screen **[Heuristic]** |
|---|---|
| `paid` | "Payment received, confirming…" with a skeleton; when the server says delivered: a success screen with what was unlocked, `notificationOccurred('success')` once, MainButton "Done" |
| `pending` | "The payment is processing. Don't pay again: we'll message you in the chat." Poll the order; MainButton hidden |
| `cancelled` | back to the cart quietly; MainButton restored; the cart intact |
| `failed`, or a refused pre-checkout | the reason from the server (for example a new price, now in the MainButton text); never "Something went wrong" |
| polling longer than ~60 s | "We're checking the payment and will message you as soon as it's confirmed" + `/paysupport`; no new payment until the order is expired or declined |

Polling: back off from 1 s to ~10 s, stop after ~60 s, resume on `activated` (the user returned to the app).
Nothing is unlocked from `invoiceClosed` or from the app's own state; only from the server's order.

## 4. Before and around the button

- MainButton: verb and amount (`Pay ⭐ 250`, `Pay €8.40`, `Subscribe · ⭐ 300 / month`); progress while the
  link is created; the tab bar is hidden on the checkout screen.
- No own payment form: no card fields, no "email for the receipt". The provider's sheet collects cards;
  Stars need no personal data **[Official]**. `scripts/miniapp_lint.py` refuses card fields.
- Under the summary, a footnote: "By paying you accept the Terms" with `openLink` to the bot's `/terms`;
  the server records the consent **[Official: terms before purchase]**.
- Orders screen: amount, date, status (paid, refunded, waiting), an empty state; on an order, "Problem with
  the payment?" → `openTelegramLink('https://t.me/<bot>?start=paysupport-<order>')`.
- Outside Telegram (a plain browser): an "Open in Telegram" button, never a fake payment.

## 5. Subscriptions: the "My plan" screen

State comes from the server: `active`, `canceled`, `failed`, `expires_at` (from
`subscription_expiration_date`), price. "Turn off renewal" (`showConfirm`, destructive) →
`editUserStarSubscription(is_canceled = true)`: access stays until the end of the period **[API]**. Turning
it back on with `is_canceled = false` works only for a subscription the bot cancelled **[API]**; one the user
cancelled is renewed by the user in Telegram. A failed renewal: one bot message and a banner "Renew · ⭐ 300"
that creates a new link. Access follows `expires_at`, not the last update.

```json
{"method": "createInvoiceLink", "params": {
  "title": "Pro plan", "description": "Unlimited workouts and weekly plans, renews monthly",
  "payload": "sub:pro.8c1e5a90d4", "currency": "XTR", "provider_token": "",
  "prices": [{"label": "Pro, 30 days", "amount": 300}], "subscription_period": 2592000}}
```

## 6. Card payments for physical goods

The same flow with a provider: `provider_token` from @BotFather (from the environment, never in code), an
ISO 4217 currency, price parts (item, delivery, discount). Address and pickup slot are collected **either**
in the Mini App (then delivery is priced on the server and `need_shipping_address` stays off) **or** by
Telegram's sheet (`need_shipping_address`, `is_flexible` → `shipping_query` / `answerShippingQuery`) —
never both **[Heuristic]**. `need_*` flags are ignored for Stars **[API]**.

```json
{"method": "createInvoiceLink", "params": {
  "title": "Order 1042", "description": "2 × Flat white, pickup 10:30 at Central",
  "payload": "ord:1042.3f9a1c22b7", "currency": "EUR", "provider_token": "PROVIDER_TOKEN_FROM_ENV",
  "prices": [{"label": "2 × Flat white", "amount": 840}]}}
```

## 7. Telegram Serverless variant

On Serverless the front end calls an endpoint with `Telegram.WebApp.Serverless.call('checkout', {lines})`;
the platform validates `initData` and passes it to the endpoint, which creates the order and the link; the
bot's update handlers (pre-checkout, successful payment) run on the same platform **[Official]**. Database
transactions are not documented: make delivery a unique insert keyed by the charge id **[Heuristic]**.

## 8. Checklist

- [ ] Rail by goods: digital → Stars, physical → provider; mixed carts become two invoices.
- [ ] Prices, currency and items decided on the server from verified `initData`; the client sends ids.
- [ ] Order created before the invoice; payload signed and bound to the user; repeated checkout reuses it.
- [ ] `openInvoice` gated (6.1), from a tap, MainButton in progress.
- [ ] Every `invoiceClosed` status mapped to a screen; nothing unlocked before the server says delivered.
- [ ] Pre-checkout and delivery follow the payments pipeline; receipt and `/paysupport` in the chat.
- [ ] No card fields or own payment forms; terms footnote before paying.
- [ ] Subscriptions: "My plan" with renewal switch; access by `expires_at`.
- [ ] Preview each status (`preview_miniapp.py`, `invoice=` parameter); test on the Telegram test server.

Not confirmed by official pages (check on the test environment): where the receipt arrives for a Main Mini
App user who never started the bot; which `invoiceClosed` status follows a refused pre-checkout; how long
an invoice link lives (rely on the order's `valid_until`).

## 9. The paywall: P1-P12

The screen that sells Premium, Pro or one locked feature. Hard rules **[Heuristic, owner decision 2026-11-26]**
over the **[API]** facts above; a paywall that breaks one is not done. Reference implementation:
`examples/mini-apps/paywall` (Road Theory, Stars subscription and a 3-month one-off plan, every state, a mock
server for the stand). Review a design with `miniapp_layout.py review` on `{"screen": "paywall", "paywall": {...}}`
(rule L26; `miniapp_layout.py example paywall` is the reference description).

| # | Rule | The failure it prevents |
|---|---|---|
| P1 | One order, top to bottom: intro (mark, title, one line) → what you get → Free and Premium → plans → terms → questions; the MainButton closes it | a card and a button in an empty screen |
| P2 | Value in numbers the server sends (`40 timed tests`, `283 sign cards`): 3-5 rows, each an icon tile, a title and one line | adjectives ("unlimited power"), hype (lint MA31), checkmark bullets crammed in a card |
| P3 | What stays free, side by side with Premium (a compact table or two columns of rows) | the user cannot tell what they lose by not paying |
| P4 | Price = the Stars glyph (SVG `.tma-star`) + amount + period (`/ month`) or `No renewal`; the plain-text `⭐ 50` only inside the MainButton | `⭐` emoji in markup, a price without its period, "50 Telegram stars per month" in a bullet list |
| P5 | 1-3 plans in ONE radio group, one preselected; savings as a plain fact (`10% less than monthly`). Stars subscriptions renew every 30 days **[API]**: a longer term is a one-off invoice that says it does not renew | a "yearly subscription" in Stars; plans as unrelated cards; nothing selected |
| P6 | The MainButton names the verb, the price and the period of the selected plan and changes with it (`Subscribe · ⭐ 50 / month`, `Pay ⭐ 135 for 3 months`); no own buy button; the tab bar is hidden | a generic "Continue"; a second CTA in the content |
| P7 | Renewal and cancellation in the footnote under the plans ("renews every 30 days until you turn it off in Profile or in Telegram settings"), the Terms link (`openLink`), and answers to cancel / progress / renewal | terms hidden in a bot command (`/premium`) or missing |
| P8 | A level-2 screen (BackButton) or a sheet, opened from the locked thing; the tab keeps its free content usable and shows the locked part dimmed with a lock | the whole tab replaced by an upsell card |
| P9 | Every state drawn: loading (skeleton rows), offer error (reason + Try again), cancelled (nothing changes), failed (reason, "No Stars were taken"), pending / paid (Confirming, "do not pay again"), timeout (we will message you), success (what is unlocked, until when), subscriber (My plan, never the paywall) | a spinner forever; a second charge; a paywall shown to a subscriber |
| P10 | The server owns the offer and the prices (the client sends the plan id; lint MA26) and unlocks only from its order (`watchOrder`; lint MA27) | a price edited in the client; unlocking on `invoiceClosed: paid` |
| P11 | Surfaces S1-S6 ([design-system.md](design-system.md) §5): 24 px between sections, 16 px insets, one radius scale; one accent (the MainButton); no gradients, glows or emoji | cramped cards, a glowing "PRO" badge |
| P12 | Outside Telegram: "Open in Telegram to pay", never a fake payment; Android back / BackButton leaves the paywall without losing the tab's state | a dead end, a payment that never existed |

Check: `?audit=1` on the stand with `--api examples/mini-apps/paywall/mock-api.json` and `invoice=paid|failed|pending|cancelled`; 0 errors
on every state; the MainButton text matches the selected plan.
