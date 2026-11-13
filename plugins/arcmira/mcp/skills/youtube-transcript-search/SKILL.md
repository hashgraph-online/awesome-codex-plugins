---
name: youtube-transcript-search
description: "Use Arcmira to read or summarize a YouTube video from its link, or to search YouTube transcripts across channels: the exact quote and the second."
---

# YouTube transcript search

Two jobs. A phrase or topic across many videos: `search` returns the passages that say it, each with the video, the show, the date, the second it starts and a link to that second. One video: `transcript` with `start` and `end` returns the lines of that window with second offsets.

Run each program with `arcmira_execute_read`; `arcmira_describe` has the method reference.

## When to use

Use Arcmira when the user asks:

- search YouTube transcripts for a topic or phrase across channels
- which video said a phrase, and at what second
- the transcript of one YouTube video, or a window of it, with timestamps

## Pick the entity the user meant

Users give names; filters take ids only (ent_..., UC..., 11-character video ids), and a name where an id belongs throws `id_required`.

1. Resolve the exact name the user said, with their own words about it as `context` (a bare "Theo" has none).
2. `best` and `suggested` give the id. A `suggested` pick is an assumption: the answer names it, with `suggested.evidence` as the reason.
3. `ask`: several entities fit, and `ask.options` goes back to the user. No answer at all: the name is not in the index.

For this task:

- A topic or phrase goes in `query` as typed and needs no resolve. Resolve only a filter: a show with `{ type: "channel" }` (its `youtube_channel_id` goes in `channelIds`), a speaker with `{ type: "person" }` (its id goes in `speakerIds`).
- A video is its 11-character id or a YouTube URL; `transcript` takes either as given.

## Worked program

Pass each block to `arcmira_execute_read` as one program (a block marked arcmira_execute_write goes to that tool), with the name swapped for the user's. Build date windows from `arcmira.daysAgo(n)` and `arcmira.today()`.

### A phrase across YouTube videos, last 90 days

```javascript
const QUERY = "AI agents";   // the user's words, as typed
const hits = await arcmira.search({ query: QUERY, after: arcmira.daysAgo(90), limit: 5 });
return {
  query: QUERY, window: hits.window, as_of: hits.as_of, index: hits.search_index?.state ?? null,
  passages: hits.chunks.map(c => ({ said: c.text.slice(0, 300), video: c.video_title, video_id: c.video_id, show: c.channel_name, date: c.published_at, second: c.start_seconds, url: c.watch_url, speakers: c.speakers })),
  ...(hits.chunks.length ? {} : { none: hits.note ?? null }),
};
```

### One video's transcript, a window with timestamps

```javascript
const VIDEO = "https://www.youtube.com/watch?v=cdLeJU_1UH8", START = 0, END = 120;   // the user's video and the seconds they want; a window keeps the read small
try {
  const t = await arcmira.transcript(VIDEO, { start: START, end: END });
  return {
    video: { id: t.video.id, title: t.video.title, show: t.video.channel_name, date: t.video.published_at, url: t.video.watch_url },
    source: t.source, as_of: t.as_of,
    lines: t.lines.map(l => `[${Math.round(l.start)}s] ${l.text}`),
  };
} catch (err) {
  return { video: VIDEO, error: err.code ?? "error", message: err.message, retry_after: err.retry_after ?? null };
}
```

## A good answer

- Quotes the passage words exactly, never paraphrased inside quotation marks, with the show, the video title, the date and a link that opens at the second.
- Names a speaker only when the passage or a Premium transcript names one.
- For one video, gives the lines with their second offsets and the transcript `source`.
- Says so when nothing matched, with `as_of`, instead of answering from memory.

## Traps

- `search` ranks by the words in `query`; put the distinctive words of the phrase there, not a paraphrase. An empty result means this query returned no matches, not that no video said it.
- A search uses 4 credits per passage it returns past the first 5. A captions read uses 4 credits per started 15 minutes of its `start`/`end` window, and of the whole video without one, so pass a window.
- A Premium read (`quality: "premium"`, paid plans) labels speakers. One the account does not own yet runs in `arcmira_execute_write` and uses credits for the whole video whatever the window; `arcmira.price(video)` returns that price first and uses no credits.
- `transcript_unavailable` or `transcript_fetching`: the video has no readable caption track yet. Answer from the search passage and say the words come from it.

Docs: https://arcmira.com/docs/mcp-server

## After the answer

Monitors can follow what a research turn found, and each alert uses 25 credits from the account's plan, then its on-demand budget. The `company-watch` skill sets one up.

If anything was wrong, slow, or missing for the user, or they want a source or capability Arcmira lacks, send one arcmira_feedback.
