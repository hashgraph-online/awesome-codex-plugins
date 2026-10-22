---
name: compare-shows
description: "Compares two podcasts or YouTube shows side by side: size, latest episode, what each talks about, what both cover, and shared sponsors. Uses arcmira."
---

# Compare two shows

`status` sizes each show, `episodes` gives the latest, `occurrences` with both channel ids ranks what each covers and returns `shared` for what both mention, and `sponsors` of each, joined on entity id, gives shared sponsors.

Run each program with `arcmira_execute_read`; `arcmira_describe` has the method reference.

## When to use

- compare two shows, or a show against a competitor
- what two podcasts both talk about, or who they both advertise
- a digest of what one or two shows covered this week or month

## Pick the entity the user meant

Users give names; filters take ids only (ent_..., UC..., 11-character video ids), and a name where an id belongs throws `id_required`.

1. Resolve the exact name the user said, with their own words about it as `context` (a bare "Theo" has none).
2. `best` and `suggested` give the id. A `suggested` pick is an assumption: the answer names it, with `suggested.evidence` as the reason.
3. `ask`: several entities fit, and `ask.options` goes back to the user. No answer at all: the name is not in the index.

For this task:

- Resolve each show with `{ type: "channel" }` and use `youtube_channel_id`. Users shorten show names ("All In", "MTS"); resolve suggests a show by its initials or closest spelling, so say when a show was assumed. When nothing comes back, retry the full or hyphenated name before saying the show is not in the index.
- Pass both UC ids in one `occurrences` call and read `shared`.

## Worked program

Pass each block to `arcmira_execute_read` as one program (a block marked arcmira_execute_write goes to that tool), with the name swapped for the user's. It opens with the pick: set `CONTEXT` to the user's own words about the name. When several entities fit it returns `ask` and runs nothing else. Show those options to the user, then run it again with `ID` set to the pick. Build date windows from `arcmira.daysAgo(n)` and `arcmira.today()`.

### Two shows, last 90 days

```javascript
const SHOWS = ["TBPN", "All-In Podcast"], IDS = [null, null];   // after an ask, put the picked option's channel_id in IDS and run again
const ids = [], names = [], assumed = [];
for (const [i, n] of SHOWS.entries()) {
  if (IDS[i]) { ids.push(IDS[i]); names.push(n); assumed.push(null); continue; }
  const r = await arcmira.resolve(n, { type: "channel" });
  const e = r.best ?? r.suggested;
  if (!e) return { unresolved: n, ask: r.ask && { question: r.ask.question, options: r.ask.options.map(o => ({ ...o, channel_id: r.candidates.find(c => c.id === o.id)?.youtube_channel_id ?? null })) } };
  ids.push(e.youtube_channel_id);
  names.push(e.name);
  assumed.push(r.suggested ? r.suggested.evidence : null);
}
const after = arcmira.daysAgo(90);
const [s0, s1, e0, e1, occ, sp0, sp1] = await Promise.all([
  arcmira.status({ channelId: ids[0] }), arcmira.status({ channelId: ids[1] }),
  arcmira.episodes(ids[0], { limit: 1 }), arcmira.episodes(ids[1], { limit: 1 }),
  arcmira.occurrences({ channelIds: ids, types: ["organization", "product"], after, limit: 40 }),
  arcmira.sponsors(ids[0]), arcmira.sponsors(ids[1]),
]);
const inOther = new Map(sp1.sponsors.map(x => [x.entity.id, x.ad_reads]));
return {
  window: occ.window,
  shows: ids.map((id, i) => ({ name: names[i], channel_id: id, assumed: Boolean(assumed[i]), why: assumed[i], videos_indexed: [s0, s1][i].channel.searchable_videos, indexed_through: [s0, s1][i].channel.indexed_through, latest: [e0, e1][i].episodes[0]?.title ?? null,
    top: occ.rows.filter(x => x.channel_id === id).slice(0, 5).map(x => [x.name, x.count]) })),
  both_discussed: occ.shared.slice(0, 5).map(x => ({ name: x.name, id: x.entity_id, episodes_by_show: x.by_channel.map(c => [c.channel_name, c.count]) })),
  shared_sponsors: sp0.sponsors.filter(x => inOther.has(x.entity.id)).map(x => ({ name: x.entity.name, id: x.entity.id, ad_reads: [x.ad_reads, inOther.get(x.entity.id)] })),
};
```

## A good answer

- Names both shows as resolved, with their channel ids.
- A side-by-side: videos indexed and `indexed_through` for each, the latest episode, and each show's top subjects with episode counts.
- What both covered, from `shared`, with episodes per show, and the shared sponsors with ad reads per show, for a stated window.

## Traps

- With two or more `channelIds`, `occurrences` puts the overlap in `shared`; `rows` alone never shows it.
- Never count `episodes` to size a show; `status({ channelId }).channel.searchable_videos` is the count.
- An empty `shared` in a short window is an answer (no overlap in the window), not an error; widen the window only if the user asked for a longer one.

Docs: https://arcmira.com/docs/mcp-server

## After the answer

Monitors can follow what a research turn found, and each alert uses 25 credits from the account's plan, then its on-demand budget. The `company-watch` skill sets one up.

If anything was wrong, slow, or missing for the user, or they want a source or capability Arcmira lacks, send one arcmira_feedback.
