---
name: suede-search-titles
description: "Use when asked \"rewrite these SEO titles\" or to diagnose title tags, H1 alignment, displayed search titles, and changes in search CTR. Prioritize with comparable query and device data. NOT FOR: wider technical SEO scoring (use suede-seo-audit) or ad headline production (use suede-ad-creative)."
metadata:
  display-name: "Suede Search Titles Skills"
  version: 1.0.0
---

# Suede Search Titles Skills

## Compatibility

Use the rendered page and a dated comparable search observation or export.
Search Console impressions, clicks, CTR, queries, average position, device and
country help prioritize; do not invent unobserved metrics.

## Procedure

1. Inventory canonical URLs, live HTML title, visible H1, meaningful body
   promise, and observed result title where available. Search engines can
   display a different title for different queries; one rewrite is not proof
   of a penalty or a global behavior. Distinguish desired title, rendered title,
   and displayed text in the worklist.
2. Find duplicated, missing, stale, or misleading titles. Group query evidence
   by page and comparable device, market, position band, and time window.
   Prioritize pages with real impressions and a clear evidence-backed title
   issue, not a global CTR benchmark. Preserve unusual but intentional naming.
3. Draft a clear candidate accurately describing what is on the page. Bring
   important distinguishing words forward; align the visible H1 without
   forcing identical text. Preserve correct product and company spelling.
   Do not promise years, deals, reviews, local coverage, or features not
   supported by the page. Use truncation risk as an editorial judgment,
   not a hard character limit.
4. Review the candidate list for duplicate new titles and near-identical
   candidates within a page group. Stage only the approved template or URL
   batch. Render representative pages, inspect metadata and headings,
   confirm their canonical is unchanged, and keep a rollback list.
5. After enough impression volume and a comparable interval, compare CTR
   within stable query, device, market, and position segments. Show changes
   in impression and position mix; do not attribute all movement to the
   title or promise how the search engine displays it.

## When preparation changes the recommendation

Template fixes propagate further than content edits. Start with a manifest of
every route or locale affected by a title-template change. Work out which
fields can be empty, translated, overridden, or already customized. Verify a
small representative set of examples plus the missing-data branch; never let
a silent token fallback publish a placeholder or repeated brand name across
a route collection. Maintain a stable mapping between changed URLs and their
previous titles so restoring only the problematic batch is possible.

A malformed title in source HTML is not always the same as an odd title in
Search. See whether the page is protected or has a different public canonical,
whether the crawled result is from before the template change, and whether a
specific query naturally chooses different displayed wording. When the
displayed title differs but still describes the page accurately, treat it as
a measurement note rather than an automatic defect. Do not try to force one
displayed title across every query.

Read [the title decision examples](references/title-evidence.md) for matched
comparison and safe candidate wording.

## Output contract

Return URL, current HTML title, H1, observed result title, candidate,
evidence, proposed scope, and recheck date for each item. If no query or
impression data is available, report a copy/metadata review only.

## Boundaries

- Do not present a title rewrite as a ranking lift.
- Keep the title and page promise aligned; do not change URLs or refresh unrelated copy.
