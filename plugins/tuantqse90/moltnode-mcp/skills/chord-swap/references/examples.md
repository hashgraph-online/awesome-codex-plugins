# Examples

Numbers below come from live calls on 2026-10-17; prices move, so always quote again.

## EVM: "Swap 100 USDC for ETH on Base"

1. Tokens: USDC on Base is `0x833589fcd6edb6e08f4c7c32d4f71b54bda02913` (6 decimals, verified); ETH is
   the zero address. 100 USDC = `100000000`.
2. Safety check: not needed for the native coin.
3. Price quote:
   `GET https://api.getchord.xyz/v1/meta/quote?chain=base&tokenIn=0x833589fcd6edb6e08f4c7c32d4f71b54bda02913&tokenOut=0x0000000000000000000000000000000000000000&amount=100000000`
   → `provider: "chord"`, `amountOut` about 0.0411 ETH, price impact 0.00 %.
4. The agent answers:

   > 100 USDC → about 0.0411 ETH on Base (at least 0.0409 ETH with 0.5 % slippage), price impact
   > under 0.01 %, routed by Chord's router. Want me to prepare the transaction for your wallet?

5. The user says yes in their next message and gives the wallet `0xUSER...`. The agent asks again with
   `&taker=0xUSER...`: `tx.to` is the Chord router, `approval` asks `approve(router, 100000000)` on
   USDC, `simulation.ok: true`.
6. The user's wallet sends the approval, then `tx`. The agent checks the receipt and links
   `https://basescan.org/tx/<hash>`.

## Solana: "Buy 0.01 SOL of BONK"

1. `GET https://api.getchord.xyz/v1/chains/solana/search?q=BONK` returned four tokens named BONK on
   2026-10-17. The real one, `DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263`, had about $160k of
   liquidity; the others had $24k, $16 and $2. The agent shows the candidates with full mints and
   their liquidity, and confirms the mint with the user before quoting.
2. `GET https://api.getchord.xyz/v1/security/token/solana/DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263`
   → read `verdict` and any failing checks.
3. `GET https://api.getchord.xyz/v1/sol/trade/quote?mint=DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263&side=buy&amount=10000000&wallet=<user wallet>`
   → `quote.route` `direct` (Orca) or `jupiter`, `outAmount` and `minOut` in BONK's smallest unit.
4. Summary, then wait for the user's yes in a later message.
5. The user's wallet signs `quote.tx` unchanged; the agent sends it with
   `POST https://api.getchord.xyz/v1/sol/trade/send` `{"tx": "<signed, base64>"}` and links
   `https://solscan.io/tx/<signature>`.
