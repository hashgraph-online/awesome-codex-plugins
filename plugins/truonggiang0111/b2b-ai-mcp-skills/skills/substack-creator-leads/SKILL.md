---
name: substack-creator-leads
description: >-
  Extract Substack publications and B2B creator leads including direct contact
  emails, subscriber scale signals, paid pricing tiers, and recent post engagement
  metrics without proxies. (Public Store listing rolling out after Apify 24h
  publication quota reset.)
---

# Substack Newsletter & Creator Email Leads

- **Actor ID:** `0bA2Nc4ylXy6xgJSt` (`ttyan0111/substack-newsletter-creator-leads` — rolling out to public Apify Store after 24h daily limit reset)
- **Dedicated MCP URL (when public):** `https://mcp.apify.com?actors=ttyan0111/substack-newsletter-creator-leads`
- **Pricing:** `$0.006` start + `$2.00/1k` newsletters + `$1.50/1k` post enrichments. Zero proxies needed.

## Example Input

```json
{
  "queries": ["b2b saas", "artificial intelligence"],
  "paidNewslettersOnly": true,
  "withContactEmailOnly": true,
  "includeLatestPosts": true,
  "maxPostsPerPublication": 3,
  "maxPublicationsPerQuery": 25
}
```

## AI-Agent Workflow

- Inspect **`RUN_SUMMARY`** for count of newsletters with verified contact emails and paid subscription tiers.
- Export `publicationName`, `contactEmails`, `subscriberCountText`, `paidTiers`, `recentPosts`, and `agentSummary`.
