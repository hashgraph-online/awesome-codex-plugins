# GrayMatter Semantic Layer Template

Use this template to create a user/workspace-specific semantic layer for analytics work that relies on GrayMatter.

## Required Inputs

- Target area, metric, dashboard, product surface, report, or recurring business question.
- Live `/v1/api-docs` read or schema summary for the current account.
- At least one user-approved source such as GrayMatter memory, a data doc, reviewed SQL, a dashboard, a repository path, an export, or a source inventory.

## Source Inventory

Before writing the layer, record:

| Source | Type | Locator | Tool Or Connector | Last Checked | Supports | Gaps Or Caveats |
| --- | --- | --- | --- | --- | --- | --- |

Include live `/v1/api-docs` as the schema source. Include GrayMatter retrieval receipts or memory reads as context sources when used. Mark any user-provided export or local file as manual evidence.

## SKILL.md Shape

```markdown
---
name: <area>-semantic-layer
description: Use when answering analytics questions for <area>, including metric definitions, source selection, live schema checks, joins, filters, and caveats.
---

# <Area> Semantic Layer

Use this skill to answer <area> analytics questions with the source-backed context in `references/semantic-layer.md`.

## Start Here

1. Read `references/semantic-layer.md`.
2. Refresh or inspect `/v1/api-docs` before relying on business objects, fields, or relationships.
3. Use GrayMatter retrieval receipts or memory reads for durable context.
4. Verify time-sensitive or high-stakes claims against live sources.

## Answering Rules

- Treat this layer as source-selection guidance, not as a substitute for live reads.
- Use only object families present in the current `/v1/api-docs`.
- Label stale, inferred, partial, or conflicted evidence.
```

## semantic-layer.md Shape

```markdown
# <Area> Semantic Layer

## Quick Reference

- Area:
- Intended users:
- Coverage level:
- Source inventory:
- Last synthesized:
- Schema source of truth: `/v1/api-docs`
- Freshness expectations:

## Live Schema Anchors

| Object Family | api-docs Path Or Component | Use It For | Required Fields Or Relationships | Caveats |
| --- | --- | --- | --- | --- |

## Key Metrics

| Metric | Definition | Numerator | Denominator | Time Grain | Canonical Source | Caveats |
| --- | --- | --- | --- | --- | --- | --- |

## Standard Filters And Dimensions

| Filter Or Dimension | Default Logic | Override When | Applies To | Sources |
| --- | --- | --- | --- | --- |

## Query Or Retrieval Patterns

- Pattern:
  - Use when:
  - Schema anchors:
  - Memory/retrieval sources:
  - Required filters:
  - Verification step:

## Gotchas

- Gotcha:
  - Impact:
  - How to avoid:
  - Source:

## Open Questions

- Question:
  - Why it matters:
  - Best source to check next:
```

## Coverage Labels

- `Limited`: one useful source exists, but live schema or important evidence lanes are missing.
- `Directional`: live schema plus one or more context sources support the main workflow, with gaps.
- `Strong`: live schema plus authoritative docs, reviewed SQL, dashboard, or source data support key facts.
- `Conflicted`: important definitions disagree and need owner or user resolution.
- `Blocked`: required schema, permission, source, or destination is unavailable.

## Safety

Do not copy private MemoryEntry bodies, credentials, tokens, raw personal data, row-level customer examples, or tenant-specific secrets into shared skill files. Summarize semantic facts and keep provenance pointers instead.
