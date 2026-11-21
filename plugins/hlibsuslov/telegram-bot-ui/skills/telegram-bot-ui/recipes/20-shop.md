# 20 — Shop: catalog → product → cart → checkout with Telegram Stars or a provider invoice

Product recipe (combines mechanisms; no registry row of its own). Uses `10.3-K01` disabled
buttons, `10.3-R04` compact tables, 9.4 button `style`. Verified 2026-11-15 against Bot API 10.4
(newest release on that date, 2026-11-09). Payments depth: `references/payments-and-stars.md`
(payments stream); index of all product recipes: `references/use-case-playbooks.md`.
Tags: **[API]** = API requirement, **[official]** = official recommendation, **[heuristic]** =
design heuristic of this skill.

1. **Request and visible result.** “We sell coffee beans. Make a shop bot: browse, add to cart,
   pay with Stars or by card, and stop people paying twice or for something that just sold out.”
   — One menu message that changes in place (catalog → product → cart → checkout), sold-out
   coffees visible but greyed out, a `− 1 +` stepper whose `+` greys out at the stock limit, one
   invoice per cart, a pre-checkout refusal that says why in the buyer's language, and one rich
   receipt with a compact table.
2. **Why these features.**
   - `disabled: {}` (10.3) for sold-out items and the stepper ends: the option stays visible with
     its price, so the user learns it exists **[heuristic]**; the server still re-checks every
     tap because a disabled button does not stop stale or crafted callbacks **[API: "does
     nothing" — the check is yours]**.
   - `style: "primary"` on the one next step (Add / Checkout / Pay ⭐), `"danger"` on *Empty the
     cart* (9.4) **[heuristic: one primary per screen]**.
   - Stars invoice: `currency: "XTR"`, `provider_token: ""`, **exactly one** `LabeledPrice`
     **[API]**; provider invoice: ISO 4217 currency, provider token from @BotFather, any number of
     price parts, `need_name` etc. (ignored for Stars) **[API]**.
   - `answerPreCheckoutQuery` within **10 seconds**, `error_message` shown to the user when
     `ok: false` **[API]**.
   - Receipt as a Rich Message with an `is_compact` table (10.3) — a list people compare
     **[heuristic]**.
3. **Requirements.** Bot API ≥ 10.3 for disabled buttons and compact tables (everything else is
   older). Production. Private chat with the bot. Card payments need a provider connected in
   @BotFather; digital goods and services must be sold for Stars, and a bot that sells them must
   answer `/paysupport` **[official, https://core.telegram.org/bots/payments-stars]**. `allowed_updates` must include
   `pre_checkout_query` and `message` (successful payments arrive as a service message).
4. **Payload.** Full request sequence: `examples/payloads/r20-shop.json`. Incoming fixtures:
   `examples/fixtures/usecase_pre_checkout_stars.json`,
   `examples/fixtures/usecase_successful_payment_stars.json`,
   `examples/fixtures/usecase_pre_checkout_card.json`.

   | Screen | Message | Buttons (row by row) | Leaves to |
   |---|---|---|---|
   | catalog | “Coffee beans … Pick a coffee:” | one row per coffee (`disabled` if sold out) · `Cart (n)` | item, cart |
   | item | title, notes, price, “In your cart: n” | `−` `n`(disabled) `+` · `Add to cart` / `Cart (n)` primary · `← Back` | item (qty), cart, back |
   | cart / empty cart | lines + total / “Your cart is empty” | `Checkout` primary · `Empty the cart` danger · `← Back` / `Catalog` | pay, catalog |
   | pay | order id, total | `Pay ⭐ 500` primary · `Pay by card · €18.40` · `← Back` | invoice (new message) |
   | invoice | sent by Telegram | Pay (client-drawn) | pre-checkout → successful payment |
   | receipt | rich: heading, compact table, note | — | — |

   Key parts:
   ```json
   {"method": "sendInvoice", "params": {"chat_id": 111111111, "title": "Order SH-1001",
     "description": "2 bag(s) of coffee, shipped in 2 days", "payload": "o:SH-1001",
     "provider_token": "", "currency": "XTR", "prices": [{"label": "Order SH-1001", "amount": 500}]}}
   {"method": "answerPreCheckoutQuery", "params": {"pre_checkout_query_id": "4382000000000920003",
     "ok": false, "error_message": "На жаль, Кенія Ньєрі AA щойно закінчилась. …"}}
   ```
5. **Code.** `examples/python/recipes/r20_shop.py` (`Shop.order_for_cart`, `send_invoice`,
   `on_pre_checkout`, `on_successful_payment`, `send_receipt`) on top of
   `examples/python/tgkit/flows.py` (`ScreenFlow`, `OnceStore`, `UpdateDedup`, `btn`, `kb`) and
   `examples/python/tgkit/rich.py::table`. TypeScript twin: `examples/ts/usecases/shop.ts`.
6. **Sequence and state.**
   ```mermaid
   stateDiagram-v2
     [*] --> catalog: /start
     catalog --> item: tap coffee
     item --> item: − / + (cart_rev += 1)
     item --> cart
     cart --> pay: Checkout (order per cart_rev)
     pay --> invoice: Pay ⭐ / card (once per order+method)
     invoice --> refused: pre_checkout ok=false (changed / sold out)
     invoice --> paid: pre_checkout ok=true → successful_payment (once per charge id)
     paid --> [*]: receipt, cart cleared
   ```
   Order record: `{id, user, items, stars, cents, status: pending|superseded|paid, charge_id}`.
   A new cart revision supersedes the pending order, so an old invoice is refused at
   pre-checkout with “Your cart changed…”. Pre-checkout compares `currency` and `total_amount`
   with the stored order and checks stock; `successful_payment` is keyed by
   `telegram_payment_charge_id` (store it — refunds need it: `refundStarPayment(user_id,
   telegram_payment_charge_id)` **[API]**).
7. **Result.** Mock-ups (not client screenshots), English / Ukrainian:
   ```
   Ethiopia Yirgacheffe                      Кенія Ньєрі AA
   Jasmine, bergamot, light roast.           Чорна смородина, яскрава кислотність.
   Price: ⭐ 250 · €9.20                      Ціна: ⭐ 300 · €11.00
   In your cart: 2                           У кошику: 1
   [ − ] [ 2 ] [ + ]                         [ − ] [ 1 ] [ + ]   (+ greyed: last bag)
   [ Cart (2) ]                              [ Кошик (1) ]
   [ ← Back ]                                [ ← Назад ]
   ```
8. **Typical mistake, limits, alternative.** Mistakes: a second invoice for every “Pay” tap;
   trusting the amount in `pre_checkout_query` without comparing it to your order; fulfilling on
   the pre-checkout instead of `successful_payment`; fulfilling twice when the update is
   redelivered; hiding sold-out items; several price parts or a tip for Stars (not supported);
   provider tokens in code (offline payloads carry `PROVIDER_TOKEN_FROM_ENV`; live mode reads the
   env var `SHOP_PROVIDER_TOKEN`). Limits **[API]**: title 1-32 chars, description 1-255,
   payload 1-128 bytes, pre-checkout answer within 10 s, `callback_data` ≤ 64 bytes (the scheme
   `sh:<ver>:qty:<key>:<±1>` stays under 20). Failure paths in the run: crafted add for a sold-out
   item → alert; double tap on an old render → “screen has changed”; same cart → “Your invoice is
   below ↓”, no new invoice; stock gone while paying → refusal in Ukrainian; another user's tap →
   “belongs to someone else”. Alternative: a Mini App storefront for big catalogs with search;
   a widget order card (recipe 05) once the order exists.
9. **Run and verify.** `py -3 examples/python/recipes/r20_shop.py` (10 self-checks) ·
   `py -3 -m unittest tests/test_usecases.py` (validators on every markup, 64-byte callbacks,
   copy in en/uk, payload drift) · `py -3 scripts/validate_keyboard.py` on any extracted markup.
   Evidence: offline contract; real Stars and provider payments were not executed.
10. **Adapt.** Keep: order per cart revision, `OnceStore` keys (`<order>:<method>` for invoices,
    charge id for fulfilment), server re-checks in pre-checkout. Replace: `PRODUCTS` with your
    catalog (localized titles), stock with a reservation in your DB (reserve at pre-checkout,
    commit at successful payment, release after a timeout), the receipt columns. Add shipping
    with `is_flexible` + `shipping_query` for physical goods with variable delivery; Stars
    subscriptions are in recipe 25. Related: `recipes/03-multi-step-form.md` (address form),
    `references/buttons-and-styles.md#disabled-buttons`, `references/tables.md#compact-tables`.
