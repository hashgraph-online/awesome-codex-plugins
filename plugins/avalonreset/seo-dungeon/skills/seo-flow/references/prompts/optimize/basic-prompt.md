<!-- Source: github.com/AgriciDaniel/flow | License: CC BY 4.0 | Synced: 2026-04-26 -->
---
title: "Basic Prompt"
description: "Basic Prompt"
updated: 2026-04-25
tags:
  - prompts
  - optimize
---

# Basic Prompt

## Use This When

Use this prompt when you need a structured optimize deliverable and want the model to separate observations, assumptions, recommended actions, and claims that need verification.

## AI Compatibility

Works with long-context reasoning models. For smaller models, provide narrower inputs and ask for one output section at a time.

## Inputs

- Business or website name.
- Target page, profile, query set, or campaign.
- Audience and geography where relevant.
- Existing evidence: analytics, search results, calls, reviews, profile facts, or source notes.
- Constraints, exclusions, and required sources.

## Prompt

```text
Act as a senior SEO strategist using the FLOW model.

Task: create a optimize deliverable for: [BUSINESS OR ASSET].

Use only the supplied inputs and clearly label any assumption. Do not invent statistics. Do not reuse private examples. Build the answer around:
1. Searcher or buyer intent.
2. Evidence available now.
3. Gaps that block trust, extraction, or conversion.
4. Recommended changes in priority order.
5. Measurement events and review cadence.
6. Claims that require source verification before publication.

Return a concise working document the team can execute.
```

## Output

- Executive summary.
- Priority table.
- Recommended copy, structure, or audit findings.
- Evidence needed.
- Measurement plan.
- Verification checklist.

## Example

Input: a local service page with weak proof and inconsistent profile details.

Expected output: a prioritized rewrite brief, facts to reconcile, internal links to add, and the conversion event to measure.

## See Also

- [Prompt Library](../README.md)
- [FLOW Framework](../../flow-framework.md)
- [Bibliography](../../bibliography.md)

## Source Note

Derived from the Local SEO Knowledge Base structure and rewritten for public use with the repository evidence standard.
