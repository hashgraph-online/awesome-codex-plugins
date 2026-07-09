---
name: technical-seo-triage
description: Diagnose technical SEO issues using discovery, crawling, indexing, ranking, Google Search Console, internal links, crawl budget, canonicals, duplicate content, redirects, and migration risk. Use when traffic drops, pages are not indexed, Search Console shows errors, canonicals differ, migrations are planned, or a technical SEO audit is needed.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Technical SEO Triage
  category: Marketing
  tags: seo,technical-seo,search-console,indexing,crawling
---

# Technical SEO Triage

Use this skill to diagnose technical SEO problems by moving from symptoms to search-system stages: discovery, crawling, indexing, ranking, and user outcomes.

This skill is derived from Eli Schwartz's *Product-Led SEO* and uses transformed guidance with durable book-topic references. Do not copy book prose into user outputs.

## Quick Start

1. Load `guidelines.md` to choose relevant references.
2. Use `workflows/triage-seo-issue.md` for traffic drops, indexing issues, canonical issues, migration risk, or crawl problems.
3. Prefer Google Search Console as the primary search visibility source.
4. Segment by URL, query, device, country, brand/non-brand, and date before proposing fixes.
5. Separate technical blockers from content, UX, and business-fit issues.

## Default Output

When asked to triage an issue, return:

1. **Symptom summary** - what changed and where.
2. **Likely search stage** - discovery, crawl, index, rank, click, or conversion.
3. **Evidence to inspect** - GSC reports, logs, crawl data, redirects, canonicals, robots, schema, templates.
4. **Priority fixes** - ordered by risk and likely impact.
5. **Validation plan** - how to verify recovery or improvement.
6. **Cautions** - migration, redirect, duplicate, or crawl-budget risks.

## Contents

| Need | Start Here |
|------|------------|
| Understand technical SEO systems | `references/core/knowledge.md` |
| Apply triage rules | `references/core/rules.md` |
| See diagnosis examples | `references/core/examples.md` |
| Triage a problem | `workflows/triage-seo-issue.md` |
| Route by task | `guidelines.md` |
