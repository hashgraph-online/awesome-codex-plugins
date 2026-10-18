---
name: fix-seo
description: "Fix the SEO problem Loomaly ranks first on a site, in this repository: get the fix-first queue, read the evidence and fix prompt, change the code on a branch, mark it fixed with the PR link, and re-check it once it's deployed."
---

# Fix what Loomaly ranks first

Use this when the user wants to fix their site's SEO, work through Loomaly issues, or asks "what should I fix first". Run it from inside the site's repository.

## Tools (Loomaly MCP)

- `get_started` (optional `domain`): call this first. If the account has no site and you pass `domain`, it adds the site and starts the first scan. If `needsSite` is true and there is no domain yet, find one and call `add_site`.
- `sites_list`: the sites this account can see, with `id`, `domain`, `healthScore` and `scan.phase`. Every other tool needs a site `id`. An empty account returns `needsSite`.
- `add_site` (`domain`, optional `path`, `language`): adds a site and starts its first scan. The homepage must resolve and answer first; otherwise the error is `site_unreachable` and no site is created. Returns `poll` so you can watch `sites_list` until `scan.phase` is `done` or `failed`. A failed scan whose homepage could not be fetched has no health score (`scan.failure` is `errored`).
- `fix_first` (`siteId`, `limit`): open problems in the order Loomaly recommends. One entry per rule by default, with `affectedPages`, `templates`, `templatePages` (pages per pattern, the same count as `fix_prompt`), `sampleUrl` (the page of `sampleFindingId`), `lastSeenAt`, `reason` and `nextStep`. A shared version across languages is one template such as `/*/2.0.0`.
- `findings_list` (`siteId`, `severity`, `state`, `ruleId`, `pathTemplate`, `url`, `cursor`): findings (one per page) with IDs, for `fix_prompt` and `verify`. The result includes `total`, `findingsTotal` (the same count) and `nextCursor`. Pass `cursor: nextCursor` until `nextCursor` is null; the first page is not the whole list. Problems (one per rule) are `sites_list`'s `problemCount`, not this total.
- `fix_prompt` (`findingId`): the rule, the evidence and `devPrompt`, an instruction written for the site's framework. `template` says how many pages of the same template have the problem.
- `mark_fixed` (`siteId` plus `findingId`, or `siteId` plus `ruleId` and `pathTemplate` or `allPages: true`; `ref`, `note`): moves the problem to pending verification. It does not use a fix check and does not re-read the page.
- `verify` (`findingId`, or `siteId` + `ruleId` + `pathTemplate` with a `limit`), then `verify_status` (`auditRunId` + `findingId`, or `runs`): re-checks live pages. Each page uses one fix check; a group call re-checks up to `limit` pages (default 1 when fix checks reset monthly, otherwise 5). The result includes `quota.used` and `costNote`. Only after the fix is deployed. It does not use a monthly in-depth page. A re-check that cannot start is not counted. At most 5 scans or re-checks start in any rolling 60 seconds; `rate_limited` includes `retryAfter` seconds. `still-open` includes `evidence` and `nextStep`. `rescan_site` is not blocked by those re-checks; its success includes `quota`. A full site slot returns `upgrade_required`; a domain that does not resolve is `site_unreachable` even then.
- `ignore_finding` (`siteId`, a target as for `mark_fixed`, `reason`): for a finding the user says is not a problem for their site.

If the tools aren't available, tell the user to connect Loomaly (`claude mcp add --transport http loomaly https://loomaly.com/mcp`) and stop.

## Steps

1. `get_started`. If `needsSite` is true, find the domain in this repository before asking the user: `package.json` `homepage`, the README, a canonical URL, the production URL in config, or a URL the user already gave you. If `suggestedDomain` is set, use that. Call `add_site` (or `get_started` again with `domain`) in this turn. Only ask when you cannot find a domain. The call starts the first scan. Poll `sites_list` until `scan.phase` is `done` or `failed` (5–20 minutes). While it is `finding_pages` or `checking_pages`, say the scan is running, not that the site is clean. If more than one site matches the repository, ask which one; don't guess.
2. `fix_first` with `limit: 5`. Tell the user the top problem in one sentence: what it is, how many pages, and `reason`. Say what you'll change before you change it.
3. `fix_prompt` with the entry's `sampleFindingId`. If `lastSeenAt` is older than the last deploy, check the live page first: it may already be fixed. Read `evidence` before the prompt: fix what the evidence shows, not what the rule's name suggests.
4. Find where the problem comes from in this repository. Prefer the shared layout, template or component over editing pages one by one: `affectedPages` tells you whether it's a template-wide fix.
5. Make the change on a new branch, run the project's own checks and tests, and open a PR. Don't push to the main branch.
6. `mark_fixed` with `siteId`, `ruleId` and the `pathTemplate` you fixed (or `allPages: true` for a layout-wide change), `ref` set to the PR URL and a one-sentence `note`. This does not use a fix check.
7. Tell the user the problem stays pending until a re-check. An unverified site has no weekly re-scan, so do not wait for one. Once they say it's deployed, `verify` one finding, or the group (`ruleId` + `pathTemplate`) with a `limit` the owner is willing to spend (each page is one fix check; monthly plans default to 1). Poll `verify_status` every 20–30 seconds until `finished`. Relay `costNote`. Report the verdict: `fixed`, `still-open` (read `evidence` for what was still measured, then follow `nextStep`), or `check-failed` (the page couldn't be loaded; not a verdict on the fix). On `check-failed`, say `failure` (`page_quota_exhausted`, `fetch_failed` with `status`, `fetch_timeout`, `fetch_network`, `start_failed`). Follow `nextStep` for pages the call did not re-check: it only mentions `rescan_site` when a manual rescan is left.

## Don't

- Don't mark something fixed before the change is merged.
- Don't call `verify` on a branch that isn't deployed: it reads the live page.
- Don't fix a problem the evidence doesn't support. If the evidence contradicts the rule (the page already has the tag it says is missing), say so instead of editing, and offer to `ignore_finding` it with that reason.
- Don't ignore a finding without the user's say-so.
