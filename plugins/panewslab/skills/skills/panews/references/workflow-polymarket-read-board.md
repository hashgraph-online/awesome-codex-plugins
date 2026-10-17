# Read a Polymarket Board

**Trigger**: The user wants the newest entries for a specific smart money board.
Common prompts include "Who is on top of the latest small sharp board?" or "Show me the active alpha board."

## Supported board keys

- `active_alpha`
- `high_win_rate`
- `small_sharp`
- `steady_profit`

## Steps

### 1. Resolve the target board

Map the user's wording to the closest public board key.

### 2. Fetch the newest entries for that board

```bash
node cli.mjs get-polymarket-board --board <board_key> --limit <n>
```

### 3. Output

Return the top entries in rank order. Prefer `display_name`; if it is missing, show the wallet address.

For each row, include these fields when present:
- `rank`
- `display_name` or `proxy_wallet`
- `profit_usd`
- `return_pct`
- `markets_traded`
- `performance_trend`
- `summary_line`

Do not claim unsupported time windows such as 6-hour or 24-hour boards unless the API later exposes them directly.
