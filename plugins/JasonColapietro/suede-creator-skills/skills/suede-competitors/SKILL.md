---
name: suede-competitors
description: "Use when asked \"write a comparison page\" or to plan an alternative or versus page from verified competitor evidence. Suede AI returns evaluator-focused copy, fair comparisons, pricing context, migration guidance and search-ready structure. NOT FOR: gathering competitor evidence (use suede-competitor-profiling), internal battle cards (use suede-sales-enablement), or scaled page systems (use suede-programmatic-seo)."
metadata:
  display-name: "Suede AI Competitor Comparison Skills"
  version: 2.0.1
---

# Suede AI Competitor Comparison Skills

Use this Suede comparison-page playbook to serve competitive search intent while keeping every product claim current, sourced, and fair.

## Compatibility

Any text-capable agent with current competitor evidence and product context. Verifying changing price or feature claims needs web access; drafting requires no CMS integration.

## Initial Assessment

Check for `.agents/product-marketing.md` (or `.claude/product-marketing.md`, or the legacy `product-marketing-context.md`) and read it if present: your value proposition, ICP, pricing model, differentiators, and proof decide which comparisons you can win on the evidence, and they are usually already written down there.

Then work the intake list under Task-Specific Questions below; ask only what the context file did not already answer. Current competitor evidence, pricing, features, ratings, comes from `suede-competitor-profiling`, not from memory.

---

## Page Formats

### Format 1: [Competitor] Alternative (Singular)

**Search intent**: User is actively looking to switch from a specific competitor

**URL pattern**: `/alternatives/[competitor]` or `/[competitor]-alternative`

**Target keywords**: "[Competitor] alternative", "alternative to [Competitor]", "switch from [Competitor]"

**Page structure**:
1. Why people look for alternatives (validate their pain)
2. Summary: You as the alternative (quick positioning)
3. Detailed comparison (features, service, pricing)
4. Who switches, and what they gain
5. Migration path
6. Social proof from switchers
7. CTA

---

### Format 2: [Competitor] Alternatives (Plural)

**Search intent**: User is researching options, earlier in journey

**URL pattern**: `/alternatives/[competitor]-alternatives`

**Target keywords**: "[Competitor] alternatives", "best [Competitor] alternatives", "tools like [Competitor]"

**Page structure**:
1. Why people look for alternatives (common pain points)
2. What to look for in an alternative (criteria framework)
3. List of alternatives (you first, but include real options)
4. Comparison table (summary)
5. Detailed breakdown of each alternative
6. Recommendation by use case
7. CTA

**Important**: Include 4-7 real alternatives. Being genuinely helpful builds trust and ranks better.

**AI-answer expectations by stage**: these pages can earn *citations* in AI answers, but whether AI *recommends* your brand from them also depends on offsite consensus (reviews, forums, analysts). For emerging brands, a self-ranked list may surface competitors while the brand receives only a citation. Treat that as a hypothesis and test it on the `suede-ai-seo` prompt panel before building more.

---

### Format 3: You vs [Competitor]

**Search intent**: User is directly comparing you to a specific competitor

**URL pattern**: `/vs/[competitor]` or `/compare/[you]-vs-[competitor]`

**Target keywords**: "[You] vs [Competitor]", "[Competitor] vs [You]"

**Page structure**:
1. TL;DR summary (key differences in 2-3 sentences)
2. At-a-glance comparison table
3. Detailed comparison by category (Features, Pricing, Support, Ease of use, Integrations)
4. Who [You] is best for
5. What customers say (testimonials from switchers)
6. Migration support
7. CTA

---

### Format 4: [Competitor A] vs [Competitor B]

**Search intent**: User comparing two competitors (not you directly)

**URL pattern**: `/compare/[competitor-a]-vs-[competitor-b]`

**Page structure**:
1. Overview of both products
2. Comparison by category
3. Who each is best for
4. The third option (introduce yourself)
5. Comparison table (all three)
6. CTA

**Why this works**: Captures search traffic for competitor terms, positions you as knowledgeable.

---

## Cliches to Refuse

A comparison page written on autopilot arrives with these already in it. Each one
tells an evaluator the page is marketing, not research, refuse them by name:

- **The strawman competitor.** A weakness stated as caricature ("clunky", "built for 2015") rather than a specific, sourced limitation a user would actually hit.
- **A "Winner" row.** No verdict row, no trophy, no score-out-of-10 that resolves to you. The reader decides; the page supplies evidence.
- **Vague superiority.** "Better in every way" or "the obvious choice" with nothing behind it. Every advantage names the specific capability, the reader it serves, and its source.
- **A table built on dimensions nobody shops on.** Pick the rows the reader's decision actually turns on (price, the job to be done, integrations, migration effort) and fill every cell with a sourced fact, so the advantages you show are ones the reader cares about.

For the two remaining defaults, the ✓/✗ feature table and a migration section with no real friction, use the concrete before/after in [references/templates.md](references/templates.md): "Comparison Table Best Practices" and "Migration Section".

---

## Essential Sections

### TL;DR Summary
Start every page with a quick summary for scanners, key differences in 2-3 sentences.

### Paragraph Comparisons
Go beyond tables. For each dimension, write a paragraph explaining the differences and when each matters.

### Feature Comparison
For each category: describe how each handles it, cite the competitor's documented limitations with sources, and state the specific advantage your product delivers.

### Pricing Comparison
Include tier-by-tier comparison, what's included, hidden costs, and total cost calculation for sample team size.

### Who It's For
Name the reader your product is built for and the outcome they get: the use
case, the team, the workflow, and the result. Specific beats broad, and a
sourced outcome beats an adjective.

Keep material facts in plain view where they decide the purchase: price, plan
limits, platform requirements, and migration effort. State them directly in the
pricing, FAQ, and migration sections rather than as caveats on the pitch.

### Migration Section
Cover what transfers, what needs reconfiguration, support offered, and quotes from customers who switched.

**For detailed templates**: See [references/templates.md](references/templates.md)

---

## Content Architecture

### Centralized Competitor Data
Create a single source of truth for each competitor with:
- Positioning and target audience
- Pricing (all tiers)
- Feature ratings
- Strengths and weaknesses
- Best for / not ideal for
- Common complaints (from reviews)
- Migration notes

**For data structure and examples**: See [references/content-architecture.md](references/content-architecture.md)

---

## Research Process

### Deep Competitor Research

For each competitor, gather:

1. **Product research**: Sign up, use it, document features/UX/limitations
2. **Pricing research**: Current pricing, what's included, hidden costs
3. **Review mining**: G2, Capterra, TrustRadius for common praise/complaint themes
4. **Customer feedback**: Talk to customers who switched (both directions)
5. **Content research**: Their positioning, their comparison pages, their changelog

### Ongoing Updates

- **Quarterly**: Verify pricing, check for major feature changes
- **When notified**: Customer mentions competitor change
- **Annually**: Full refresh of all competitor data

---

## SEO Considerations

### Keyword Targeting

| Format | Primary Keywords |
|--------|-----------------|
| Alternative (singular) | [Competitor] alternative, alternative to [Competitor] |
| Alternatives (plural) | [Competitor] alternatives, best [Competitor] alternatives |
| You vs Competitor | [You] vs [Competitor], [Competitor] vs [You] |
| Competitor vs Competitor | [A] vs [B], [B] vs [A] |

### Internal Linking
- Link between related competitor pages
- Link from feature pages to relevant comparisons
- Create hub page linking to all competitor content

### Answer-Engine Readiness

"[X] vs [Y]" and "[X] alternatives" are among the prompts buyers put to
ChatGPT, Perplexity, Copilot, and AI Overviews, and comparison pages are a
common source for those answers. Build every page so a passage can be lifted
accurately:

- The TL;DR answers the comparison in the first 40 to 80 words and names both
  products.
- Section headings are the questions buyers ask ("Is [You] cheaper than
  [Competitor] for a 10-person team?").
- The comparison is a real `<table>`, every cell sourced and dated.
- Product and company names match each vendor's canonical spelling.
- A visible "last checked" date reflects the actual claim review.

### Schema Markup
Article markup with `author`, `datePublished`, and `dateModified` that match
the visible byline and dates; `BreadcrumbList` when a breadcrumb is shown.
FAQPage markup no longer produces Google rich results (ended May 2026); use it
only to mirror a visible FAQ. Never mark up a competitor's ratings or reviews as
your own.

### KPIs
Impressions and clicks for the page's query family (Search Console), citation
and recommendation share on the matching prompt cluster (`suede-ai-seo`),
assisted sign-ups or demos from the page (analytics), and the claim-review
date, which should never be older than a quarter.

---

## Before You Hand It Over

Boundaries below requires a final claim review before any comparison page ships.
This is that review, run it as a second pass over the finished draft, not while
drafting:

1. Re-read every claim about a competitor: pricing, tier contents, feature
   availability, ratings, review counts, testimonials, headcount, funding.
2. Each one carries a source URL and the date you checked it. A claim without
   both is **cut, or explicitly marked unverified in the page**: never softened
   into hedged prose ("reportedly", "many users find", "known for"). Hedging an
   unsourced claim keeps the claim and loses the accountability.
3. Anything sourced more than a quarter ago gets re-checked before publication,
   not carried forward. Pricing pages move.
4. Claims about your own live visibility or how AI answers cite the page are not
   verifiable from here; measure them with the `suede-ai-seo` prompt panel.

---

## Output Format

Three deliverables, all with their schemas in the references: do not invent a
shape for them:

- **Competitor data file**: the centralized per-competitor record; structure in [references/content-architecture.md](references/content-architecture.md).
- **Page content**: URL, meta tags, full copy by section, tables, CTAs; section templates in [references/templates.md](references/templates.md).
- **Page set plan**: which pages to create, in priority order by search volume and evidence readiness.

---

## Task-Specific Questions

1. What are common reasons people switch to you?
2. Do you have customer quotes about switching?
3. What's your pricing vs. competitors?
4. Do you offer migration support?

---

## Boundaries

- Do not invent, cherry-pick, or present stale competitor claims, prices, features, testimonials, or rankings as current fact.
- Do not publish, deploy, index, or update comparison pages without explicit authorization and a final claim review.
- Do not use competitor trademarks in a way that implies affiliation or reuse protected creative assets without rights.
- Do not claim universal superiority; tie each advantage to its audience, criteria, source, and checked date.

## Routing

- Need current competitor evidence -> use `suede-competitor-profiling`.
- Need review-mining or forum synthesis for the "common complaints" and switching-reason sections -> use `suede-customer-research`.
- Need scaled comparison-page architecture -> use `suede-programmatic-seo`.
- Need final page copy or organic QA -> use `suede-copy` or `suede-seo-audit`.
- Need to know whether answer engines cite or recommend the page -> use `suede-ai-seo`.
- Need internal battle cards -> use `suede-sales-enablement`.
- From those skills, route evidence-backed public alternative and versus-page composition back to `suede-competitors`.

## Worked contract

[Worked contract](references/usage-contract.md) gives a bounded input, expected output and failure check for this workflow.
