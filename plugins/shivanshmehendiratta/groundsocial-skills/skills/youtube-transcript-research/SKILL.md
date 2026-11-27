---
name: youtube-transcript-research
description: Use when the user wants to research a topic, creator or product through YouTube videos - find the relevant videos, pull their transcripts, and extract claims, steps, opinions, quotes with timestamps, or compare what different creators say.
license: MIT
metadata:
  author: Groundsocial
  homepage: https://groundsocial.dev
  repository: https://github.com/shivanshmehendiratta/groundsocial-skills
  requires_env: GROUNDSOCIAL_API_KEY
---

# YouTube Transcript Research

Search YouTube, pick the videos that matter, read their transcripts and comments, and write a sourced summary with
timestamped quotes.

## When to use

- "What do YouTubers say about <product>?"
- "Summarize the last 10 videos from <channel>"
- "Pull every claim about <topic> from these videos, with timestamps"
- Turning tutorials into step lists, or reviews into a pros/cons table

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

1. **Find videos (1 credit per page).**

```bash
gs /v1/youtube/search --data-urlencode "q=supabase review" -d type=video -d sort=relevance -d upload_date=year
gs /v1/youtube/channels/@mkbhd/videos -d sort=latest            # a channel's uploads; sort=popular for its best
```

   Pick 5 to 10 videos by relevance, views and recency. For exact view, like and comment counts, chapters and paid
   promotion flags: `gs /v1/youtube/videos/{id}` (1 credit).

2. **Transcripts.**

```bash
gs /v1/youtube/videos/dQw4w9WgXcQ/transcript -d language=en     # 2 credits; timestamped segments plus full text
curl -sS -X POST https://api.groundsocial.dev/v1/youtube/transcripts/batch \
  -H "Authorization: Bearer $GROUNDSOCIAL_API_KEY" -H 'content-type: application/json' \
  -d '{"ids": ["id1", "id2", "id3"], "language": "en"}'       # up to 10 videos, 15 credits
```

   Shorts work the same way. A video without captions returns an error with a hint, and is not charged.

3. **Extract.** Work from the transcript segments so every point keeps its timestamp. Link quotes as
   `https://www.youtube.com/watch?v=<id>&t=<seconds>s`.

4. **Audience reaction (optional, 1 credit per page).** `gs /v1/youtube/videos/{id}/comments -d order=top`.

## Output

- **Sources:** table of videos used (title, channel, date, views, link).
- **Findings:** grouped by theme or question, each point with the creator, a short exact quote and a timestamp link.
- **Agreement and disagreement:** where creators agree, where they contradict each other.
- **Gaps:** questions the videos don't answer (often visible in the comments).

## Notes

- Auto-generated captions misspell names and jargon; fix obvious ones and keep quotes otherwise exact.
- Note sponsored segments (`/v1/youtube/videos/{id}/sponsors`, 3 credits) when weighing a creator's opinion.
