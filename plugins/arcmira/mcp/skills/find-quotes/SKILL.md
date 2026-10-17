---
name: find-quotes
description: "Finds exact spoken quotes and clip-ready moments on podcasts and YouTube: verbatim words, speaker, date, a timestamped link, clip start and end. Uses arcmira."
---

# Find quotes and clip moments

`search` finds the passage; `transcript` with `start` and `end` returns the exact lines around it with second offsets, which give the verbatim quote and the clip boundaries.

Run each program with `arcmira_execute_read`; `arcmira_describe` has the method reference.

## When to use

- find a quote, with the source and a timestamp
- the moment a show talked about a topic, to clip or cite
- what a specific person said about a topic, in their words

## Pick the entity the user meant

Users give names; filters take ids only (ent_..., UC..., 11-character video ids), and a name where an id belongs throws `id_required`.

1. Resolve the exact name the user said, with their own words about it as `context` (a bare "Theo" has none).
2. `best` and `suggested` give the id. A `suggested` pick is an assumption: the answer names it, with `suggested.evidence` as the reason.
3. `ask`: several entities fit, and `ask.options` goes back to the user. No answer at all: the name is not in the index.

For this task:

- A speaker resolves with `{ type: "person" }`; pass the id as `speakerIds` (who said it). A person or brand the passage is about goes in `about`. A show goes in `channelIds` as its UC id.
- People are often named by first name ("Chamath"). Pass what the user said about them as `context`; resolve suggests the person when one stands out and asks when several fit.
- The topic words go in `query`, never in `about`. If a filtered search returns no chunks, rerun it with fewer filters before saying nothing was found.

## Worked program

Pass each block to `arcmira_execute_read` as one program (a block marked arcmira_execute_write goes to that tool), with the name swapped for the user's. It opens with the pick: set `CONTEXT` to the user's own words about the name. When several entities fit it returns `ask` and runs nothing else. Show those options to the user, then run it again with `ID` set to the pick. Build date windows from `arcmira.daysAgo(n)` and `arcmira.today()`.

### What one person said about a topic, with clip boundaries

```javascript
const NAME = "Chamath", CONTEXT = undefined, ID = null;   // CONTEXT: the user's own words about the name, never a guess. After an ask, set ID to the picked option's id and run again
const r = ID ? null : await arcmira.resolve(NAME, { type: "person", context: CONTEXT });
const e = r && (r.best ?? r.suggested);
if (r && !e) return { ask: r.ask };
const id = ID ?? e.id;
const assumed = Boolean(r?.suggested), why = r?.suggested?.evidence ?? null;
const hits = await arcmira.search({ query: "Anthropic IPO", speakerIds: [id], limit: 5 });
const moments = [];
for (const c of hits.chunks.slice(0, 2)) {
  const moment = { episode: c.video_title, show: c.channel_name, date: c.published_at, url: c.watch_url, speakers: c.speakers_by.map(s => s.name) };
  try {
    const t = await arcmira.transcript(c.video_id, { start: Math.max(0, c.start_seconds - 10), end: c.start_seconds + 50 });
    moment.clip = { start: t.lines[0]?.start ?? c.start_seconds, end: t.lines.at(-1)?.end ?? c.start_seconds + 60 };
    moment.lines = t.lines.map(l => `[${Math.round(l.start)}s] ${l.text}`);
  } catch (err) {
    moment.clip = { start: c.start_seconds, end: c.start_seconds + 60 };
    moment.passage = c.text;
    moment.transcript = err.code;
  }
  moments.push(moment);
}
return { speaker: { id, name: e?.name ?? null, assumed, why }, as_of: hits.as_of, ...(moments.length ? { moments } : { none: hits.note ?? null }) };
```

## A good answer

- Names the speaker or show it searched, with the id, and quotes the words exactly as the transcript lines give them, trimmed to whole sentences, never paraphrased inside quotation marks.
- Gives the show, the episode title, the date, and the speaker when the chunk or a premium transcript names one.
- Links the `watch_url`, which starts at the moment, and gives a clip start and end in seconds from the transcript lines.
- Says so when nothing matched, with `as_of`, instead of offering a quote from memory.

## Traps

- `search` ranks by the words in `query`; put the distinctive words of the phrase there, not a paraphrase.
- A chunk found with `speakerIds` also holds other people's lines. Quote only lines that start with the speaker's name ("Chamath Palihapitiya: ..."), never the whole passage.
- Caption lines are machine text: fix nothing inside the quotation marks. A premium transcript (`quality: "premium"`, paid plans) adds speaker ids into `speakers[]`.
- A caption read uses 4 credits per started 15 minutes of its `start`/`end` window, and of the whole episode without one. A Premium read uses credits for the whole video whatever the window.
- Some videos have no readable caption track yet (`transcript_unavailable`, `transcript_fetching`); quote the search chunk `text` for those and say the words come from the search passage.

Docs: https://arcmira.com/docs/mcp-server

## After the answer

Monitors can follow what a research turn found, and each alert uses 25 credits from the account's plan, then its on-demand budget. The `company-watch` skill sets one up.

If anything was wrong, slow, or missing for the user, send one arcmira_feedback.
