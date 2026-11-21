---
name: creator-vetting
description: Vet an influencer or creator on TikTok, Instagram or YouTube before a deal. Pulls their profile and last ~30 posts, computes median views, engagement and posting rhythm against their own baseline, checks for bought followers, one-hit averages and heavy sponsorship, reads audience comments and scans for brand-safety risks, then gives a go or no-go scorecard. Use for influencer vetting, due diligence, comparing creators for a campaign, or "is this creator worth it".
---

# Creator vetting

A go or no-go on a creator, from public numbers: how many people really see their posts, how those people react, how steady they are, how much they already sell, and anything a brand should worry about.

<!-- lurkapi:access -->
## Calling LurkAPI

**With MCP** (the LurkAPI plugin or connector), call the tools by name, like `tiktok_profile`; your client may prefix them (`mcp__plugin_lurkapi_lurkapi__tiktok_profile`). With only `find_endpoints` and `call_endpoint`, run a tool as `call_endpoint` with `endpoint` set to its name and `params` to its arguments. Results come trimmed: no nulls, one URL per image or video. A long result comes in parts: its `_note` gives the `offset` for the next part, which is free.

**Without MCP** (Codex, Cursor, scripts), every tool is `GET https://api.lurkapi.com` plus its path, with the same params as a query string (URL-encoded) and the key from `LURKAPI_API_KEY` in the `x-api-key` header:

```bash
curl -s "https://api.lurkapi.com/v1/tiktok/profile?handle=nike" -H "x-api-key: $LURKAPI_API_KEY"
```

If `LURKAPI_API_KEY` isn't set but `LURKAPI_KEY` is (the name older docs used), use that. Raw answers are big: pipe them through `jq` to keep the fields you need. No key yet? Ask the user to create one at https://lurkapi.com/dashboard (100 free credits on sign-up, then a balance below 25 tops back up to 25 every day) and to set `LURKAPI_API_KEY` in their shell. Never ask for the key in the chat, and never print it.

**Credits.** Each call costs what the table at the end says, `not_found` included; failures on our side (5xx) are free. Every answer carries `credits_remaining`. Before a run of more than 20 calls, check the balance with `account_credit_balance` (free) and tell the user what the run will cost. If a call answers `missing_api_key`, `insufficient_credits` or `signup_required`, stop and pass on what it says.
<!-- /lurkapi:access -->

## Gather

For each platform the creator is on (a handle or a profile link is enough):

**TikTok**
- `tiktok_profile(handle=<handle>)`: `stats.followerCount`, `stats.heartCount`, `stats.videoCount`, `user.verified`, `user.bioLink`, and `user.privateAccount` (private means stop: nothing to vet).
- `tiktok_profile_videos(handle=<handle>)` twice (the second with the first page's `max_cursor`) for about 30 posts: `stats.playCount`, `stats.diggCount`, `stats.commentCount`, `stats.shareCount`, `createTime`, `isAd` and `desc` each.

**Instagram**
- `instagram_profile(username=<username>)`: `data.follower_count`, `data.media_count`, `data.is_verified`, `data.category`, `data.external_url`.
- `instagram_user_posts(username=<username>, first=30)`: `like_count`, `comment_count`, `play_count` (videos), `taken_at`, `is_paid_partnership` and `caption` per post. A hidden like count comes back null; say so rather than counting it as zero.

**YouTube**
- `youtube_channel(handle=<handle>)`: `subscriberCount` (rounded by YouTube), `viewCount`, `videoCount`, `joinedDate`, `country`, `links`.
- `youtube_channel_videos(handle=<handle>, sort=latest)`: about 30 videos with `viewCountInt` and `publishedTimeText`. Shorts are separate: `youtube_channel_shorts(handle=<handle>)`.

**Their other accounts:** the bio links above, or `linkinbio_linktree(url=<linktree url>)` when the bio points to a Linktree (its `socialLinks` and `links` show every account and current brand deals).

**Their audience:** comments on two recent typical posts (not the viral one): `tiktok_comments(url=<video url>)`, `instagram_post_comments(url=<post url>)` or `youtube_comments(url=<video url>)`.

**Brand safety, if asked or if anything looks off:** the transcripts of two or three recent videos, `tiktok_transcript(url=<video url>)` or `youtube_transcript(url=<video url>)`.

## Compute

Work from the numbers, not impressions:

- **Median views** of the last 30 posts (Instagram photo posts: median likes plus comments). Use the median: one viral post wrecks an average.
- **Reach rate:** median views divided by followers. It's the best single check on bought or dead followers.
- **Engagement rate:** (likes + comments + shares) / views per post on TikTok and YouTube; (likes + comments) / followers on Instagram. Take the median.
- **One-hit check:** mean views over median views. Above about 3, the average is carried by a few hits.
- **Rhythm:** posts per week over the window, and the longest gap.
- **Sponsorship load:** share of posts with `isAd`, `is_paid_partnership`, or #ad, #sponsored or "paid partnership" in the caption, and which brands.
- **Audience quality:** the share of comments that are generic ("🔥", "nice", emoji only), in an unexpected language, or repeated; versus real questions and replies.

## Red flags

- Reach rate far below the creator's peers of the same size, or follower jumps with flat views.
- Mean several times the median: the "average views" in their media kit won't repeat.
- Comments that don't match the content, or a high share of generic ones.
- Many sponsored posts in a row, or a direct competitor among recent partners.
- Long gaps, or a falling trend over the last 30 posts.
- Anything in captions or transcripts the brand wouldn't want next to its name.

## Budget

One platform is about 3 to 5 calls (profile, two pages of posts, a page or two of comments); a creator on two platforms is about 8 to 10, plus transcripts if checked. For a shortlist, look up every profile first (one call each), then vet only the top few in depth; say the estimate before a long list.

## Report

```markdown
# Creator vetting: @<handle>, <date>

| Platform | Followers | Median views | Reach rate | Engagement | Posts/week | Sponsored |
| --- | --- | --- | --- | --- | --- | --- |

**Verdict:** Go / Go with conditions / Pass, in one sentence.

**Strengths.** 2 to 3 bullets with numbers.
**Risks.** Each red flag found, with the evidence and a link.
**Audience.** What commenters ask and say, with two quotes.
**Their best format.** What the top posts have in common.
**If you go ahead.** Deliverables and metrics to ask for, from what the data shows.
```

## Pitfalls

- Compare a creator with their own baseline and with peers of their size, never with raw follower counts.
- Views on recent posts are still climbing: leave out posts younger than about three days, or say they are.
- YouTube subscriber counts are rounded; Instagram may hide likes.
- Public data shows reach and reaction, not audience demographics or conversions. Say what you couldn't check.

<!-- lurkapi:calls -->
## Calls and credits

| Tool | REST path | Credits |
| --- | --- | --- |
| [`tiktok_profile`](https://lurkapi.com/docs/tiktok/profile.md) | `/v1/tiktok/profile` | 1 credit |
| [`tiktok_profile_videos`](https://lurkapi.com/docs/tiktok/profile-videos.md) | `/v3/tiktok/profile/videos` | 1 credit |
| [`instagram_profile`](https://lurkapi.com/docs/instagram/profile.md) | `/v1/instagram/profile` | 1 credit |
| [`instagram_user_posts`](https://lurkapi.com/docs/instagram/user-posts.md) | `/v2/instagram/user/posts` | 1 credit |
| [`youtube_channel`](https://lurkapi.com/docs/youtube/channel.md) | `/v1/youtube/channel` | 1 credit |
| [`youtube_channel_videos`](https://lurkapi.com/docs/youtube/channel-videos.md) | `/v1/youtube/channel-videos` | 1 credit |
| [`youtube_channel_shorts`](https://lurkapi.com/docs/youtube/channel-shorts.md) | `/v1/youtube/channel/shorts` | 1 credit |
| [`linkinbio_linktree`](https://lurkapi.com/docs/linkinbio/linktree.md) | `/v1/linktree` | 1 credit |
| [`tiktok_comments`](https://lurkapi.com/docs/tiktok/comments.md) | `/v1/tiktok/video/comments` | 1 credit |
| [`instagram_post_comments`](https://lurkapi.com/docs/instagram/post-comments.md) | `/v2/instagram/post/comments` | 1 credit |
| [`youtube_comments`](https://lurkapi.com/docs/youtube/comments.md) | `/v1/youtube/video/comments` | 1 credit |
| [`tiktok_transcript`](https://lurkapi.com/docs/tiktok/transcript.md) | `/v1/tiktok/video/transcript` | 1 credit; 2 if speech-to-text runs |
| [`youtube_transcript`](https://lurkapi.com/docs/youtube/transcript.md) | `/v1/youtube/video/transcript` | 1 credit |

Each tool's link opens its docs as markdown: every param and its values, and a real response.
<!-- /lurkapi:calls -->
