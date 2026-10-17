---
name: site-health
description: "Explain a site's SEO health from Loomaly in plain language: the score, what it's made of, and the few problems worth fixing first, with how many pages each affects."
---

# Site health in plain language

Use this when the user asks how their site is doing, what Loomaly found, or wants a summary for someone non-technical.

## Tools (Loomaly MCP)

- `sites_list`: sites with `id`, `domain`, `healthScore`, `lastScanAt`, `openIssues` and `scan.phase`.
- `fix_first` (`siteId`, `limit`): open problems in fix-first order, with `ruleTitle`, `severity`, `affectedPages`, `reason` and `message`.
- `findings_list` (`siteId`, `severity`, `ruleId`): individual issues, when a problem needs an example page.

## Steps

1. `sites_list`, and pick the site the user means (ask if it's ambiguous). If `scan.phase` is `finding_pages` or `checking_pages`, say the scan is still running and the numbers will change; `failed` means Loomaly could not read the site (`scan.failure` says why).
2. `fix_first` with `limit: 5`.
3. Write the summary:
   - The score out of 100 and when the site was last scanned. The score is built from five dimensions (indexability, page basics, content and AI readability, structured data, performance); explain it at https://loomaly.com/docs/scoring if asked.
   - The three to five problems to fix first: what each means for the business, in one sentence, and how many pages it's on. Errors first.
   - What to do next, in one line: usually "fix the first one" (the `fix-seo` skill does it in the repository).
4. Keep it short. Don't list every notice, and don't repeat rule IDs to a non-technical reader.

## Accuracy

- Only report what the tools return. Don't estimate traffic or rankings; the only search numbers Loomaly has are Search Console's: the whole site in `search_performance` (needs the `gsc:read` permission) and the focus page in `focus_page` (see the `weekly-loop` skill).
- `affectedPages` counts pages Loomaly checked, not every page on the web.
