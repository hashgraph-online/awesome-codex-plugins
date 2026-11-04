---
name: suede-seo-audit
description: "Audit technical access, intent, metadata, links, schema, generative search, copy, E-E-A-T, and topic architecture with A-F lanes and exact fixes. Use when asked to \"audit this site for SEO\", investigate traffic or indexation problems, or produce a scored report. Includes offline source-review tools. NOT FOR: a quick promotion grade (use suede-visibility-grader), AI crawler and citation measurement (use suede-ai-seo), or conversion-path changes (use suede-site-alchemy)."
metadata:
  display-name: "Suede AI SEO Audit Skills"
---

# Suede AI SEO Audit Skills

## Compatibility

Live audits need web/browser access; supplied-source audits remain available offline. Bundled dependency-free source-review CLI requires Node.js 22 or later.

For a concrete input, expected handoff, and failure check, read
[the worked handoff](references/worked-handoff.md).

A deep, scored audit of how search engines and answer engines reach,
understand, and present a page. Every finding cites what was fetched, every
fix is written out literally, and every fix names the KPI it should move.

## Gate policy: advisory, not blocking

Every check, grade, and ship gate here is a recommendation to the user, not a
control on the agent. A failed gate changes what you report, never what you
do. Single exception: an extremely risky finding (data loss, credential
exposure, legal or rights violations, payment mistakes, irreversible public
damage) pauses for the user's choice.

## Where this audit stops

| Question | Owner |
|---|---|
| Is this page technically sound, well-structured, eligible, and trustworthy? Graded, with fixes. | **this skill** |
| Is this page ready to promote today? One fast A-F read including design and CTA. | `suede-visibility-grader` |
| Do ChatGPT, Perplexity, Claude, Copilot and AI Overviews cite and recommend us, and how do we measure it? | `suede-ai-seo` |
| The page is found but does not convert. | `suede-site-alchemy` |
| Hundreds of templated pages. | `suede-programmatic-seo` |

Lane 6 applies the extractability standard that `suede-ai-seo` owns. Cite it;
do not redefine it here.

## Offline source tools (Node 22+)

This folder includes a standalone CLI and self-contained modules. No install,
API key, network request, Search Console connection, or provider call is needed.
Run from this skill folder; output goes into a **new** directory:

```bash
node scripts/seo-review.mjs audit --input scripts/fixtures/pages.json --out reports/baseline
node scripts/seo-review.mjs audit --input scripts/fixtures/pages.json --merchant --out reports/merchant
node scripts/seo-review.mjs drift --before reports/baseline/metadata-snapshot.json --after reports/merchant/metadata-snapshot.json --out reports/drift
node scripts/seo-review.mjs serp-clusters --input scripts/fixtures/serp.json --context "Synthetic fixture only" --depth 2 --threshold 0.5 --out reports/clusters
node --test scripts/tests/*.test.mjs
```

- Lane 1: validate HTML hreflang codes, self annotations, duplicate/conflicting
  destinations, inspected reciprocal links, canonical and HTML noindex conflicts.
  Uncollected alternates stay **unmeasured**, never broken by assumption.
- Lane 3: audit img source fallbacks, missing/empty alt, intrinsic dimensions,
  width-based srcset/sizes, and lazy/high-priority conflicts. Empty alt needs human
  decorative-purpose review; asset bytes, rendering and CWV remain unmeasured.
- Lane 3: every audit saves a new metadata snapshot. Drift compares fields and
  exact URL identities. Supplied inventories are partial: omitted URLs are
  **not-observed**, never proof of deletion or a live 404.
- Lane 5: `--merchant` explicitly enables a Product/Offer merchant profile,
  including local graph references, active prices/currency, availability,
  supplied identifiers and variant relationships. Never invent prices, ratings,
  shipping or return policies. This is source review, not eligibility certification.
- Lane 0/9: cluster supplied organic-result exports by same-depth document URL
  overlap. Require collection context; deterministic complete-link grouping avoids
  transitive chains. Demand and current rankings stay unknown.

Read [offline input formats and limits](references/offline-tools.md) before
supplying your own evidence. These tools add findings to the existing lanes;
they do not replace live verification or change the audit's routing boundaries.

## Current rules

Before applying any Google-specific rule, read
`references/google-search-guidance.md` (verified 2026-10-23). It records what
changed recently and must be re-checked before a ship decision: FAQ rich
results ended in May 2026, several structured data features were retired in
2025, AI Overviews and AI Mode have no extra technical requirements, and
Search Console now has a Search Generative AI performance report.

## 1. Source truth

Never audit from memory. Before any finding, fetch and record exactly:

- HTTP status, every redirect hop, final URL
- `robots.txt` rules for `*`, `Googlebot`, and `Bingbot` (other named crawlers
  only when asked; AI crawler policy belongs to `suede-ai-seo`)
- `<meta name="robots">`, `X-Robots-Tag`, snippet directives
- `<link rel="canonical">` and whether it is self-referencing
- Sitemap presence and whether the URL is listed
- `<title>`, meta description (text and length as a preview diagnostic)
- Open Graph and Twitter/X card tags
- Every JSON-LD block, parsed
- Primary H1 and heading outline
- Raw HTML vs rendered DOM for primary content

If the URL is inaccessible, audit source files and mark live checks
unverified. If content is behind auth or a paywall, say so and limit scope.

## 2. Audit lanes

Run every lane. Mark each checklist item pass, fail, or N/A with location.
Checklists live in `references/`:

| Lane | Checklist |
|---|---|
| 0 Keyword research (optional) | `references/keyword-research.md` |
| 1-4, 6-9 | `references/lane-checklists.md` |
| 5 Schema | `references/schema-templates.md` |

### Lane 0: Keyword research (optional)

Run only when discovery is requested. Produces a keyword and content brief,
not a grade. Numeric demand stays `unknown` unless a dated source supplies it.

### Lane 1: Technical access

Can Google and Bing crawl, render, and index the page? Status, redirects,
canonical, robots, sitemap, rendering, Bing Webmaster Tools and IndexNow
setup, and the Core Web Vitals protocol (LCP 2.5 s, INP 200 ms, CLS 0.1 at
the 75th percentile). Measure CWV with PageSpeed Insights or CrUX field data
when available; otherwise report "not measurable" plus observed risk factors.
CWV never enters the grade.

Drops to C or below: an indexability block, wrong canonical, failing
redirects, or primary content missing from the rendered result. Using
JavaScript is not a failure by itself.

### Lane 2: Search and answer intent

One primary reader, one primary query theme, one action the page should earn,
and no cannibalization. Write the standalone definition ("[Entity] is [what]
for [whom] by [how]") from the opening; if the page cannot support one, report
the ambiguity.

Drops to C or below: no clear reader, intent conflicts with the title, or the
opening answers a different question than the URL implies.

### Lane 3: Metadata

Title, meta description, Open Graph, Twitter/X card, alt text, author and
publisher entity names. Character counts are preview diagnostics; Google sets
no fixed limit and may rewrite title links and snippets.

Drops to D or below: title missing or misleading, meta description missing on
a priority landing page, broken social preview assets, or the entity cannot be
identified from title, description, and H1 together. Length alone never drops
a grade.

### Lane 4: Structure and internal links

Heading hierarchy, heading self-sufficiency, real `<table>` markup for tabular
content, section order that follows the reader's task, internal links
(descriptive anchors, click depth, orphans, broken links), and natural topic
coverage. No universal template, word count, or keyword density.

Drops to C or below: H1 missing, the page omits information its primary intent
requires, internal anchors are non-descriptive throughout, or the page is
reachable only through search or the sitemap (orphan). The retrieval-chunk and
heading checks in the checklist are warnings, never grade drops: Google states
that content does not need to be chunked for its AI features.

### Lane 5: Schema markup

Decide whether a Google-supported feature fits; "no supported feature
identified" is a valid result. Then confirm every JSON-LD block validates,
matches visible content, describes a structure the visible page actually has,
and uses an entity `@id` consistent with the site's Organization and Person
nodes. Write the corrected block inline when markup is missing or broken.

Drops to D or below: misleading, invalid, or hidden markup, or a type claimed
for a Google feature it is not eligible for. Drops to C or below: schema
declares a structure the prose lacks, or a material claim exists only in
JSON-LD. FAQPage and HowTo markup earn no Google rich result; never promise
one.

### Lane 6: Answer extractability (generative search)

Can a person or an answer engine lift an accurate, attributable answer from
this page? Apply the `suede-ai-seo` extractability standard: direct answer up
top, question headings that name their subject, self-contained passages,
quotable sourced facts, original information, explicit entity names, primary
content in HTML text, and no snippet directive hiding the answer. Record
`llms.txt` only when a named consumer documents support; Google Search ignores
it.

Drops to C or below: the opening cannot state the subject and answer, material
claims lack sources, primary content is unavailable without JavaScript and has
no crawlable fallback, or the title or URL promises a comparison the body never
makes.

### Lane 7: Copy and conversion quality

Directness, proof before the ask, verifiable claims, specific CTA text, trust,
and filler removal.

Drops to C or below: the intended action is absent or undiscoverable, a
published statement is unverifiable, or the copy could describe any competitor
unchanged.

### Lane 8: E-E-A-T signals

Experience, expertise, authoritativeness, and trust as a quality lens Google's
raters use, not a ranking score. Grade: A (all four strong), B (three), C
(two), D/F (one or none).

Drops to C or below: no visible proof of experience or expertise, contact or
privacy information absent, or misleading UI patterns.

### Lane 9: Topic clusters and site architecture

For multi-page audits where a pillar and cluster model serves the site: pillar
ownership, cluster coverage, two-way links, orphan pages, click depth from the
home page, and query-intent owners. N/A for single pages.

Drops to C or below: declared pillar missing, important pages orphaned or
deeper than four clicks, or multiple pages competing for one intent with no
owner.

## 3. Finding format

```
[HIGH|MEDIUM|LOW] Finding title
Location: <URL, selector, or file + line>
Issue: <what is wrong and why it matters>
Fix: <exact corrective action>
Suggested copy or code: <literal rewrite, JSON-LD block, robots line, or command>
KPI: <metric this should move, its source, and when to re-check>
Verification: <how to confirm the fix worked>
```

Severity: HIGH blocks indexing, breaks the CTA, publishes a false statement,
or ships invalid schema. MEDIUM reduces result clarity, sourceability, or task
success. LOW is polish.

KPIs to draw from: indexed pages (Search Console Pages report), impressions
and clicks for the target query family (Performance, Web), CTR on the target
URL, rich result valid items (Enhancements), Core Web Vitals pass rate (CrUX),
Bing indexed pages and Copilot citations (Bing Webmaster Tools), organic
conversions on the URL (GA4). Never forecast the size of the change.

## 4. Scoring

Grades are mechanical, from finding counts:

| Grade | Rule |
|---|---|
| A | No HIGH or MEDIUM findings in the lane |
| B | No HIGH; one or two MEDIUM |
| C | Exactly one HIGH, or three or more MEDIUM |
| D | Two or three HIGH |
| F | Four or more HIGH, or the lane is absent or actively harmful |

Hard caps:
- No A overall without a verified live URL.
- No A if the primary CTA is broken or absent.
- No A if any published statement is false, unverifiable, or invented.
- No A in Lane 5 if present or warranted schema does not validate, or declares
  a structure (`FAQPage`, `HowTo`, `ItemList`, `BreadcrumbList`) the visible
  page lacks.
- No A in Lane 6 if primary content was unavailable to the tested clients.
- No A in Lane 8 without contact, privacy policy, and HTTPS.
- No A in an in-scope Lane 9 with unresolved intent-ownership conflicts.

Overall: A=4, B=3, C=2, D=1, F=0. Lanes 1, 3, and 6 weigh 1.5x; Lanes 2, 4, 5,
7, 8, 9 weigh 1x; Lane 0 excluded. Max 42. Letter: 38+ A, 30+ B, 22+ C, 14+ D,
below 14 F. When Lane 9 is N/A, rescale the maximum to 38 and the cutoffs
proportionally, and state it.

## 5. Output template

Fill every field; write "none found" or "not applicable" rather than leaving
one blank.

```
=== SEO AUDIT REPORT ===
Audited URL:            Audit date:            Source checked: [live | source | both]

--- KEYWORD BRIEF (Lane 0 only) ---
Primary query theme: [query family], [intent], [evidence source/date]
Demand: [sourced value | unknown]
Supporting themes / related entities / content gaps / feature eligibility / brief

--- METADATA ---
SEO title (suggested):            Meta description (suggested):
H1 (suggested):                   Subhead (suggested):

--- CONVERSION ---
Primary CTA (text -> destination):   Secondary CTA:

--- CONTENT ADDITIONS ---
Required subjects: [from intent and verified gaps]
Question headings to add: [H2 text -> answer summary]
Internal links to add (anchor -> destination):
External sources to cite (claim -> source URL):
Competitor gap: [URL checked, date] -> [missing subject, priority]

--- SCHEMA ---
[Corrected or new JSON-LD block]
Entity @id used: [Organization / Person @id] | consistent with site: [yes/no]
Retrievability: [property], [prose-backed | indexable-only | decorative | unclassified], evidence
Schema-only claims: [property = value | none]
Structure claim vs prose: [@type] declares [N] | visible headings [N] | [match/mismatch]

--- ANSWER EXTRACTABILITY (Lane 6) ---
Opening answer: [quoted | absent]
Extractability checks passing: [N of 9, per suede-ai-seo]
Hallucination risk claims: [quoted | none]
llms.txt: [named consumer and use | none warranted]; Google Search effect: none

--- E-E-A-T NOTES ---
Experience / Expertise / Authoritativeness / Trust gaps:

--- ARCHITECTURE (omit for single pages) ---
Pillar -> clusters map | Orphans | Pages deeper than 4 clicks | Cannibalization

--- CORE WEB VITALS (never graded) ---
LCP / INP / CLS: [field value (source) | lab value | not measurable: reason]
Risk: low | medium | high      Risk factors observed:

--- SCORES ---
Lane 1-9 grades:                Overall:

--- KPI WATCHLIST ---
[KPI | source | baseline | re-check date] for each HIGH and MEDIUM fix

--- EVIDENCE BOUNDARIES ---
Safe to publish: | Hold until verified (user's call): | Remove:

--- VERIFICATION CHECKLIST ---
[ ] Status 200 and canonical confirmed  [ ] robots.txt allows path
[ ] Schema validates (Schema.org Validator) and Rich Results Test where a Google feature applies
[ ] Internal links return 200           [ ] Primary CTA loads
[ ] og:image loads                      [ ] JSON-LD contains no invented content
[ ] Declared schema structure matches visible structure

--- SHIP GATE ---
ship | ship-with-caveats | hold        Reason:
```

## 6. Workflow

1. Fetch the live URL and the source when both exist; note divergence.
2. Record the source-truth fields exactly.
3. Fetch `robots.txt` and the sitemap; confirm the URL is allowed and listed.
4. Run Lanes 1 to 8 on every audit, Lane 9 for multi-page scope, Lane 0 on
   request. Work each checklist item.
5. Write findings in the format above, HIGH first within each lane.
6. Write literal rewrites, JSON-LD, or config for every HIGH and MEDIUM.
7. Fill the template, score mechanically, apply caps.
8. Recommend the gate: `ship` with no HIGH findings and all caps met;
   `ship-with-caveats` with only MEDIUM or LOW and no false claim; `hold` with
   any unresolved HIGH, false claim, or broken CTA. Name what could not be
   verified and why.

## Red Flags: Stop

- "I know this page; I can grade it from memory." Fetch it.
- "curl was fast, so CWV is fine." curl times server response only.
- "I'll describe the schema fix." Write the JSON-LD.
- "Add FAQPage so it gets rich results." Google ended FAQ rich results in May
  2026. Recommend FAQ markup only to mirror visible Q&A for entity clarity.
- "The title crossed 60 characters." Google publishes no fixed limit; judge
  truncation in context.
- "A traffic estimate will make this land harder." Never invent traffic,
  rankings, or ROI.
- "The lane mostly passes." Every item gets pass, fail, or N/A.

## Boundaries

- Do not invent traffic estimates, ranking positions, citation frequency, or
  ROI.
- Do not present `llms.txt`, content chunking, keyword density, word count, or
  unsupported schema as Google ranking requirements.
- Do not edit production pages, robots.txt, or schema without explicit
  approval; the audit is read-only unless the user asks for fixes applied.
- Name what was checked, which primary guidance was used, what was skipped,
  and what needs more tooling (Search Console, Bing Webmaster Tools, CrUX,
  log files).

## Routing

- Fast A-F promotion verdict: `suede-visibility-grader`.
- AI crawler policy, entity graph, prompt-panel measurement: `suede-ai-seo`.
- Conversion fixes (CTA, friction, offer): `suede-site-alchemy`.
- New copy rather than fixes: `suede-copy`.
- Editorial gaps the audit exposes: `suede-content-strategy`.
- Templated page systems: `suede-programmatic-seo`.
- Audit passed and the page ships in a release: `suede-launch-packaging`.
