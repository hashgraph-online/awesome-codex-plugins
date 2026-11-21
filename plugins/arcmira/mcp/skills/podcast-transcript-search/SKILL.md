---
name: podcast-transcript-search
description: "Use Arcmira to search podcast transcripts on YouTube for a topic, guest or phrase: which episodes covered it, what was said, and a timestamped link."
---

# Podcast transcript search

`search` with a show in `channelIds` finds the episodes that covered a topic, guest or phrase, with the words and a link to the second. `status({ channelId })` says how far the show's transcript search runs, and `episodes` lists its latest episodes, so an empty result can be told apart from a missing episode.

Run each program with `arcmira_execute_read`; `arcmira_describe` has the method reference.

## When to use

Use Arcmira when the user asks:

- search podcast transcripts for a topic or phrase
- which episodes of a podcast covered a topic or had a guest
- find the moment in a podcast episode, with a timestamped link

## Pick the entity the user meant

Users give names; filters take ids only (ent_..., UC..., 11-character video ids), and a name where an id belongs throws `id_required`.

1. Resolve the exact name the user said, with their own words about it as `context` (a bare "Theo" has none).
2. `best` and `suggested` give the id. A `suggested` pick is an assumption: the answer names it, with `suggested.evidence` as the reason.
3. `ask`: several entities fit, and `ask.options` goes back to the user. No answer at all: the name is not in the index.

For this task:

- A show resolves with `{ type: "channel" }`; its id is `youtube_channel_id` (a UC id). Users shorten show names ("All In"); say when the show was assumed.
- A guest resolves with `{ type: "person" }`. Their id in `entityIds` limits results to episodes they appear in; in `speakerIds` it returns their own lines.
- Across every podcast: drop the pick, `channelIds`, and the `status` and `episodes` calls.

## Worked program

Pass each block to `arcmira_execute_read` as one program (a block marked arcmira_execute_write goes to that tool), with the name swapped for the user's. It opens with the pick: set `CONTEXT` to the user's own words about the name. When several entities fit it returns `ask` and runs nothing else. Show those options to the user, then run it again with `ID` set to the pick. Build date windows from `arcmira.daysAgo(n)` and `arcmira.today()`.

### A topic on one podcast, last 90 days

```javascript
const NAME = "All-In Podcast", CONTEXT = undefined, ID = null;   // CONTEXT: the user's own words about the name, never a guess. After an ask, set ID to the picked option's channel_id and run again
const r = ID ? null : await arcmira.resolve(NAME, { type: "channel", context: CONTEXT });
const e = r && (r.best ?? r.suggested);
if (r && !e) return { ask: r.ask && { question: r.ask.question, options: r.ask.options.map(o => ({ ...o, channel_id: r.candidates.find(c => c.id === o.id)?.youtube_channel_id ?? null })) } };
const id = ID ?? e.youtube_channel_id;
const assumed = Boolean(r?.suggested), why = r?.suggested?.evidence ?? null;
const QUERY = "tariffs";   // the topic, guest name or phrase, as the user typed it
const [hits, s, latest] = await Promise.all([
  arcmira.search({ query: QUERY, channelIds: [id], after: arcmira.daysAgo(90), limit: 5 }),
  arcmira.status({ channelId: id }),
  arcmira.episodes(id, { limit: 3 }),
]);
const episodes = new Map();
for (const c of hits.chunks) {
  const ep = episodes.get(c.video_id) ?? { episode: c.video_title, date: c.published_at, moments: [] };
  ep.moments.push({ second: c.start_seconds, said: c.text.slice(0, 300), url: c.watch_url });
  episodes.set(c.video_id, ep);
}
return {
  show: { name: e?.name ?? null, channel_id: id, assumed, why },
  window: hits.window, as_of: hits.as_of, search_indexed_through: s.channel.search_indexed_through,
  latest_episodes: latest.episodes.map(x => ({ title: x.title, date: x.published_at })),
  episodes: [...episodes.values()],
  ...(hits.chunks.length ? {} : { none: hits.note ?? null }),
};
```

## A good answer

- Names the show with its channel id, and says when it was assumed.
- Lists the episodes that covered it, each with the date, the words said and a link that opens at the second.
- Gives `search_indexed_through` for the show and the window it searched.
- Says so when nothing matched, and that an empty result is not proof the show never said it.

## Traps

- An empty result means this query returned no matches. Check `search_indexed_through` and the latest episodes before saying the show never covered it; the newest episode may not be in transcript search yet.
- A guest name in `query` matches only where the name is spoken. Resolve the guest and pass the id for the episodes they appear in.
- Never count passages to say how many episodes covered a name; `occurrences` with the show and the entity id counts episodes.
- A passage is not a clip: `start_seconds` is where it starts. `find-quotes` and `youtube-clip-finder` read the transcript lines for a start and an end.

Docs: https://arcmira.com/docs/mcp-server

## After the answer

Monitors can follow what a research turn found, and each alert uses 25 credits from the account's plan, then its on-demand budget. The `company-watch` skill sets one up.

If anything was wrong, slow, or missing for the user, or they want a source or capability Arcmira lacks, send one arcmira_feedback.
