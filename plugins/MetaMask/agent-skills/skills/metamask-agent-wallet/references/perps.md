# Perpetual Trading Commands

Use `perps` commands to trade perpetual futures on supported venues. Currently supported venue: `hyperliquid`.

## Common Flags

Most `perps` commands accept these flags (`list-venues` does not):

| Name | Required | Description |
| --- | --- | --- |
| `--venue` | No | Perpetual venue. Defaults to `hyperliquid` |
| `--network` | No | Target network: `mainnet` or `testnet`. Defaults to `mainnet` |

The `--yes` flag skips interactive confirmation on `open`, `close`, `modify`, and `cancel` only. On `deposit`, `transfer`, and `withdraw`, `--yes` is accepted but has no effect because those commands do not prompt. Perps commands do not use `--wait`.

`open`, `close`, `modify`, `cancel`, `positions`, `orders`, and `balance` accept `--vault <address>` to trade or read on behalf of a Hyperliquid vault instead of the connected wallet. `deposit`, `withdraw`, `transfer`, and vault deposits or withdrawals are not available on behalf of a vault and return `UNSUPPORTED_ROUTE`. In BYOK mode with an encrypted mnemonic, state-changing commands also accept `--password` to unlock the mnemonic. Set `MM_PASSWORD` env var instead of passing inline.

## `perps markets` Command

List perpetual markets for a venue.

### Syntax

```bash
mm perps markets [--venue <venue>] [--network <network>] [--symbol <symbol>] [--symbols <list>] [--dex <name>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--venue` | No | Perpetual venue. Defaults to `hyperliquid`. Run `mm perps list-venues` to see options |
| `--network` | No | Target network: `mainnet` or `testnet`. Defaults to `mainnet` |
| `--symbol` | No | Filter to a single market symbol such as BTC |
| `--symbols` | No | Comma-separated market symbols to filter such as BTC,ETH,SOL |
| `--dex` | No | HIP-3 DEX name; omit for the main Hyperliquid DEX. Run `mm perps dexs` to see options |

### Example

```bash
mm perps markets --venue hyperliquid
mm perps markets --venue hyperliquid --symbol BTC
mm perps markets --venue hyperliquid --symbols BTC,ETH,SOL --network testnet
mm perps markets --venue hyperliquid --dex <name from mm perps dexs>
```

## `perps balance` Command

Show the connected wallet's perpetual account balances for a venue.

### Syntax

```bash
mm perps balance [--venue <venue>] [--network <network>] [--dex <dex>] [--all-dexes] [--vault <address>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--venue` | No | Perpetual venue. Defaults to `hyperliquid` |
| `--network` | No | Target network: `mainnet` or `testnet`. Defaults to `mainnet` |
| `--dex` | No | HIP-3 DEX name. Omit to query only the main Hyperliquid DEX. Run `mm perps dexs` to see options |
| `--all-dexes` | No | Aggregate balances across all DEXs. Mutually exclusive with `--dex` |
| `--vault` | No | Hyperliquid vault address, 0x-prefixed hex, to read the vault's account instead of the connected wallet's. Malformed values return `INVALID_ADDRESS` |

### Example

```bash
mm perps balance --venue hyperliquid
mm perps balance --venue hyperliquid --network testnet
mm perps balance --venue hyperliquid --all-dexes
```

## `perps positions` Command

List open positions for the connected wallet on a venue.

With `--funding`, each position also carries `fundingRate`, the current hourly market rate in the same units as `mm perps markets`. The field is omitted when the markets request fails; the positions still return.


### Syntax

```bash
mm perps positions [--venue <venue>] [--network <network>] [--dex <dex>] [--all-dexes] [--funding] [--vault <address>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--venue` | No | Perpetual venue. Defaults to `hyperliquid` |
| `--network` | No | Target network: `mainnet` or `testnet`. Defaults to `mainnet` |
| `--dex` | No | HIP-3 DEX name. Omit to query only the main Hyperliquid DEX. Run `mm perps dexs` to see options |
| `--all-dexes` | No | Aggregate positions across all DEXs. Mutually exclusive with `--dex` |
| `--funding` | No | Also fetch the current market funding rate for each open position. Without it, the extra markets request is skipped |
| `--vault` | No | Hyperliquid vault address, 0x-prefixed hex, to read the vault's account instead of the connected wallet's. Malformed values return `INVALID_ADDRESS` |

### Example

```bash
mm perps positions --venue hyperliquid
mm perps positions --venue hyperliquid --network testnet
mm perps positions --venue hyperliquid --all-dexes
mm perps positions --venue hyperliquid --funding
```

## `perps funding` Command

List funding payments for the connected wallet on a venue. Each row is one funding credit or debit from the account ledger. For market funding rates, use `mm perps funding-rates`.

### Syntax

```bash
mm perps funding [--venue <venue>] [--network <network>] [--symbol <symbol>] [--start-time <ms>] [--end-time <ms>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--venue` | No | Perpetual venue. Defaults to `hyperliquid` |
| `--network` | No | Target network: `mainnet` or `testnet`. Defaults to `mainnet` |
| `--symbol` | No | Filter to one market symbol such as BTC. Omit to list every funding payment in the window |
| `--start-time` | No | Window start as a whole Unix timestamp in milliseconds, not seconds or an ISO date. Any other format, or a start later than `--end-time`, returns `INVALID_INPUT`. Defaults to 30 days before the end of the window. The window cannot exceed 365 days; a longer one returns `HYPERLIQUID_ERROR` |
| `--end-time` | No | Window end as a whole Unix timestamp in milliseconds, not seconds or an ISO date. Any other format returns `INVALID_INPUT`. Defaults to now |

### Example

```bash
mm perps funding --venue hyperliquid
mm perps funding --venue hyperliquid --symbol BTC
mm perps funding --venue hyperliquid --start-time 1760000000000 --end-time 1760600000000
```

## `perps funding-rates` Command

Show hourly market funding rates for one symbol over a lookback window. This is public market history, not the connected account's funding payments.

### Syntax

```bash
mm perps funding-rates [--venue <venue>] --symbol <symbol> --window <window> [--network <network>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--venue` | No | Perpetual venue. Defaults to `hyperliquid` |
| `--symbol` | Yes | Market symbol such as BTC. HIP-3 markets use the prefixed symbol such as `xyz:XYZ100` |
| `--window` | Yes | Lookback window: `1h`, `8h`, or `1d`. Any other value returns `INVALID_WINDOW` |
| `--network` | No | Target network: `mainnet` or `testnet`. Defaults to `mainnet` |

### Example

```bash
mm perps funding-rates --venue hyperliquid --symbol BTC --window 8h
mm perps funding-rates --venue hyperliquid --symbol ETH --window 1d
```

## `perps quote` Command

Estimate entry price, notional, fees, and liquidation price without placing an order.

### Syntax

```bash
mm perps quote [--venue <venue>] --symbol <symbol> --side <side> --size <size> --leverage <leverage> [--type <type>] [--limit-px <price>] [--tif <tif>] [--network <network>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--venue` | No | Perpetual venue. Defaults to `hyperliquid` |
| `--symbol` | Yes | Market symbol such as BTC, ETH, or SOL |
| `--side` | Yes | Position direction: `long` or `short` |
| `--size` | Yes | Size in base asset, human-readable such as 0.01 or 1 |
| `--leverage` | Yes | Leverage multiplier as a positive integer such as 5 or 10 |
| `--type` | No | Order type: `market` or `limit`. Defaults to `market` |
| `--limit-px` | If `--type limit` | Limit price, human-readable such as 60000 for BTC |
| `--tif` | No | Time in force: `gtc`, `ioc`, or `alo`. `alo` is post-only. `gtc` and `alo` require `--type limit` and `--limit-px`; `ioc` works with any order type. Omit to keep the defaults: `ioc` for market and `gtc` for limit. Invalid values or combinations return `INVALID_TIF` |
| `--network` | No | Target network: `mainnet` or `testnet`. Defaults to `mainnet` |

### Example

```bash
mm perps quote --venue hyperliquid --symbol BTC --side long --size 0.01 --leverage 5
mm perps quote --venue hyperliquid --symbol ETH --side short --size 1 --leverage 10 --type limit --limit-px 2500
mm perps quote --venue hyperliquid --symbol ETH --side short --size 1 --leverage 10 --type limit --limit-px 2500 --tif alo
```

## `perps open` Command

Open a new perpetual position by placing an order.

### Syntax

```bash
mm perps open [--venue <venue>] --symbol <symbol> --side <side> --size <size> --leverage <leverage> [--type <type>] [--limit-px <price>] [--tif <tif>] [--max-slippage-bps <bps>] [--reduce-only] [--network <network>] [--vault <address>] [--dry-run] [--yes] [--password <password>] [--wallet-timeout <seconds>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--venue` | No | Perpetual venue. Defaults to `hyperliquid` |
| `--symbol` | Yes | Market symbol such as BTC, ETH, or SOL |
| `--side` | Yes | Position direction: `long` or `short` |
| `--size` | Yes | Size in base asset, human-readable such as 0.01 or 1 |
| `--leverage` | Yes | Leverage multiplier as a positive integer such as 5 or 10 |
| `--type` | No | Order type: `market` or `limit`. Defaults to `market` |
| `--limit-px` | If `--type limit` | Limit price; required when `--type` is `limit` such as 60000 for BTC |
| `--tif` | No | Time in force: `gtc`, `ioc`, or `alo`. `alo` is post-only. `gtc` and `alo` require `--type limit` and `--limit-px`; `ioc` works with any order type. Omit to keep the defaults: `ioc` for market and `gtc` for limit. Invalid values or combinations return `INVALID_TIF` |
| `--max-slippage-bps` | No | Slippage cap in basis points for IOC market pricing such as 50 |
| `--reduce-only` | No | Submit an order that can only reduce or close the existing position. If it would increase or flip the position, the venue rejects it with `REDUCE_ONLY_REJECTED` |
| `--network` | No | Target network: `mainnet` or `testnet`. Defaults to `mainnet` |
| `--vault` | No | Hyperliquid vault address, 0x-prefixed hex, to trade on behalf of a vault you lead. Malformed values return `INVALID_ADDRESS` |
| `--dry-run` | No | Validate and preview the order without signing or submitting |
| `--yes` | No | Skip interactive confirmation |
| `--password` | No | Password to unlock the BYOK mnemonic. Only applies to BYOK mode. Set `MM_PASSWORD` env var instead of passing inline |
| `--wallet-timeout` | No | Seconds to wait per wallet job including MFA and signing, max 600. Overrides config `walletTimeoutSeconds` |

### Example

```bash
mm perps open --venue hyperliquid --symbol BTC --side long --size 0.01 --leverage 5
mm perps open --venue hyperliquid --symbol ETH --side short --size 1 --leverage 10 --type limit --limit-px 2500
mm perps open --venue hyperliquid --symbol BTC --side long --size 0.05 --leverage 3 --dry-run
mm perps open --venue hyperliquid --symbol BTC --side short --size 0.01 --leverage 5 --reduce-only
mm perps open --venue hyperliquid --symbol ETH --side long --size 1 --leverage 5 --type limit --limit-px 2400 --tif alo
```

## `perps orders` Command

List resting orders for the connected wallet on a venue.

### Syntax

```bash
mm perps orders [--venue <venue>] [--network <network>] [--dex <dex>] [--vault <address>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--venue` | No | Perpetual venue. Defaults to `hyperliquid` |
| `--network` | No | Target network: `mainnet` or `testnet`. Defaults to `mainnet` |
| `--dex` | No | HIP-3 DEX name. Omit to query only the main Hyperliquid DEX. Run `mm perps dexs` to see options |
| `--vault` | No | Hyperliquid vault address, 0x-prefixed hex, to read the vault's account instead of the connected wallet's. Malformed values return `INVALID_ADDRESS` |

### Example

```bash
mm perps orders --venue hyperliquid
mm perps orders --venue hyperliquid --network testnet
mm perps orders --venue hyperliquid --dex <name from mm perps dexs>
```

## `perps close` Command

Close one position, part of a position, or all open positions.

### Syntax

```bash
mm perps close [--venue <venue>] [--symbol <symbol>] [--size <size>] [--all] [--max-slippage-bps <bps>] [--network <network>] [--vault <address>] [--dry-run] [--yes] [--password <password>] [--wallet-timeout <seconds>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--venue` | No | Perpetual venue. Defaults to `hyperliquid` |
| `--symbol` | Yes, unless `--all` | Market symbol to close such as BTC or ETH |
| `--size` | No | Partial close size in base asset such as 0.5; omit for full close. Not allowed with `--all` |
| `--all` | No | Close all open positions; mutually exclusive with `--symbol` |
| `--max-slippage-bps` | No | Slippage cap in basis points for IOC pricing such as 50 |
| `--network` | No | Target network: `mainnet` or `testnet`. Defaults to `mainnet` |
| `--vault` | No | Hyperliquid vault address, 0x-prefixed hex, to trade on behalf of a vault you lead. Malformed values return `INVALID_ADDRESS` |
| `--dry-run` | No | Preview the close action without signing or submitting |
| `--yes` | No | Skip interactive confirmation |
| `--password` | No | Password to unlock the BYOK mnemonic. Only applies to BYOK mode. Set `MM_PASSWORD` env var instead of passing inline |
| `--wallet-timeout` | No | Seconds to wait per wallet job including MFA and signing, max 600. Overrides config `walletTimeoutSeconds` |

### Validation Rules

- `--size` is not allowed with `--all`.

### Example

```bash
mm perps close --venue hyperliquid --symbol BTC
mm perps close --venue hyperliquid --symbol ETH --size 0.5
mm perps close --venue hyperliquid --all
mm perps close --venue hyperliquid --symbol BTC --dry-run
```

## `perps modify` Command

Modify leverage, take-profit, or stop-loss for an existing position.

### Syntax

```bash
mm perps modify [--venue <venue>] --symbol <symbol> [--leverage <leverage>] [--tp <price>] [--sl <price>] [--network <network>] [--vault <address>] [--dry-run] [--yes] [--password <password>] [--wallet-timeout <seconds>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--venue` | No | Perpetual venue. Defaults to `hyperliquid` |
| `--symbol` | Yes | Market symbol such as BTC, ETH, or SOL |
| `--leverage` | No | New leverage multiplier as a positive integer such as 5 or 10 |
| `--tp` | No | Take-profit trigger price, human-readable such as 3000 or 2500.50 |
| `--sl` | No | Stop-loss trigger price, human-readable such as 2000 or 1800.75 |
| `--network` | No | Target network: `mainnet` or `testnet`. Defaults to `mainnet` |
| `--vault` | No | Hyperliquid vault address, 0x-prefixed hex, to trade on behalf of a vault you lead. Malformed values return `INVALID_ADDRESS` |
| `--dry-run` | No | Preview the modify action without signing or submitting |
| `--yes` | No | Skip interactive confirmation |
| `--password` | No | Password to unlock the BYOK mnemonic. Only applies to BYOK mode. Set `MM_PASSWORD` env var instead of passing inline |
| `--wallet-timeout` | No | Seconds to wait per wallet job including MFA and signing, max 600. Overrides config `walletTimeoutSeconds` |

### Validation Rules

- At least one of `--leverage`, `--tp`, or `--sl` must be provided.

### Example

```bash
mm perps modify --venue hyperliquid --symbol BTC --leverage 10
mm perps modify --venue hyperliquid --symbol ETH --tp 3000 --sl 2000
mm perps modify --venue hyperliquid --symbol BTC --leverage 3 --dry-run
```

## `perps cancel` Command

Cancel a resting perps order.

### Syntax

```bash
mm perps cancel [--venue <venue>] --order-id <id> [--symbol <symbol>] [--network <network>] [--vault <address>] [--dry-run] [--yes] [--password <password>] [--wallet-timeout <seconds>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--venue` | No | Perpetual venue. Defaults to `hyperliquid`. Run `mm perps list-venues` to see options |
| `--order-id` | Yes | Venue order ID to cancel. Must be a positive integer |
| `--symbol` | No | Market symbol, speeds up cancel by avoiding an open-order lookup. For example BTC or ETH |
| `--network` | No | Target network: `mainnet` or `testnet`. Defaults to `mainnet` |
| `--vault` | No | Hyperliquid vault address, 0x-prefixed hex, to trade on behalf of a vault you lead. Malformed values return `INVALID_ADDRESS` |
| `--dry-run` | No | Preview the cancel action without signing or submitting |
| `--yes` | No | Skip interactive confirmation |
| `--password` | No | Password to unlock the BYOK mnemonic. Only applies to BYOK mode. Set `MM_PASSWORD` env var instead of passing inline |
| `--wallet-timeout` | No | Seconds to wait per wallet job including MFA and signing, max 600. Overrides config `walletTimeoutSeconds` |

### Example

```bash
mm perps cancel --venue hyperliquid --order-id 12345
mm perps cancel --venue hyperliquid --order-id 12345 --symbol BTC
mm perps cancel --venue hyperliquid --order-id 12345 --dry-run
mm perps cancel --venue hyperliquid --order-id 12345 --yes
```

## `perps deposit` Command

Deposit USDC into a perpetual venue.

### Syntax

```bash
mm perps deposit [--venue <venue>] --amount <amount> [--asset <asset>] [--source-chain-id <chain>] [--network <network>] [--dry-run] [--yes] [--password <password>] [--wallet-timeout <seconds>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--venue` | No | Perpetual venue. Defaults to `hyperliquid`. Run `mm perps list-venues` to see options |
| `--amount` | Yes | Human-readable USDC amount to deposit such as 100 or 50.5 |
| `--asset` | No | Deposit asset. Defaults to `USDC` |
| `--source-chain-id` | No | Source chain as a CAIP-2 ID or decimal chain ID. Defaults to Arbitrum for the selected network: `eip155:42161` on mainnet, `eip155:421614` on testnet |
| `--network` | No | Target network: `mainnet` or `testnet`. Defaults to `mainnet` |
| `--dry-run` | No | Preview the transaction without signing or submitting |
| `--yes` | No | Skip interactive confirmation |
| `--password` | No | Password to unlock the BYOK mnemonic. Only applies to BYOK mode. Set `MM_PASSWORD` env var instead of passing inline |
| `--wallet-timeout` | No | Seconds to wait per wallet job including MFA and signing, max 600. Overrides config `walletTimeoutSeconds` |

### Example

```bash
mm perps deposit --venue hyperliquid --amount 100 --asset USDC
mm perps deposit --venue hyperliquid --amount 100 --asset USDC --dry-run
```

## `perps withdraw` Command

Withdraw USDC from a perpetual venue.

### Syntax

```bash
mm perps withdraw [--venue <venue>] --amount <amount> [--asset <asset>] [--destination <address>] [--network <network>] [--dry-run] [--include-spot] [--yes] [--password <password>] [--wallet-timeout <seconds>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--venue` | No | Perpetual venue. Defaults to `hyperliquid`. Run `mm perps list-venues` to see options |
| `--amount` | Yes | Human-readable USDC amount to withdraw such as 50 or 25.5 |
| `--asset` | No | Withdrawal asset. Defaults to `USDC` |
| `--destination` | No | EVM destination address. Defaults to your connected wallet |
| `--network` | No | Target network: `mainnet` or `testnet`. Defaults to `mainnet` |
| `--dry-run` | No | Preview the withdrawal without signing or submitting |
| `--include-spot` | No | Move free spot USDC to perp before withdrawing if needed |
| `--yes` | No | Skip interactive confirmation |
| `--password` | No | Password to unlock the BYOK mnemonic. Only applies to BYOK mode. Set `MM_PASSWORD` env var instead of passing inline |
| `--wallet-timeout` | No | Seconds to wait per wallet job including MFA and signing, max 600. Overrides config `walletTimeoutSeconds` |

### Example

```bash
mm perps withdraw --venue hyperliquid --amount 50 --asset USDC
mm perps withdraw --venue hyperliquid --amount 50 --asset USDC --include-spot
mm perps withdraw --venue hyperliquid --amount 50 --asset USDC --destination 0x742d35Cc6634C0532925a3b844Bc9e7595f2bD18
```

## `perps transfer` Command

Transfer USDC between spot and perp accounts on a perpetual venue.

### Syntax

```bash
mm perps transfer [--venue <venue>] --amount <amount> --direction <direction> [--asset <asset>] [--network <network>] [--dry-run] [--yes] [--password <password>] [--wallet-timeout <seconds>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--venue` | No | Perpetual venue. Defaults to `hyperliquid` |
| `--amount` | Yes | Human-readable USDC amount to transfer such as 100 or 50.5 |
| `--direction` | Yes | Transfer direction: `spot-to-perp` or `perp-to-spot` |
| `--asset` | No | Transfer asset. Defaults to `USDC` |
| `--network` | No | Target network: `mainnet` or `testnet`. Defaults to `mainnet` |
| `--dry-run` | No | Preview the transfer without signing or submitting |
| `--yes` | No | Skip interactive confirmation |
| `--password` | No | Password to unlock the BYOK mnemonic. Only applies to BYOK mode. Set `MM_PASSWORD` env var instead of passing inline |
| `--wallet-timeout` | No | Seconds to wait per wallet job including MFA and signing, max 600. Overrides config `walletTimeoutSeconds` |

### Example

```bash
mm perps transfer --venue hyperliquid --amount 100 --direction spot-to-perp --asset USDC
mm perps transfer --venue hyperliquid --amount 50 --direction perp-to-spot --asset USDC
```

## `perps list-venues` Command

List available perpetual futures venues.

### Syntax

```bash
mm perps list-venues
```

### Supported Flags

This command does not support additional flags beyond output format options.

### Example

```bash
mm perps list-venues
```

## `perps dexs` Command

List available DEX identifiers a venue exposes. For Hyperliquid, this includes the main DEX and any HIP-3 builder-deployed DEXs.

### Syntax

```bash
mm perps dexs [--venue <venue>] [--network <network>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--venue` | No | Perpetual venue. Defaults to `hyperliquid` |
| `--network` | No | Target network: `mainnet` or `testnet`. Defaults to `mainnet` |

### Example

```bash
mm perps dexs --venue hyperliquid
```

## `perps vault list` Command

List the connected wallet's equity in Hyperliquid vaults.

### Syntax

```bash
mm perps vault list [--venue <venue>] [--network <network>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--venue` | No | Perpetual venue. Defaults to `hyperliquid` |
| `--network` | No | Target network: `mainnet` or `testnet`. Defaults to `mainnet` |

### Example

```bash
mm perps vault list --venue hyperliquid
```

## `perps vault info` Command

Show metadata for a Hyperliquid vault.

### Syntax

```bash
mm perps vault info [--venue <venue>] --vault <address> [--network <network>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--venue` | No | Perpetual venue. Defaults to `hyperliquid` |
| `--vault` | Yes | Hyperliquid vault address, 0x-prefixed hex. Malformed values return `INVALID_ADDRESS`, and an address with no vault returns `INVALID_INPUT` |
| `--network` | No | Target network: `mainnet` or `testnet`. Defaults to `mainnet` |

### Example

```bash
mm perps vault info --venue hyperliquid --vault 0xdfc24b077bc1425ad1dea75bcb6f8158e10df303
```

## `perps vault deposit` Command

Deposit USDC from the connected wallet's perp balance into a Hyperliquid vault. Creating a vault is not supported.

### Syntax

```bash
mm perps vault deposit [--venue <venue>] --vault <address> --amount <amount> [--network <network>] [--dry-run] [--yes] [--password <password>] [--wallet-timeout <seconds>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--venue` | No | Perpetual venue. Defaults to `hyperliquid` |
| `--vault` | Yes | Hyperliquid vault address, 0x-prefixed hex. Malformed values return `INVALID_ADDRESS` |
| `--amount` | Yes | Human-readable USDC amount such as 100. The minimum is 1 USDC. The amount must fit in the perp spendable balance, otherwise `INSUFFICIENT_BALANCE`. In standard account mode, move spot USDC to perp first with `mm perps transfer`; unified accounts already include free spot USDC |
| `--network` | No | Target network: `mainnet` or `testnet`. Defaults to `mainnet` |
| `--dry-run` | No | Validate the flags and return a `prepared` status without signing. Balance, minimum, and vault checks only run on a live deposit |
| `--yes` | No | Skip interactive confirmation |
| `--password` | No | Password to unlock the BYOK mnemonic. Only applies to BYOK mode. Set `MM_PASSWORD` env var instead of passing inline |
| `--wallet-timeout` | No | Seconds to wait per wallet job including MFA and signing, max 600. Overrides config `walletTimeoutSeconds` |

### Example

```bash
mm perps vault deposit --venue hyperliquid --vault 0xdfc24b077bc1425ad1dea75bcb6f8158e10df303 --amount 100 --dry-run
mm perps vault deposit --venue hyperliquid --vault 0xdfc24b077bc1425ad1dea75bcb6f8158e10df303 --amount 100
```

## `perps vault withdraw` Command

Withdraw USDC from a Hyperliquid vault back to the connected wallet's perp balance.

### Syntax

```bash
mm perps vault withdraw [--venue <venue>] --vault <address> --amount <amount> [--network <network>] [--dry-run] [--yes] [--password <password>] [--wallet-timeout <seconds>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--venue` | No | Perpetual venue. Defaults to `hyperliquid` |
| `--vault` | Yes | Hyperliquid vault address, 0x-prefixed hex. Malformed values return `INVALID_ADDRESS` |
| `--amount` | Yes | Human-readable USDC amount such as 50. The minimum is 1 USDC, and the amount cannot exceed your equity in the vault, otherwise `INSUFFICIENT_BALANCE`. Equity still inside its lock period returns `UNSUPPORTED_ROUTE` with the unlock time |
| `--network` | No | Target network: `mainnet` or `testnet`. Defaults to `mainnet` |
| `--dry-run` | No | Validate the flags and return a `prepared` status without signing. Equity, minimum, and lock checks only run on a live withdrawal |
| `--yes` | No | Skip interactive confirmation |
| `--password` | No | Password to unlock the BYOK mnemonic. Only applies to BYOK mode. Set `MM_PASSWORD` env var instead of passing inline |
| `--wallet-timeout` | No | Seconds to wait per wallet job including MFA and signing, max 600. Overrides config `walletTimeoutSeconds` |

### Example

```bash
mm perps vault withdraw --venue hyperliquid --vault 0xdfc24b077bc1425ad1dea75bcb6f8158e10df303 --amount 50
```

## `perps account mode get` Command

Show the Hyperliquid account abstraction mode for the connected wallet. In `standard` mode spot and perp balances are separate; in `unified` mode they are pooled.

### Syntax

```bash
mm perps account mode get [--venue <venue>] [--network <network>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--venue` | No | Perpetual venue. Defaults to `hyperliquid` |
| `--network` | No | Target network: `mainnet` or `testnet`. Defaults to `mainnet` |

### Example

```bash
mm perps account mode get --venue hyperliquid
```

## `perps account mode set` Command

Switch the Hyperliquid account abstraction mode for the connected wallet. This changes how spot and perp balances are pooled for the whole Hyperliquid account, not only for one command.

### Syntax

```bash
mm perps account mode set [--venue <venue>] --mode <mode> [--network <network>] [--yes] [--password <password>] [--wallet-timeout <seconds>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--venue` | No | Perpetual venue. Defaults to `hyperliquid` |
| `--mode` | Yes | Target mode: `standard` for separate spot and perp balances, or `unified` for pooled balances. If the account is already in that mode, the command returns `ALREADY_SET_ACCOUNT_MODE` |
| `--network` | No | Target network: `mainnet` or `testnet`. Defaults to `mainnet` |
| `--yes` | No | Skip interactive confirmation |
| `--password` | No | Password to unlock the BYOK mnemonic. Only applies to BYOK mode. Set `MM_PASSWORD` env var instead of passing inline |
| `--wallet-timeout` | No | Seconds to wait per wallet job including MFA and signing, max 600. Overrides config `walletTimeoutSeconds` |

There is no `--dry-run`. Run `mm perps account mode get` first to show the user the current mode.

### Output

`venue`, `network`, `previousRawState`, `rawState`, `mode`, and `changed`. The CLI reads the mode back after switching and returns `HYPERLIQUID_ERROR` if the change did not take effect.

### Example

```bash
mm perps account mode set --venue hyperliquid --mode unified
```

## Notes

- If the user does not mention a token symbol, use `mm perps markets` to list available markets and confirm the symbol with the user before proceeding.
- To answer "how much funding have I paid or earned", use `mm perps funding` for the payment ledger or the `funding` object from `mm perps positions` for running totals. To answer "what is the funding rate", use `mm perps funding-rates` for history or `mm perps positions --funding` and `mm perps markets` for the current rate.
