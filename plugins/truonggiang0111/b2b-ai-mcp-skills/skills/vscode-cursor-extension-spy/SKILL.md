---
name: vscode-cursor-extension-spy
description: >-
  Scrape VS Code Marketplace and Open-VSX (Cursor/Windsurf) extensions, combined
  installs, verified developer domains, GitHub repos, and 1-3 star bug reviews.
  (Public Apify Store rollout at 22:00+07:00 today.)
---

# VS Code & Open-VSX Extension & Bug Review Spy (`ttyan0111/vscode-cursor-extension-spy`)

- **Actor ID:** `tHlOKzyDNjIZ258tZ` (`ttyan0111/vscode-cursor-extension-spy` — staged private until 22:00+07:00 quota reset)
- **Dedicated MCP URL (when public):** `https://mcp.apify.com?actors=ttyan0111/vscode-cursor-extension-spy`
- **Pricing:** `$0.006` start + `$2.00/1k` extensions + `$1.20/1k` bug reviews. Zero proxies needed.

## Example Input

```json
{
  "queries": ["mcp", "ai coding"],
  "maxExtensionsPerQuery": 10,
  "sortBy": "installs",
  "includeOpenVsxStats": true,
  "includeReviews": true,
  "maxRatingFilter": 3,
  "maxReviewsPerExtension": 15
}
```

## AI-Agent Workflow

- Read Key-Value Store **`RUN_SUMMARY`** first for combined VS Code + Open-VSX install totals, verified domain coverage, and `painSignalTotals` (`crash_bug`, `auth_config_issue`, `billing_subscription`, `performance_slow`, `broken_after_update`).
- Project item fields: `displayName,uniqueIdentifier,publisherDisplayName,verifiedDomain,githubRepoUrl,vscodeInstalls,openVsxDownloads,totalCombinedInstalls,averageRating,reviewsCount,topPainSignals,agentSummary`.
