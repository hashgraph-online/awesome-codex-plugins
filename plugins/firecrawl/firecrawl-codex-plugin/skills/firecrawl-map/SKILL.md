---
name: firecrawl-map
description: |
  Discover and list all URLs on a website, with optional search filtering. Use this skill when the user wants to find a specific page on a large site, list all URLs, see the site structure, find where something is on a domain, or says "map the site", "find the URL for", "what pages are on", or "list all pages". Essential when the user knows which site but not which exact page.
---

# firecrawl map

Discover URLs on a site. Use `--search` to find a specific page within a large site.

## When to use

- You need to find a specific subpage on a large site
- You want a list of all URLs on a site before scraping or crawling
- Step 3 in the [workflow escalation pattern](../firecrawl-cli/SKILL.md): search → scrape → **map** → crawl → interact

## Quick start

```bash
# Find a specific page on a large site
firecrawl map "<url>" --search "authentication" -o .firecrawl/filtered.txt

# Get all URLs
firecrawl map "<url>" --limit 500 --json -o .firecrawl/urls.json
```

## Options

| Option                            | Description                  |
| --------------------------------- | ---------------------------- |
| `--limit <n>`                     | Max number of URLs to return |
| `--search <query>`                | Filter URLs by search query  |
| `--sitemap <include\|skip\|only>` | Sitemap handling strategy    |
| `--include-subdomains`            | Include subdomain URLs       |
| `--json`                          | Output as JSON               |
| `-o, --output <path>`             | Output file path             |

## Tips

- **Map + scrape is a common pattern**: use `map --search` to find the right URL, then `scrape` it.
- Example: `map https://docs.example.com --search "auth"` → found `/docs/api/authentication` → `scrape` that URL.

## See also

- [firecrawl-scrape](../firecrawl-scrape/SKILL.md) — scrape the URLs you discover
- [firecrawl-crawl](../firecrawl-crawl/SKILL.md) — bulk extract instead of map + scrape
