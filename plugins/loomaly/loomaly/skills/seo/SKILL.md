---
name: seo
description: "Fix SEO problems Loomaly ranks first: status → todo (fix is on the top item) → change code on a branch → check target fix with the PR link. For solo and developers."
---

# Fix SEO in this repository

1. `status` (optional `domain`). If `needsSite`, find the domain and `add_site`. Poll `status` until `scan.phase` is `done` or `failed`.
2. `todo` for `weeklyPlan`. The top open item already carries `fixPrompt`, evidence, url, and verify. If `needsBrief`, ask once and `set_goals`. Foundations (sitemap, robots, Search Console, homepage) before ordinary findings. Use `google` when setup is required.
3. Solo: apply `fixPrompt` here. Team ops: `send_to_dev` for paste-ready task text. Call `problem` only when you need more detail.
4. Open a PR, then immediately `check` with `target: fix`, `findingId`, and `ref` = PR URL. Loomaly waits up to 40 s; if not deployed yet it awaits deploy and re-checks on its own. The next `status` announces the result.
5. `triage` `ignore` only when the owner says it is not a problem. Never invent Search Console or paid ranking numbers.
