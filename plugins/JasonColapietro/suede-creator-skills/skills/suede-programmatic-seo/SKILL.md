---
name: suede-programmatic-seo
description: "Suede AI Programmatic SEO Skills: playbook, source model, templates, unique value, internal links, sitemaps, phased rollout, and KPIs. Use when asked \"build location pages at scale\" or to rescue thin templated pages. NOT FOR: site audits (suede-seo-audit), AI-answer measurement (suede-ai-seo), editorial planning (suede-content-strategy), or bulk publishing without approval."
metadata:
  display-name: "Suede AI Programmatic SEO Skills"
  version: 3.0.1
---

# Suede AI Programmatic SEO Skills

## Compatibility

Requires a source dataset with reuse rights, query-pattern evidence, and page/template access. Current search policies require browsing. Local planning/building needs no new integration; publication requires authority.

For a concrete input, expected output, recovery path, and validation check, read
[the worked contract](references/worked-contract.md). Use it to check the handoff
before treating the task as complete.

Programmatic pages work when each one answers a real query with data the
searcher cannot get faster elsewhere. They fail, and can drag the whole site
down, when they are one template with a swapped city name. This skill treats
page count as something a sample earns, never a target.

## Gate policy: advisory, not blocking

Every gate and verdict here is a recommendation to the user, not a control on
the agent. A failed gate changes what you report, never what you do. Single
exception: an extremely risky finding (data loss, credential exposure, legal or
rights violations, payment mistakes, irreversible public damage) pauses for the
user's choice.

## The policy line you must stay behind

Google's spam policies name three patterns programmatic sites trip most:

- **Scaled content abuse**: many pages generated mainly to manipulate rankings
  or AI answers and not to help people, whatever tool produced them.
- **Doorway abuse**: sites or pages created to rank for similar queries that
  funnel users to the same destination ("[service] in [city]" pages with
  nothing local on them).
- **Site reputation abuse**: third-party pages published on a host site to
  borrow its ranking signals with little first-party oversight.

Google also says AI answers need no special pages; producing variants for AI
is the same abuse. Every gate below exists to keep a page set on the right
side of this line. Source: https://developers.google.com/search/docs/essentials/spam-policies

## Initial assessment

Read `.agents/product-marketing.md` (or `.claude/product-marketing.md`, or the
legacy `product-marketing-context.md`) if present. Then establish:

1. **Business**: product, audience, the conversion each page should earn.
2. **Pattern and demand**: the repeating query pattern, its variables, how many
   combinations have evidence of demand (Search Console, Keyword Planner, or a
   dated export; otherwise `unknown`).
3. **Competition**: who ranks now, what their pages contain, and whether you
   can offer something they do not.
4. **Data**: what populates each page, where it comes from, how often it
   refreshes, and whether you have the rights to publish it.
5. **Delivery**: CMS or framework, and whether it can template, split sitemaps,
   and set `noindex` and canonicals per page.

## Data defensibility

The data decides whether the set is worth building. Rank it:

1. Proprietary (you created it: usage stats, tests, benchmarks)
2. Product-derived (aggregated from your users, with consent)
3. User-generated (reviews, submissions, community)
4. Licensed (exclusive or contracted)
5. Public (anyone can publish it; weakest, needs real added analysis)

A set built only on tier-5 data needs an original layer (scoring, comparison,
calculation, local verification) or it is a doorway set.

## Playbooks

| Playbook | Pattern | Example |
|---|---|---|
| Templates | "[type] template" | "invoice template" |
| Curation | "best [category] for [segment]" | "best CRM for agencies" |
| Conversions | "[X] to [Y]" | "kg to lbs" |
| Comparisons | "[X] vs [Y]" | "webflow vs wordpress" |
| Examples | "[type] examples" | "landing page examples" |
| Locations | "[service] in [place]" | "coworking in austin" |
| Personas | "[product] for [audience]" | "crm for real estate" |
| Integrations | "[A] [B] integration" | "slack asana integration" |
| Glossary | "what is [term]" | "what is churn rate" |
| Translations | localized versions | "/es/", "/de/" |
| Directory | "[category] tools" | "ai writing tools" |
| Profiles | "[entity]" or "[entity] [attribute]" | "stripe pricing history" |

Read `references/playbooks.md` when choosing, layering, or implementing one. It
holds per-playbook value requirements, URL patterns, and the asset-to-playbook
table.

## Implementation

### 1. Pattern and demand

Name the pattern, the variables, and the candidate list. Keep only
combinations with demand evidence or a clear reader need. Combinations with no
evidence wait for phase 2 or never ship.

### 2. Data model

One row per page. Columns for every page-unique field, its source, its
last-verified date, and a `publish` flag computed from the gates below. Rows
that fail stay in the table with `publish = false`.

### 3. Template

- H1 and title that carry the page's variables naturally.
- A direct answer in the opening that uses the row's own data ("Median [metric]
  in [city] was [value] in [month year], per [source]"), never generic copy.
- Data sections that render only when the row has the data (conditional
  blocks, not empty placeholders).
- An original layer: a calculation, ranking, comparison, or note that exists
  only because you combined the data.
- Related-page links and a CTA matched to intent.
- Schema only where a supported feature fits; `BreadcrumbList` and
  `Organization` via a shared `@id` are usually safe.

### 4. Internal linking

- Hub pages per category and per parent (city, industry, integration category)
  that link to every published child.
- Children link to the hub, to siblings that share a real relationship (nearby
  cities, adjacent integrations), and to the main product page.
- No orphans: every published page reachable within three or four clicks from
  the home page through crawlable `<a href>` links.
- Breadcrumbs, visible and marked up.

### 5. Indexation

- One sitemap per page type so indexation can be read per set.
- Rows below the gates are not generated, or are generated with `noindex` and
  left out of the sitemap until they pass.
- Self-referencing canonicals; no canonicalizing many thin pages to one hub as
  a substitute for not publishing them.
- Use subfolders under the main domain unless there is a technical or
  organizational reason for a subdomain; Google treats both as crawlable, but a
  subdomain is managed and measured as a separate property.
- Crawl budget matters only for very large sets (tens of thousands of URLs or
  more); below that, quality gates are the constraint.

## Quality gates

Run on a **sample of 10 pages or 5% of the planned set, whichever is larger**,
drawn across the data range (best-populated, median, thinnest rows), never
only showcase pages. **At least 90% of the sample must pass every gate** before
generating, publishing, or submitting anything beyond the sample. A failing
sample means fix the template or shrink the set.

**Index-worthiness (content)**
- [ ] At least **5 page-unique data fields** differ from every sibling, and at
      least one is not on any competing page you checked
- [ ] **Template-shared text is 40% or less** of rendered body words, measured
      on the thinnest row
- [ ] The opening answers the query with this row's data, not generic copy
- [ ] An original layer exists (calculation, ranking, comparison, verified
      local detail)
- [ ] A reader who never buys the product still leaves with something useful
- [ ] Facts carry a source and a last-verified date

**Doorway test**
- [ ] Swap the variable (city, persona, tool) with a sibling's: if the page
      still reads as true, it fails
- [ ] Pages do not all funnel to one destination with nothing in between
- [ ] No near-duplicate pages for synonyms of the same query ("CRM for
      realtors" and "CRM for real estate agents" is one page)

**Technical**
- [ ] Unique title, meta description, and H1 per page
- [ ] Schema validates and matches visible content
- [ ] Core Web Vitals measured on a real sample page (field data where
      available), not assumed
- [ ] Mobile render checked

**Linking and indexation**
- [ ] Linked from a hub and from at least one sibling
- [ ] In the right per-type sitemap, crawlable, no conflicting `noindex`

## Rollout and KPIs

Ship in phases: sample, then phase 1 (the strongest rows), then expansion only
when phase 1 earns it. Read these at 30 and 60 days after each phase:

| KPI | Source | Expand when | Stop and fix when |
|---|---|---|---|
| Indexation rate (indexed / submitted per sitemap) | Search Console Pages | 70% or more | Below 60% |
| Pages with impressions / pages indexed | Search Console Performance | Rising | Flat after 60 days |
| CTR on the set vs site average | Search Console | At or above | Well below |
| Engaged sessions per page | GA4 | Comparable to hand-built pages | Near zero |
| Conversions from the set | GA4 | Positive and growing | None after 60 days |
| "Crawled, currently not indexed" count | Search Console | Falling | Rising |
| Manual actions | Search Console | None | Any: halt and remove |

These thresholds are Suede defaults; adjust them to the user's baseline and
record the change. Hand ongoing reporting to `suede-analytics`.

## Common mistakes

- City or persona swapped into identical copy (doorway).
- Pages for combinations nobody searches.
- Stale or unverified data presented as current.
- Canonicalizing hundreds of thin pages instead of not publishing them.
- Generating AI-written filler to hit a word count.
- Publishing the full set before the sample passes.

## Output Contract

Close every programmatic SEO pass with this block. Write the literal templates.

```text
PLAYBOOK: [name], chosen because [pattern + data fit]
DATA DEFENSIBILITY: [tier 1-5], source, rights, provenance, refresh cadence
ORIGINAL LAYER: [what exists only because the data was combined]
PAGE-COUNT BOUND: sample [N] -> phase 1 [N] -> ceiling [N], expansion condition [KPI threshold]
URL: [literal pattern]   TITLE: [literal]   META: [literal]   H1: [literal]
OPENING ANSWER TEMPLATE: [literal, with data variables]
UNIQUENESS: [page-unique fields per page] | template-shared body text: [N%]
DOORWAY TEST: [pass/fail on sample, examples]
LINK PLAN: hub [URL] -> spokes [pattern] | cross-links [rule] | sitemap [file]
SAMPLE VERDICT: [N of N pass], failing gates: [list or "none"]
KPI PLAN: [metrics, sources, 30/60-day thresholds]
SHIP GATE: ship | ship-with-caveats | hold, reason
```

## Boundaries

- Do not generate, publish, submit, or index a full page set before a bounded
  sample passes. When the sample fails or was never run, name the blocking
  gate and failing count, give 2 to 4 options (fix the template, narrow the
  set, add data, publish the passing subset), and recommend one. Proceeding is
  the user's call.
- Do not invent source data, claim rankings or traffic, scrape sources whose
  terms forbid it, or treat keyword volume as user value.
- Do not alter production routes, templates, canonicals, sitemaps, or internal
  links without an approved scope and current-site verification.

## Routing

- Audit shipped pages and technical health: `suede-seo-audit`.
- Make the set quotable and measure AI citations: `suede-ai-seo`.
- Editorial (non-templated) planning: `suede-content-strategy`.
- Comparison-page evidence and framing: `suede-competitors`.
- Interactive tools as page anchors: `suede-free-tools`.
- Rollout reporting: `suede-analytics`.
