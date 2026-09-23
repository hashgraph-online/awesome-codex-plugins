# Search

**Trigger**: User wants to search for a keyword, project, event, or topic.
Common phrases: "Search for Bitcoin ETF articles", "Any reports on XX", "Find news about XX".

Difference from other scenarios:
- Search → user actively inputs keywords, finds matching content
- Deep dive ([workflow-topic-research](./workflow-topic-research.md)) → user wants a comprehensive understanding of a topic from multiple sources
- Today's briefing → focused on current day's latest content

## Steps

### 1. (Optional) Get hot search keywords for inspiration

When the user has no clear keyword or wants to discover trending topics:

```bash
node cli.mjs get-hooks --category search-keywords --lang <lang>
```

Present the hot keywords for the user to choose from.

### 2. Execute the search

```bash
node cli.mjs search-articles "<keyword>" --mode hit --take 10 --lang <lang>
```

Keywords are matched across titles, summaries, and article bodies.

**Sort modes**:
- `hit` (default) — relevance with freshness weighting
- `time` — publication time, newest first

Use `--take` for up to 50 results (default: 5). Each invocation reads one page and releases its search snapshot; it does not return a reusable cursor or exhaust all matches.

### Filter by publication time

For a request such as "Bitcoin coverage published on September 21 in Shanghai":

```bash
node cli.mjs search-articles "比特币" --mode time --take 10 --lang zh \
  --published-from "2026-09-21T00:00:00+08:00" \
  --published-to "2026-09-22T00:00:00+08:00"
```

Both bounds are optional ISO 8601 timestamps with `Z` or a timezone offset. `--published-from` is inclusive; `--published-to` is exclusive and must be later than the start. Use the user's intended timezone and the following midnight for an inclusive calendar end date. A date inside the keyword searches for dates mentioned in the content; it does not filter publication time.

### 3. Deep dive into an article

Get the article ID from the search results and go to [workflow-read-article](./workflow-read-article.md).

## Output requirements

- Include title, summary, and publish time with each result. When the match comes from the article body, the CLI also returns a plain-text `snippet` as supporting context; it is not the full article.
- If a translated title or summary is missing, that field falls back to the original article language.
- If results are sparse or irrelevant, try different keywords or broaden the date range. Changing `--mode` changes ordering, not matching rules.
- Do not add information beyond the search results
