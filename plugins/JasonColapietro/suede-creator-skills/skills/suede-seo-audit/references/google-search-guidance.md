# Current Search Guidance

Primary-source baseline verified on 2026-10-23. Re-check the linked page when
a rule affects a ship decision; Google and Microsoft change these often.

## Generative AI features (AI Overviews, AI Mode)

- Rooted in core Search ranking and quality systems. "There are no additional
  requirements to appear in AI Overviews or AI Mode, nor other special
  optimizations necessary."
- Eligibility: indexed and eligible to show with a snippet. No other technical
  requirement. Serving is not guaranteed.
- Both may use query fan-out (multiple related searches across subtopics), so
  topic coverage across a site matters more than one page per phrasing.
- No special schema, AI text files, markup, or Markdown copies are needed.
  Google Search does not use `llms.txt`.
- No need to break content into tiny chunks or write in a special style.
- Mass-producing pages to manipulate rankings or AI responses violates the
  scaled content abuse policy.
- Controls: `nosnippet`, `data-nosnippet`, `max-snippet`, and `noindex` limit
  what AI features show. `Google-Extended` affects Gemini training and
  grounding outside Search; Google says it does not affect Search inclusion or
  ranking.
- Reporting: AI feature clicks and impressions count in the Performance report
  under the Web search type. Google introduced a Search Generative AI
  performance report in June 2026 (impressions by page, country, device, date;
  no clicks or queries; shown only above an impressions threshold).

Sources:
- https://developers.google.com/search/docs/appearance/ai-features
- https://developers.google.com/search/docs/fundamentals/ai-optimization-guide (last updated 2026-07-10)
- https://developers.google.com/search/blog/2026/06/gen-ai-performance-reports
- https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers

## Helpful content and spam policies

- Helpfulness is assessed by core ranking systems; there is no separate
  helpful content update to recover from. Use Google's self-assessment
  questions: original information, first-hand expertise, a satisfying answer,
  content made for people rather than for search engines.
- Spam policies that matter most for audits: scaled content abuse, doorway
  abuse, site reputation abuse, expired domain abuse, keyword stuffing, hidden
  text, and misleading structured data.
- There is no keyword-density target and no ideal word count.

Sources:
- https://developers.google.com/search/docs/fundamentals/creating-helpful-content
- https://developers.google.com/search/docs/essentials/spam-policies
- https://developers.google.com/search/docs/fundamentals/seo-starter-guide

## Titles and snippets

- No fixed character limit for titles or meta descriptions; results truncate
  by device and query.
- Google may generate title links and snippets from page content.
- Character counts are preview diagnostics only.

Sources:
- https://developers.google.com/search/docs/appearance/title-link
- https://developers.google.com/search/docs/appearance/snippet

## Structured data: what earns a result in 2026

- Markup must describe visible content, use a supported type for the targeted
  feature, and include that feature's required properties. Valid markup
  creates eligibility, not a guarantee.
- **FAQ rich results ended on May 7, 2026** for all sites. The Search Console
  FAQ report and Rich Results Test support were scheduled for removal in June
  2026 and API support in August 2026. FAQPage remains valid schema.org
  vocabulary and Google may still read it to understand pages; it no longer
  produces a Google rich result.
- **HowTo rich results** were removed in 2023 (mobile first, then desktop). Do
  not recommend HowTo markup for a Google feature.
- **Retired in June 2025** (simplifying search results): Course Info, Claim
  Review, Estimated Salary, Learning Video, Special Announcement, Vehicle
  Listing. Book Actions was announced for retirement and later kept because
  some features still use it. Practice Problems was announced for deprecation
  with Search Console support for several retired types ending January 2026.
  Check the search gallery for the current list before naming any feature.
- Still useful and supported (verify in the gallery): Organization, Article,
  Breadcrumb, Product and merchant listings, Review snippet, Video, Event,
  Local Business, Recipe, Software App, Dataset (Dataset Search only), Job
  Posting, Profile Page, Discussion Forum, Q&A.
- Validate with the Rich Results Test for Google features and the Schema.org
  Validator for vocabulary. Record which was used.

Sources:
- https://developers.google.com/search/docs/appearance/structured-data/search-gallery
- https://developers.google.com/search/docs/appearance/structured-data/sd-policies
- https://developers.google.com/search/docs/appearance/structured-data/faqpage
  (direct fetch was blocked during this check; dates confirmed through
  https://www.techwyse.com/news/ai-search/google-faq-rich-results-deprecated-2026)
- https://developers.google.com/search/blog/2025/06/simplifying-search-results
- https://developers.google.com/search/blog/2023/08/howto-faq-changes

## Core Web Vitals

| Metric | Good | Needs improvement | Poor |
|---|---|---|---|
| LCP | 2.5 s or less | up to 4 s | over 4 s |
| INP | 200 ms or less | up to 500 ms | over 500 ms |
| CLS | 0.1 or less | up to 0.25 | over 0.25 |

Assessed at the 75th percentile of field data (CrUX), split by mobile and
desktop. INP replaced FID in March 2024. CWV is part of page experience, not a
standalone ranking guarantee.

Sources:
- https://web.dev/articles/vitals
- https://developers.google.com/search/docs/appearance/core-web-vitals
(Both fetches were blocked during this check; thresholds unchanged per
multiple 2026 secondary sources.)

## Bing and IndexNow

- Copilot grounds on the Bing index. Verify the site in Bing Webmaster Tools,
  submit sitemaps, and allow `Bingbot`.
- Bing Webmaster Tools AI Performance report (public preview February 2026):
  Copilot citations, cited pages, grounding queries.
- IndexNow pings participating engines when URLs change. Google does not
  participate; keep sitemaps accurate for Google.

Sources:
- https://www.bing.com/webmasters
- https://www.indexnow.org/

## Evidence boundary

Search Console, Bing Webmaster Tools, analytics, third-party SEO tools, and
live results measure different things. Name the source, market, scope, and
date. Unobserved results are `unknown`. Never turn a heuristic into a traffic,
ranking, citation, or conversion promise.
