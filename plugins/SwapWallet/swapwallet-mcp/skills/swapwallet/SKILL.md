---
name: swapwallet
description: Use the SwapWallet MCP tools safely. Use when the user asks about their SwapWallet balance, profit and loss, transactions or deposit address, or wants to swap, transfer or withdraw crypto or toman through SwapWallet.
---

# Using SwapWallet

SwapWallet is a custodial crypto exchange and wallet. Its MCP server (`swapwallet`) reads the user's own account and files money-moving requests that the user approves in Telegram.

## Reading the account

- Call the tools for balances, prices, profit and loss and history; never answer from memory.
- `get_total_balance` gives the whole portfolio; `get_balance` only the tokens you name.
- Amounts are decimal strings. `token` and `network` are enums: use the exact values in the tool's input schema.

## Moving money (request_* tools)

- `request_swap`, `request_transfer`, `request_crypto_withdraw` and `request_fiat_withdraw` never move money themselves. Each one prices the action and sends it to the user's Telegram (the SwapWallet bot) with Approve and Cancel buttons, then returns at once with status `PENDING`.
- Before calling one, confirm the amount, token, destination and (for crypto) the network with the user. A wrong network or address can lose funds.
- After calling one, tell the user to open Telegram and approve or cancel it there, and that it expires in 15 minutes. Show the returned preview (amounts, fees, destination); do not invent prices or fees.
- Never say a swap, transfer or withdrawal has happened until `get_action_request` reports `EXECUTED`. `PENDING` only means "waiting for the user in Telegram". The other outcomes are `REJECTED`, `EXPIRED` and `FAILED` (with a `failureReason`).
- Transfers go only to the user's saved contacts (`get_contacts`); toman withdrawals only to a verified IBAN (`get_ibans`).

## Known errors

- `MCP_TELEGRAM_NOT_LINKED`: the account is not linked to Telegram, so no request can be approved. Ask the user to link it in the SwapWallet app.
- `MCP_TWO_FACTOR_ACTIVE`: with two-factor authentication on, crypto withdrawals and transfers must be made in the app. Swaps and toman withdrawals still work.
- A missing scope means the user did not grant it on the consent page; they can reconnect and grant it.

Reference: https://swapwallet.app/docs/mcp
