---
name: revid-research-make-and-post
description: Research what already goes viral on a topic, make a finished short-form video from the strongest pattern, and publish or schedule it on TikTok, YouTube, Instagram or X. Use when the user wants a video posted, not just made, or asks what to post. Calls the Revid MCP server (search_viral_videos, calculate_credits, render_video, get_project_status, list_social_accounts, schedule_publish).
metadata: {"openclaw":{"requires":{"config":["REVID_API_KEY"]}}}
---

# Research, make and post

The full loop in one skill: find what works, make a video like it, post it.
Everything runs through the **Revid MCP server** (`https://www.revid.ai/api/mcp`).
Install it once, see [`revid-api-foundations`](../revid-api-foundations/SKILL.md#install-the-revid-mcp-server).

## When to use this skill

- The user wants a video **posted** ("make a TikTok about X and post it Friday").
- The user asks what to post, or wants the video based on what already performs.
- For a video the user will post themselves, use [`revid-prompt-to-video`](../revid-prompt-to-video/SKILL.md).
- For a script the user already wrote, use [`revid-script-to-video`](../revid-script-to-video/SKILL.md).

## Steps

1. **Research.** Call `search_viral_videos` with the topic as `query`, `viralOnly: true`,
   and the platforms the user posts on. Searches cost no credits. Read 5 to 10 results:
   the hook (first line of the transcript), the length, the format, the engagement.
   Tell the user in two or three lines which pattern you will use and why.
2. **Write.** Draft a 20 to 45 second script that uses the strongest hook pattern for
   the user's own subject. Never copy a creator's words. Show the script and wait for an
   OK unless the user said to go ahead.
3. **Price.** Call `calculate_credits` with the exact payload you will render and tell
   the user the cost in credits.
4. **Make.** Call `render_video`:
   ```json
   {
     "workflow": "script-to-video",
     "source": { "text": "<the approved script>" },
     "aspectRatio": "9:16",
     "voice": { "enabled": true },
     "captions": { "enabled": true },
     "music": { "generateMusic": true }
   }
   ```
   Use `prompt-to-video` with `source.prompt` instead when the user wants Revid to write
   the script. Keep the returned `pid`.
5. **Wait.** Poll `get_project_status` with the `pid` every 20 to 30 seconds until it
   returns `videoUrl`. Most videos take a few minutes; motion graphics take longer.
   Share the link and let the user watch it.
6. **Post.** Call `list_social_accounts`, pick the account the user named, then:
   - `schedule_publish` with `scheduledTime` (ISO 8601 with offset, for example
     `2026-10-30T18:00:00+01:00`) for a set time, or without it for the next free slot
     of the user's posting queue;
   - `publish_now` to post right away.
   Write a caption with 3 to 5 hashtags from the research. Accounts flagged
   `tokenInvalid: true` must be reconnected in Revid first.
7. **Confirm.** Call `get_publish_status` with the returned `contentId` and give the
   user the post link once it is live.

## Rules

- Posting is public: always confirm the account, the caption and the time with the user
  before `publish_now` or `schedule_publish`, unless they gave all three already.
- Rendering needs an active Revid plan. A `402 SUBSCRIPTION_REQUIRED` answer carries an
  `upgrade.url`: pass it to the user.
- Never call `render_video` twice for the same video: poll the first `pid` instead.
