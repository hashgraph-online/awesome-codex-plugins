---
name: comment-mining
description: Use when the user wants to mine the comments on a Reddit thread, YouTube video, TikTok, Instagram post or Hacker News story for audience questions, objections, complaints, feature requests, buying intent and exact customer language.
license: MIT
metadata:
  author: Groundsocial
  homepage: https://groundsocial.dev
  repository: https://github.com/shivanshmehendiratta/groundsocial-skills
  requires_env: GROUNDSOCIAL_API_KEY
---

# Comment Mining

Read every comment on one or more posts and sort them into what the audience asks, wants, dislikes and how they
say it.

## When to use

- "What are people asking in the comments of this video?"
- "Pull objections and complaints from this Reddit thread"
- "Voice-of-customer language for our landing page"

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

1. **Fetch the comments.** Use the post URL with `/v1/utility/resolve` (free) if you're not sure of the id:
   `gs /v1/utility/resolve --data-urlencode "input=<url>"`.

| Source | Call | Credits |
|---|---|---|
| Reddit thread (full tree) | `/v1/reddit/posts/{id}?sort=top&limit=500` (id, or the URL-encoded post URL) | 1 |
| YouTube | `/v1/youtube/videos/{id}/comments?order=top` (paginate with `after`) | 1 per page |
| TikTok | `/v1/tiktok/videos/{id}/comments` (paginate with `cursor`) | 1 per page |
| Instagram | `/v1/instagram/posts/{shortcode}/comments` | 2 per page |
| Hacker News | `/v1/hackernews/items/{id}/comments` | 1 |
| Any supported link, every page | `/v1/prism/comments?url=<link>&max=500` | metered |

2. **Clean lightly.** Drop spam and exact duplicates. Keep slang and typos when they carry meaning.

3. **Classify** each useful comment: question, objection, complaint/pain, feature request, praise, comparison
   (names another product), buying intent ("where can I get", "does it work with").

4. **Count and rank** each bucket by frequency and by likes or score.

## Output

- **Top questions, objections, pains, requests:** each with a count and 2 or 3 exact quotes (with likes).
- **Customer language:** phrases people use for the problem and the outcome they want, ready for copy.
- **Buying intent:** comments that look like leads, with links.
- **Content ideas:** questions worth answering in a post or video.

Quote exactly and link to the source post. Don't publish commenters' usernames without a reason.
