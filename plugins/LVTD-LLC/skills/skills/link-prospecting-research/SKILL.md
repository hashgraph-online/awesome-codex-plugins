---
name: link-prospecting-research
description: Research link-building opportunities by mapping assets to opportunity types, building query libraries, analyzing competitor backlinks, finding scrapeable lists, and expanding prospecting seeds. Use when finding link prospects, creating link prospecting queries, mapping guest post/resource/directory opportunities, or producing a prospect research map before qualification or outreach.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Link Prospecting Research
  category: Marketing
  tags: seo,link-building,research,prospecting,organic-growth
---

# Link Prospecting Research

Use this skill to find potential link opportunities and produce a research map. Stop at research: do not qualify final targets, send outreach, submit forms, buy links, or promise acquisition.

This skill is derived from Garrett French and Eric Ward's *Ultimate Guide to Link Building* and uses transformed guidance with durable book-topic references. Do not copy book prose into user outputs.

## Quick Start

1. Use the Contents table below to choose the smallest useful reference set.
2. Use `workflows/research-link-prospects.md` for a full prospecting pass.
3. Start from available linkable assets and campaign goals.
4. Build keyword classes, opportunity types, query patterns, competitor backlink angles, list sources, and autocomplete expansions.
5. Return a deduped prospect research map with next qualification steps.

## Default Output

When asked to research prospects, return:

1. **Objective and scope** - site, target asset, audience, market, geography, and excluded tactics.
2. **Asset-to-opportunity fit** - assets mapped to likely opportunity types.
3. **Keyword universe** - market, customer, product, expert, competitor, geo, and adjacent vertical terms.
4. **Opportunity type map** - query patterns, signals, asset fit, and priority.
5. **Query library** - reusable research phrases, operators, footprints, and exclusions.
6. **Competitor backlink angles** - patterns worth investigating.
7. **List-scrape and autocomplete sources** - seed sets and filters.
8. **Risks and next actions** - noise, paid/sponsored risk, spam risk, and qualification gaps.

## Contents

| Need | Start Here |
|------|------------|
| Understand prospecting concepts | `references/core/knowledge.md` |
| Apply research rules | `references/core/rules.md` |
| Use query pattern examples | `references/core/examples.md` |
| Run a research pass | `workflows/research-link-prospects.md` |

## Core Posture

- Opportunity equals a linkable asset concept plus enough likely linkers.
- Query design should prequalify by asset fit and page type.
- More precise query segments beat digging deep into weak search results.
- Competitor backlinks are evidence, not an outreach-ready list.
- Final approval belongs to `link-prospect-qualification`.
