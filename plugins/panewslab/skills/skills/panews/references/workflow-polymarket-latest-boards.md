# Latest Polymarket Boards

**Trigger**: The user wants the newest public smart money leaderboard snapshot.
Common prompts include "Show me the latest smart money boards", "What boards are available right now?", or "Give me the newest Polymarket leaderboard overview."

## Steps

### 1. Fetch the newest completed board run

```bash
node cli.mjs list-polymarket-boards
```

### 2. Read the returned run metadata

Focus on:
- `generated_at`
- `window_label`
- `boards`

### 3. Output

- Start with the newest run time and label
- List the available board categories
- For each board, show `board_name`, `board_key`, and `entry_count`

If no completed board run exists, say so directly.
