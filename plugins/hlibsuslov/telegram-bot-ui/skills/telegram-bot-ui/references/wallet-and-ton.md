# Wallet and TON features (Bot API 10.4)

> Verified 2026-11-12 (Widgets guide "Payments with the wallet", `WidgetQueryType*`,
> `TonWalletCard`, `TonWalletTransfer`, `MessageEntity`, `RichTextTonAddress`). This is the
> Telegram side only — not a blockchain tutorial. Recipe: [07 wallet](../recipes/07-wallet.md).

## What Telegram provides

| Thing | Where | Trust |
|---|---|---|
| `widget_query.type = {"type":"data","wallet_card"?}` | request made with `{wallet: true}` on a tap | `from` authenticated by Telegram; the card is the **profile** wallet |
| `{"type":"sign_data","wallet","sign_data"}` | after `TelegramWidget.wallet.signData` | **you** verify the ed25519 signature, domain `bot<bot_id>`, timestamp, key↔address |
| `{"type":"sent_transaction","wallet","msg_hash"}` | after `wallet.sendTransaction` | a **notification**, not proof of payment |
| `ChatFullInfo.ton_wallet_card` (`TonWalletCard` → stickers `TonWalletCardSticker{position: AreaPosition, nft: TonNft}`) | `getChat` on a private chat | public profile data |
| `Message.ton_wallet_transfer` (`TonWalletTransfer`) | service message | amount negative = outgoing; empty `transaction_id` = not sent yet; `comment` omitted if encrypted |
| `MessageEntity` `ton_address`; `RichTextTonAddress{text,address}` | text / rich text | read `address`, not the possibly shortened `text` |

Amounts are decimal strings in the smallest units (nanotons): never parse as float for money.

## Payment flow

1. Draw "Pay" only when `TelegramWidget.wallet` is not `null` (no wallet in this app/country,
   preview, or no requests allowed → offer another path).
2. Tap → `request("pay:<order>", {wallet: true})` → bot gets `type: data` (+ `wallet_card`).
3. Bot creates the order server-side (`INVOICED`; a replayed `pay:` within validity gets the
   **same** request; an order that is awaiting/paid/disputed gets its state, **never** a new
   transaction) and answers a TON Connect `sendTransaction`
   request: `{valid_until, messages:[{address, amount: "<nanotons>", payload?}]}` — **no `from`**
   (the device wallet pays; it may differ from the profile card). Put the order reference in a
   text-comment `payload` built with your TON library.
4. The widget calls `wallet.sendTransaction(tx, "paid:<order>")` within 10 s of the answer.
5. Bot gets `sent_transaction` → order becomes **AWAITING_CONFIRMATION**, not paid. Remember
   each `msg_hash` → order: one transfer can't be claimed for two orders.
6. Your chain checker verifies sender, recipient, amount, comment and success → **PAID** (or
   MISMATCH) → `editMessageWidgetData` pushes the state; tell the user in plain words.
7. Widget errors: `REJECTED` (user declined), `BAD_REQUEST` (wallet refused), `TIMEOUT` — the
   payment **may** have gone out: keep Pay **disabled** ("Checking the order…") until a `sync`
   answer or a state push says otherwise; never offer to pay again blindly.

Telegram ↔ your bot ↔ the chain are three trust boundaries; only the chain proves a payment.

## Signing

`signData` payload: TON Connect `{type:'text'|'binary'|'cell', …}`. The bot first issues a
**single-use challenge** (user id + nonce + time) and the widget signs exactly that text. Bot
checks: signature with `wallet.public_key` (absent → can't verify, say so), the key belongs to
`wallet.address` (derive the address from `state_init`), domain `bot<bot_id>`, payload = the
challenge, fresh timestamp; then marks the challenge used. Without the challenge and the address
binding, a signature for wallet B could be replayed as wallet A. Link the proven address; store
the link, not the signature (`tgkit.wallet.SignChallenge`, `on_sign_data`).

## Wallet cards and transfers

Show a card summary (address shortened `UQAs…0003`, balance, NFT count) only to the user it
belongs to or where they shared it. `AreaPosition` (renamed from `StoryAreaPosition` in 10.4,
fields unchanged) positions stickers on the card. Transfers: phrase as "Sent 1.25 TON to …
(pending)"; don't claim settlement from a service message alone.

## TON addresses in text

Offer a `copy_text` button for an address entity; never rebuild addresses from display text;
mask nothing (addresses are public), but treat `bank_card_number` entities as sensitive
(`specialized-updates.md#bank-card-and-ton-entities`).
