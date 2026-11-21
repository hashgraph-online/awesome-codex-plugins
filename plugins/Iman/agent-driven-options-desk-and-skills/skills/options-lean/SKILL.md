---
name: options-lean
description: Export fixed option legs to a local LEAN backtest bundle or import completed tagged results. Use when handing a plan to a historical engine, not modeled-premium strategy backtests.
---

# Options Lean

Use `option_lean` with action export or import. Export requires plan, start, end, exercise_style, multiplier and data_mode. MCP writes a new bundle under the desk artifact directory. The CLI also accepts an explicit destination.

```sh
optiondesk lean export --plan PLAN.json --destination NEW_DIRECTORY --start 2016-01-04 --end 2016-01-06 --exercise-style american --multiplier 100 --data-mode user-licensed
optiondesk lean import --result RESULT.json --bundle NEW_DIRECTORY/plan.json
```

Replace the example paths and dates with the actual plan and test interval. Only single-expiry American US equity option legs with integer contract quantities and multiplier 100 are supported. Stock legs, time spreads and degraded plans are refused. Model premiums do not become fill prices.

The export provides main.py and plan.json; a local LEAN runtime, configuration and permitted historical data are separate requirements. The template permits backtests only, enters at the first common quote slice and liquidates on the final date using separate orders. It does not validate point-in-time selection, atomic spread fills or historical data coverage.

Import requires completed status, fully filled orders, matching source-plan tags and data mode. Report degraded status first: passing those checks does not validate data coverage or financial model suitability. Preserve LEAN statistic units and distinguish synthetic fixtures from historical results. Assignment-generated orders without the plan tag are refused; do not label that path validated.

Research software, not investment advice. See DISCLAIMER.md.
