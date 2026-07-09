---
name: basemind-stats
description: >-
  Show a quick dashboard of basemind activity in this session: how many code-map
  tool calls have run, the per-tool histogram, and the estimated tokens saved vs
  a hypothetical grep+Read baseline. Use when the user asks "what has basemind
  done?", "how much is basemind helping?", "show me basemind stats", or invokes
  `/basemind-stats` directly.
---

# basemind-stats — on-demand usage dashboard

Call the `telemetry_summary` MCP tool and render the result as a markdown report.

## What to do

1. Call `telemetry_summary` with `{ "window": "today" }` (the default). If the
   user asks for a specific range, map it to one of `"today"`, `"1h"`, `"24h"`,
   `"all"`.
2. Render a markdown block in this shape:

   ```text
   ## basemind activity (today)
   - **N tool calls** ; top tools: outline (18), search_symbols (12), …
   - **~K tokens saved** vs grep + Read baseline
   - recent: outline (4ms, 312B), search_symbols (2ms, 180B), …
   ```

3. If `total_calls` is 0, say so plainly ("no basemind activity in the window yet").
   Don't pretend to have data.
4. **Always disclose the savings model.** Add one sentence at the end:

   > Savings are heuristics. Tools with no realistic baseline (memory, document
   > search, git wrappers) report 0 saved — see the `saved_baseline` column on
   > each row.

   The exact wording can vary; the principle (it's an estimate, here's why) cannot.

## When the user asks "--explain"

If they invoke `/basemind-stats --explain` or ask how the savings number is
derived, include the per-baseline breakdown from the `per_baseline` field of the
response and call out which tools fall into which bucket. The estimator lives in
`src/mcp/savings.rs` if they want to read the code.

## Don't

- Don't auto-display the dashboard at the start of every conversation. This skill
  is strictly user-invoked.
- Don't pad missing data. If `recent` is empty, say so; don't invent example rows.
- Don't claim a token-savings number without the disclosure sentence.
