---
name: panews
description: >
  Entry point for reading PANews cryptocurrency / blockchain news, market narratives,
  and Polymarket smart money leaderboards.
  Triggers: today's headlines, breaking news, trending rankings, article search,
  reading specific articles, browsing columns / series / community topics,
  industry events & conferences, event calendar, platform hot searches and editorial picks,
  latest smart money boards, board highlights, and board comparisons.
metadata:
  author: Seven Du
  version: "2026.09.23"
---

This is the core PANews reading skill for users who want to follow cryptocurrency and blockchain news through PANews coverage and public Polymarket smart money leaderboard snapshots. Use it for market-moving headlines, project and token updates, rankings, deep dives, topics, columns, series, events, editorial picks, and structured leaderboard discovery.

It is best suited for structured news discovery, explanation, and leaderboard reading. The skill should help users understand what is happening, why it matters, where to keep reading, and how the latest public board snapshots changed, while staying accessible to readers who may not be technical.

## Common User Phrases

- "What are the biggest crypto stories today?"
- "Can you find coverage about Bitcoin, Solana, or this project?"
- "Show me the latest Polymarket smart money boards."
- "Who is on top of the newest small sharp board?"
- "What changed in the latest smart money board cycle?"

## Capabilities

| Scenario | Trigger intent | Reference |
|----------|---------------|-----------|
| Today's briefing | What's the big news today? What's happening in crypto? | [workflow-today-briefing](./references/workflow-today-briefing.md) |
| Search | Search for XX / find reports about XX within a publication date range | [workflow-search](./references/workflow-search.md) |
| Deep dive | What's going on with Bitcoin / a project / an event lately? | [workflow-topic-research](./references/workflow-topic-research.md) |
| Read an article | User provides an article URL or ID | [workflow-read-article](./references/workflow-read-article.md) |
| Discover trending | What is everyone talking about right now? | [workflow-trending](./references/workflow-trending.md) |
| Latest news | Breaking news / what just happened | [workflow-latest-news](./references/workflow-latest-news.md) |
| Browse columns | What columns are there / this author's column | [workflow-columns](./references/workflow-columns.md) |
| Browse series | Any series coverage on XX | [workflow-series](./references/workflow-series.md) |
| Browse topics | What do people think about XX / what's the community discussing | [workflow-topics](./references/workflow-topics.md) |
| Events | Any recent summits / hackathons / activities | [workflow-events](./references/workflow-events.md) |
| Event calendar | Important events this month / project schedule | [workflow-calendar](./references/workflow-calendar.md) |
| Platform picks | What is the editor recommending / what are the hot searches | [workflow-hooks](./references/workflow-hooks.md) |
| Latest Polymarket boards | Latest smart money board / newest leaderboard snapshot | [workflow-polymarket-latest-boards](./references/workflow-polymarket-latest-boards.md) |
| Read a Polymarket board | Who is on top of small sharp / active alpha / high win rate / steady profit | [workflow-polymarket-read-board](./references/workflow-polymarket-read-board.md) |
| Polymarket highlights | What changed in the newest board cycle | [workflow-polymarket-highlights](./references/workflow-polymarket-highlights.md) |
| Compare Polymarket boards | Compare small sharp vs steady profit / compare board categories | [workflow-polymarket-compare-boards](./references/workflow-polymarket-compare-boards.md) |

## General principles

- Do not predict price movements or give investment advice
- Content strictly from PANews - do not add information PANews has not reported
- Polymarket smart money board requests are read-only public leaderboard reads, not PANews editorial article coverage
- For publishing content, use the panews-creator skill

## Execution guidance

- Use judgment for open-ended discovery tasks such as briefings, topic research, and trend summaries. Multiple valid paths are acceptable if the result stays grounded in PANews coverage.
- Be more specific for fragile tasks:
  - Article URL or ID provided: resolve the article directly instead of broadening into generic search.
  - Rankings, events, calendar items, and platform picks: use the most direct matching workflow instead of combining unrelated workflows first.
  - Weak or missing PANews coverage: say so directly rather than filling gaps with outside knowledge.
  - Polymarket smart money board tasks: use the dedicated leaderboard workflows instead of article search.
  - Board requests: stay grounded in returned leaderboard fields and highlights; do not infer unsupported market or trader behavior.

## Language

PANews article, ranking, topic, series, column, event, and calendar commands support `--lang`, accepting standard locale strings (e.g. `zh`, `en`, `zh-TW`, `en-US`, `ja-JP`), automatically mapped to the nearest supported language. If omitted, the system locale is auto-detected. Match `--lang` to the user's question language.

Polymarket smart money leaderboard endpoints currently expose fixed public fields and should not be assumed to localize with `--lang`. If the returned board data is in Chinese, translate or summarize it for the user rather than claiming the API itself localized it.

## Scripts

- `scripts/cli.mjs`: unified entrypoint for PANews reader commands

```bash
node {Skills Directory}/panews/scripts/cli.mjs <command> [options]
```

When unsure about parameters, check with `--help` first:

```bash
node {Skills Directory}/panews/scripts/cli.mjs --help
node {Skills Directory}/panews/scripts/cli.mjs <command> --help
```

Available commands:

```text
         list-articles    List latest articles by type
  get-daily-must-reads    Get daily must-read articles
          get-rankings    Get article hot rankings (daily: 24h hot | weekly: 7-day search trending)
       search-articles    Search articles by keyword and publication date
           get-article    Get full article content by ID
          list-columns    List or search PANews columns
            get-column    Get column details and recent articles
           list-series    List or search PANews series
            get-series    Get series details and articles
           list-topics    List or search PANews topics
             get-topic    Get topic details and latest comments
           list-events    List PANews events / activities
  list-calendar-events    List PANews calendar events
             get-hooks    Fetch PANews hooks / injection-point data by category
 list-polymarket-boards    Show the newest completed smart money board run and categories
  get-polymarket-board    Read the latest entries for a specific smart money board
 get-polymarket-highlights    Summarize highlights from the newest completed smart money board run
 compare-polymarket-boards    Compare multiple smart money board categories from the newest run
```
