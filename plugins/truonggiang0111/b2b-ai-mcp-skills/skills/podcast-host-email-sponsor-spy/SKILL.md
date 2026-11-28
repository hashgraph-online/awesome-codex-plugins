---
name: podcast-host-email-sponsor-spy
description: >-
  Find B2B podcast host direct emails from live RSS XML (<itunes:email>), filter
  active shows (non-podfaded), and extract recurring sponsor domains at $0 proxy cost.
  (Public Apify Store rollout at 22:00+07:00 today.)
---

# Apple Podcasts Host Emails & Sponsor Leads (`ttyan0111/podcast-host-email-sponsor-spy`)

- **Actor ID:** `VRbovzx0V0yMGBA2Q` (`ttyan0111/podcast-host-email-sponsor-spy` — staged private until 22:00+07:00 quota reset)
- **Dedicated MCP URL (when public):** `https://mcp.apify.com?actors=ttyan0111/podcast-host-email-sponsor-spy`
- **Pricing:** `$0.006` start + `$2.50/1k` verified host leads + `$1.50/1k` sponsor RSS parses. Zero proxies needed.

## Example Input

```json
{
  "queries": ["B2B SaaS", "AI engineering"],
  "country": "US",
  "maxPodcastsPerQuery": 15,
  "onlyWithEmail": true,
  "activeWithinDays": 90,
  "episodesToAnalyze": 5
}
```

## AI-Agent Workflow

- Bounded 400 KB XML stream extracts direct host emails without overflowing LLM context windows.
- Read Key-Value Store **`RUN_SUMMARY`** first for email coverage %, active show count, `topSponsorDomains`, and `topEmails`, then project `podcastName,hostAuthor,hostEmail,isPlatformRelayEmail,daysSinceLastEpisode,isActive,sponsorDomainsDetected,websiteUrl,agentSummary`.
