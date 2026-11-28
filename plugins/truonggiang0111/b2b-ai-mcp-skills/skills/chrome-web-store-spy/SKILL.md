---
name: chrome-web-store-spy
description: >-
  Extract Chrome Web Store extensions, developer support emails (Micro-SaaS B2B
  leads), install counts, ratings, and user reviews with automated pain-signal tags.
  (Public Store listing rolling out after Apify 24h publication quota reset.)
---

# Chrome Web Store Extensions, Dev Emails & Reviews

- **Actor ID:** `gfQJdGY82XhWQfHi9` (`ttyan0111/chrome-web-store-extension-spy` — rolling out to public Apify Store after 24h daily limit reset)
- **Dedicated MCP URL (when public):** `https://mcp.apify.com?actors=ttyan0111/chrome-web-store-extension-spy`
- **Pricing:** `$0.006` start + `$2.00/1k` extensions + `$1.20/1k` reviews. Zero proxies needed.

## Example Input

```json
{
  "queries": ["notion", "ai writing"],
  "includeReviews": true,
  "maxExtensionsPerQuery": 15,
  "maxReviewsPerExtension": 10,
  "onlyWithDeveloperEmail": true
}
```

## AI-Agent Workflow

- Read Key-Value Store **`RUN_SUMMARY`** for developer email coverage and top negative review pain-signal tags (`crash_bug`, `billing_subscription`, `performance_slow`, `broken_after_update`, `feature_request`).
