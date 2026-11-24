# 93 — Mini App shop: catalogue → product → cart → checkout

Product recipe (no registry row). Verified 2026-11-24 against Bot API 10.5. App-side payments:
`references/mini-apps/payments.md`; bot-side pipeline: `references/payments-and-stars.md` (this recipe changes no
payment logic of the pipeline; it shows where the Mini App hands over). Layout:
`references/mini-apps/layout-rules.md`. Tags: **[API]**, **[official]**, **[heuristic]**.

1. **Request and visible result.** “Turn our coffee shop bot into a proper store with photos and a cart.” — A
   menu (or a catalogue grid), product screens with variants, a cart with steppers, “Pay €8.40” in the
   MainButton, Telegram's payment sheet from the provider, a confirming screen that follows the server's order
   state, and the receipt as a bot message.
2. **Why these features.** Coffee is a physical good, so it is paid through a **provider** in EUR; Stars are
   for digital goods **[official: Stars for digital goods; heuristic: provider for physical]**. The server
   prices the cart from item ids and ignores the client's price **[heuristic]**; the order exists before the
   invoice and the payload is a signed order reference bound to the buyer **[heuristic]**; `createInvoiceLink`
   on the server + `WebApp.openInvoice` in the app **[API]/[official]**; `invoiceClosed` is a hint and the
   order is paid only on `successful_payment` **[official]**; pre-checkout answered within 10 s **[API]**.
3. **Requirements.** Bot API ≥ 6.1 for `openInvoice`; a provider connected in @BotFather (token from the
   environment); `allowed_updates` with `pre_checkout_query` and `message` **[API]**. A digital add-on in the
   same cart would be a second, Stars invoice (`XTR` and EUR cannot mix) **[API]**.
4. **Payload.** `examples/payloads/r93-mini-app-shop.json`: `createInvoiceLink` (EUR, provider token
   placeholder, signed payload `ord:<id>.<hmac>`) and the receipt `sendMessage` after `successful_payment`.
5. **Code.** Server and bot: `r90_99_mini_apps.py::Orders` (`checkout` reuses an open order for the same
   cart, `pre_checkout` checks signature, owner, expiry, amount; `paid` delivers once per charge) and `::r93`.
   App: `tma.pay(link)` then `tma.watchOrder(fetchOrder, isFinal)` from the kit; screens in
   `examples/mini-apps/vanilla` (menu rows, item detail, cart) and `examples/mini-apps/catalog` (grid tiles).
6. **Sequence and state.**
   ```mermaid
   sequenceDiagram
     participant A as Mini App
     participant S as Server
     participant T as Telegram
     A->>S: cart (ids, sizes, quantities) + initData
     S->>S: price, order 1042 (owner, amount, valid_until), payload ord:1042.<hmac>
     S->>T: createInvoiceLink (EUR, provider)
     S-->>A: {order_id, link}
     A->>T: openInvoice(link)
     T->>S: pre_checkout_query → owner, expiry, amount (≤ 10 s)
     T->>S: successful_payment → deliver once (charge id), receipt in the chat
     A->>S: GET /orders/1042 until delivered (invoiceClosed is only a hint)
   ```
7. **Result.** MainButton `Pay €8.40`; after paying, “Payment received, confirming…”, then the success
   screen; the chat shows “Paid €8.40. Order 1042: 2 × Flat white, pickup 10:30 at Central.”
8. **Typical mistake, limits, alternative.** Prices from the client; an unsigned payload such as `o:1042`
   that any payer can reuse; converting a fiat price to Stars at a fixed rate; selling physical goods in Stars
   without a decision on it; fulfilling on `invoiceClosed: paid`; a second order for every tap; own card fields
   (lint MA25). Limits **[API]**: title 1-32, description 1-255, payload 1-128 bytes. Alternative: a message
   shop (recipe 20) for ≤ 5 items.
9. **Run and verify.** `py -3 examples/python/recipes/r90_99_mini_apps.py r93` (7 self-checks: server price,
   reused order, provider rail, signed payload, refused stranger / forged payload / changed total, one
   delivery per charge, expired order) · the preview stand with `?invoice=paid|failed|pending` · lint
   MA25-MA27. Evidence: offline contract; no real payment, not checked on the Telegram test environment.
10. **Adapt.** Keep: server pricing, order before invoice, the signed payload bound to the buyer, delivery on
    `successful_payment` once per charge, the receipt in the chat. Replace: `MENU` and `Orders` with the
    payments pipeline and your database (reserve stock at pre-checkout). Related: recipes 20 (payments), 52
    (widget to checkout), 96 (subscriptions), `references/mini-apps/payments.md`.
