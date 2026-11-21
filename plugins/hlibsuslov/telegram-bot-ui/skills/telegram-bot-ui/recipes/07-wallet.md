# 07 — Wallet interaction from a widget (pay, sign, confirm)

Registry rows: `10.4-W06`, `10.4-T01`, `10.4-T02`, `10.4-X03` (`recipes/registry.json`). Verified 2026-11-12, Bot API 10.4.

1. **Request and visible result.** “Let users pay 1.25 TON for order 42 right in the chat and show when it's actually paid.” — A pay card: “Pay with Wallet” → the app's own wallet window → “Waiting for the network…” → “Paid ✓” only after the bot checked the chain; declines and refusals explained; after a timeout the card says “Don't pay again — checking the order…”.
2. **Why the new feature.** 10.4 widgets carry TON Connect-format wallet requests (`{wallet: true}`, `sendTransaction`, `signData`) with Telegram's built-in wallet — no manifest/bridge; the bot also gets profile wallet cards and transfer service messages.
3. **Requirements.** Bot API ≥ 10.4. Production: private chats; the user must have the wallet in their app (otherwise `TelegramWidget.wallet` is null). Your own TON indexer/node for confirmation and an ed25519 verifier for signatures.
4. **Payload.** Full request sequence: `examples/payloads/r07-wallet.json` (generated from the code); incoming fixture: `examples/fixtures/widget_query_sent_transaction.json`. Key part:
   ```json
   {"ok": true, "tx": {"valid_until": 1762900300, "messages": [{"address": "UQAs…0005", "amount": "1250000000"}]}}
   ```
5. **Code.** `examples/widgets/wallet-pay.html`, `examples/python/tgkit/wallet.py` (order states, `transaction_request`, `on_sent_transaction`, `on_sign_data`, `describe_transfer`), `examples/python/recipes/r07_wallet.py`, TS `examples/ts/recipes.ts::walletPayment`.
6. **Sequence and state.** tap → widget_query{type: data, wallet_card} → order INVOICED → answer tx (no `from`) → wallet.sendTransaction → widget_query{type: sent_transaction, wallet, msg_hash} → AWAITING → chain check → PAID / MISMATCH → editMessageWidgetData. Sign: widget_query{type: sign_data} → verify (domain bot<bot_id>).
7. **Result.** Mock-up: `Order #42 · 1.25 TON · [Waiting for the network…]` → `[Paid ✓]`.
8. **Typical mistake, limits, alternative.** Marking paid on `sent_transaction`; float amounts; putting `from` in the transaction; re-asking for payment after TIMEOUT; trusting a profile card as the paying wallet. Alternative: Telegram Stars invoices (`sendInvoice`) or a payment link.
9. **Run and verify.** py -3 examples/python/recipes/r07_wallet.py · tests/test_widgets.py. Evidence: offline contract with injected chain/signature fakes; real chain checks are outside this repo.
10. **Adapt.** Copy the order state machine; implement `ChainVerifier` and `SignatureVerifier` with your TON stack; add the comment payload. Related: `wallet-and-ton.md`, 05.
