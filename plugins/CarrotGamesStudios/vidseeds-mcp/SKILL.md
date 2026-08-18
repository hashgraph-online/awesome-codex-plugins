---
name: vidseeds
description: Registry fallback entry point for the VidSeeds.ai MCP connector. Use the bundled domain skills for setup, efficiency, thumbnails, projects, analytics, local video, and publishing workflows.
license: MIT
---

# VidSeeds.ai MCP Connector

VidSeeds.ai is a pre-upload video SEO, metadata optimization, AI thumbnail, and multi-platform publishing connector for existing videos.

Use the focused skills in `skills/` for real workflows:

- `vidseeds-setup`
- `vidseeds-efficiency`
- `vidseeds-projects`
- `vidseeds-thumbnails`
- `vidseeds-analytics`
- `vidseeds-local-video`
- `vidseeds-publishing`

The hosted endpoint is `https://vidseeds.ai/api/mcp`. The connector uses a user-provided `VIDSEEDS_PAT` token and does not ship credentials.
