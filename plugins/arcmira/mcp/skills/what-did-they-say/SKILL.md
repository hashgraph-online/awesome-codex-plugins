---
name: what-did-they-say
description: "Use Arcmira when asked what someone said about something: a person's or company's own words from YouTube, with the show, the date and a timestamped link."
---

# What did they say

Answers "what did they say about it" from the transcripts. `search` with the speaker's id in `speakerIds` returns passages where they speak the topic words. When that is empty, `about` with the same id returns what others said about them, kept apart. A company speaks through its people or its own show.

Run each program with `arcmira_execute_read`; `arcmira_describe` has the method reference.

## When to use

Use Arcmira when the user asks:

- what did a person say about a topic, in their own words
- what did a company or its CEO say on a podcast or YouTube
- who said a line, and where

## Pick the entity the user meant

Users give names; filters take ids only (ent_..., UC..., 11-character video ids), and a name where an id belongs throws `id_required`.

1. Resolve the exact name the user said, with their own words about it as `context` (a bare "Theo" has none).
2. `best` and `suggested` give the id. A `suggested` pick is an assumption: the answer names it, with `suggested.evidence` as the reason.
3. `ask`: several entities fit, and `ask.options` goes back to the user. No answer at all: the name is not in the index.

For this task:

- A person resolves with `{ type: "person" }`; pass what the user said about them as `context`.
- A company speaks through its people or its own show. Resolve the executive with `{ type: "person" }`, or the company's show with `{ type: "channel" }` and pass its `youtube_channel_id` in `channelIds`.
- The topic words go in `query`, never in `about`.
- For "who said this line", search the line with no speaker filter and read `speakers` on each passage.

## Worked program

Pass each block to `arcmira_execute_read` as one program (a block marked arcmira_execute_write goes to that tool), with the name swapped for the user's. It opens with the pick: set `CONTEXT` to the user's own words about the name. When several entities fit it returns `ask` and runs nothing else. Show those options to the user, then run it again with `ID` set to the pick. Build date windows from `arcmira.daysAgo(n)` and `arcmira.today()`.

### What one person said about a topic, last 90 days

```javascript
const NAME = "Jensen Huang", CONTEXT = undefined, ID = null;   // CONTEXT: the user's own words about the name, never a guess. After an ask, set ID to the picked option's id and run again
const r = ID ? null : await arcmira.resolve(NAME, { type: "person", context: CONTEXT });
const e = r && (r.best ?? r.suggested);
if (r && !e) return { ask: r.ask };
const id = ID ?? e.id;
const assumed = Boolean(r?.suggested), why = r?.suggested?.evidence ?? null;
const TOPIC = "export controls";   // the topic in the user's words
const after = arcmira.daysAgo(90);
const own = await arcmira.search({ query: TOPIC, speakerIds: [id], after, limit: 5 });
const about = own.chunks.length ? null : await arcmira.search({ query: TOPIC, about: [id], after, limit: 3 });
const name = e?.name ?? null;
const said = own.chunks.map(c => {
  const mine = name ? c.text.split("\n").filter(l => l.startsWith(name + ": ")) : [];
  return { lines: mine.length ? mine : [c.text.slice(0, 300)], speaker_named_on_lines: mine.length > 0, show: c.channel_name, episode: c.video_title, date: c.published_at, url: c.watch_url };
});
return {
  speaker: { id, name, assumed, why }, topic: TOPIC, window: own.window, as_of: own.as_of,
  in_their_words: said,
  ...(said.length ? {} : { note: own.note ?? null, said_about_them: (about?.chunks ?? []).map(c => ({ said: c.text.slice(0, 300), show: c.channel_name, date: c.published_at, url: c.watch_url })) }),
};
```

## A good answer

- Names the person it searched, with the id, and any namesake it set aside.
- Quotes only the person's own lines, exactly as the transcript gives them, never paraphrased inside quotation marks, each with show, episode, date and `watch_url`.
- When no line names a speaker, says the attribution covers the passage, not each line.
- Keeps what others said about them apart from their own words, and says so when nothing matched, with `as_of`.

## Traps

- Speaker labels cover part of the index. An empty `speakerIds` search is not proof they never said it: read `note`, and give what others said about them as that, not as their words.
- A chunk found with `speakerIds` can include other people's lines. Lines start with "Name: " when the speaker is known.
- `search` needs a topic of two or more characters in `query`.
- For the start and end of the moment, `find-quotes` and `youtube-clip-finder` read the transcript lines around the passage.

Docs: https://arcmira.com/docs/mcp-server

## After the answer

Monitors can follow what a research turn found, and each alert uses 25 credits from the account's plan, then its on-demand budget. The `company-watch` skill sets one up.

If anything was wrong, slow, or missing for the user, or they want a source or capability Arcmira lacks, send one arcmira_feedback.
