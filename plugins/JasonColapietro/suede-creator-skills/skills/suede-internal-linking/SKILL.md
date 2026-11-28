---
name: suede-internal-linking
description: "Use when asked \"find our orphan pages\" or to improve contextual internal links, click depth, crawl paths, and useful connections from resource pages to offers. NOT FOR: off-site backlinks, or broad technical SEO triage (use suede-seo-audit)."
metadata:
  display-name: "Suede Internal Linking Skills"
  version: 1.0.0
---

# Suede Internal Linking Skills

## Compatibility

Requires a public, authorized crawl or a supplied crawl export and sitemap.
Use page edits only in an available repository with authorization; use Search
Console or analytics exports when available to add an evidence-based priority.

## Procedure

1. Build a graph using rendered, crawlable HTML links and final internal
   destinations. Keep source, anchor, link type, position, original href, and
   final URL. Separate global navigation and breadcrumbs from contextual links.
   Reconcile the graph with sitemap and known landing-page exports; a URL absent
   from one graph can mean the crawl was incomplete, not that it is an orphan.
2. Define priority destinations and their intended readers. Fix broken links,
   wasteful redirect hops, wrong canonical targets, and pages that truly have
   no inlinks before asking for more links. Inbound counts are not an objective
   on their own: find where a source directly supports a useful next step.
3. Rank candidate source→destination pairs by topic relevance, demonstrated
   source visibility, destination importance, and whether the target answers the
   adjacent question. Sketch a natural anchor and exact placement. Favor
   contextual links that a reader could use; avoid adding the same exact-match
   anchor everywhere, injecting unrelated calls to action, or linking private
   or intentionally non-indexable destinations as an SEO fix.
4. Stage the small batch in authorized scope, or hand over an actionable
   plan if edits are unavailable. Render the changed pages and confirm every
   new link is visible, crawlable, descriptive, goes directly to the expected
   canonical 200 target, and is useful on mobile and with keyboard navigation.
5. Compare the same URL set before and after: contextual inlinks, depth from
   the chosen entry pages, broken- and redirected-link counts, and remaining
   orphans. Track navigational use or downstream outcomes separately from
   organic visibility. Leave missing analytics as unknown.

## Resolve common graph edge cases

Use the rendered DOM as the verification record, especially if the website's
navigation is client-rendered. In a graph from a hydrated page, exclude disabled
controls and event-only pseudo-links that have no crawlable destination. Check
if links from a paginated list are discoverable without submitting a form,
scrolling a virtual list, or signing in. Do not treat canonical and hreflang
metadata as navigational edges.

A deep page with a steady audience may deserve a clearer path; a low-interest
legal archive does not need one. Check representative crawls by site section
and access mode so a large campaign does not mask regressions on product or
support pages. If crawl discovery grew after the edit, report that separately
from matched-subset before/after counts. Do not claim the missing URLs inside
the new coverage area became broken because they were not measured before.

If two destinations look reasonable, prefer the page that gets the visitor
closer to completing the task in context, then confirm that the destination
does not make them re-enter unnecessary information. Record why the rejected
option was less useful. Read [the graph comparison example](references/graph-comparison.md)
for a reproducible before/after check.

## Output contract

Provide a graph delta plus a change table with source, destination, anchor,
placement, relevance, and verification. Separate proposed edits from verified
changes and note the crawl boundary. Do not deploy or change global navigation
without authorization.

## Boundaries

- Do not add links to blocked, noncanonical, or unrelated targets.
- Keep existing navigational and accessibility semantics intact.
