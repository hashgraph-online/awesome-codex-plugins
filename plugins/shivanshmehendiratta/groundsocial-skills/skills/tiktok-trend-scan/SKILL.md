---
name: tiktok-trend-scan
description: Use when the user wants to know what's trending on TikTok right now - rising hashtags, top videos, sounds and formats for a country or niche - and turn it into content ideas, or check whether a hashtag or topic is growing.
license: MIT
metadata:
  author: Groundsocial
  homepage: https://groundsocial.dev
  repository: https://github.com/shivanshmehendiratta/groundsocial-skills
  requires_env: GROUNDSOCIAL_API_KEY
---

# TikTok Trend Scan

Pull TikTok's trending boards and niche searches, then turn them into a short list of trends worth acting on, with
example videos and why each works.

## When to use

- "What's trending on TikTok in the US this week?"
- "Is #<hashtag> growing?"
- "Give me TikTok content ideas for <niche> based on what's working now"

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

1. **Country-level boards (1 credit each).**

```bash
gs /v1/tiktok/trending/hashtags -d country=US -d period=7      # period: 7, 30 or 120 days; optional industry
gs /v1/tiktok/trending/videos -d country=US -d period=7 -d order=views   # order: views, engagement, completion
gs /v1/tiktok/trending -d region=US                             # the feed a new visitor sees (~30 videos)
```

   Hashtag items include `hashtagName`, `rankIndex`, `publishCnt`, `vv` (views) and a `popularityCurve`.
   Use the curve's direction to separate rising tags from ones already peaking.

   One call across TikTok, YouTube, Pinterest, X and Bluesky: `gs /v1/prism/trend-board -d country_code=US`
   (metered, about 10 to 30 credits).

2. **Niche view (1 credit per page).**

```bash
gs /v1/tiktok/search/videos --data-urlencode "q=meal prep"      # 16 a page, pass cursor for more
gs /v1/tiktok/hashtags/mealprep                                 # video and view counts for a tag
gs /v1/tiktok/hashtags/mealprep/videos                          # ~30 videos with the tag
```

3. **Score the videos.** For each video, use views, likes, comments, shares and the author's follower count. Flag
   videos with views far above the author's followers (breakout content) and recent `createTime`.

4. **Look inside the winners (1 credit each).** For the top 3 to 5:
   - transcript: `gs /v1/tiktok/videos/{id}/transcript` (only videos with a caption track; others return `target_not_found`, uncharged)
   - comments: `gs /v1/tiktok/videos/{id}/comments` (what viewers react to and ask)
   - sound: `gs /v1/tiktok/songs/{id}` and `/v1/tiktok/songs/{id}/videos` when a sound drives the trend

## Output

- **Trends:** 5 to 10 items, each with the hashtag/sound/format, direction (rising, peaking, fading), scale (views or
  post count) and 2 example video links.
- **Why it works:** hook, format and length patterns from transcripts and top comments.
- **Ideas:** 3 to 5 concrete video ideas that fit the user's niche, each tied to a trend.
- **Skip list:** trends that look big but don't fit or are already fading.

## Notes

- Boards are per country; say which market you used. Rankings change daily.
- Don't recommend reusing other creators' footage or copyrighted sounds for ads.
