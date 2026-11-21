# 64 — Delivery tracker: one status card per order, edited in place

Product recipe (combines mechanisms; no registry row of its own). Uses `editMessageText`, regular-HTML
`<tg-time>`, `10.3` disabled buttons, inline `force_reply` (10.3), `tgkit.errors` retry policy.
Verified 2026-11-15 against Bot API 10.4 (newest release on that date, 2026-11-09). Index of all
product recipes: `references/use-case-playbooks.md`. Tags: **[API]** = API requirement, **[official]**
= official recommendation, **[heuristic]** = design heuristic of this skill.

1. **Request and visible result.** “After a customer orders, show where the parcel is. One message
   that updates, not ten notifications — but ring the phone when the courier is on the way and when
   it arrives. Let them change the address until we ship.” — One card per order:
   `Order O-5001 / ▰▰▰▱▱ 3/5 · shipped / Expected <time> / Address: …`, edited through placed →
   packed → shipped → out for delivery → delivered. `Track` (URL) appears from shipped,
   `Contact courier` once the courier is out, `Change address` only before shipping and then a greyed
   `Change address · shipped`. Only two moments send a NEW short message; after delivery the card
   asks for a 1–5 rating, once.
2. **Why these features.**
   - Edit in place (`editMessageText`) instead of a message per event: the chat keeps one source of
     truth and one scroll position **[heuristic]**. Edits do not ring the phone, new messages do;
     that is observed client behaviour, not an API guarantee **[heuristic]**, so the two alert
     messages (`out_for_delivery`, `delivered`) are the deliberate exception.
   - `<tg-time unix=… format="wDT">` for ETA and delivery time: each reader sees their own zone
     **[API]**.
   - `disabled: {}` (10.3) on `Change address · shipped`: the option stays visible and the label
     carries the reason; a crafted tap is still refused with the full reason because a disabled
     button only "does nothing" **[API]** and the check is yours.
   - Inline `force_reply` (10.3) on the address prompt: the reply field opens together with the
     `Keep address` button **[API: fixed for the message's lifetime]**.
   - `Machine` + sequence numbers: couriers send events twice and out of order; an older or repeated
     `seq` is dropped, a skipping event is refused **without** advancing `seq` **[heuristic]**.
   - Private-chat alternative: a live widget card (recipes 05 and 09, `references/widgets.md`,
     `references/widget-*.md`) updates its data without edit churn **[API: widgets in private chats
     only in production, 10.4]**; this recipe is the version that works in every chat.
3. **Requirements.** Bot API ≥ 10.3 for the disabled button and inline `force_reply`
   (`<tg-time>` and edits are older). Production. Private chat. A source of courier events with a
   per-order sequence number (webhook, polling); a stored `card` message id per order.
   `allowed_updates` must include `message` and `callback_query`. A card message that the user
   deleted cannot be edited: plan the fallback (point 8).
4. **Payload.** Full request sequence: `examples/payloads/r64-delivery-tracker.json`. Incoming
   fixture (courier webhook, not a Telegram update): `examples/fixtures/usecase_delivery_courier_events.json`.

   | Screen | Message | Buttons (row by row) | Leaves to |
   |---|---|---|---|
   | card: placed / packed | `▰▱▱▱▱ 1/5 · placed`, ETA, address | `Change address` | address prompt |
   | card: shipped | `▰▰▰▱▱ 3/5 · shipped` | `Track` (URL) · `Change address · shipped` (disabled) | — |
   | card: out for delivery | `▰▰▰▰▱ 4/5` | `Track` · `Contact courier` · disabled address | courier info (alert) |
   | card: delivered | `▰▰▰▰▰ 5/5`, delivery time, “How was the delivery?” | `Track` · `1` `2` `3` `4` `5` | card with “you rated it n/5” |
   | alert (new message) | “O-5001 is out for delivery — Courier Taras, arriving 13:00.” / “O-5001 is delivered.” | — | — |
   | address prompt | “Send the new delivery address as a reply…” (**force_reply**) | `Keep address` | card edit |

   Key parts:
   ```json
   {"method": "editMessageText", "params": {"chat_id": 111111111, "message_id": 1001,
     "text": "<b>Order O-5001</b>\n▰▰▰▱▱ 3/5 · shipped\nExpected <tg-time unix=\"1795060800\" format=\"wDT\">19.11 04:00</tg-time>\nAddress: 5 Long Market, Gdansk",
     "parse_mode": "HTML", "reply_markup": {"inline_keyboard": [[{"text": "Track", "url": "https://track.example.com/O-5001"}],
       [{"text": "Change address · shipped", "disabled": {}}]]}}}
   ```
5. **Code.** `examples/python/recipes/r64_delivery_tracker.py` (`Tracker.card`, `refresh`,
   `on_courier_event`, `on_callback`, `on_text`) on top of `examples/python/tgkit/flows.py`
   (`Machine`, `OnceStore`, `btn`, `kb`, `pack`, `tg_time`), `examples/python/tgkit/errors.py`
   (`call_with_policy`) and `tgkit.transport.TelegramErrorResponse` for scripting failures. No
   TypeScript twin.
6. **Sequence and state.**
   ```mermaid
   stateDiagram-v2
     [*] --> placed: order created (card sent)
     placed --> packed: pack
     packed --> shipped: ship
     shipped --> out_for_delivery: out (+ alert message)
     out_for_delivery --> delivered: deliver (+ alert message, rating row)
     delivered --> [*]: rated once
   ```
   Order record: `{id, user, lang, status, address, eta, seq, rev, card, courier, rating}`. `rev` is in
   the card's callbacks (`dt:<rev>:<action>:<order>[:<n>]`) and bumps on every edit, so buttons of an
   older card are stale. Courier event handling order: unknown order → older or repeated `seq` →
   ignored → `Machine` refuses a skipped state (seq untouched) → apply, silent edit, alert only for
   `out_for_delivery` and `delivered`. Edit failures: `message to edit not found` → `sendMessage` of a
   fresh card, the new `message_id` replaces the stored one; `429` → `call_with_policy` sleeps
   `max(retry_after, backoff)` (never a tight loop) and retries; `message is not modified` → success.
7. **Result.** Mock-ups (not client screenshots), English / Ukrainian:
   ```
   Order O-5001                          Замовлення O-5002
   ▰▰▰▰▱ 4/5 · out for delivery          ▰▰▰▱▱ 3/5 · відправлено
   Expected Thu 19.11 13:00              Очікуємо Чт 19.11 …
   Address: 5 Long Market, Gdansk        Адреса: вул. Хрещатик 1, Київ
   [ Track ]                             [ Відстежити ]
   [ Contact courier ]
   [ Change address · shipped ]          [ Адреса · вже відправлено ]
   ```
8. **Typical mistake, limits, alternative.** Mistakes: a new message per status (the chat becomes a
   log and the phone rings ten times); trusting arrival order of courier events; advancing the
   sequence on a refused event (the legitimate one that follows is then dropped as “old”); keeping
   the old `message_id` after a failed edit; retrying a 429 immediately; honouring a disabled button
   as the only guard. Limits **[API]**: `callback_data` ≤ 64 bytes (`dt:<ver>:rate:O-5001:5`);
   `answerCallbackQuery` text ≤ 200 chars; the URL button needs a valid URL. Failure paths in the run:
   late `pack` (seq 2 after 3) and a replayed `ship` → ignored; `deliver` while shipped → refused;
   `Change address` after shipping → alert with the reason; deleted card → fresh card; 429 with
   `retry_after: 3` → one wait of 3 s; a stranger's rating tap → alert; a rating tap from an older card
   → stale toast; a second rating → toast. Alternative: the private-chat widget (point 2).
9. **Run and verify.** `py -3 examples/python/recipes/r64_delivery_tracker.py` (11 self-checks) ·
   `py -3 -m unittest tests/test_usecases.py` (validators on every markup, 64-byte callbacks, copy in
   en/uk, payload drift). Evidence: offline contract; whether an edit rings a given client was not
   measured here.
10. **Adapt.** Keep: one card id per order, `Machine` + `seq`, the alert-only-twice rule, the
    `rev` guard, the not-found and 429 handling. Replace: `STEPS` and `MACHINE` (a pickup order has
    no courier), copy, the tracking URL, the in-memory dicts, `Contact courier` (a masked-phone relay
    is safer than showing a number), the event source. Add a “problem with delivery” escalation to
    recipe 21 (support desk). Related: `recipes/05-private-widget.md`, `recipes/09-tracker-bot.md`
    (widget updates), `recipes/20-shop.md` (the order), `references/errors-and-fallbacks.md`,
    `references/streaming-and-editing.md`.
