---
name: subreddit-research
description: Use when the user wants to find the right subreddits for a topic or product, understand a community's rules, size and culture, see what kinds of posts do well there, and spot recurring questions or pain points before posting or doing market research.
license: MIT
metadata:
  author: Groundsocial
  homepage: https://groundsocial.dev
  repository: https://github.com/shivanshmehendiratta/groundsocial-skills
  requires_env: GROUNDSOCIAL_API_KEY
---

# Subreddit Research

Find the communities where a topic is discussed, check their rules, learn what gets upvoted and what people keep
asking, so the user can participate without getting removed.

## When to use

- "Which subreddits should I post my tool in?"
- "What does r/<name> care about? What are the rules?"
- "What are people's pain points about <topic> on Reddit?"

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

1. **Find candidate subreddits (1 credit per call).**

```bash
gs /v1/reddit/search/subreddits --data-urlencode "q=self hosting"
gs /v1/reddit/search/posts --data-urlencode "q=self hosted analytics" -d sort=top -d t=year -d limit=50   # 2 credits; count which subreddits the hits come from
```

   Combine both: subreddits from the name search plus the ones that host the most top posts for the topic.

2. **Profile each candidate (1 credit each).**

```bash
gs /v1/reddit/subreddits/selfhosted              # description, subscribers, flags
gs /v1/reddit/subreddits/selfhosted/rules        # posting rules (self-promotion limits, flair, weekly threads)
gs /v1/reddit/subreddits/selfhosted/posts -d sort=top -d t=month -d limit=50
gs /v1/reddit/subreddits/selfhosted/posts -d sort=new -d limit=50
```

   For many subreddits at once: `POST /v1/reddit/subreddits/batch` with `{"names": [...]}` (5 credits for up to 25).

3. **What does well.** From top-of-month posts, note post types (question, showcase, guide, meme, link), title
   patterns, flair, and median score and comments. From new posts, see how many get no traction.

4. **Recurring questions and pain points.**

```bash
gs /v1/reddit/search/posts --data-urlencode "q=recommend OR alternative OR struggling" -d subreddit=selfhosted -d sort=top -d t=year
gs /v1/prism/audience-questions -d topic="self hosting" -d max_questions=20    # metered, ~20-30 credits, Reddit+YouTube+HN+SO
```

5. **Read 2 or 3 representative threads** in full: `gs /v1/reddit/posts/<id> -d sort=top`.

## Output

- **Ranked subreddits:** name, subscribers, activity (posts per day from `new`), fit for the user's goal, and the
  self-promotion rule in one line.
- **Per subreddit:** what gets upvoted (post types and title patterns with examples), what gets removed, best flair.
- **Pain points and questions:** grouped, with links and short quotes.
- **How to post:** a draft title and angle per top subreddit that follows its rules. Never suggest vote manipulation
  or posting the same thing across many subreddits at once.
