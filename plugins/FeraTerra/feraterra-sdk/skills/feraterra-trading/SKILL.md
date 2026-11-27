---
name: feraterra-trading
description: Guides autonomous AI agents and developers in onboarding wallets, previewing cross-margin orders, quoting with mark pegs, executing zero-capital arbitrage and liquidations, and verifying cryptographic ledger tips on FeraTerra / Arena Exchange via MCP, Python SDK, or C++23 HFT wire. Use when trading, market-making, integrating feraterra-sdk, calling Arena MCP tools, or building quantitative bots against feraterra.app.
---

# FeraTerra / Arena Exchange Trading & Quantitative SDK Skill

Use this skill when interacting with **FeraTerra / Arena Exchange** (`https://feraterra.app`, public Base Sepolia testnet `https://testnet.feraterra.app`), configuring the 24-tool MCP gateway (`feraterra-sdk`), writing Python bots (`import feraterra_sdk`), or integrating the 64-byte C++23 HFT binary wire (`feraterra::hft_client`).

## 1. Fixed-Point Scales (Zero Floating-Point Drift)

All engine prices, quantities, and collateral balances use deterministic 64-bit integer fixed-point arithmetic:

| Quantity | Integer Unit | Scale Factor | Example Conversion | Python SDK Helpers |
| :--- | :--- | :--- | :--- | :--- |
| **Price** | `1 tick = $0.01` | `100` ticks / `$1.00` | `$50,000.00` = `5_000_000` ticks | `usd_to_price_ticks("50000.00")`, `price_ticks_to_usd_str(ticks)` |
| **Order / Position Size** | `1 lot = 1e-4` base | `10_000` lots / `1.0` base | `0.0500 BTC` = `500` lots | `base_to_qty_lots("0.0500")`, `qty_lots_to_base_str(lots)` |
| **USD Collateral / PnL** | `1 micro = $1e-6` | `1_000_000` micro / `$1.00` | `$10,000.00` = `10_000_000_000` micro | `usd_to_micro("10000.00")`, `micro_to_usd_str(micro)` |

MCP tools accept human-readable decimal strings/numbers (`price_usd`, `amount_base`, `min_profit_usd`) **or** exact integer units (`price_ticks`, `qty_lots`, `min_profit_micro`). Prefer integer ticks/lots/micros in tight algorithmic loops.

## 2. MCP Connectivity: Zero-Install Remote vs. Local Guardrailed Trading

### Option A — Zero-Install Remote Streamable HTTP MCP (Read-Only & Previews)
Connect immediately with zero local dependencies or keys for market discovery (`arena_list_markets`), L2/L3 order books (`arena_get_orderbook`), Gladiator standings (`arena_get_leaderboard`), ledger-tip verification (`arena_verify_ledger_tip`), and stateless order dry-runs (`arena_preview_order`):

```json
{
  "mcpServers": {
    "feraterra-remote": {
      "type": "streamable-http",
      "url": "https://mcp.feraterra.app/mcp"
    }
  }
}
```

### Option B — Local `stdio` Trading MCP (EIP-191 Signing & Notional Caps)
For authenticated order entry, quoting, wallet onboarding, and L2 deposits, run the zero-dependency Python MCP server locally via `uvx feraterra-sdk --testnet --max-order-notional-usd 5000` (or configure `mcpServers` with pre-dispatch risk guardrails):

```json
{
  "mcpServers": {
    "feraterra-trading": {
      "command": "uvx",
      "args": [
        "feraterra-sdk",
        "--testnet",
        "--max-order-notional-usd",
        "5000"
      ]
    }
  }
}
```

- Keys (`EthWalletSigner`, `ARENA_API_SECRET`) remain strictly inside your local process.
- `--max-order-notional-usd 5000` rejects oversize orders locally before network dispatch; add `--read-only` to hard-disable all mutating tools.

## 3. Standard Agent Execution Workflow

### Step 1: Discover Markets & Fixed-Point Specs
- Over MCP: call `arena_health_and_manifest` and `arena_list_markets` (`kind="perp"` or `""` for all Spot, Perp, FormulaPerp, BoundedClaim, and SpreadBook markets).
- Over HTTPS: fetch `GET https://testnet.feraterra.app/llms.txt` and `GET https://testnet.feraterra.app/openapi.json`.

### Step 2: Self-Service Testnet Onboarding (`arena_onboard_and_deposit`)
Provision an ephemeral `secp256k1` wallet, authenticate via EIP-191 (`POST /auth/challenge` -> `POST /auth/login`), mint Base Sepolia (`chain_id=84532`) testnet USD + gas via `POST /faucet`, and deposit ERC-20 margin into the L2 `Clearinghouse` contract in one MCP call:

```json
{
  "name": "arena_onboard_and_deposit",
  "arguments": {
    "generate_ephemeral": true,
    "request_faucet": true,
    "faucet_amount": "10000",
    "drip_gas": true,
    "deposit_onchain": true,
    "deposit_amount": "10000",
    "wait_for_credit": true
  }
}
```

### Step 3: Always Dry-Run First with Stateless `arena_preview_order`
Before placing any live order, simulate execution via `arena_preview_order` (`POST /order/preview`). It performs **zero WAL, L3 order book, or balance mutation**:

- **Unfunded / Stateless Mode (`account_id=0`):** Simulates immediate L3 fills, VWAP slippage, resting remainder, and maker/taker fees or rebates without requiring an account or login.
- **Funded Portfolio Mode (`account_id=<funded_id>`):** Computes exact pre-trade and post-trade cross-margin portfolio requirements (`IMR`, `MMR`, free collateral, and rejection reasons) against your live positions.

```json
{
  "name": "arena_preview_order",
  "arguments": {
    "account_id": 0,
    "symbol": "BTC/USD:USD",
    "side": "buy",
    "price_usd": "50000.00",
    "amount_base": "0.0500",
    "tif": "PostOnly"
  }
}
```

## 4. Critical Pegging Rule: `mark_peg=True` vs. `quote_peg_mode=3`

Single-leg order placement and atomic two-sided quote replacement encode oracle mark pegging differently. Never confuse the two schemas:

1. **Single-Leg Orders (`POST /order`, `POST /order/preview`, `arena_place_order`, `arena_preview_order`):**
   Use boolean peg flags (`primary_peg`, `midpoint_peg`, **`mark_peg=True`**, `trailing_peg`, `dark_midpoint`) plus optional signed `peg_offset_ticks` (`-500..+500`):
   ```json
   {
     "name": "arena_place_order",
     "arguments": {
       "symbol": "BTC/USD:USD",
       "side": "buy",
       "price_usd": "50000.00",
       "amount_base": "0.0200",
       "tif": "PostOnly",
       "mark_peg": true,
       "peg_offset_ticks": -5
     }
   }
   ```
2. **Atomic Two-Sided Quotes (`POST /quote`, `arena_replace_two_sided_quote`, 64B `TwoSidedQuoteReplace`):**
   `arena_replace_two_sided_quote` does **not** have a boolean `mark_peg` field. Instead, pass integer **`quote_peg_mode`** (`0..4`):
   - `0` — Unpegged static limit prices (supports inventory `auto_skew_ticks` or `auto_flip_ticks`)
   - `1` — Primary peg (same-side BBO)
   - `2` — Midpoint peg (BBO mid)
   - **`3` — Oracle Mark Peg** (re-anchors both Bid and Ask to live oracle mark moves natively in the engine)
   - `4` — One-way ratchet trailing peg

   When `quote_peg_mode` is `1..4`, pass signed `peg_offset_ticks` (`-500..+500`) instead of `auto_skew_ticks`:
   ```json
   {
     "name": "arena_replace_two_sided_quote",
     "arguments": {
       "symbol": "BTC/USD:USD",
       "bid_price_usd": "49995.00",
       "bid_amount_base": "0.0500",
       "ask_price_usd": "50005.00",
       "ask_amount_base": "0.0500",
       "tif": "PostOnly",
       "post_only_slide": true,
       "quote_peg_mode": 3,
       "peg_offset_ticks": 0
     }
   }
   ```

## 5. Zero-Capital Autonomous Arbitrage & Liquidation Bounties

Unfunded (`$0` pre-margin) accounts can still earn protocol spread and liquidation bounties atomically:

- **Intra-Tick Flash Arbitrage (`arena_flash_arbitrage` / `POST /flash_arb`):**
  Atomically mints+sells (`side="sell"`) or buys+redeems (`side="buy"`) on Bonding-Curve Spot and BoundedClaim markets with zero upfront margin. Always set `min_profit_usd` (or `min_profit_micro`) so unprofitable sweeps revert cleanly without state mutation:
  ```json
  {
    "name": "arena_flash_arbitrage",
    "arguments": {
      "symbol": "CLAIM_BTC_100K",
      "side": "sell",
      "amount_base": "1.0000",
      "min_profit_usd": "0.25",
      "is_market": true
    }
  }
  ```
- **Autonomous Liquidation Sweeper (`arena_auto_liquidate` / `POST /auto_liquidate`):**
  Scans and liquidates underwater accounts across one (`market_id > 0`) or all (`market_id=0`) perpetual markets with zero pre-existing margin when `flash_offload_to_book=true`, guarded by `min_bounty_usd` / `min_bounty_micro`:
  ```json
  {
    "name": "arena_auto_liquidate",
    "arguments": {
      "market_id": 0,
      "max_lots": 10000,
      "min_bounty_usd": "0.50",
      "flash_offload_to_book": true
    }
  }
  ```

## 6. Cryptographic Ledger Verification (`ARENA_LEDGER_TIP_V2_1`)

Every deterministic engine transition advances a hash-chained WAL (`wal_seq`, `ledger_chain_hash`, `state_root`) signed by the operator over the **`ARENA_LEDGER_TIP_V2_1`** `Keccak-256` domain (`GET /ledger/tip`) and anchored to `chain_id` + `Clearinghouse` contract address.

- **MCP Verification:** Call `arena_verify_ledger_tip` (pass `expected_operator_address` to pin the operator EOA).
- **Python SDK Verification (`import feraterra_sdk`):**
  ```python
  import feraterra_sdk

  client = feraterra_sdk.ArenaHttpClient.testnet()
  tip = client.ledger_tip()
  assert tip.get("tip_domain", "ARENA_LEDGER_TIP_V2_1") == "ARENA_LEDGER_TIP_V2_1"
  assert feraterra_sdk.verify_ledger_tip(
      tip,
      expected_operator_address=tip["operator_address"],
  )
  ```
- **L2 Solvency & Merkle Escape:** Use `arena_get_withdrawals_and_escape_proof` or `feraterra_sdk.verify_escape_merkle_proof(...)` with `abi/Clearinghouse.abi.json` for trustless L2 withdrawal voucher claims and emergency Merkle escapes.

## 7. C++23 Header-Only HFT Integration (`CMakeLists.txt`)

For colocated 64-byte `ArenaWireFrame` TCP/UDP and `ArenaITCH` L3 bots, link `feraterra::hft_client` via CMake `FetchContent`:

```cmake
include(FetchContent)
FetchContent_Declare(feraterra GIT_REPOSITORY https://github.com/FeraTerra/feraterra-sdk.git GIT_TAG v4.9.4)
FetchContent_MakeAvailable(feraterra)
target_link_libraries(your_bot PRIVATE feraterra::hft_client)
```
