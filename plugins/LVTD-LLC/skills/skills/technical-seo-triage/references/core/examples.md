# Technical SEO Triage Examples

Examples for classifying and diagnosing technical SEO issues.

## Symptom Classification

| Symptom | Likely Stage | First Checks |
|---------|--------------|--------------|
| Page not in Google | Discovery or indexing | Internal links, sitemap, robots, URL inspection, canonical |
| Crawled but excluded | Indexing | Duplicate, thin content, canonical, quality, noindex |
| Impressions dropped, clicks stable | SERP display or reporting shift | GSC comparison, query/page segmentation |
| Clicks dropped, impressions stable | CTR or snippet issue | Title, meta, SERP features, intent mismatch |
| All old URLs lose traffic after relaunch | Migration | Redirect map, redirect status, canonicals, internal links |
| Important pages rarely crawled | Crawl budget/link graph | Internal links, low-value URL traps, sitemap, logs |

## Internal Linking Patterns

| Pattern | Issue | Better Approach |
|---------|-------|-----------------|
| Hub-only linking | Crawlers repeatedly pass through the same hubs | Add multiple paths between related and important pages |
| Popular-to-popular modules | New or niche pages remain hidden | Include recent, exploratory, and random/discovery modules |
| No HTML sitemap on large site | Deep pages may be hard to discover | Add a useful site directory or sitemap linked from stable pages |
| Dead-end pages | External authority does not flow onward | Add contextual links to related and priority pages |

## Migration Checklist Example

| Area | Check |
|------|-------|
| URL map | Every old URL has a mapped destination or intentional retirement |
| Redirect type | Permanent moves use 301 redirects |
| Pre-launch crawl | Old URLs resolve to expected new URLs |
| Canonicals | New URLs self-canonicalize or point to the intended canonical |
| Internal links | Navigation and content links point to new URLs |
| Monitoring | GSC, logs, and analytics are reviewed after launch |

## Traffic Drop Interpretation

### Weak Diagnosis

"Google updated the algorithm and punished the site."

### Strong Diagnosis

"The drop is concentrated in non-brand informational URLs on mobile in the US. Impressions fell on some query groups while clicks stayed stable on others. We should inspect affected URLs in GSC, compare canonical/index status, and review recent template/content changes before assuming an algorithm-wide issue."
