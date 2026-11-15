# 09 — Monitoring bot upgraded to 10.3/10.4 (btc-tracker case study)

Registry rows: none of its own — combines `10.4-W02`, `10.4-W03`, `10.4-W08`, `10.4-W09`,
`10.3-R04`, `10.3-K01`, `10.3-K02` with 9.4 custom emoji. Verified 2026-11-12, Bot API 10.4.
Background: `references/case-study-btc-tracker.md`, `references/visual-language.md`.

1. **Request and visible result.** “Our wallet tracker sends four messages per transaction, the
   icons look mismatched, and the address check is a wall of code lines.” — One card per
   transaction that fills its progress bar 0 → 3 in place (no "edited" mark), a single
   “✅ Confirmed” message only if the user wants that sound, a live BTC price card, the address
   check as a compact table, taken address numbers greyed out, and every icon from one family —
   in titles and on buttons.
2. **Why the new features.** 10.4 widgets keep one message alive with silent state edits; a
   shared widget pushes one price to every copy; 10.3 compact tables, disabled buttons and
   `force_reply` on keyboards. Before: a message per confirmation, price lines repeated, errors
   explained only after a tap.
3. **Requirements.** Widgets: Bot API ≥ 10.4, **production private chats only**, aiogram 3.31
   needs the adapter's `SendWidget` method class (`examples/python/sdk_aiogram/adapter.py`); no
   `widget_query` needed (state is pushed). Custom emoji: owner Premium or Fragment usernames.
   Rich table: 10.3. Fallback path works everywhere.
4. **Payload.** Full sequence: `examples/payloads/r09-tracker-bot.json`; icon data:
   `examples/case-studies/btc-tracker/icon-map.json`. Key part (one confirmation):
   ```json
   {"method": "editMessageWidgetData", "params": {"chat_id": 111111111, "message_id": 1002,
    "chat_data": "{\"d\":\"in\",\"w\":\"Main\",\"amt\":\"0.0125\",\"usd\":\"1215.63\",\"conf\":2,\"target\":3,\"url\":\"https://mempool.space/tx/…\",\"tx\":\"…\",\"r\":2}"}}
   ```
5. **Code.** `examples/python/recipes/r09_tracker_bot.py` (`TxCard`, `price_ticker`,
   `verify_addresses_table`, `analysis_short_list`, `position_picker`, `main_menu`),
   `examples/python/tgkit/icons.py` (`IconSystem`), widgets
   `examples/widgets/tx-confirmations.html` and `examples/widgets/price-ticker.html`.
6. **Sequence and state.** poller sees tx → `sendWidget(chat_data conf 0, caption, Explorer +
   Copy TXID buttons)` → each new confirmation (replays ignored) → `editMessageWidgetData` (r+1)
   + `editMessageCaption` (chat list stays true) → at target: `sendMessage` reply to the card
   only if the user enabled sound for that level. Price: `sendWidget(is_shared)` once →
   `editSharedWidgetData(cache_time 10)` on changes → `sendSharedWidget` per user.
7. **Result.** Mock-up (not a client screenshot):
   `↘ Incoming · Main / +0.0125 BTC / ≈ $1215.63 / ▰▰▱ Confirmation 2 of 3 / [Copy TXID] [Explorer]`.
8. **Typical mistake, limits, alternative.** Expecting a widget edit to notify (it's silent);
   a widget per alert in groups (test server only); a new widget per confirmation; mixing icon
   families; Unicode emoji in a label that already has a custom icon; tables for 4 facts.
   Alternative: one text message edited in place (built in as the fallback).
9. **Run and verify.** `py -3 examples/python/recipes/r09_tracker_bot.py` ·
   `py -3 scripts/validate_widget.py examples/widgets/tx-confirmations.html --caption "…"` ·
   `py -3 scripts/audit_icons.py examples/case-studies/btc-tracker/icon-map.json` · tests in
   `tests/test_visual_language.py`. Evidence: offline contract; not rendered in Telegram.
10. **Adapt.** Copy `TxCard` (keep the replay guard and the sound rule) and `IconSystem`;
    rebuild the icon map from one family with `examples/python/icons/build_icon_map.py`; map your
    i18n keys onto the widget's built-in texts or pass labels in `chat_data`. Related: 05, 06,
    03, `references/bot-archetypes.md#monitoring--alerts-uptime-orders-status-price-alerts`.
