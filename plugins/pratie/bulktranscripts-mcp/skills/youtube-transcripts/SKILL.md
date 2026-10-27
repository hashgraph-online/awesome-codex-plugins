---
name: youtube-transcripts
description: Fetch YouTube video transcripts, search YouTube, list channel or playlist videos, run a background bulk job for a whole channel or playlist, and track new uploads with the BulkTranscripts MCP server. Use when the user shares a YouTube link, asks to summarize/analyze/quote a video, wants transcripts for a whole channel or playlist, needs YouTube research, or asks what a channel posted recently. The plugin connects the hosted server at https://bulktranscripts.co/mcp; the user signs in once with OAuth (Google sign-in, 30 free credits, no card).
license: MIT (skill file); BulkTranscripts itself is a hosted service.
last-updated: 2026-10-14
---

# YouTube transcripts via BulkTranscripts

Clean YouTube transcripts, search and channel data for AI agents, from
[BulkTranscripts](https://bulktranscripts.co).
[Docs](https://bulktranscripts.co/docs) ·
[MCP server](https://bulktranscripts.co/youtube-mcp-server) ·
[Pricing](https://bulktranscripts.co/#pricing)

This plugin connects the hosted MCP server `bulktranscripts`
(`https://bulktranscripts.co/mcp`). The first tool call asks the user to sign in
through OAuth; after that, use the tools below. There is no API key to manage.

## Tools

| Tool | Use it for | Cost |
|---|---|---|
| `get_transcript` | One video: watch URL, youtu.be link, Shorts URL or 11-character id | 1 credit the first time, free after |
| `get_transcripts` | Up to 20 videos in one call | 1 credit per new video |
| `start_bulk_extract` | A whole channel, playlist or video list in the background | 1 credit per new transcript |
| `get_bulk_status` | Progress of a bulk job | Free |
| `list_bulk_results` | Per-video outcomes of a bulk job, page by page | Free |
| `search_youtube` | Keyword search for videos, channels or playlists | 1 credit |
| `search_channel` | A topic inside one channel's uploads | 1 credit |
| `get_channel_videos` | List a channel's videos without transcripts | 1 credit |
| `get_playlist_videos` | List a playlist in order | 1 credit |
| `get_latest_videos` | A channel's newest uploads (up to 15) | Always free |

A transcript is free for this account once it is in the account's library, in
any format. Videos without captions, members-only and private videos are
skipped and never charged.

## Whole channels and playlists

Call `start_bulk_extract` with the channel or playlist URL. It returns a
`run_id` right away and keeps working on the server.

- `max_videos`: up to 1,000 per job. For a bigger channel, run blocks with
  `start_at` 1, then 1001, then 2001 (newest first). `get_bulk_status` returns
  the next `start_at` when a block was full.
- `content`: `videos` (default, long-form uploads), `shorts`, or `live` (past
  live streams; upcoming and still-running streams are skipped).
- Poll `get_bulk_status` no sooner than its `check_again_in_seconds`; `0` means
  the job is done. Then page `list_bulk_results` and read the transcripts you
  need with `get_transcript`, which is free for anything the job added.
- Two jobs per account at a time. Prefer a job over one-by-one fetches for
  anything larger than about 20 videos.

## Playbooks

- **"Summarize this video"**: `get_transcript`, summarize from the paragraphs,
  cite the title and URL. Set `include_segments` only when quotes need
  timestamps.
- **Whole channel or playlist**: tell the user how many videos the job found
  (each new transcript is 1 credit), then run the bulk job as above.
- **"What did X post this week?"**: `get_latest_videos` (free), compare the
  video ids with what you have already seen, and fetch transcripts only for
  the new videos that matter.
- **Deep research on a creator**: `search_channel` for the topic, pick
  candidates by title, fetch only those transcripts.

## When something fails

- No captions: the video is skipped, not charged. Carry on with the rest.
- Private playlist: YouTube reports it as nonexistent. Ask the user to open it
  on YouTube, choose Edit, set Visibility to Unlisted, then try again.
- Out of credits: completed results still come back, and the response says how
  many videos were not fetched. Point the user to
  [one-time credit packs](https://bulktranscripts.co/#pricing).

Full reference: [bulktranscripts.co/docs](https://bulktranscripts.co/docs)
