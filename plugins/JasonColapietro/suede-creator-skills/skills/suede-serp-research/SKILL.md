---
name: suede-serp-research
description: "Use when asked \"cluster keywords by live SERP overlap\" or to research query intent, result composition, and citations from comparable returned results. Turn the observations into defensible URL mapping. NOT FOR: drafting comparison pages (use suede-competitors) or a full prompt-panel program (use suede-ai-seo)."
metadata:
  display-name: "Suede SERP Research Skills"
  version: 1.0.0
---

# Suede SERP Research Skills

## Compatibility

Use a dated authorized SERP export, current direct observations, or a connected
search data provider with approval for any paid queries. Do not request
secrets in chat, install a connector, or spend credits on your own.

## Procedure

1. Define the buyer and seed queries. Record query spelling, geography, locale,
   device, engine, observation time, source, and requested result depth. Keep
   materially different cohorts apart, and preserve unknown fields as
   `not collected`. Search volume and CPC are provider estimates, not
   observed demand or revenue.
2. Collect a comparable sample of organic results and keep ads, local packs,
   shopping, and AI summaries as separate features. Save ranked URLs,
   visible titles, page type, and observed citations where available. Normalize
   harmless URL differences only when evidence supports the equivalence;
   canonicalize with verified same URL outcomes, not broad text matching.
3. Compare the intersection of landed URLs at a consistent rank depth for
   pairs of queries. Record denominator, URL evidence, repeated observation,
   and dominant intent. High overlap is a candidate for one URL, not a rule;
   a local/purchase intent split or an unstable sample merits manual review.
   Check which existing page already answers each query before suggesting
   a new page. Do not create a template per keyword.
4. For AI summary citations, record the cited page and how it supports the
   answer separately from classic result rank. Group recurring source gaps
   by answer need; prioritize retrieving an original source or improving a
   specific passage instead of copying competitor wording.
5. Recommend keep, refresh, consolidate, add, or no action for each cluster.
   Record the page owner, intended reader task, evidence and date of the next
   measurement. When data is missing, state which decision it prevents.

## Keep comparison decisions reproducible

A rank list can change by hour even when locale and device match. Record
whether data came from a fresh request or a cached export and define what
counts as one observation. Use only the common supported depth across
compared queries. If a query has fewer legitimate organic entries because of
a local pack or other interface feature, report that shortfall separately and
avoid filling the gap with sponsored or unrelated result types.

Document why a URL has been grouped with another variant. Evidence may
include the same verified canonical, a clear tracking-only parameter, or a
stable redirect to the same meaningful page. Do not flatten query strings from
tools with multiple user workflows or merge locale and pagination paths by
default. When the sample is thin or changes materially, a low-confidence
decision and a direct recheck are better than creating many pages from a
spurious split.

Read [the comparable cohort example](references/cohort-comparison.md) for
cases where overlap, task, and citation evidence point to different
recommendations.

## Output contract

Return a SERP evidence table, comparable-cohort notes, a query-to-page map,
and unresolved merge/split or citation decisions. Label live observations,
exports, estimates, and interpretations. No copy, paid query, or deployment
outside authorized scope.

## Boundaries

- Keep locale, device, date and data source explicit. Do not merge unlike cohorts.
- Respect service access conditions; use authorized exports rather than spending or bypassing access.
