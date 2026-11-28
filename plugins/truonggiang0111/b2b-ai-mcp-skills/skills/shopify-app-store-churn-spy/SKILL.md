---
name: shopify-app-store-churn-spy
description: >-
  Scrape Shopify App Store 1-star and 2-star churn reviews, merchant store names,
  pricing tiers, and developer support emails via zero-proxy SSR endpoints.
  (Public Apify Store rollout at 22:00+07:00 today.)
---

# Shopify App Store 1-Star Churn & Dev Emails (`ttyan0111/shopify-app-store-churn-spy`)

- **Actor ID:** `CTYHbca6cOKRknDqV` (`ttyan0111/shopify-app-store-churn-spy` — staged private until 22:00+07:00 quota reset)
- **Dedicated MCP URL (when public):** `https://mcp.apify.com?actors=ttyan0111/shopify-app-store-churn-spy`
- **Pricing:** `$0.006` start + `$2.00/1k` apps + `$1.20/1k` churn reviews. Zero proxies needed.

## Example Input

```json
{
  "queries": ["klaviyo-email-marketing", "upsell"],
  "maxAppsPerQuery": 5,
  "includeReviews": true,
  "starRatings": ["1", "2"],
  "sortBy": "newest",
  "maxReviewsPerApp": 20,
  "onlyWithDeveloperEmail": false
}
```

## AI-Agent Workflow

- Read Key-Value Store **`RUN_SUMMARY`** first for developer email coverage, total churn reviews, and `painSignalTotals` (`crash_bug`, `billing_subscription`, `support_unresponsive`, `performance_slow`, `broken_after_update`, `switching_competitor`).
- Project item fields: `name,handle,rating,ratingCount,pricingSummary,developerName,developerEmail,developerWebsite,reviewsCount,mentionedDomains,painSignalSummary,agentSummary`.
