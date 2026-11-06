# Sources

Primary sources behind the claims in this skill. Checked 2026-10-23 unless
noted. Re-check before any client deliverable quotes a rule as current.

## Google

- AI features and your website (AI Overviews, AI Mode, eligibility, controls,
  reporting): https://developers.google.com/search/docs/appearance/ai-features
- Optimizing for generative AI features (no special files, no chunking, scaled
  content abuse; last updated 2026-07-10):
  https://developers.google.com/search/docs/fundamentals/ai-optimization-guide
- Search Generative AI performance reports in Search Console (June 2026):
  https://developers.google.com/search/blog/2026/06/gen-ai-performance-reports
- Google common crawlers, including Google-Extended:
  https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers
- FAQ rich results ended May 7, 2026 (notice on the FAQPage doc; direct fetch
  was blocked during this check, confirmed via secondary coverage at
  https://www.techwyse.com/news/ai-search/google-faq-rich-results-deprecated-2026):
  https://developers.google.com/search/docs/appearance/structured-data/faqpage
- Spam policies (scaled content abuse, doorway abuse, site reputation abuse):
  https://developers.google.com/search/docs/essentials/spam-policies
- Organization structured data:
  https://developers.google.com/search/docs/appearance/structured-data/organization

## Answer-engine crawlers

- OpenAI: https://developers.openai.com/api/docs/bots
- Anthropic: https://support.claude.com/en/articles/8896518
- Perplexity: https://docs.perplexity.ai/docs/resources/perplexity-crawlers

## Microsoft

- Bing Webmaster Tools (AI Performance report, public preview February 2026):
  https://www.bing.com/webmasters
- IndexNow: https://www.indexnow.org/

## Research

- Generative engine optimization research (KDD 2024), which tested content
  edits against generative engines and found that adding citations, quotations,
  and statistics improved source visibility while keyword stuffing did not:
  https://arxiv.org/abs/2311.09735
  Use the direction of the finding. Its benchmark and engines predate current
  products, so do not quote its percentages as current lifts.

## Not verified

- `llms.txt` support: no major engine operator documents reading it as of this
  check. Google states Search does not use it. Vendor reports claiming adoption
  cite no primary statements.
- OKF ingestion by any answer engine: none announced.
