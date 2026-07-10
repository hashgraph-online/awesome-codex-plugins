---
name: directory-link-evaluation
description: Evaluate directories, listings, profiles, citations, associations, and resource indexes for legitimate link-building value, editorial quality, spam risk, local relevance, and submission fit. Use when deciding whether to submit to a directory, audit directory backlinks, compare listing opportunities, or reject low-quality indexes.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Directory Link Evaluation
  category: Marketing
  tags: seo,link-building,directories,local-seo,qualification
---

# Directory Link Evaluation

Use this skill to decide whether a directory, listing, association profile, citation site, or resource index is worth pursuing or keeping.

This skill is derived from Garrett French and Eric Ward's *Ultimate Guide to Link Building* and uses transformed guidance with durable book-topic references. Do not copy book prose into user outputs.

## Quick Start

1. Use the Contents table below to choose the smallest useful reference set.
2. Use `workflows/evaluate-directory-links.md` for a full evaluation pass.
3. Confirm the directory serves a real audience or market function.
4. Apply hard rejects before considering authority metrics.
5. Return submit, update, monitor, or reject recommendations with evidence.

## Default Output

When asked to evaluate directories, return:

1. **Directory type** - local citation, niche directory, association, marketplace, resource index, or paid listing.
2. **Audience and relevance** - who uses it, category fit, geography, and business fit.
3. **Quality evidence** - editorial standards, indexing, visible traffic signals, outbound link quality, and maintenance.
4. **Risk flags** - thin pages, paid-link footprints, links across the whole site, irrelevant categories, or low-quality neighbors.
5. **Tool choices** - browser inspection, search operators, crawlers, backlink tools, index checks, and tracking sheet.
6. **Recommendation** - submit, update, monitor, reject, or remove/disavow review if toxic.

## Contents

| Need | Start Here |
|------|------------|
| Understand directory link concepts | `references/core/knowledge.md` |
| Apply evaluation rules | `references/core/rules.md` |
| See scoring examples | `references/core/examples.md` |
| Evaluate directories | `workflows/evaluate-directory-links.md` |

## Core Posture

- A good directory helps users find relevant options.
- Relevance and editorial standards matter more than raw authority.
- Paid inclusion requires extra scrutiny and link qualification.
- Local citations are evaluated differently from national SEO directories.
- Reject directories whose main purpose is selling ranking-passing links.
