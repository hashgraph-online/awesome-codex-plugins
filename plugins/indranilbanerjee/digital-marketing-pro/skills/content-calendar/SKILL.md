---
name: content-calendar
description: "Plan content calendars. Use when: monthly or quarterly scheduling, platform assignments, content pillars, repurposing."
argument-hint: "[month or quarter]"
---

# /digital-marketing-pro:content-calendar

## Purpose

Generate a structured content calendar that maps topics to platforms, aligns with content pillars, and includes a repurposing workflow to maximize output from each core piece.

## Input Required

The user must provide (or will be prompted for):

- **Time period**: Month, quarter, or custom date range
- **Platforms**: Which channels to plan for (blog, social, email, video, podcast)
- **Content pillars**: Core themes or topics (or let the system recommend based on brand profile)
- **Publishing cadence**: How often per platform (e.g., 3 blogs/month, daily social)
- **Key dates**: Product launches, holidays, industry events, promotions
- **Team capacity**: Who creates content and how much bandwidth exists

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. **Also check for guidelines** at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions and relevant category files. Check for custom templates at `~/.claude-marketing/brands/{slug}/templates/`. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. Define or validate content pillars based on brand expertise and audience needs
3. Map key dates, seasonal trends, and industry events to the calendar
4. Generate topic ideas for each pillar, distributed across the time period
5. Assign each topic to a primary platform and content format
6. Build repurposing chains: blog to social snippets, video to short clips, email to blog, etc.
7. Balance content types: educational, promotional, engagement, thought leadership
8. Add SEO keyword targets to relevant content pieces
9. Output the calendar in a structured, sortable format

## Output

A structured content calendar containing:

- Monthly/weekly view with publish dates and platforms
- Topic and title for each content piece
- Content pillar and funnel stage tags
- Primary format and repurposing derivatives
- Keyword targets for SEO-driven content
- Owner/assignee column (if team info provided)
- Repurposing workflow diagram showing content atomization paths

## Agents Used

- **content-creator** — Topic ideation, pillar strategy, repurposing workflows, editorial planning
- **seo-specialist** — Keyword alignment, search trend timing, topic gap identification
- **social-media-manager** — Platform-specific posting cadence, content format recommendations, hashtag strategy, calendar validation
