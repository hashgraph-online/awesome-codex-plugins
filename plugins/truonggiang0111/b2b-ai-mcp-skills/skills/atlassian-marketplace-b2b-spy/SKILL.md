---
name: atlassian-marketplace-b2b-spy
description: >-
  Extract Atlassian Marketplace (Jira, Confluence, Bitbucket, JSM) app installs,
  active users, Cloud Fortified & partner tiers, pricing, vendor emails, and
  1-2 star enterprise churn reviews ($0 proxy cost).
---

# Atlassian Marketplace App & Churn Spy (`ttyan0111/atlassian-marketplace-b2b-spy`)

- **Actor ID:** `okE229LJXfmguNyI4` (`ttyan0111/atlassian-marketplace-b2b-spy` — staged private pending daily Apify Store publication slot)
- **Dedicated MCP URL (when public):** `https://mcp.apify.com?actors=ttyan0111/atlassian-marketplace-b2b-spy`
- **Pricing:** `$0.006` start + `$2.00/1k` apps + `$1.20/1k` churn reviews analyzed. Zero proxies needed (`256 MB` RAM).

## Example Input

```json
{
  "queries": ["time tracking", "workflow automation"],
  "application": "jira",
  "hosting": "cloud",
  "maxAppsPerQuery": 5,
  "includeChurnReviews": true,
  "maxReviewsPerApp": 15
}
```

## AI-Agent Workflow

- Read Key-Value Store **`RUN_SUMMARY`** first for `totalApps`, `vendorEmailsFound`, `totalChurnReviews`, `highInstallVulnerableApps`, and `topPainCategories` (`cloud_migration_bug`, `support_sla`, `billing_pricing`, `performance_scale`, `missing_enterprise_feature`).
- Project item fields: `name,addonKey,vendorName,vendorEmail,vendorDomain,totalInstalls,totalUsers,averageStars,cloudFortified,partnerTier,startingPriceUsd,churnReviewsCount,topPainCategories,marketplaceUrl,agentSummary`.
