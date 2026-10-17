---
name: broken-link-building
description: Run broken link building and link equity salvage workflows by finding relevant resource pages, checking outbound link status, verifying dead URLs, qualifying dead backlinks, preparing replacement outreach, and mapping old owned URLs to redirects. Use when finding broken link prospects, replacing dead resources, recovering lost backlinks, or auditing old URLs after migrations and redesigns.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Broken Link Building
  category: Marketing
  tags: seo,link-building,broken-links,backlinks,technical-seo
---

# Broken Link Building

Use this skill to find pages linking to dead resources, qualify live opportunities, prepare replacement-resource outreach, or recover link equity from the user's own dead historical URLs.

This skill is derived from Garrett French and Eric Ward's *Ultimate Guide to Link Building* and uses transformed guidance with durable book-topic references. Do not copy book prose into user outputs.

## Quick Start

1. Use the Contents table below to choose the smallest useful reference set.
2. Use `workflows/run-broken-link-building.md` for a full campaign.
3. Start with a strong replacement asset.
4. Recheck every dead URL before metrics, backlink review, or outreach.
5. Return verified dead opportunities, qualified backlink prospects, contact queue, outreach notes, and salvage redirect map when applicable.

## Default Output

When asked for broken link building, return:

1. **Campaign summary** - asset, topic, target prospect type, and replacement strength.
2. **Prospecting plan** - resource page sources, queries, and inclusion criteria.
3. **Status findings** - dead URL counts and recheck plan.
4. **Dead URL opportunities** - topic, dead type, metrics, and replacement fit.
5. **Qualified backlink prospects** - referring pages that still link to the dead resource.
6. **Contact and outreach notes** - selected contact path and message angle.
7. **Salvage redirect map** - old URL, destination, and verification when the user owns the site.
8. **Risks and next actions** - false positives, content gaps, and verification gaps.

## Contents

| Need | Start Here |
|------|------------|
| Understand BLB concepts | `references/core/knowledge.md` |
| Apply BLB rules | `references/core/rules.md` |
| See tracking examples | `references/core/examples.md` |
| Run BLB or salvage workflow | `workflows/run-broken-link-building.md` |

## Core Posture

- Broken-link outreach works only when the replacement is genuinely useful.
- Initial dead-link findings are suspects until rechecked.
- Backlink exports are raw data until deduped, filtered, and verified.
- Link equity salvage requires historical URL discovery, not only current crawling.
