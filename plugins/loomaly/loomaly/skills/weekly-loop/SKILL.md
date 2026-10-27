---
name: weekly-loop
description: "Product weekly loop on the focus page: judge the last change, propose one next change with evidence."
---

# Weekly loop on the focus page

1. `status` → `todo` → `focus`. If no brief, ask once and `set_goals`. If no focus page, suggest a candidate and `set_goals` with `page` after the owner picks.
2. Report the week in short: Search numbers from `focus` / `visibility` `view: google` (and rankings/ai when stored), and each change verdict. Say when traffic is too thin to judge. For paid refreshes use `check` with estimate → maxCost.
3. If any change is `watching`, recommend nothing new. Otherwise recommend **one** change: checkup `fail` items first, then the top open plan item from `todo` (it already carries the fix).
4. Wait for the owner's yes. When it ships, `set_goals` with `summary` / `shippedOn` / `ref`, then `check` with `target: fix` and the PR URL as `ref`.
5. Foundations in `todo` beat focus-page tweaks. Connect Google with `google` when needed.
