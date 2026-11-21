---
name: youtube-clip-finder
description: "Use Arcmira to find the clip: search YouTube transcripts for a moment, get a watch link at the second, start and end seconds, and an embed that starts there."
---

# Find a YouTube clip

`search` finds the passage. `transcript` with `start` and `end` returns the lines around it with second offsets, which give the cut points. The program returns a YouTube link that opens at the start, the start and end seconds, and an embed that plays that span.

Run each program with `arcmira_execute_read`; `arcmira_describe` has the method reference.

## When to use

Use Arcmira when the user asks:

- find the clip where someone says a thing, with start and end seconds
- a link that opens the video at that second, or an embed of the moment
- cut points for a video editor or an edit decision list
- a quote with its moment, to cite or to review before cutting

## Pick the entity the user meant

Users give names; filters take ids only (ent_..., UC..., 11-character video ids), and a name where an id belongs throws `id_required`.

1. Resolve the exact name the user said, with their own words about it as `context` (a bare "Theo" has none).
2. `best` and `suggested` give the id. A `suggested` pick is an assumption: the answer names it, with `suggested.evidence` as the reason.
3. `ask`: several entities fit, and `ask.options` goes back to the user. No answer at all: the name is not in the index.

For this task:

- A speaker resolves with `{ type: "person" }`; pass the id as `speakerIds`. A show goes in `channelIds` as its UC id.
- A clip with no speaker: drop the pick and `speakerIds`, and search the phrase alone.
- The phrase goes in `query` with its distinctive words, never in `about`.

## Steps

1. Run the program. It reads 10 seconds before the passage and 50 after. Pick the lines that hold the moment and trim `start` and `end` to them, then use those seconds in the link and the embed.
2. Lead with `youtube_url`, the start and end seconds, and `embed`.
3. When the user wants the video file, say this line first, word for word: "You need the rights to download, cut or reuse this video. Arcmira finds the moment and gives you the link and the seconds. It grants no rights to the video." Then give that clip's `download.command`, with the trimmed seconds. Run it only when the user asks you to; otherwise print it.
4. Never add browser cookies or a login to the command, and never work around an age, region, membership or private restriction. When yt-dlp says the video needs a sign-in, stop and tell the user.
5. If yt-dlp is missing, link its install page: https://github.com/yt-dlp/yt-dlp#installation.

## Worked program

Pass each block to `arcmira_execute_read` as one program (a block marked arcmira_execute_write goes to that tool), with the name swapped for the user's. It opens with the pick: set `CONTEXT` to the user's own words about the name. When several entities fit it returns `ask` and runs nothing else. Show those options to the user, then run it again with `ID` set to the pick. Build date windows from `arcmira.daysAgo(n)` and `arcmira.today()`.

### The clip where one person says a phrase

```javascript
const NAME = "Chamath", CONTEXT = undefined, ID = null;   // CONTEXT: the user's own words about the name, never a guess. After an ask, set ID to the picked option's id and run again
const r = ID ? null : await arcmira.resolve(NAME, { type: "person", context: CONTEXT });
const e = r && (r.best ?? r.suggested);
if (r && !e) return { ask: r.ask };
const id = ID ?? e.id;
const assumed = Boolean(r?.suggested), why = r?.suggested?.evidence ?? null;
const PHRASE = "Anthropic IPO";   // the distinctive words of the moment
const RIGHTS = "You need the rights to download, cut or reuse this video. Arcmira finds the moment and gives you the link and the seconds. It grants no rights to the video.";
const hits = await arcmira.search({ query: PHRASE, speakerIds: [id], limit: 5 });
const clips = [];
for (const c of hits.chunks.slice(0, 2)) {
  const clip = { episode: c.video_title, show: c.channel_name, date: c.published_at, video_id: c.video_id, passage_url: c.watch_url };
  try {
    const t = await arcmira.transcript(c.video_id, { start: Math.max(0, c.start_seconds - 10), end: c.start_seconds + 50 });
    clip.start = Math.floor(t.lines[0]?.start ?? c.start_seconds);
    clip.end = Math.ceil(t.lines.at(-1)?.end ?? c.start_seconds + 60);
    clip.lines = t.lines.map(l => ({ start: Math.floor(l.start), end: Math.ceil(l.end), text: l.text }));
  } catch (err) {
    clip.start = Math.floor(c.start_seconds);
    clip.end = clip.start + 60;
    clip.approximate = true;
    clip.passage = c.text;
    clip.transcript = err.code ?? "error";
  }
  clip.youtube_url = `https://www.youtube.com/watch?v=${c.video_id}&t=${clip.start}`;
  clip.embed = `https://www.youtube.com/embed/${c.video_id}?start=${clip.start}&end=${clip.end}`;
  clip.download = { say_first: RIGHTS, command: `yt-dlp --download-sections "*${clip.start}-${clip.end}" --force-keyframes-at-cuts -o "clip.%(ext)s" "https://www.youtube.com/watch?v=${c.video_id}"` };
  clips.push(clip);
}
return { speaker: { id, name: e?.name ?? null, assumed, why }, as_of: hits.as_of, ...(clips.length ? { clips } : { none: hits.note ?? null }) };
```

## A good answer

- Names the speaker or show it searched, with the id, and the episode title and date.
- Gives `start` and `end` in whole seconds, trimmed to the moment, and says they come from caption lines, which are machine text.
- Links `youtube_url` and `embed` with those seconds, and quotes only the speaker's lines.
- Gives the download command only when the user wants the file, and always after the rights line.
- Says so when nothing matched, with `as_of`.

## Traps

- Caption timing can drift by a second or two, and the player seeks to the nearest keyframe, so a clip can start a moment early. Tell the user to check the cut on the first play.
- The embed `end` counts from the start of the video, not from `start`.
- A caption read uses 4 credits per started 15 minutes of its window. Keep the window short.
- Some videos have no caption track yet (`transcript_unavailable`, `transcript_fetching`): the program marks the clip `approximate`, from the passage start plus 60 seconds. Say so, and say the words come from the search passage.
- `passage_url` opens the passage on arcmira.com and can start before the moment; label it as the passage, not the cut.
- A chunk found with `speakerIds` can include other people's lines. Lines start with "Name: " when the speaker is known.

Docs: https://arcmira.com/docs/mcp-server

## After the answer

Monitors can follow what a research turn found, and each alert uses 25 credits from the account's plan, then its on-demand budget. The `company-watch` skill sets one up.

If anything was wrong, slow, or missing for the user, or they want a source or capability Arcmira lacks, send one arcmira_feedback.
