# Linkable Content Architecture Examples

Use these examples to turn architecture findings into fixes.

## Audit Finding Pattern

```
Finding: Data report is orphaned.
Evidence: Crawl found zero incoming internal links; only XML sitemap includes URL.
Risk: External links point to a page users cannot discover from related content.
Fix: Add links from /resources/, two topical guides, and the relevant product education page.
Verification: Re-crawl and confirm incoming internal links.
```

## Readiness Rubric

| Area | Ready | Not Ready |
|------|-------|-----------|
| Status | 200 OK, clean URL | 404, soft 404, redirect chain |
| Search index status | Canonical self or intended URL can appear in search | Blocked, hidden from search, canonical elsewhere |
| Internal links | Relevant hubs and articles link in | Orphan or buried |
| Next steps | Useful related links | Forced sales path only |
| Stability | Durable campaign URL | Temporary or parameter-only URL |

## Internal Link Plan

| Source Page | Link Target | Anchor Intent |
|-------------|-------------|---------------|
| Topic hub | Linkable report | "industry benchmark report" |
| How-to guide | Tool or template | "download the checklist" |
| Product education page | Research asset | "see the methodology" |
| Asset page | Commercial explainer | "compare implementation options" |

## Promotion Pause Cases

- The asset is still staged or hidden from search.
- A redesign or migration will move URLs during outreach.
- The asset has no internal path from the topic hub.
- The citable content is hidden behind a lead form.
