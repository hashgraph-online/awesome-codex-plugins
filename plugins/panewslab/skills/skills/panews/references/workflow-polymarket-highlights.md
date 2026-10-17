# Polymarket Board Highlights

**Trigger**: The user wants a concise explanation of what changed in the newest smart money board cycle.
Common prompts include "What changed in the newest board cycle?" or "Explain the latest smart money board highlights."

## Steps

### 1. Fetch the latest highlights payload

```bash
node cli.mjs get-polymarket-highlights
```

### 2. Use the highlights as the primary summary

Treat the returned `highlights` array as the source of truth.

### 3. Output

- Give 3 to 5 concise bullets or a short paragraph
- Mention the newest run time when useful
- Keep the summary grounded in the returned highlights only

If the latest board exists but the highlights payload is empty, say that highlight coverage is weak rather than inventing changes.
