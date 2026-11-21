# Suede AI SEO Audit Skills: Worked Handoff

## Inputs

Request: “Audit this site for SEO before launch.” Supply the exact URL and scope,
or saved HTML and the evidence envelope defined in `offline-tools.md`. Synthetic
case: the observed page has a canonical pointing elsewhere; the reciprocal page
and mobile rendering have not been collected. No Search Console export exists.

## Expected output

Run the nine lanes, marking inspected evidence, gaps, and N/A items. Report the
canonical target actually observed with source location, explain the indexation
decision it affects, and propose an exact correction only after the intended
canonical is established. Do not declare the uncollected page missing or infer
traffic loss. An offline smoke run from the skill directory is:

```sh
node scripts/seo-review.mjs audit --input scripts/fixtures/pages.json --out /path/to/new-report
```

Read its report and metadata snapshot. These findings supplement the lane audit;
they do not establish live Google eligibility or a rendered mobile result.

## Failure case

A live fetch fails or an input inventory omits a URL. Use available source and
mark live checks unverified; an omitted URL is `not-observed`, not deleted.
If an output directory already exists, choose a fresh location rather than
overwriting evidence. Invalid JSON or unsupported input is an operational error,
not a measured score for the site.

## Validation

Verify every finding has a lane, source location, literal fix, and KPI to watch.
Check canonical, robots, redirect, and schema interactions against the captured
facts. Reopen current primary guidance before a ship decision. Confirm no
ranking, demand, CWV, or citation metric was fabricated from source HTML.
