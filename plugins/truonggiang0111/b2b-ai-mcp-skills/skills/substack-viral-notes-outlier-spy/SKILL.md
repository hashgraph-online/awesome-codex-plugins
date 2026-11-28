---
name: substack-viral-notes-outlier-spy
description: >-
  Analyze Substack creators and niches for viral Notes ranked by weighted
  engagement (Likes + 3x Replies + 5x Restacks), detect >= 2.0x outliers,
  compute best word-length buckets and UTC hours, and export Ghostwriter swipe prompts.
---

# Substack Viral Notes Outlier & Hook Spy (`ttyan0111/substack-viral-notes-outlier-spy`)

- **Actor ID:** `M94EJel0a0kLProDy` (`ttyan0111/substack-viral-notes-outlier-spy` — staged private for public Store rollout)
- **Dedicated MCP URL (when public):** `https://mcp.apify.com?actors=ttyan0111/substack-viral-notes-outlier-spy`
- **Pricing:** `$0.005` start + `$1.50/1k` notes + `$0.003/creator` insights. Zero proxies required (`256 MB` RAM).

## Example Input

```json
{
  "queries": ["gurwinder", "dan"],
  "maxNotesPerCreator": 25,
  "maxCreatorsPerKeyword": 3,
  "onlyOutliers": false,
  "minOutlierMultiplier": 1,
  "sortBy": "viralScore"
}
```

## AI-Agent Workflow (Low-Token Inspection)

- Read Key-Value Store **`RUN_SUMMARY`** first — includes `insights` (`avgViralScore`, `bestLengthBucket`, `bestHourUTC`, `bestDayOfWeek`, `mediaLiftPct`), `outlierCount`, `topHooks`, and pre-built `ghostwriterSwipePrompt`.
- Project compact dataset fields: `noteId,handle,hook,viralScore,outlierMultiplier,isOutlier,lengthBucket,likes,comments,restacks,wordCount,publishedAt,noteUrl,agentSummary`.
