---
name: creator-vetting
description: Use when the user wants to vet an influencer or creator before a sponsorship or partnership - real reach and engagement, posting cadence, comment authenticity signals, which platforms they're on, what they post about and any red flags.
license: MIT
metadata:
  author: Groundsocial
  homepage: https://groundsocial.dev
  repository: https://github.com/shivanshmehendiratta/groundsocial-skills
  requires_env: GROUNDSOCIAL_API_KEY
---

# Creator Vetting

Check whether a creator's audience and engagement look real and fit the brand, before money changes hands.

## When to use

- "Should we sponsor @creator?"
- "Is this influencer's engagement real?"
- "Vet these 10 creators for our campaign"

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

1. **Find all their accounts (metered, about 4 to 8 credits).**

```bash
gs /v1/prism/creator-card -d handle=mkbhd
```

   One card per platform found (TikTok, Instagram, YouTube, X and more) with followers, posts, verified and bio.
   Check the cards are the same person (bio, links, name), not a namesake.

2. **Engagement quality on their main platform (metered, about 5 to 50 credits).**

```bash
gs /v1/prism/creator-vet -d handle=mkbhd -d platform=tiktok
```

   Returns `engagement` (median, mean, stdev, `rate_per_follower`, `median_views`), `cadence`
   (`posts_per_week`, `days_since_last_post`) and `comments` signals (`short_or_emoji_share`,
   `duplicate_share`, `repeat_commenter_share`). Repeat for each platform that matters to the campaign.

3. **What works for them (4 credits).** `gs /v1/prism/format-lift -d platform=tiktok -d handle=mkbhd`

4. **Brand fit.** Read their latest 20 to 30 posts or video titles (see the table in `competitor-social-audit`) and,
   for YouTube, the transcript of one or two recent sponsored videos (`/v1/youtube/videos/{id}/transcript`, 2 credits).
   `/v1/youtube/videos/{id}/sponsors` (3 credits) lists paid-promotion signals and sponsors named in a video.

5. **Reputation check.** `gs /v1/prism/mentions -d handle=<handle>` for what others say about them.

## Red flags

- `short_or_emoji_share` above about 0.4, or `duplicate_share` above about 0.1: comments look like pods or bots.
- `rate_per_follower` far below peers of similar size (under about 0.5% on TikTok/Instagram for accounts over 100k).
- Big follower count with very low median views.
- `days_since_last_post` over 30, or a sudden drop in cadence.
- Engagement driven by one viral outlier (mean far above median, high stdev).

Treat these as signals to look closer, not proof.

## Output

A one-page card per creator: accounts and followers, median views and engagement rate per platform, cadence,
comment quality signals, content themes, past sponsors seen, red flags, and a verdict: **good fit / check further /
pass**, with the reason. For several creators, end with a comparison table sorted by expected value for the
user's goal.
