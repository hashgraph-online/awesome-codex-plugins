# International Technical SEO — Hreflang, URL Structures & Global Site Architecture

A comprehensive reference for building and maintaining websites that target multiple countries, languages, or regions. International SEO is one of the most technically complex areas of SEO — a single hreflang mistake can cause the wrong language version to rank in the wrong country.

---

## URL Structure Strategies

### Three Approaches

| Strategy | Example | Pros | Cons | Best For |
|---|---|---|---|---|
| **ccTLD** (country code top-level domain) | `example.de`, `example.co.uk`, `example.fr` | Strongest geo-targeting signal; users trust local domains; clear separation of properties | Most expensive (multiple domains to register and maintain); link equity does not transfer between domains; requires separate GSC properties; separate SEO authority per domain | Enterprise businesses with strong local presence in each market; brand already well-known in target countries |
| **Subdomain** | `de.example.com`, `uk.example.com`, `fr.example.com` | Easy to set up; can host on different servers/CDNs per region; separate GSC properties possible; geotargeting in GSC | Treated as semi-separate sites by Google; link equity from root domain has limited transfer; user trust slightly lower than ccTLD | Companies wanting regional separation with a single domain; sites needing different hosting per region |
| **Subdirectory** | `example.com/de/`, `example.com/uk/`, `example.com/fr/` | All link equity stays on one domain; easiest to maintain; single hosting setup; single GSC property with filtering; strongest domain authority consolidation | Cannot host on different servers per region without complex CDN configuration; less clear geo-targeting signal than ccTLD | Most businesses; the default recommendation unless specific requirements dictate otherwise |

### Decision Framework

**Choose ccTLD when:**
- The brand has separate business entities per country
- Strong local brand identity is essential (e.g., banking, government, legal services)
- Budget supports maintaining separate domains and separate SEO strategies
- Target countries have strong ccTLD preference (e.g., .de in Germany, .co.uk in UK)

**Choose subdomain when:**
- Regional content is managed by separate teams or hosted on different infrastructure
- The business needs separate GSC analytics per region but does not want multiple domains
- Content and user experience differ significantly by region (not just language)

**Choose subdirectory when (default recommendation):**
- SEO authority consolidation is a priority (most cases)
- A single team manages the website globally
- Budget and resources are limited
- The business is entering new markets and does not have established local authority

### Language vs Region in URL Structure

| URL Pattern | Targets | Example |
|---|---|---|
| `/es/` | Spanish language (all regions) | A blog post for all Spanish speakers |
| `/es-mx/` | Spanish language, Mexico specifically | A product page with Mexico-specific pricing, shipping, and legal requirements |
| `/es-es/` | Spanish language, Spain specifically | A product page with Spain-specific pricing and regulations |

Use language-only paths (`/es/`) when content is identical for all speakers of that language. Use language-region paths (`/es-mx/`) when content differs by country (pricing, legal, shipping, cultural references, local phone numbers, currency).

---

## Hreflang Implementation

### Purpose

Hreflang tags tell search engines which language and regional version of a page to show to users in different locations. Without hreflang, Google may show the French version of a page to English-speaking users, or the US version to UK users.

### Syntax

The hreflang attribute uses ISO 639-1 language codes and optional ISO 3166-1 Alpha-2 country codes:

| Format | Meaning | Example |
|---|---|---|
| `hreflang="en"` | English (any region) | General English content |
| `hreflang="en-us"` | English (United States) | US-specific pricing and content |
| `hreflang="en-gb"` | English (United Kingdom) | UK-specific pricing and content |
| `hreflang="es"` | Spanish (any region) | General Spanish content |
| `hreflang="es-mx"` | Spanish (Mexico) | Mexico-specific content |
| `hreflang="zh-hans"` | Chinese (Simplified) | Simplified Chinese content |
| `hreflang="zh-hant"` | Chinese (Traditional) | Traditional Chinese content |
| `hreflang="x-default"` | Default/fallback | Language selector page or default language version |

### Implementation Methods

**Method 1: HTML Link Elements (in `<head>`)**

```html
<link rel="alternate" hreflang="en-us" href="https://example.com/page">
<link rel="alternate" hreflang="en-gb" href="https://example.com/uk/page">
<link rel="alternate" hreflang="de" href="https://example.com/de/page">
<link rel="alternate" hreflang="fr" href="https://example.com/fr/page">
<link rel="alternate" hreflang="x-default" href="https://example.com/page">
```

**Best for**: Sites with fewer than 20 language/region versions per page. Above that, the HTML `<head>` becomes bloated.

**Method 2: HTTP Headers**

```
Link: <https://example.com/page>; rel="alternate"; hreflang="en-us",
      <https://example.com/uk/page>; rel="alternate"; hreflang="en-gb",
      <https://example.com/de/page>; rel="alternate"; hreflang="de",
      <https://example.com/fr/page>; rel="alternate"; hreflang="fr",
      <https://example.com/page>; rel="alternate"; hreflang="x-default"
```

**Best for**: Non-HTML resources (PDFs, documents) that need hreflang but cannot contain HTML tags.

**Method 3: XML Sitemap (Recommended for Large Sites)**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
  <url>
    <loc>https://example.com/page</loc>
    <xhtml:link rel="alternate" hreflang="en-us" href="https://example.com/page"/>
    <xhtml:link rel="alternate" hreflang="en-gb" href="https://example.com/uk/page"/>
    <xhtml:link rel="alternate" hreflang="de" href="https://example.com/de/page"/>
    <xhtml:link rel="alternate" hreflang="fr" href="https://example.com/fr/page"/>
    <xhtml:link rel="alternate" hreflang="x-default" href="https://example.com/page"/>
  </url>
  <url>
    <loc>https://example.com/uk/page</loc>
    <xhtml:link rel="alternate" hreflang="en-us" href="https://example.com/page"/>
    <xhtml:link rel="alternate" hreflang="en-gb" href="https://example.com/uk/page"/>
    <xhtml:link rel="alternate" hreflang="de" href="https://example.com/de/page"/>
    <xhtml:link rel="alternate" hreflang="fr" href="https://example.com/fr/page"/>
    <xhtml:link rel="alternate" hreflang="x-default" href="https://example.com/page"/>
  </url>
</urlset>
```

**Best for**: Sites with 20+ language/region versions, or any site where maintaining hreflang in HTML `<head>` is impractical. The sitemap method keeps the HTML clean and is easier to generate programmatically.

### Common Hreflang Mistakes

| Mistake | Impact | Fix |
|---|---|---|
| **Missing self-referencing hreflang** | Google may not process the hreflang set correctly | Every page must include a hreflang tag pointing to itself |
| **Missing x-default** | No fallback for users in unlisted regions/languages | Add x-default pointing to the language selector page or the primary language version |
| **Missing return links (bidirectional)** | If page A hreflang-links to page B, but page B does not link back to page A, Google ignores the annotation | Ensure every page in the hreflang set includes the complete set of all alternate versions |
| **Hreflang pointing to non-canonical URL** | If canonical and hreflang reference different URLs, Google may ignore hreflang | Hreflang href values must match the canonical URL of each page |
| **Hreflang pointing to noindex/blocked page** | Google cannot index a page it cannot access; hreflang signal is lost | All hreflang targets must be indexable, crawlable, and return 200 |
| **Wrong language/region codes** | `hreflang="uk"` is not valid (UK is a country code; the language code for Ukrainian is `uk`, but English for the UK is `en-gb`) | Use ISO 639-1 for language and ISO 3166-1 Alpha-2 for country. Validate codes |
| **Inconsistent URL formats** | Mixing `http` and `https`, or `www` and non-www, in hreflang URLs | Use the exact canonical URL format consistently across all hreflang annotations |
| **Using hreflang for duplicate content** | Two pages with the same content in the same language, just different URLs | Hreflang is for different language/region versions. Use canonical for same-language duplicates |

### Hreflang Validation

- **Google Search Console > International Targeting report**: Shows hreflang errors detected by Google
- **Screaming Frog**: Crawls all hreflang annotations and flags missing return links, invalid codes, and conflicts with canonicals
- **Aleyda Solis' Hreflang Tags Generator**: Generates correct hreflang markup from a URL matrix
- **Merkle Hreflang Tag Testing Tool**: Validates hreflang implementation on live pages

---

## Geotargeting

### Google Search Console International Targeting

For subdirectories and subdomains (not ccTLDs — ccTLDs are automatically geo-targeted):

1. Go to Google Search Console > Legacy tools > International Targeting
2. Select the property (e.g., `example.com/de/`)
3. Set the target country (e.g., Germany)

**Note**: This feature targets a **country**, not a language. A subdirectory can target Germany but not "German speakers worldwide." For language targeting without country restriction, use hreflang without GSC geotargeting.

### IP-Based Redirection: Do Not Do This

Redirecting users based on their IP address is a common mistake in international SEO:

- **Problem**: Googlebot primarily crawls from US IP addresses. If you redirect US IPs to the English version, Google may never crawl or index your non-English versions
- **Alternative**: Show a banner suggesting the appropriate language/region version (e.g., "It looks like you are in Germany. View our German site?") without redirecting. Let the user choose
- **Exception**: Using IP detection to set a default language preference on the first visit is acceptable if the user can easily switch and if all versions are accessible to crawlers without IP-based blocking

---

## Content Localization vs Translation

### Translation

Direct linguistic conversion of content from one language to another. Necessary but insufficient for effective international SEO.

### Localization

Adapting content for the cultural, legal, and market context of the target region:

| Dimension | Translation Only | Full Localization |
|---|---|---|
| **Currency** | Dollar amounts left as-is | Converted to local currency |
| **Units** | Imperial measurements | Metric (or local standard) |
| **Date formats** | MM/DD/YYYY | DD/MM/YYYY or YYYY-MM-DD per locale |
| **Phone numbers** | US format | Local format with country code |
| **Legal references** | US regulations | Local regulations and compliance |
| **Cultural references** | US holidays, sports, idioms | Locally relevant references |
| **Images** | Global stock photos | Locally relevant people, settings, products |
| **Payment methods** | Credit cards | iDEAL (Netherlands), Klarna (Nordics), PIX (Brazil), UPI (India) |
| **Social proof** | Global testimonials | Local customer testimonials and case studies |
| **Keyword targeting** | Translated keywords | Locally researched keywords (search behavior differs) |

### International Keyword Research

Keywords do not translate 1:1 between languages. Differences include:

- **Search volume**: A keyword with 10K monthly searches in English may have a direct translation with only 500 searches in German because Germans use a different phrase
- **Search intent**: The same translated phrase may have different intent in different markets
- **Colloquialisms**: "Sneakers" (US) vs "trainers" (UK) vs "Turnschuhe" (DE) — all mean athletic shoes
- **Brand vs generic**: Some markets search for brand names more than generic terms (or vice versa)

Always conduct keyword research natively in each target language using local search data, not by translating an English keyword list.

---

## International Site Architecture Patterns

### Pattern 1: Single Domain, Subdirectories (Most Common)

```
example.com/           (English, US — default)
example.com/uk/        (English, UK)
example.com/de/        (German)
example.com/fr/        (French)
example.com/es-mx/     (Spanish, Mexico)
```

- Single domain authority
- One hosting setup (use CDN for global performance)
- Hreflang in XML sitemap
- GSC: One property with directory-level filtering

### Pattern 2: Subdomains Per Region

```
www.example.com        (English, US — default)
uk.example.com         (English, UK)
de.example.com         (German)
fr.example.com         (French)
mx.example.com         (Spanish, Mexico)
```

- Semi-separate authority (subdomains inherit some root domain authority)
- Can host on different servers/CDNs per region for performance
- Separate GSC properties per subdomain
- More complex to manage

### Pattern 3: ccTLDs Per Country

```
example.com            (English, US)
example.co.uk          (English, UK)
example.de             (German)
example.fr             (French)
example.com.mx         (Spanish, Mexico)
```

- Completely separate domain authority
- Strongest geo-targeting signal
- Most expensive and complex to maintain
- Each domain needs its own link building and SEO strategy

### Pattern 4: Hybrid (ccTLD + Subdirectories for Languages)

```
example.de/            (German, Germany)
example.de/en/         (English version for Germany)
example.co.uk/         (English, UK)
example.com/           (English, US — default)
example.com/es/        (Spanish, general)
example.com/fr/        (French, general)
```

- Used when some markets justify ccTLDs (major markets) but others do not
- Combines strong local signals for key markets with consolidated authority for secondary markets

---

## CDN and Server Location

### Impact on International Performance

- **Server location affects TTFB**: A server in the US serving pages to users in Australia adds 200-300ms of latency per request
- **CDN is essential for international sites**: Cache static assets and HTML at edge locations near users in each target market
- **Key CDN providers**: Cloudflare (broadest free tier), Fastly (best real-time purging), CloudFront (best for AWS infrastructure), Akamai (enterprise)

### CDN Configuration for International Sites

1. **Cache HTML at the edge** — not just static assets. This eliminates TTFB latency for cached pages
2. **Set cache keys to include language/region** — ensure `/de/` pages are cached separately from `/en/` pages
3. **Use the Vary header** if serving different content from the same URL based on Accept-Language: `Vary: Accept-Language` (not recommended — subdirectory approach is cleaner)
4. **Monitor CDN cache hit rates by region** — low hit rates in a region indicate either insufficient edge presence or aggressive cache expiry

---

## Search Engine Market Share by Country

| Country | Primary Search Engine | Market Share | Notes |
|---|---|---|---|
| United States | Google | ~87% | Bing has ~7% (important for B2B due to workplace defaults) |
| United Kingdom | Google | ~92% | |
| Germany | Google | ~90% | |
| France | Google | ~91% | |
| Japan | Google | ~76% | Yahoo Japan (~15%) uses Google's index |
| South Korea | Naver | ~55% | Google ~35%. Naver requires separate optimization |
| China | Baidu | ~65% | Google is blocked. Baidu requires ICP license, Simplified Chinese, .cn domain |
| Russia | Yandex | ~60% | Google ~38%. Yandex has different ranking factors |
| Czech Republic | Seznam | ~25% | Google ~72%. Seznam still significant |
| Brazil | Google | ~96% | |
| India | Google | ~98% | |

### SEO Implications by Search Engine

**Baidu (China):**
- Requires an ICP license to host in China (mandatory)
- Simplified Chinese content is essential
- .cn ccTLD is strongly preferred
- JavaScript rendering is limited — SSR or static HTML required
- Meta keywords tag is still used as a ranking signal
- Baidu Webmaster Tools for submission and monitoring

**Yandex (Russia):**
- Strong behavioral signals (user engagement metrics affect rankings)
- Yandex Webmaster tools for submission and monitoring
- Regional ranking algorithm differs from Google (strong local geo signals)
- Supports its own structured data formats alongside schema.org
- Slower to crawl than Google — sitemaps are critical

**Naver (South Korea):**
- Blog and knowledge content (Naver Blog, Naver Knowledge iN) ranks prominently
- Naver Webmaster Tools for submission
- Korean-language content on Naver's own platforms gets priority
- Consider Naver Blog as a content channel alongside the website

---

## Legal and Compliance Considerations

### GDPR (European Economic Area)

- Cookie consent banner required before setting non-essential cookies
- Privacy policy must be available in local language
- Data processing agreements required with third-party tools
- Right to erasure affects user-generated content
- Analytics must comply (server-side analytics, anonymized IP, consent-based tracking)

### CCPA/CPRA (California, US)

- "Do Not Sell My Personal Information" link required for California users
- Privacy policy must disclose data collection practices

### ePrivacy Directive (EU)

- Applies to electronic communications, cookies, and tracking
- Stricter than GDPR for certain marketing activities (email marketing requires explicit opt-in)

### Country-Specific Requirements

| Country | Requirement | Impact on Website |
|---|---|---|
| Germany | Impressum (legal notice) page mandatory | Add `/impressum` page with company details |
| France | Legal mentions (mentions legales) required | Add `/mentions-legales` page |
| China | ICP license number displayed on homepage | Required for hosting in China |
| Australia | Privacy Act compliance, spam act for email | Privacy policy and email consent mechanisms |
| Brazil | LGPD (similar to GDPR) | Cookie consent and privacy compliance |
| Canada | CASL for email marketing, PIPEDA for privacy | Explicit consent for marketing emails |
| Japan | APPI (data protection law) | Privacy policy and consent mechanisms |

### Structured Data for Legal Compliance

- Implement Organization schema with `address` per country entity
- Use LocalBusiness schema for physical locations in each country
- Include `areaServed` in Service and Product schema to clarify geographic availability
- Ensure `priceRange` and `priceCurrency` in Product schema match the local currency and pricing
