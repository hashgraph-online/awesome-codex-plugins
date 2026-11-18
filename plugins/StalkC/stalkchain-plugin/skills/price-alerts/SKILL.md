---
name: price-alerts
description: Set up, list and delete StalkChain alerts by email or webhook. Use when the user asks to be alerted or notified when a token goes above or below a price, when smart money or several tracked traders buy a token, wants to see their alerts, or wants to cancel or delete an alert.
argument-hint: "[token and price, e.g. BONK above 0.00005]"
---

# Price and smart-money alerts

Create, list and delete the user's alerts with the StalkChain connector. Creating and deleting change the user's account, so **always confirm the details before you do either.**

## Alert kinds

- `price_above` / `price_below`: fires when the token's USD price crosses `priceUsd`.
- `smart_money_buy`: fires when `minTraders` tracked traders (default 2) buy the token.

Every alert fires **once** and then switches off. Alerts are checked every few minutes, so delivery is not instant. An account can have up to 20 active alerts.

## Create an alert

1. **Get the address.** Alerts need a token address, not a ticker. For a ticker, call `stalkchain_fomo_search` with `q` and `type: "tokens"` (250 credits). If several tokens share the ticker, list them with chain and market cap and ask which one. Never guess.
2. **Current price (optional).** If the user hasn't seen it, show it so they can sanity-check the target: `stalkchain_token_prices` with `tokens: [mint]` for Solana, or `stalkchain_token_prices_multichain` for other chains (250). The create call also returns the current price, and refuses a target the price has already crossed.
3. **Confirm**, in one short message: token (ticker and shortened address), chain, kind, target price or trader count, where it goes (the account's email by default, or the webhook URL), and that it fires once. Wait for a clear yes.
4. **Create** with `stalkchain_alert_create`:
   - `kind`: `"price_above"`, `"price_below"` or `"smart_money_buy"`
   - `token`: the address
   - `chain`: `"solana"` (default), `"ethereum"`, `"base"` or `"bsc"`. Alerts don't cover other chains yet; say so if asked.
   - `priceUsd`: required for the price kinds
   - `minTraders`: for `smart_money_buy`, default 2
   - `channel`: `"email"` (default, the account's email) or `"webhook"` with `webhookUrl`: a Discord webhook, a Slack incoming webhook, or a Telegram bot URL ending `/sendMessage?chat_id=<id>`. Other URLs are refused. Use only a URL the user gave you.
   - `note`: optional, a short reminder the user wants to see when it fires
5. Reply with the alert's id and what will happen.

## List alerts

`stalkchain_alert_list`: show a short table of id, token, kind, target, status and when it last fired. Say how many of the 20 active slots are used.

## Delete an alert

Call `stalkchain_alert_list` first to find the right id. Confirm which alert you're deleting, then call `stalkchain_alert_delete` with `id`. A fired alert is already off; offer to create a new one instead if the user wants it again.

## Rules

- Never create or delete without the user's confirmation in this conversation.
- An alert is a notification, not a trade. This plugin never buys or sells, and an alert won't either.
- If an alert tool isn't available on the connector, say alerts aren't available yet. Don't promise to watch the price yourself.
- Keep raw JSON out of the answer. Data, not financial advice.
