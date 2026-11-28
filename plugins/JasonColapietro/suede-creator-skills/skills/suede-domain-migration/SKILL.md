---
name: suede-domain-migration
description: "Use when asked \"move this site without breaking search\" or to plan a domain rebrand, URL move, or folder consolidation. Map old pages to equivalents, verify redirects and canonical parity, and prepare cutover monitoring. NOT FOR: changing DNS or deploying without approval, or a general SEO audit (use suede-seo-audit)."
metadata:
  display-name: "Suede Domain Migration Skills"
  version: 1.0.0
---

# Suede Domain Migration Skills

## Compatibility

A URL inventory and old/new crawl or page exports are enough to plan. Use a
read-only crawl, approved staging access, and Search Console exports when
available. Implementation needs scoped repository access; publication and
configuration changes need separate authority.

## Procedure

1. Record the old and proposed origins, relevant environments, cutover owner,
   current hosting controls, and matching date windows. Build an inventory
   from sitemaps, crawls, landing-page traffic, known backlinks, historic
   URL lists, and manually protected assets. Reconcile URLs that exist in
   only one source instead of silently excluding them.
2. Make one decision per old URL: keep, permanently redirect to an equivalent,
   return 404 or 410 for a genuine retirement, or defer to a named reviewer.
   Record the reason, priority, canonical target, and expected response.
   Do not redirect unrelated URLs to the homepage. Preserve functional query
   parameters only where the destination uses them; ensure old URLs cannot
   create chains, loops, or alternate-host detours.
3. Save a map suitable for the actual host and a staging test list.
   Compare status, final URL, rendered content, canonical, robots directives,
   sitemap inclusion, hreflang reciprocation where applicable, structured
   data identity, pagination, and dependency availability. Check header
   redirects and rendered/document signals independently. Include priority
   files and old path variants, plus intentionally private and gone URLs.
4. Build a cutover checklist specifying which DNS, CDN, application, and
   search-console steps an authorized operator owns, what monitoring changes,
   and which reversible rollback action follows each predefined failure.
   Avoid unrelated redesigns and content changes in the cutover. A sitemap or
   Google Change of Address action is conditional on applicability and access.
5. Compare pre/post crawl samples and Search Console reports at agreed
   intervals. Record uncertainty from recrawl and data latency. Distinguish
   redirect/configuration regressions from expected temporary visibility
   variation; never guarantee traffic or ranking retention.

## Decision traps worth testing

A distinct locale, product variant, or case-sensitive path is not a duplicate
just because the slug looks similar. Confirm the final destination represents the
same reader task. If two good old pages are consolidated, record the evidence
that the combined page retains the specific useful material from both. Put
uncertain mappings in a review queue, not in the redirect output. For URLs with
meaningful fragments, check whether the original anchor content has an
equivalent heading even though the HTTP request omits the fragment.

Define comparison windows before the launch. Track coverage of priority source
URLs, status of the intended destination, old and new impressions, and qualified
conversions as separate signals. A sudden rise in redirected requests can mean
the transition is working rather than a problem. An unexplained cluster of
old priority URLs returning 404 or new pages losing crawlability calls for a
technical recheck before interpreting rankings. Log the incident start in
UTC, preserve the failed request sample, and report which changes were
actually reverted and reproduced.

Read [the cutover evidence example](references/cutover-evidence.md) for an
inventory row and coordinated go/rollback decisions.

## Output contract

Return the old-to-new inventory, unresolved decisions, proposed diffs,
staging replay results, checkpoint owner and evidence, and the rollback
conditions. Clearly say planned, staged, deployed, or live verified. Do not
publish or contact linking sites unless the user authorizes that action.

## Boundaries

- Do not promise unchanged rankings.
- Do not apply redirects or alter DNS outside the approved plan.
