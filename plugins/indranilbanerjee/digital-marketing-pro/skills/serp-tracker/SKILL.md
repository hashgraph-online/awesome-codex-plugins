---
name: serp-tracker
description: "Deprecated — merged into rank-monitor. Use /digital-marketing-pro:rank-monitor --features for SERP-feature tracking (AI Overviews, snippets, PAA, local pack)."
---

# /digital-marketing-pro:serp-tracker (deprecated → rank-monitor)

**This skill has been merged into `/digital-marketing-pro:rank-monitor`.** SERP-feature tracking is now the `--features` mode of that single skill, so ranking positions and SERP features are captured in one run against one config.

## What to run instead

```
/digital-marketing-pro:rank-monitor --features
```

That mode tracks the same features this skill used to — AI Overviews, Featured Snippets, People Also Ask, Knowledge Panels, Local Pack, Image Pack, Video Carousel, Shopping, Sitelinks — plus feature ownership vs. competitors, and the query-by-feature matrix.

## Notes on what changed

- **One skill, one config.** No more maintaining a separate SERP-feature keyword list — `rank-monitor` reads the same keyword set for both positions and features.
- **AI Overview tracking is a binary presence signal** (did an AI Overview appear, is the brand cited). It is **not** an AI-visibility score. For scored AI visibility across the 6 canonical surfaces use `/digital-marketing-pro:geo-monitor` / `/digital-marketing-pro:aeo-audit`; for actual AI impressions use `/digital-marketing-pro:gsc-ai-performance`.
- **GSC does not export per-query SERP-feature layout or AI Overview citation lists** — feature presence comes from a connected rank-tracker MCP or manual observation. (An earlier version of this skill overstated GSC's coverage here.)

See `/digital-marketing-pro:rank-monitor` for the full methodology, data-source notes, and output format.
