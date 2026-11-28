---
name: wordpress-plugin-churn-spy
description: >-
  Extract WordPress.org and WooCommerce plugin active installs, domain-verified
  vendor emails, 1-2 star RSS churn reviews, and live unresolved merchant
  support forum tickets ($0 proxy cost).
---

# WordPress & WooCommerce Plugin Churn Spy (`ttyan0111/wordpress-plugin-churn-spy`)

- **Actor ID:** `gpcdQYoORhHYCPREc` (`ttyan0111/wordpress-plugin-churn-spy` — staged private pending daily Apify Store publication slot)
- **Dedicated MCP URL (when public):** `https://mcp.apify.com?actors=ttyan0111/wordpress-plugin-churn-spy`
- **Pricing:** `$0.006` start + `$2.00/1k` plugins + `$1.20/1k` churn reviews & unresolved tickets analyzed. Zero proxies needed (`256 MB` RAM).

## Example Input

```json
{
  "queries": ["woocommerce stripe", "checkout upsell"],
  "maxPluginsPerQuery": 5,
  "minActiveInstalls": 500,
  "includeChurnReviews": true,
  "maxReviewsPerPlugin": 15,
  "includeUnresolvedSupport": true,
  "enrichAuthorContacts": true
}
```

## AI-Agent Workflow

- Read Key-Value Store **`RUN_SUMMARY`** first for `totalPlugins`, `totalChurnReviews`, `totalUnresolvedTickets`, `vendorEmailsFound`, and `topPainCategories` (`woocommerce_checkout_bug`, `site_slowdown_crash`, `unresponsive_support`, `broken_update_regression`, `billing_upsell_lockin`).
- Project item fields: `name,slug,authorName,vendorEmail,vendorDomain,activeInstalls,averageStars,oneStarCount,unresolvedSupportThreads,churnReviewsCount,unresolvedTicketsCount,topPainCategories,pluginUrl,agentSummary`.
