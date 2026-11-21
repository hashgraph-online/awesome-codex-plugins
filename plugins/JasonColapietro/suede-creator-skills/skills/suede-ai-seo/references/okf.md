# Open Knowledge Format (OKF)

A v0.1 Markdown specification from Google Cloud for packaging knowledge as a
directory of cross-linked files with YAML frontmatter, readable by agents
without scraping. Announced on the Google Cloud blog in June 2026 and shipped
inside Knowledge Catalog.

Sources:
- https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing
- https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/HEAD/okf/SPEC.md

## What it is

Each file has YAML frontmatter (`type` required; `title`, `description`,
`resource`, `tags`, `timestamp` recommended), a Markdown body, and Markdown
links to other files, which the spec treats as relationships. An optional
`index.md` lists the files. Bundles ship as a git repo, an archive, or a
subdirectory.

```markdown
---
type: Article
title: How to connect Acme to Slack
description: Setup steps, permissions, and troubleshooting.
resource: https://example.com/docs/slack/
tags: [integrations, slack]
---

# How to connect Acme to Slack

Body as clean Markdown, linking to [permissions](permissions.md).
```

## Accurate framing for clients

- Google built OKF for data teams sharing catalog metadata (tables, APIs,
  metrics, playbooks). Using it to expose a marketing site's content is a
  repurposing, legitimate but not the spec's primary use.
- No answer engine, including Google Search, has announced reading OKF bundles.
  It has no known effect on AI Overviews, ChatGPT, Perplexity, or Claude today.
- Treat it as an optional, low-cost bet, the same category as `llms.txt`.

## When to ship one

Ship when all are true: the site has 10 or more substantive pages; the host can
serve files at a custom path (`/okf/`); `llms.txt` and schema are already in
place; someone owns regenerating it when content changes.

Side benefit available now: generating the bundle maps every internal link, so
orphan pages and disconnected clusters become visible. That feeds the
internal-linking work in `suede-seo-audit` Lane 9.

## How to ship

1. Generate one Markdown file per substantive page with the frontmatter above.
   Third-party generators and CMS plugins exist; review the output and the
   tool's data handling before use.
2. Add `index.md` listing every file.
3. Serve at `/okf/index.md`; add a line to `llms.txt` pointing to it.
4. Regenerate on publish, or at least quarterly.

## What to watch

- Any engine announcing OKF ingestion.
- The spec moving toward v1.0 (breaking changes are possible before then).
- Public ingestion endpoints in Knowledge Catalog.
