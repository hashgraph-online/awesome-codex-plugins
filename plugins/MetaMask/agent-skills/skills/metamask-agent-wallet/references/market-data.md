# Market Data Commands

Use `price`, `token`, and `pulse` commands for read-only token metadata, token discovery, tokenized real-world assets, price data, and AI-generated market summaries.

The token discovery commands `token list popular|trending|top-gainer|search`, `token assets`, and `token rwas` check each requested chain against `mm token networks` before querying. A chain outside that list, including every testnet, returns `TOKEN_UNSUPPORTED_CHAIN`.

## `price spot` Command

Fetch spot prices for one or more CAIP-19 assets.

### Syntax

```bash
mm price spot --asset-ids <asset-ids> [--vs <currency>] [--market-data]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--asset-ids` | Yes | Comma-separated CAIP-19 asset IDs. A bare CAIP-2 chain id such as `eip155:1` auto-completes to that chain's native asset (`eip155:1/slip44:60`). Malformed ids return `INVALID_ASSET_ID` |
| `--vs` | No | Quote currency. Defaults to `usd` |
| `--market-data` | No | Include market cap, supply, and change percent |

### Example

```bash
mm price spot --asset-ids "eip155:1/slip44:60,eip155:137/slip44:966"
mm price spot --asset-ids eip155:1
mm price spot --asset-ids "eip155:1/slip44:60" --vs eur
mm price spot --asset-ids "eip155:1/slip44:60" --market-data
```

## `price history` Command

Fetch historical prices for an asset.

### Syntax

```bash
mm price history --chain-id <caip2-chain-id> [--asset-type <asset-type>] [--time-period <period>] [--interval <interval>] [--from <unix>] [--to <unix>] [--vs <currency>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--chain-id` | Yes | CAIP-2 chain ID, such as `eip155:1`. Run `mm price networks` to see supported chains |
| `--asset-type` | No | CAIP-19 asset type, such as `slip44:60` for ETH or `erc20:0x...` for ERC-20 tokens. Defaults to the chain's native asset. Invalid types return `INVALID_ASSET_ID` |
| `--time-period` | No | Time period, such as `1d`, `7d`, `30d`, `2M`, `1y`, or `3y` |
| `--interval` | No | Sampling interval: `5m`, `15m`, `30m`, `hourly`, or `daily` |
| `--from` | No | Start time as a Unix timestamp in seconds. Use with `--to` instead of `--time-period` for custom ranges |
| `--to` | No | End time as a Unix timestamp in seconds. Use with `--from` instead of `--time-period` for custom ranges |
| `--vs` | No | Quote currency code. Defaults to `usd`. Run `mm price currencies` to see options |

### Example

```bash
mm price history --chain-id eip155:1 --time-period 7d --interval daily
mm price history --chain-id eip155:1 --asset-type slip44:60 --time-period 7d --interval daily
```

## `price currencies` Command

List supported quote currencies.

### Syntax

```bash
mm price currencies
```

### Example

```bash
mm price currencies
```

## `price networks` Command

List CAIP-2 networks supported by the price API.

### Syntax

```bash
mm price networks
```

### Example

```bash
mm price networks
```

## `token list` Commands

List popular, trending, or top-gainer tokens.

### Syntax

```bash
mm token list popular [--chain-id <chain>]
mm token list trending [--chain-id <chain>]
mm token list top-gainer [--chain-id <chain>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--chain-id` | No | Chain id, CAIP-2 id, or configured chain key. Defaults to the active wallet chain, or `eip155:1` if none is selected |

### Example

```bash
mm token list popular --chain-id 1
mm token list trending --chain-id 1
mm token list top-gainer --chain-id 1
```

## `token list search` Command

Search tokens by query.

### Syntax

```bash
mm token list search <query> [--chain-ids <chains>] [--limit <n>] [--after <cursor>]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `<query>` | Yes | Search query by symbol or name, such as USDC or Wrapped Ether. Positional argument; `--query` is also accepted |
| `--chain-ids` | No | Comma-separated chain IDs, CAIP-2 IDs, or configured chain keys. Defaults to the active wallet chain, or `eip155:1` if none is selected |
| `--limit` | No | Maximum results. Defaults to 10, range 1-500 |
| `--after` | No | Pagination cursor |

### Example

```bash
mm token list search USDC --chain-ids 1,137 --limit 25
mm token list search "Wrapped Ether" --chain-ids eip155:8453
```

### Notes

- Quote multi-word queries so they arrive as a single positional argument.
- With no query, the command returns `MISSING_QUERY`; it never prompts for one.

## `token networks` Command

List networks supported by token APIs.

### Syntax

```bash
mm token networks
```

### Example

```bash
mm token networks
```

## `token assets` Command

Fetch asset metadata for one or more CAIP-19 assets.

### Syntax

```bash
mm token assets --asset-ids <asset-ids> [--include-market-data] [--include-token-security-data] [--include-labels] [--include-aggregators] [--include-coingecko-id] [--include-occurrences] [--include-rwa-data]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--asset-ids` | Yes | Comma-separated CAIP-19 asset IDs, such as `eip155:1/erc20:0xa0b8...`. Run `mm token networks` to see supported chains. Bare CAIP-2 chain ids are rejected with `INVALID_ASSET_ID`; pass a full asset id |
| `--include-market-data` | No | Include market cap, volume, and price data |
| `--include-token-security-data` | No | Include token security signals such as scam risk and honeypot detection |
| `--include-labels` | No | Include token labels and categories |
| `--include-aggregators` | No | Include aggregator sources that list this token |
| `--include-coingecko-id` | No | Include the CoinGecko identifier for cross-referencing |
| `--include-occurrences` | No | Include occurrence count across chains |
| `--include-rwa-data` | No | Include real-world asset data |

### Example

```bash
mm token assets --asset-ids "eip155:1/erc20:0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48,eip155:137/slip44:966"
mm token assets --asset-ids "eip155:1/erc20:0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48" --include-market-data --include-token-security-data --include-labels
mm token assets --asset-ids "eip155:1/slip44:60" --include-aggregators --include-coingecko-id --include-rwa-data
```

## `token rwas` Command

List tokenized real-world assets, or RWAs, such as stocks, ETFs, and closed-end funds.

### Syntax

```bash
mm token rwas [--chain-ids <chains>] [--active <true|false>] [--custodian <custodian>] [--type <type>] [--industry <industry>] [--sort-by <sort>] [--limit <n>] [--after <cursor>] [--include-token-security-data]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--chain-ids` | No | Comma-separated chain IDs, CAIP-2 IDs, or configured chain keys, such as `1,137`. Omit to list every chain. Run `mm token networks` to see supported chains |
| `--active` | No | Filter by active status: `true` or `false` |
| `--custodian` | No | Filter by custodian: `ondo` or `robinhood` |
| `--type` | No | Filter by underlying asset type: `stock`, `etf`, `cef`, or `unspecified` |
| `--industry` | No | Filter by industry: `industrials`, `technology`, `healthcare`, `consumer discretionary`, `financials`, `materials`, `utilities`, `energy`, `real estate`, `infrastructure`, `unspecified`, or `unknown`. Quote multi-word values |
| `--sort-by` | No | Sort order: `price_change_asc`, `price_change_desc`, `volume_asc`, `volume_desc`, `market_cap_asc`, or `market_cap_desc` |
| `--limit` | No | Maximum results. Must be a positive integer |
| `--after` | No | Pagination cursor from the `nextCursor` of a previous response |
| `--include-token-security-data` | No | Include token security signals |

`--custodian`, `--type`, `--industry`, and `--sort-by` are case-insensitive.

### Example

```bash
mm token rwas --chain-ids 1 --type stock --sort-by market_cap_desc --limit 20
mm token rwas --custodian ondo --type etf
mm token rwas --industry technology --active true
```

### Notes

- Each item includes `symbol`, and when available a CAIP-19 `assetId`, `address`, `chainId`, `name`, `decimals`, `active`, `custodian`, `type`, `industry`, `price`, `marketCap`, and `volume24hUsd`.
- When `hasNextPage` is `true`, pass `nextCursor` as `--after` to fetch the next page.
- Use the returned `assetId` with `mm price spot` or `mm token assets`.

## `pulse` Command

Show the featured AI-generated market highlight from the Digest API.

### Syntax

```bash
mm pulse [--full]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--full` | No | Include full trend details, sources, articles, and related assets. Without it, the output is a brief `headline`, `summary`, and `trends` list |

### Example

```bash
mm pulse
mm pulse --full
```

## `pulse asset` Command

Show an AI-generated summary for a single asset.

### Syntax

```bash
mm pulse asset <asset> [--full]
mm pulse asset --caip-asset-type <caip19> [--full]
mm pulse asset --hl-perps-market <market> [--full]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `<asset>` | One of three | Asset symbol, name, or CAIP-19 id, matched exactly, such as `ETH`. Positional argument; `--asset` is also accepted |
| `--caip-asset-type` | One of three | CAIP-19 asset type, such as `eip155:1/slip44:60` |
| `--hl-perps-market` | One of three | Hyperliquid perpetuals market name, such as `BTC` |
| `--full` | No | Include full trend details, sources, articles, and related assets. Without it, the output is a brief `assetId`, `assetSymbol`, `headline`, `summary`, and `trends` list |

### Example

```bash
mm pulse asset ETH
mm pulse asset --caip-asset-type eip155:1/slip44:60
mm pulse asset --hl-perps-market BTC --full
```

### Notes

- If a symbol matches several assets, the command returns `PULSE_AMBIGUOUS`. Retry with `--caip-asset-type` or `--hl-perps-market`.
- If no summary exists for the asset, the command returns `PULSE_NOT_FOUND`. Retry with another identifier type before reporting that no summary exists.
- For RWAs, prefer `--hl-perps-market` over a bare symbol. The two can return different summaries for the same asset; for example, `NVDA` and `xyz:NVDA` differ.
- Social posts and their URLs are unverified. Flag lookalike handles and airdrop or "checker" links as possible phishing.

## `pulse market` Command

Show the latest AI-generated market-wide overview.

### Syntax

```bash
mm pulse market [--full]
```

### Supported Flags

| Name | Required | Description |
| --- | --- | --- |
| `--full` | No | Include full trend details, sources, articles, and related assets. Without it, the output is a brief `generatedAt` timestamp and `trends` list |

### Example

```bash
mm pulse market
mm pulse market --full
```

### Notes

- Pulse summaries are AI-generated. Present them as summaries, not as trading advice, and cite `generatedAt` when the user asks how recent they are.
