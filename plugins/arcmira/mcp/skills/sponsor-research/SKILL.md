---
name: sponsor-research
description: "Sponsor and ad-read research on podcasts and YouTube: who sponsors a show, or which shows a brand sponsors, how often, since when. Uses arcmira."
---

# Sponsor research

Two directions. A show to its sponsors: `arcmira.sponsors(channelId)` ranks recurring sponsors by ad reads with first and last seen dates. A brand to the shows it sponsors: `arcmira.recommendations(entityId, { kind: "sponsored" })` lists each ad read, which the program groups by show.

Run each program with `arcmira_execute_read`; `arcmira_describe` has the method reference.

## When to use

- who sponsors a show, how many ad reads, since when, still active
- which shows a brand sponsors or advertises on, and how often
- sponsors two shows share (sponsors of each, then intersect by entity.id)

## Pick the entity the user meant

Users give names; filters take ids only (ent_..., UC..., 11-character video ids), and a name where an id belongs throws `id_required`.

1. Resolve the exact name the user said, with their own words about it as `context` (a bare "Theo" has none).
2. `best` and `suggested` give the id. A `suggested` pick is an assumption: the answer names it, with `suggested.evidence` as the reason.
3. `ask`: several entities fit, and `ask.options` goes back to the user. No answer at all: the name is not in the index.

For this task:

- A show resolves with `{ type: "channel" }`; its id is `youtube_channel_id` (a UC id).
- A brand resolves with no type (a company can be typed product). A sponsor is a company: a person or a topic with the same name ("Freddie Mercury") is not the brand.
- When two company rows compete, the one with ad reads is the sponsor: run the brand program for each and keep the one with reads.

## Worked program

Pass each block to `arcmira_execute_read` as one program (a block marked arcmira_execute_write goes to that tool), with the name swapped for the user's. It opens with the pick: set `CONTEXT` to the user's own words about the name. When several entities fit it returns `ask` and runs nothing else. Show those options to the user, then run it again with `ID` set to the pick. Build date windows from `arcmira.daysAgo(n)` and `arcmira.today()`.

### A show's sponsors

```javascript
const NAME = "TBPN", CONTEXT = undefined, ID = null;   // CONTEXT: the user's own words about the name, never a guess. After an ask, set ID to the picked option's channel_id and run again
const r = ID ? null : await arcmira.resolve(NAME, { type: "channel", context: CONTEXT });
const e = r && (r.best ?? r.suggested);
if (r && !e) return { ask: r.ask && { question: r.ask.question, options: r.ask.options.map(o => ({ ...o, channel_id: r.candidates.find(c => c.id === o.id)?.youtube_channel_id ?? null })) } };
const id = ID ?? e.youtube_channel_id;
const assumed = Boolean(r?.suggested), why = r?.suggested?.evidence ?? null;
const s = await arcmira.sponsors(id);   // limit is a Pro+ filter; slice instead
return {
  show: s.channel.name, channel_id: id, page: s.channel.page, assumed, why, sponsors_total: s.meta.total,
  sponsors: s.sponsors.slice(0, 10).map(x => ({ name: x.entity.name, id: x.entity.id, page: x.entity.page, ad_reads: x.ad_reads, episodes: x.videos, first_seen: x.first_seen, last_seen: x.last_seen, status: x.sponsor_status?.status ?? null })),
};
```

### The shows a brand sponsors, last 90 days

```javascript
const NAME = "Mercury", CONTEXT = undefined, ID = null;   // CONTEXT: the user's own words about the name, never a guess. After an ask, set ID to the picked option's id and run again
const r = ID ? null : await arcmira.resolve(NAME, { context: CONTEXT });
const e = r && (r.best ?? r.suggested);
if (r && !e) return { ask: r.ask };
const id = ID ?? e.id;
const assumed = Boolean(r?.suggested), why = r?.suggested?.evidence ?? null;
const after = arcmira.daysAgo(90);
const reads = [];
let cursor, entity, window;
do {
  const page = await arcmira.recommendations(id, { kind: "sponsored", after, limit: 100, cursor });
  entity = page.entity;
  window = page.window;
  reads.push(...page.recommendations);
  cursor = page.has_more ? page.next_cursor : undefined;
} while (cursor && reads.length < 500);
const shows = new Map();
for (const x of reads) {
  const name = x.media.source_channel?.name ?? x.media.channel_id;
  const row = shows.get(name) ?? { show: name, channel_id: x.media.channel_id, ad_reads: 0, episodes: new Set(), latest: "" };
  row.ad_reads += 1;
  row.episodes.add(x.media.video_id);
  if (x.media.published_at > row.latest) row.latest = x.media.published_at;
  shows.set(name, row);
}
return {
  brand: { id, name: entity?.name ?? e?.name ?? null, type: entity?.type ?? e?.type ?? null, assumed, why }, window, ad_reads_total: reads.length,
  shows: [...shows.values()].sort((a, b) => b.ad_reads - a.ad_reads).slice(0, 10).map(s => ({ ...s, episodes: s.episodes.size })),
  sample_read: reads[0] ? { said: reads[0].verbatim_quote, show: reads[0].media.source_channel?.name ?? null, date: reads[0].media.published_at, promo_code: reads[0].promo_code } : null,
};
```

## A good answer

- Names the brand or show it used, with its type and id, and any look-alike it set aside.
- Ranks sponsors (or shows) by ad reads and gives the counts, first and last seen dates, and the sponsor status.
- States the window and the as-of date, and that counts cover the shows Arcmira indexes.
- Quotes one ad read verbatim with its promo code when there is one, and links each name to the `page` the result carries.

## Traps

- `recommendations` can return `recommendations_not_enabled`. Explain the account-access limit and required tier reported by the API; a channel sponsor list does not answer which shows recommend a brand.
- An ad read is sponsored; an unpaid on-air endorsement is `kind: "organic"`. Do not mix them in one count.
- Page with `cursor` until `has_more` is false before you count reads; one page is at most 100 rows.

Docs: https://arcmira.com/docs/mcp-server

## After the answer

Monitors can follow what a research turn found, and each alert uses 25 credits from the account's plan, then its on-demand budget. The `company-watch` skill sets one up.

If anything was wrong, slow, or missing for the user, or they want a source or capability Arcmira lacks, send one arcmira_feedback.
