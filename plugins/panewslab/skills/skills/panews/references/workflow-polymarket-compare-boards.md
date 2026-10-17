# Compare Polymarket Boards

**Trigger**: The user wants to compare multiple smart money board categories from the newest completed run.
Common prompts include "Compare small sharp and steady profit" or "How does active alpha differ from high win rate?"

## Steps

### 1. Resolve the requested board keys

Prefer the public board keys:
- `active_alpha`
- `high_win_rate`
- `small_sharp`
- `steady_profit`

### 2. Fetch the newest comparison payload

```bash
node cli.mjs compare-polymarket-boards --boards <key1,key2,...>
```

### 3. Output

Compare only the fields that are actually returned by the API, typically:
- `board_name`
- `top_count`
- `median_profit_usd`
- `median_return_pct`
- `top_wallet`
- `top_wallet_profit_usd`
- `top_wallet_return_pct`

Do not introduce unsupported dimensions such as dominant market unless the API later exposes them directly.
