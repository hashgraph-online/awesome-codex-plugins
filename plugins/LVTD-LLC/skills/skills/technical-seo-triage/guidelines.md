# Technical SEO Triage Guidelines

Load the minimum files needed for the task.

## By Task

| What you're doing | Load these files |
|-------------------|------------------|
| Diagnosing a traffic drop | `references/core/knowledge.md`, `references/core/rules.md`, `workflows/triage-seo-issue.md` |
| Investigating indexing/canonical issues | `references/core/rules.md`, `references/core/examples.md` |
| Planning a migration or URL change | `references/core/rules.md`, `workflows/triage-seo-issue.md` |
| Reviewing internal linking or crawl budget | `references/core/knowledge.md`, `references/core/examples.md` |
| Explaining technical SEO to non-technical stakeholders | `references/core/knowledge.md` |

## By Problem

| If you notice... | Load these files |
|------------------|------------------|
| Pages discovered but not indexed | `references/core/knowledge.md`, `references/core/rules.md` |
| Traffic drop after an update | `workflows/triage-seo-issue.md` |
| Canonical selected by Google differs from declared canonical | `references/core/rules.md` |
| Large site has orphaned or weakly linked pages | `references/core/knowledge.md`, `references/core/examples.md` |
| Migration would change many URLs | `references/core/rules.md` |

## Decision Tree

```text
What is the symptom?
|
+-- Not found by Google -> discovery/internal links/sitemaps
+-- Crawled less than expected -> crawl budget, low-value URLs, internal links
+-- Crawled but not indexed -> duplicate, thin, canonical, quality, robots
+-- Indexed but no clicks -> relevance, snippets, CTR, intent mismatch
+-- Drop after migration -> redirects, URL map, canonicals, internal links
+-- Drop after algorithm update -> segment URL/query winners and losers in GSC
```

## File Index

| File | Purpose |
|------|---------|
| `references/core/knowledge.md` | Search stages, GSC, internal links, crawl budget, duplicate, migrations |
| `references/core/rules.md` | Triage rules and cautions |
| `references/core/examples.md` | Diagnosis examples and check tables |
| `workflows/triage-seo-issue.md` | Step-by-step technical triage workflow |
