---
name: video-transcripts
description: Get what is said in YouTube videos and Shorts, TikToks and Instagram reels as text, for one link or a creator's latest or most-viewed videos, then summarize it, pull hooks, claims and quotes, or repurpose it into posts and scripts. Use when the user shares a video link and asks what it says, wants a transcript or summary, or wants to study what a creator says across many videos.
---

# Video transcripts

Turn videos into text, then into something useful: a summary, the hooks and claims, quotes with timestamps, or a script to reuse. One link or a whole channel.

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

## One video

Pick the call by the link:

- **YouTube** (watch, youtu.be, /shorts/, /live/): `youtube_transcript(url=<url>)`. The text is `transcript_only_text`; the timed version is `transcript` (each part with `startTimeText`), which MCP returns instead with `timestamps=true`. `language=es` picks a caption track from `availableLanguages`. `isGenerated` true means YouTube's auto-captions: expect misheard names.
- **TikTok:** `tiktok_transcript(url=<url>)`. The text is `text`. A `transcript` of null with empty `languages` means the video has no captions; `use_ai_as_fallback=true` then transcribes the audio itself (videos up to 2 minutes), which costs more (see the table). Ask before turning it on for many videos. When you also want the video's views and likes, `tiktok_video(url=<url>, get_transcript=true)` gives stats and captions in one call, as WEBVTT.
- **Instagram reels:** `instagram_media_transcript(url=<url>)`. Reels have no captions to read, so a new one always goes through speech-to-text at the higher price in the table; one we've transcribed before costs the base price. Up to 120 seconds.
- **Anything else** (Facebook, X, podcasts): not supported. Say so.

A video with no speech (music only) answers `transcript_unavailable`, at the base price.

## Many videos

List first, then transcribe only the videos that matter.

- **YouTube:** `youtube_channel_videos(handle=<handle>, sort=latest)` (about 30 a page; `sort=popular` for the most viewed), or `youtube_channel_shorts(handle=<handle>)`. Then `youtube_transcript` on the chosen `url`s.
- **TikTok:** `tiktok_profile_videos(handle=<handle>)`: 15 a page, newest first, with `stats.playCount`. Then `tiktok_transcript` on the chosen ones.
- **Instagram:** `instagram_user_reels(username=<username>)` gives play counts, then `instagram_media_transcript(code=<code>)` per reel. At the speech-to-text price, ten reels cost more than ten captioned TikToks: say the total first.

To find a creator's best videos rather than their latest, rank the list by views and take the top few, or the ones far above the creator's median.

## Budget

A transcript is one call; a listing page is one more. "The last 10 TikToks" is 11 calls; "the top 5 videos on a channel" is 6. Instagram reels and TikTok's audio fallback cost more per video: work it out from the table and say it before a batch.

## What to make of it

Unless the user asks for something else, give:

- **Summary:** what the video argues or shows, in three sentences.
- **Hook:** the first two sentences, verbatim, and why they work.
- **Structure:** the beats in order, with timestamps when you have them.
- **Claims:** each factual claim or number, quoted, so it can be checked.
- **Call to action:** what the viewer is asked to do.
- **Reusable lines:** quotes that stand alone.

Across many videos, compare hooks, recurring topics and phrases, video length against views, and how the best performers open.

## Pitfalls

- Never quote what isn't in the transcript. Auto-captions mishear names, brands and numbers; flag doubtful ones.
- A transcript is what's said, not what's shown: on-screen text and visuals aren't in it.
- Asking for the same transcript again is charged again, at the base price: keep what you fetched.

<!-- lurkapi:calls -->
## Calls and credits

| Tool | REST path | Credits |
| --- | --- | --- |
| [`youtube_transcript`](https://lurkapi.com/docs/youtube/transcript.md) | `/v1/youtube/video/transcript` | 1 credit |
| [`tiktok_transcript`](https://lurkapi.com/docs/tiktok/transcript.md) | `/v1/tiktok/video/transcript` | 1 credit; 2 if speech-to-text runs |
| [`tiktok_video`](https://lurkapi.com/docs/tiktok/video.md) | `/v2/tiktok/video` | 1 credit |
| [`instagram_media_transcript`](https://lurkapi.com/docs/instagram/media-transcript.md) | `/v2/instagram/media/transcript` | 1 credit; 2 if speech-to-text runs |
| [`youtube_channel_videos`](https://lurkapi.com/docs/youtube/channel-videos.md) | `/v1/youtube/channel-videos` | 1 credit |
| [`youtube_channel_shorts`](https://lurkapi.com/docs/youtube/channel-shorts.md) | `/v1/youtube/channel/shorts` | 1 credit |
| [`tiktok_profile_videos`](https://lurkapi.com/docs/tiktok/profile-videos.md) | `/v3/tiktok/profile/videos` | 1 credit |
| [`instagram_user_reels`](https://lurkapi.com/docs/instagram/user-reels.md) | `/v1/instagram/user/reels` | 1 credit |

Each tool's link opens its docs as markdown: every param and its values, and a real response.
<!-- /lurkapi:calls -->
