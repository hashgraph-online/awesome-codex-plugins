---
name: google-ads-transparency-spy
description: >-
  Spy on competitor Google Search, Display, and YouTube ads via Google Ads
  Transparency Center. Accepts domains, URLs, brands, or AR advertiser IDs to
  return active duration (Winning Ads filter), creative previews, and EU DSA
  impression reach stats.
---

# Google Ads Transparency Spy & EU DSA Ad Spend MCP

- **Apify Store:** `https://apify.com/ttyan0111/google-ads-transparency-spy`
- **Dedicated MCP URL:** `https://mcp.apify.com?actors=ttyan0111/google-ads-transparency-spy`
- **Pricing:** `$0.003` start + `$1.50/1k` ads + `$1.50/1k` enriched creatives & EU DSA stats.

## Connect via MCP (Claude Code, Cursor, VS Code)

```json
{
  "mcpServers": {
    "google-ads-spy": {
      "url": "https://mcp.apify.com?actors=ttyan0111/google-ads-transparency-spy"
    }
  }
}
```

## Example Input (Long-Running "Winning Ads")

```json
{
  "queries": ["shopify.com"],
  "countryCode": "US",
  "adFormat": "ALL",
  "minDaysActive": 30,
  "includeDetails": true,
  "maxAdsPerQuery": 25,
  "proxyConfiguration": {
    "useApifyProxy": true
  }
}
```

## AI-Agent Output Highlights

- Check **`RUN_SUMMARY`** for format breakdowns (`TEXT`, `IMAGE`, `VIDEO`), `winningAdsCount`, and resolved advertiser stats.
- Each item carries `agentSummary` summarizing advertiser, ad format, active days, and EU DSA reach range.
