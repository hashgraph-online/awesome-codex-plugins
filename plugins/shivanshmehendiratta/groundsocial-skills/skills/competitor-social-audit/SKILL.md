---
name: competitor-social-audit
description: Use when the user wants to audit a competitor's (or their own) social presence - which accounts they run on X, YouTube, TikTok, Instagram, LinkedIn and GitHub, follower counts, posting cadence, what content performs, and what their audience says about them.
license: MIT
metadata:
  author: Groundsocial
  homepage: https://groundsocial.dev
  repository: https://github.com/shivanshmehendiratta/groundsocial-skills
  requires_env: GROUNDSOCIAL_API_KEY
---

# Competitor Social Audit

Map a company's official accounts, measure each one, find the posts that over-perform and summarise what the
audience says. Works for one competitor or a side-by-side of 2 to 5.

## When to use

- "Audit <competitor>'s social media"
- "Compare our socials with <A> and <B>"
- "What content works for <brand> on TikTok / YouTube?"

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

1. **Find the official accounts (metered, about 6 to 30 credits).**

```bash
gs /v1/prism/find-accounts -d name=Supabase -d type=company -d website=supabase.com
```

   Each platform returns ranked `candidates` with `handle`, `verified`, `links_to_website` and a `score`. Keep
   candidates that are verified or link to the website; ask the user if two look equally likely.
   For a handle you already know, `gs /v1/prism/creator-card -d handle=supabase` returns one card per platform
   (followers, posts, verified, bio).

2. **Profile and recent posts per platform (1 to 5 credits each).**

| Platform | Profile | Recent posts |
|---|---|---|
| X | `/v1/x/users/{username}` | `/v1/x/users/{username}/tweets` |
| YouTube | `/v1/youtube/channels/{channel}` | `/v1/youtube/channels/{channel}/videos?sort=latest` (or `sort=popular`) |
| TikTok | `/v1/tiktok/users/{handle}` | `/v1/tiktok/users/{handle}/videos?sort=latest` |
| Instagram | `/v1/instagram/users/{username}` | `/v1/instagram/users/{username}/posts`; engagement: `/v1/instagram/users/{username}/engagement` |
| LinkedIn | `/v1/linkedin/companies/{company}` (5) | `/v1/linkedin/companies/{company}/posts` (5) |
| GitHub | `/v1/github/users/{handle}` | `/v1/github/users/{handle}/repos` |

   YouTube `{channel}` accepts an @handle or channel id.

3. **What format works (4 credits per account).**

```bash
gs /v1/prism/format-lift -d platform=tiktok -d handle=supabase
```

   Compares formats against the account's own median, so you can say "carousels do 2.3x their median".

4. **Outliers.** From the recent posts, compute the median views or likes per account and flag posts above 3x
   the median. Those are the ones to study.

5. **Audience view.** Run the `brand-mention-scan` skill's step 2 for the brand name, or pull comments on the top 2
   outlier posts (see `comment-mining`).

## Output

- **Accounts table:** platform, handle, followers, posts, verified, posts per week, median engagement.
- **What works:** best formats and topics per platform, with 3 to 5 outlier posts linked and the multiple of median.
- **Cadence and gaps:** where they post often, where they're absent or stale (last post date).
- **Audience:** top praise and complaints, with quotes.
- **Takeaways:** 3 to 5 concrete moves for the user (formats to try, platforms they can win, topics to answer).

## Notes

- Follower counts are rounded by some platforms (TikTok shows "2.3M"). Say "about" where that applies.
- Compare engagement as a rate per follower when accounts differ a lot in size.
