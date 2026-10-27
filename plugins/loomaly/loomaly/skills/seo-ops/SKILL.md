---
name: seo-ops
description: "Ops loop: weekly report, hand work to developers, track fix progress, and read charts from tool text (tables and sparklines)."
---

# SEO ops in chat

1. `status` then `report` `kind: weekly` (and `roi` if they ask about impact). Share `report` `kind: public` when they want a link.
2. `todo` for this week's plan. The top open item already carries the fix. For each item: `send_to_dev` (or `problem` if you need more detail) → paste the task. Do not open GitHub Issues.
3. When a PR opens: `check` with `target: fix` and the PR URL as `ref`. Loomaly awaits deploy if needed and announces on the next `status`. `todo` `view: links` for link suggestions; `triage` `decide_link` for each.
4. Relay each tool's `say`. Use `chart.table` / `sparkline` when present. Human steps use `handoff` toward `/account/...` — never `/dashboard`.
5. Paid data: `set_goals` for trackKeywords / competitors / aiPrompts → `visibility` to read → `check` without `maxCost` for an estimate → `check` with `maxCost` to spend. Do not invent numbers.
