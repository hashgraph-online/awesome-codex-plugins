---
name: brand-mention-scan
description: Use when the user wants to know where and how a brand, product, person, handle or link is being talked about across Reddit, Hacker News, X, Bluesky, YouTube, TikTok and other public platforms, with sentiment, top threads and the posts worth replying to.
license: MIT
metadata:
  author: Groundsocial
  homepage: https://groundsocial.dev
  repository: https://github.com/shivanshmehendiratta/groundsocial-skills
  requires_env: GROUNDSOCIAL_API_KEY
---

# Brand Mention Scan

Find recent public mentions of a brand, product, handle or URL across platforms, then turn them into a short brief:
volume by platform, what people praise and complain about, the threads that matter, and which ones deserve a reply.

## When to use

- "What are people saying about <brand> this week?"
- "Find mentions of our product / our launch / our domain"
- "Any complaints about <competitor> on Reddit or HN?"
- Weekly social listening digest for a brand

## Setup

This skill reads public data through the [Groundsocial](https://groundsocial.dev) API.

- **MCP connected?** If tools named like `reddit_search_posts` or `prism_mentions_get` are available, the
  Groundsocial MCP server (`https://api.groundsocial.dev/mcp`) is connected. Call the tool with the same name as the
  endpoint id below (dots become underscores) and the same parameters.
- **Otherwise use REST.** Needs `GROUNDSOCIAL_API_KEY` (100 free credits at
  https://groundsocial.dev/app/sign-in?new=1, or see the `groundsocial-api` skill for agent self-signup). Define:

```bash
gs() { curl -sS -G "https://api.groundsocial.dev$1" -H "Authorization: Bearer $GROUNDSOCIAL_API_KEY" "${@:2}"; }
# usage: gs /v1/reddit/search/posts --data-urlencode "q=my product" -d sort=new
```

Errors come back as `{"error": {"code", "message", "hint", "retryable"}}`. Follow the `hint`; failed calls are not
charged. Tell the user before a run that will cost more than about 200 credits.

## Workflow

1. **Pin down the terms.** Ask for (or infer) the brand name, any handles, the website domain and obvious misspellings.
   Ambiguous names ("Notion", "Linear") need a qualifier such as "notion app" or the domain.

2. **Cross-platform mentions (metered, usually 4 to 20 credits).**

```bash
gs /v1/prism/mentions --data-urlencode "name=Supabase" -d platforms=reddit,hackernews,x,bluesky,youtube,threads
gs /v1/prism/mentions -d handle=supabase          # posts that mention @supabase
gs /v1/prism/mentions --data-urlencode "url=https://supabase.com" -d since=2026-11-01
```

   The response has `count`, `by_platform` and `mentions[]`, each with `platform`, `url`, `title`, `text`,
   `author`, `created_at`, `likes` and `comments`. `failed` lists platforms that didn't answer (not charged).

3. **Go deeper where the talk is.** Discussion threads with comments:

```bash
gs /v1/search/forums --data-urlencode "query=supabase" -d timeframe=month -d comments=5      # Reddit + HN + Stack Overflow, with top comments
gs /v1/reddit/search/comments --data-urlencode "q=supabase" -d sort=new -d t=week -d limit=50  # the comments themselves (2 credits)
gs /v1/hackernews/search --data-urlencode "q=supabase" -d sort=date -d hitsPerPage=30          # HN stories (1 credit)
```

4. **Optional trend line (50+ credits, ask first).** Mention counts over time with a sentiment split:

```bash
gs /v1/prism/brand-mentions -d keyword=supabase -d date_from=2026-10-01 -d date_group=week
```

5. **Read the top threads.** For the 3 to 5 most-discussed Reddit posts, fetch the full comment tree:
   `gs /v1/reddit/posts/<id> -d sort=top -d limit=100` (1 credit each).

## Output

- **Volume:** mentions by platform for the window, and whether that looks up or down.
- **Themes:** 3 to 6 recurring themes (praise, complaints, questions, comparisons), each with 1 or 2 short verbatim
  quotes and links.
- **Threads that matter:** a table of the top 5 to 10 by engagement: platform, title or first line, likes, comments,
  date, link.
- **Reply candidates:** open questions or complaints where an answer from the brand would help, with the link.
- **Competitors named:** brands mentioned alongside it.

## Notes

- Mentions come from each platform's public search, so they are a sample, not a census. Say so in the brief.
- Quote people exactly; don't paraphrase complaints into something milder.
- Don't include usernames in a report the user will publish unless they're public figures or brands.
