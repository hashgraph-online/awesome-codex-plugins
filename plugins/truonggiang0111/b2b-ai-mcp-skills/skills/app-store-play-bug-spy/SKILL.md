---
name: app-store-play-bug-spy
description: >-
  Extract iOS App Store and Android Google Play reviews in one unified JSON schema
  by app name, bundle ID, or URL. Uses server-side Google Play star filtering and
  automated pain-signal tagging (crashes, billing, slow performance). Use for
  competitor PM research or bug hunting via MCP.
---

# App Store + Google Play Reviews 2-in-1 Bug Spy

- **Apify Store:** `https://apify.com/ttyan0111/app-store-play-reviews-spy`
- **Dedicated MCP URL:** `https://mcp.apify.com?actors=ttyan0111/app-store-play-reviews-spy`
- **Pricing:** `$0.005` start + `$0.005/app` + `$1.20/1k` reviews + `$1.50/1k` pain-signal analyses (free `$5/mo` Apify credit works out of the box).

## Connect via MCP (Claude Code, Cursor, VS Code)

```json
{
  "mcpServers": {
    "app-reviews-spy": {
      "url": "https://mcp.apify.com?actors=ttyan0111/app-store-play-reviews-spy"
    }
  }
}
```

## Example Input (Extract 1–2 Star Competitor Complaints)

```json
{
  "apps": ["Notion", "Obsidian"],
  "platforms": ["ios", "android"],
  "countries": ["us", "gb"],
  "sortBy": "mostRecent",
  "minRating": 1,
  "maxRating": 2,
  "maxReviewsPerPlatform": 30
}
```

## AI-Agent Workflow

1. Inspect **`RUN_SUMMARY`** in Key-Value Store for `painSignalCounts` (`crash_bug`, `billing_subscription`, `performance_slow`, etc.) across iOS and Android.
2. Fetch compact rows with `fields=platform,rating,appVersion,painSignals,agentSummary,body`.
