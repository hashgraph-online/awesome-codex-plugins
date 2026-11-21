# SEO Fundamentals Reference

**Purpose**: Core SEO knowledge for audit analysis. Load when evaluating findings against standards.
**Last verified**: 2026-09-21 against Google Search Essentials and spam policies, the Google Search updates log, Google structured-data policies and the Search Gallery, Google AI-features guidance, and web.dev Core Web Vitals guidance.
**Evidence note**: Official requirements are platform policy, not guaranteed ranking outcomes. Re-check the applicable page before making a current/platform-sensitive recommendation.

## Contents

- Search Essentials
- Crawl, Render, Index & Appearance Pipeline
- E-E-A-T Framework
- Core Web Vitals
- Priority Model
- Schema Markup Types
- Structured Data Support Status
- Keyword And Intent Strategy
- AI Content Guidelines
- Spam And Abuse Policies
- Entity And Trust Signals
- Source Ledger
- Measurement Tools

## Search Essentials

Use these as the highest-confidence baseline:

1. Meet technical requirements so important pages can be crawled, rendered, indexed, and shown with snippets.
2. Avoid spam or deceptive tactics.
3. Create helpful, reliable, people-first content.
4. Use words people would use to find the content in prominent places such as title, main heading, alt text, and link text.
5. Make links crawlable and important content available as visible text.
6. Use structured data, images, videos, and JavaScript best practices where relevant.

## Crawl, Render, Index & Appearance Pipeline

Eligibility moves through four stages, in this order. Satisfying one stage never guarantees the next: not every crawled page is rendered, not every rendered page is indexed, and not every indexed page is shown. Audit each stage on its own, and label the stage a finding belongs to.

| Stage | Verify | Does not guarantee |
|---|---|---|
| `crawl` | Server responses, robots.txt rules, reachable URLs, sitemap discovery, links that are real `<a href>` elements | A successful crawl says nothing about rendering, indexing, or appearance |
| `render` | Rendered DOM content, meta tags, canonical, structured data, and internal links compared with the raw response | A browser or lab render is not evidence that Google rendered or indexed the page, and rendering is not guaranteed |
| `index` | Index state vocabulary (discovered, crawled, duplicate, indexed), canonical selection, `noindex`, soft 404, filtered or thin URLs | Indexing does not guarantee ranking, a snippet, or a rich result |
| `appearance` | Titles, snippets, rich results, AI surfaces, and how each is measured in Search Console | Appearance is not stable; platforms add and retire features and reporting without notice |

Stage boundaries to keep:

- Unblocking robots.txt is not index recovery. A blocked URL can stay indexed, and an unblocked URL can stay out of the index.
- A rendering check explains why content may be missing from an index check. It is not itself an index check.
- Report each observation with its stage and the tool that produced it.

## E-E-A-T Framework

E-E-A-T is not a single direct ranking factor. Treat it as a self-assessment and quality framework that helps identify trust signals, especially for YMYL topics.

| Pillar | Meaning | Signals |
|--------|---------|---------|
| **Experience** | First-hand knowledge of the topic | Original photos, tested examples, case studies, lived or product experience |
| **Expertise** | Credentials and deep topic knowledge | Author bio, credentials, technical accuracy, expert review |
| **Authoritativeness** | Recognition by others | Quality citations, reputable mentions, topic cluster consistency |
| **Trustworthiness** | Reliability and transparency | HTTPS, clear contact, privacy policy, accurate sourcing, no deception |

Trust is the most important pillar. Content does not need every E-E-A-T signal equally, but YMYL topics require stricter evidence and expertise.

## Core Web Vitals

Assess Core Web Vitals at the 75th percentile across real users when field data is available. Lab tools are useful for debugging but should be labeled lower confidence than field data.

| Metric | Full Name | Good | Needs Improvement | Poor |
|--------|-----------|------|-------------------|------|
| **LCP** | Largest Contentful Paint | ≤ 2.5s | > 2.5s – 4.0s | > 4.0s |
| **INP** | Interaction to Next Paint | ≤ 200ms | > 200ms – 500ms | > 500ms |
| **CLS** | Cumulative Layout Shift | ≤ 0.1 | > 0.1 – 0.25 | > 0.25 |

### LCP Optimization

- Optimize the largest image/text block above the fold.
- Use framework image components or correct `<img>` loading priorities for hero assets.
- Preload critical resources only when they are truly critical.
- Minimize server response time (TTFB) and render-blocking resources.

### INP Optimization

- Break up long tasks (> 50ms).
- Defer non-critical work with scheduling APIs or framework-specific lazy loading.
- Minimize main thread blocking JavaScript and expensive event handlers.
- Prefer interaction-specific profiling over only Lighthouse scores.

### CLS Optimization

- Set explicit `width` and `height` or aspect ratio on images/videos.
- Reserve space for ads, embeds, banners, and dynamic content.
- Avoid inserting content above existing content after load.
- Use stable font loading and layout containment where appropriate.

## Priority Model

Do not present this as a universal ranking-factor order. Use it as a practical audit triage model:

1. **Eligibility** — crawlability, indexability, canonical correctness, snippet eligibility.
2. **People-first usefulness** — original, complete, accurate content that satisfies intent.
3. **Trust and safety** — transparent authorship/organization, sourcing, policies, no deceptive behavior.
4. **Search appearance** — titles, descriptions, structured data, images/video metadata.
5. **Page experience** — Core Web Vitals, mobile usability, HTTPS, intrusive interstitial avoidance.
6. **Authority and discovery** — internal links, external mentions/backlinks, promotion in relevant communities.
7. **AEO/GEO readiness** — answer blocks, sourceable claims, entity clarity, AI crawler policy, citation probes.

## Schema Markup Types

Common Schema.org types to consider. Schema.org validity and Google rich-result eligibility are separate: confirm the current Google Search Gallery and type-specific policy before scoring a missing type. Structured data must match visible page content and use the most specific applicable type.

| Type | When to Use | Caveat |
|------|-------------|--------|
| `Article` | Blog posts, news articles, guides | Include accurate author/date/image where visible or appropriate |
| `Organization` | Company/about pages | Keep name/logo/contact/social profiles consistent |
| `Person` | Author/team profile pages | Use only for real, visible people/entities |
| `FAQPage` | FAQ content with one accepted answer per question | Google's FAQ rich result is retired; the vocabulary stays valid and FAQ content is still useful to people |
| `QAPage` | User-submitted multiple answers to one question | Do not use FAQPage for forums or multi-answer Q&A |
| `Product` | Ecommerce product pages | Price/availability/reviews must match visible content |
| `Review` | Review content/testimonials | Avoid fake or hidden reviews |
| `BreadcrumbList` | Navigation breadcrumbs | Match visible or logical site hierarchy |
| `WebSite` | Site identity and supported site-level properties | Do not promise a particular visual search feature |
| `LocalBusiness` | Local business pages | Keep address/hours consistent with visible content and profiles |
| `HowTo` | Semantic step-by-step content where genuinely useful | Google's HowTo rich result has ended; do not require HowTo markup for procedural content |

## Structured Data Support Status

Google's support for a rich-result feature changes independently of the Schema.org vocabulary. The vocabulary can stay valid and useful while a Google feature is retired, so confirm the current status before scoring a missing type.

| Type | Status | Notice | Effective | Notes |
|---|---|---|---|---|
| `FAQPage` | retired | 2026-05-08 | 2026-05-07 | The Google FAQ rich result is no longer shown and its documentation was removed 2026-06-15. The vocabulary and the human-readable FAQ content stay useful |
| `HowTo` | retired | unconfirmed | unconfirmed | Google's HowTo rich result has ended. Do not require HowTo markup for procedural content; serving non-Google consumers is a separate question |
| `Product` | supported | — | — | Product snippet for a single product page; price, availability, and reviews must match visible content |
| `merchant listing` | supported | — | — | Requires Merchant Center eligibility; valid markup alone does not qualify a page |
| `ProductGroup` | supported | — | — | Use when variants share one page, with `variesBy`, `hasVariant`, and `productGroupID` |
| `LocalBusiness` | supported | — | — | Keep address and hours consistent with visible content and profiles |
| `SpecialAnnouncement` | retired | 2025-04-23 | 2025-07-31 | The deprecation notice preceded the effective date; documentation was removed 2025-09-09 |
| `ClaimReview` | unverified | — | — | Current status was not confirmed in this pass. Do not assert either support or retirement |
| `Book actions` | unverified | — | — | Announced and then withdrawn; current status was not confirmed. Do not assert either support or retirement |

Commerce branching: a site that does not sell products gets no commerce markup finding. A site that sells products uses `Product`, `merchant listing`, or `ProductGroup` according to page structure and Merchant Center eligibility, not all three by default.

`Notice` is the date a change was announced and `Effective` the date it took effect. The two can differ, and a notice can be published after the effective date. `unconfirmed` means the date was not verified against a primary source.

## Keyword And Intent Strategy

- **Intent first**: Match content format to informational, commercial, transactional, or navigational intent.
- **Natural language**: Use terms users actually search for in titles, headings, first paragraphs, alt text, and links.
- **No stuffing**: Avoid fixed-density targets as a scoring shortcut; readability and intent fit matter more.
- **Semantic coverage**: Include related entities, comparisons, limitations, and examples naturally.

## AI Content Guidelines

- AI-generated content can be acceptable when it is helpful, accurate, reviewed, and people-first.
- Prefer AI-assisted drafts plus human review, fact checking, source verification, and original examples.
- Avoid mass-produced thin pages, unreviewed generated text, unsupported claims, or content made only to capture search traffic.

## Spam And Abuse Policies

Spam policies are an eligibility axis, not a style guide. A violation can lower rankings or remove pages from results, so treat each policy as an audit check that needs evidence rather than as an opinion about content quality.

| Policy | Covers | Audit question |
|---|---|---|
| `scaled content abuse` | Large amounts of unoriginal content created mainly to manipulate rankings | Which page set exists mainly to rank rather than to help users, and what does each page add? |
| `expired domain abuse` | An expired domain bought and repurposed mainly to manipulate rankings | Does the current content inherit its audience from the domain's previous owner? |
| `site reputation policy` | Third-party content published on a host mainly because of that host's established ranking signals | Is the third-party content there because of the host's signals, or because it serves the site's own audience? |
| `doorway abuse` | Pages that exist to funnel visitors to other destinations | Does each page stand on its own, or only as a route to another page? |
| `thin affiliation` | Affiliate pages whose descriptions and reviews are copied from the merchant | Is there original evaluation, testing, or comparison beyond the merchant's own copy? |
| `scraped content` | Content copied from other sites without added value | Can each claim be traced to the site's own work or to a cited source? |
| `generative AI use` | Not a violation by itself | Was the content produced with generative AI, and if so, was it reviewed, verified, and given original value? Automation, human effort, and a mix are judged the same way |

Rules to keep:

- Generative AI use alone never decides a violation. Judge purpose, user value, and the operating context.
- Third-party content alone is not the site reputation problem; the problem is publishing it mainly because of the host's established ranking signals.
- Regional branches exist. From 2026-08-30 the site reputation policy has a different enforcement effect inside the EEA than outside it, so record the region and the date it was checked.
- A policy page can change without a dated notice, so record the date the policy was read.

## Entity And Trust Signals

Clear, consistent entity information improves machine readability and auditability, but its effect on rankings or AI citations is not deterministic.

### Inspect

- Consistent organization, product, author, and topic names across pages.
- Author/about/contact pages and visible expertise signals.
- Topic clusters that cover definitions, comparisons, implementation, risks, and examples.
- JSON-LD `@id`/`@graph` links where they accurately reflect visible content.

### Avoid

- Claiming that schema guarantees AI citations or rich results.
- Marking up invisible, misleading, or irrelevant content.
- Treating domain authority, entity authority, or freshness as single magic levers.

## Source Ledger

`Notice` is the date a change was announced and `Effective` the date it took effect; `—` means the source documents no such date. `Accessed` is the date this reference last read the source and `Observed` the date the recorded state was last directly observed. `Confirmed at` is where the dates in the row can be re-checked.

| Source | Notice | Effective | Confirmed at | Accessed | Observed | Supports | Caveat |
|---|---|---|---|---|---|---|---|
| https://developers.google.com/search/docs/essentials | — | — | — | 2026-09-21 | 2026-09-21 | Search eligibility and crawlable-content baseline | Eligibility and best practices do not guarantee indexing or ranking |
| https://developers.google.com/search/docs/essentials/spam-policies | — | — | — | 2026-09-21 | 2026-09-21 | Spam and abuse definitions used by the policy section | The page carries no revision date; policy text can change without a dated notice |
| https://developers.google.com/search/blog/2026/08/update-site-reputation-policy | 2026-08-28 | 2026-08-30 | https://developers.google.com/search/blog/2026/08/update-site-reputation-policy | 2026-09-21 | 2026-09-21 | EEA branch of the site reputation policy | Enforcement differs inside and outside the EEA; the notice is not a per-site result |
| https://developers.google.com/search/updates | — | — | — | 2026-09-21 | 2026-09-21 | Notice and effective dates for feature deprecations (FAQ, SpecialAnnouncement) | Log entries describe announcements; a notice can be published after the effective date |
| https://developers.google.com/search/docs/appearance/structured-data/sd-policies | — | — | — | 2026-07-28 | 2026-07-28 | Visible-content parity, specificity, supported formats, no rich-result guarantee | Type-specific eligibility changes; check current feature docs |
| https://developers.google.com/search/docs/appearance/structured-data/search-gallery | — | — | — | 2026-09-21 | 2026-09-21 | Current rich-result feature list behind the support-status table | Gallery membership is not a guarantee for a specific site |
| https://developers.google.com/search/docs/appearance/structured-data/product-variants | — | — | — | 2026-09-21 | 2026-09-21 | ProductGroup properties and merchant listing eligibility | Merchant Center eligibility is separate from markup validity |
| https://developers.google.com/search/docs/fundamentals/creating-helpful-content | — | — | — | 2026-09-21 | 2026-09-21 | People-first content baseline; no preferred word count | Quality guidance is not a measurable pass/fail rule |
| https://developers.google.com/search/docs/appearance/ai-features | — | — | — | 2026-07-28 | 2026-07-28 | No special AI schema/text-file requirement; indexed and snippet-eligible supporting pages | Google AI surfaces and reporting can change |
| https://web.dev/articles/vitals | — | — | — | 2026-09-21 | 2026-09-21 | LCP/INP/CLS thresholds, 75th-percentile field measurement | Lab results do not substitute for field data |

## Measurement Tools

| Tool | Purpose | Evidence grade |
|------|---------|----------------|
| Google Search Console | Indexing, performance, coverage, Search traffic | `field`/`official` |
| Google Analytics / server logs | Traffic, user behavior, conversions, AI referrers | `field` |
| PageSpeed Insights / CrUX | Core Web Vitals field and lab diagnostics | `field` + `lab` |
| Lighthouse | Lab audit for performance/accessibility/SEO | `lab` |
| Rich Results Test / Schema validator | Structured data validation | `tool` |
| Local crawler/static scan | Links, metadata, robots, schema, headings | `lab` |
| AI citation prompt set | Citation/mention visibility in AI answers | `synthetic` |
| Ahrefs/Semrush/etc. | Backlinks, keyword rankings, competitor research | `tool` |

See `references/aeo-geo-guide.md` for AEO/GEO measurement KPIs, crawler policy, and citation probe guidance.

## Sources

> No new external source was used. Content checked 2026-09-22; the sources below were last read on the dates recorded in the ledger above.

| Claim | Source |
|---|---|
| Search eligibility and crawlable-content baseline | <https://developers.google.com/search/docs/essentials>, accessed 2026-09-21 |
| Spam and abuse definitions used by the policy section | <https://developers.google.com/search/docs/essentials/spam-policies>, accessed 2026-09-21 |
| EEA branch of the site reputation policy | <https://developers.google.com/search/blog/2026/08/update-site-reputation-policy>, accessed 2026-09-21 |
| Notice and effective dates for feature deprecations (FAQ, SpecialAnnouncement) | <https://developers.google.com/search/updates>, accessed 2026-09-21 |
| Visible-content parity, specificity, supported formats, no rich-result guarantee | <https://developers.google.com/search/docs/appearance/structured-data/sd-policies>, accessed 2026-07-28 |
| Current rich-result feature list behind the support-status table | <https://developers.google.com/search/docs/appearance/structured-data/search-gallery>, accessed 2026-09-21 |
| ProductGroup properties and merchant listing eligibility | <https://developers.google.com/search/docs/appearance/structured-data/product-variants>, accessed 2026-09-21 |
| People-first content baseline; no preferred word count | <https://developers.google.com/search/docs/fundamentals/creating-helpful-content>, accessed 2026-09-21 |
| No special AI schema or text-file requirement; indexed and snippet-eligible supporting pages | <https://developers.google.com/search/docs/appearance/ai-features>, accessed 2026-07-28 |
| LCP/INP/CLS thresholds and 75th-percentile field measurement | <https://web.dev/articles/vitals>, accessed 2026-09-21 |
