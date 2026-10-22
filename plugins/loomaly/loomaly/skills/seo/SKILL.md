---
name: seo
description: "Fix SEO problems Loomaly ranks first: status → todo → problem, change code on a branch, triage mark_fixed with the PR link, check after deploy. For solo and developers."
---

# Fix SEO in this repository

1. `status` (optional `domain`). If `needsSite`, find the domain and `add_site`. Poll `status` until `scan.phase` is `done` or `failed`.
2. `todo` for `weeklyPlan`. If `needsBrief`, ask once and `set_goals`. Foundations (sitemap, robots, Search Console, homepage) before ordinary findings. Use `google` when setup is required.
3. `problem` with the item's `findingId`. Solo: apply `devPrompt` here. Team ops: `send_to_dev` for paste-ready task text.
4. Open a PR. `triage` with `action: mark_fixed`, `ref` = PR URL. After deploy, `check` `target: problem`, then `check` `target: page` to poll.
5. `triage` `ignore` only when the owner says it is not a problem. Never invent Search Console or paid ranking numbers.
