# 05 — Interactive widget in a private chat (production)

Registry rows: `10.4-W01`, `10.4-W02`, `10.4-W04`, `10.4-W07`, `10.4-W08` (`recipes/registry.json`). Verified 2026-11-12, Bot API 10.4.

1. **Request and visible result.** “Instead of re-sending the order every time someone changes delivery, show one card that updates.” — An order card inside the message: items, Standard/Express toggle, total, Confirm. Taps update it in place (no “edited” mark); errors read “Too fast — try again”, “The bot didn't answer. Your order is unchanged.”; the caption “Order #1042 · $23.50” is what the chat list, notifications and old apps show; a “Change in chat” button is the plain alternative.
2. **Why the new feature.** 10.4 widgets: interactive state inside one message, drawn natively in the chat's theme, without hosting a Mini App. Before: edit text + keyboard, or open a web app.
3. **Requirements.** Bot API ≥ 10.4. **Production: private chats only.** `allow_queries: true`. `allowed_updates` must include `widget_query`. SDKs on 2026-11-12 need an adapter (aiogram/grammY).
4. **Payload.** Full request sequence: `examples/payloads/r05-private-widget.json` (generated from the code); incoming fixture: `examples/fixtures/widget_query_ship.json`. Key part:
   ```json
   {"chat_id": 111111111, "html": "<style>…</style><div class=\"c\">…</div><script>…</script>",
    "chat_data": "{\"o\":\"1042\",…,\"st\":\"draft\",\"r\":0}", "caption": "Order #1042 · $23.50 · Standard delivery",
    "allow_queries": true, "reply_markup": {"inline_keyboard": [[{"text": "Change in chat", "callback_data": "order:1042:edit"}]]}}
   ```
5. **Code.** Widget: `examples/widgets/order-card.html` (theme vars, safe area, RTL-safe layout, revisions, every error code). Bot: `examples/python/tgkit/widgets.py` (`check_widget`, `WidgetStore`, `handle_widget_query`), `examples/python/recipes/r05_private_widget.py`, TS `examples/ts/recipes.ts::privateWidget`. Adapters: `examples/python/sdk_aiogram/adapter.py`, `examples/ts/sdk-grammy/adapter.ts`.
6. **Sequence and state.** sendWidget → Message.widget → tap → `widget_query{id, from, chat, message_id, data:'ship:fast'}` → decide against the stored state → editMessageWidgetData(chat_data with r+1) → commit → answerWidgetQuery({ok, s, r}) → widget redraws; duplicate query id → skipped; flood wait → error answer, state not committed.
7. **Result.** Mock-up: `Order #1042 · 2 × Margherita · 1 × Lemonade · [Standard][Express] · Total $28.50 · [Confirm order]`.
8. **Typical mistake, limits, alternative.** Trusting widget-sent state; changing state inside the answer (it can't); answering twice or not at all (TIMEOUT); no caption; `fetch()` / `<input>` / `100vh` (absent in the sandbox); measuring size by string length. Alternative: inline keyboard card (any chat) or a Mini App (text input).
9. **Run and verify.** py -3 examples/python/recipes/r05_private_widget.py · py -3 scripts/validate_widget.py examples/widgets/order-card.html --caption 'Order #1042' · tests/test_widgets.py. Evidence: offline contract + real aiogram/grammY routing tests; not rendered in Telegram clients.
10. **Adapt.** Copy `widgets.py` and the HTML skeleton; adapt `decide()` to your order service and the HTML texts (i18n table inside). Keep data ≤ 1024 bytes; keep the full record server-side. Related: 06, 07, `widgets.md`.
