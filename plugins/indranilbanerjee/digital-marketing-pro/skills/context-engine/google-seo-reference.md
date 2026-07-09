# Google SEO Quick Reference (March 2026)

Concise reference guide for agents and skills. Not a reproduction of Google's documentation — see Official Documentation Links at the bottom for full details.

---

## How Google Search Works

Three stages: **Crawling** (Googlebot discovers pages via links and sitemaps), **Indexing** (processes and stores content, metadata, signals), **Serving** (ranks indexed pages by relevance, quality, usability). Pages must be crawlable and indexable to appear.

---

## Google Search Essentials

### Technical Requirements
- Pages accessible to Googlebot (not blocked by robots.txt or noindex)
- HTTP 200 for indexable content
- HTML preferred; JS-rendered content supported but slower to index
- HTTPS required

### Spam Policies
- No cloaking, doorway pages, hidden text/links
- No keyword stuffing, link spam (buying links, excessive exchanges)
- No scraped or auto-generated content without added value
- No sneaky redirects, thin affiliate pages
- **Scaled Content Abuse** (March 2024): AI-generated content at scale without unique value — major enforcement since June 2025
- **Site Reputation Abuse** (November 2024): Third-party content on high-authority domains without editorial oversight

### Key Best Practices
- Content for users, not search engines
- Clear hierarchy, descriptive unique titles and meta descriptions
- Heading tags (H1-H6) for logical structure
- Image alt text and appropriate file sizes
- Mobile-friendly responsive design
- Core Web Vitals optimization
- XML sitemap in Search Console
- JSON-LD structured data

---

## E-E-A-T (Content Quality)

- **Experience**: First-hand experience (original photos, personal stories, demonstrated use)
- **Expertise**: Relevant knowledge or credentials (professional background, technical depth)
- **Authoritativeness**: Recognized as a go-to source (citations, brand mentions, expert recognition)
- **Trustworthiness**: Reliable and transparent (contact info, secure site, editorial standards)

**YMYL**: Health, finance, safety, legal topics held to highest E-E-A-T standards.

**December 2025 update**: E-E-A-T evaluation now extends to ALL competitive queries, not just YMYL topics.

---

## Core Web Vitals

Measured at the 75th percentile of real user data (field data).

| Metric | Good | Needs Improvement | Poor |
|--------|------|-------------------|------|
| **LCP** (Largest Contentful Paint) | ≤ 2.5s | 2.5s – 4.0s | > 4.0s |
| **INP** (Interaction to Next Paint) | ≤ 200ms | 200ms – 500ms | > 500ms |
| **CLS** (Cumulative Layout Shift) | ≤ 0.1 | 0.1 – 0.25 | > 0.25 |

- INP replaced FID on March 12, 2024. FID fully removed from all Chrome tools September 9, 2024. Do NOT reference FID.
- CWV are a confirmed ranking signal (since June 2021)
- Field data (CrUX) preferred over lab data (Lighthouse)

---

## Schema Markup Status (March 2026)

### Active and Supported
Article, BreadcrumbList, Course, Dataset, Event, ItemList, JobPosting, LocalBusiness, Organization, Person, Product, ProductGroup, ProfilePage, Recipe, Review, SoftwareApplication, SoftwareSourceCode, VideoObject, Clip, SeekToAction, BroadcastEvent, Certification, OfferShippingDetails, MerchantReturnPolicy, DiscussionForumPosting

### Deprecated / Restricted
- **HowTo**: Deprecated (Sept 2023) — rich results removed
- **FAQ**: Restricted to gov/health sites only (Aug 2023)
- **SpecialAnnouncement**: Deprecated (July 2025)
- **EnergyConsumptionDetails**: Replaced by Certification (April 2025)

### JSON-LD Required
Google recommends JSON-LD for all structured data. Microdata and RDFa are supported but not preferred.

---

## Image SEO Best Practices

- **Format**: WebP (97%+ support) or AVIF (92%+) over JPEG/PNG
- **`<picture>`**: Progressive enhancement with AVIF > WebP > JPEG fallback
- **LCP image**: `fetchpriority="high"`, NO `loading="lazy"`, NO `decoding="async"`
- **Non-LCP images**: `loading="lazy"` + `decoding="async"`
- **Dimensions**: Always set `width` and `height` on `<img>` for CLS prevention
- **Alt text**: Descriptive (10-125 chars), natural keyword inclusion, not "image.jpg"
- **File names**: Descriptive, hyphenated, lowercase (`blue-running-shoes.webp`)
- **JPEG XL**: Chrome support being restored (Nov 2025 announcement) — not yet in stable. Monitor.

---

## AI Search Optimization (GEO/AEO)

### Key Surfaces (2026)
- Google AI Overviews
- ChatGPT web search
- Perplexity
- Microsoft Copilot
- Gemini

### Optimization Signals
- **Entity consistency**: Brand name, descriptions, key claims consistent across website, social profiles, directories, third-party mentions
- **Citation-worthy content**: Stats, original research, expert quotes, structured data
- **Structured answers**: Concise answer blocks suitable for featured snippets and AI extraction
- **Speakable content**: Short, clear answers for voice search and AI assistants
- **Source authority**: Established domain authority, quality backlinks, E-E-A-T signals

---

## Official Documentation Links

- Google Search Central: https://developers.google.com/search
- Search Console Help: https://support.google.com/webmasters
- Structured Data: https://developers.google.com/search/docs/appearance/structured-data
- Core Web Vitals: https://web.dev/vitals/
- Search Quality Rater Guidelines: https://guidelines.raterhub.com/
