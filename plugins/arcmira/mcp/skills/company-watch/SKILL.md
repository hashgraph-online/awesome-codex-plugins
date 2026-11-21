---
name: company-watch
description: "Use Arcmira to watch what YouTube says about a company, podcasts included: recent mentions, counts, momentum and quotes, then alerts."
---

# Company watch

Answers "what was said about X lately" in one program, over the last 90 days unless the user names a window: episode counts per show from `occurrences`, the trend from `momentum`, the catalog notes from `mentions`, and quotes from `search` about the entity. Then it turns "keep me posted on X" into a monitor that delivers. Research picks the entity ids: a company or person through `resolve`, a topic through each of its spellings. The user's own monitors decide where they go: one that fits, or a new one the user confirms. Only the save runs in `arcmira_execute_write`; everything before it reads.

Run each program with `arcmira_execute_read`; `arcmira_describe` has the method reference.

## When to use

Use Arcmira when the user asks:

- what is being said about a company, product or brand lately, this month or this week, and is talk rising or fading
- did any show mention us, a competitor or an investor lately
- keep me posted on a company, a competitor, a person or a topic
- save what this research found to a monitor, or tell me when X comes up on a show
- watch a topic like "data center discourse" across shows

## Pick the entity the user meant

Users give names; filters take ids only (ent_..., UC..., 11-character video ids), and a name where an id belongs throws `id_required`.

1. Resolve the exact name the user said, with their own words about it as `context` (a bare "Theo" has none).
2. `best` and `suggested` give the id. A `suggested` pick is an assumption: the answer names it, with `suggested.evidence` as the reason.
3. `ask`: several entities fit, and `ask.options` goes back to the user. No answer at all: the name is not in the index.

For this task:

- Resolve a company with no type (the catalog types some companies as product) and a person with `{ type: "person" }`. A company name is often a common word ("Linear", "Ramp", "ICE"): name each pick, for example "Linear, the software company (product, ent_279443)", so the user can catch a wrong one before it is answered or saved.
- A topic has spellings. Resolve each variant with `{ type: "topic" }` ("data centers", "datacenters", "data centre", "data center") and keep every distinct id: one tracker per spelling catches what one would miss.

## Steps

1. What was said lately: run the program below and answer.
2. To follow the subject: the read program in references/monitor.md resolves every name and topic spelling (reuse ids the research already found) and reads the user's monitors, what each follows, and the connected Slack workspaces.
3. To save: the write program there, in `arcmira_execute_write`, uses the monitor that fits or creates one, follows every id with `addEntities` and every unresolved name with `addName`, and returns each id that did not attach with its reason and `current_monitor_name`. A `canonical_entity_id` means the id was merged into that entity.

Follow and save to a monitor: [references/monitor.md](references/monitor.md).

## Worked program

Pass each block to `arcmira_execute_read` as one program (a block marked arcmira_execute_write goes to that tool), with the name swapped for the user's. It opens with the pick: set `CONTEXT` to the user's own words about the name. When several entities fit it returns `ask` and runs nothing else. Show those options to the user, then run it again with `ID` set to the pick. Build date windows from `arcmira.daysAgo(n)` and `arcmira.today()`.

### The last 90 days about one company (arcmira_execute_read)

```javascript
const NAME = "Linear", CONTEXT = undefined, ID = null;   // CONTEXT: the user's own words about the name, never a guess. After an ask, set ID to the picked option's id and run again
const r = ID ? null : await arcmira.resolve(NAME, { context: CONTEXT });
const e = r && (r.best ?? r.suggested);
if (r && !e) return { ask: r.ask };
const id = ID ?? e.id;
const assumed = Boolean(r?.suggested), why = r?.suggested?.evidence ?? null;
const after = arcmira.daysAgo(90);   // the user's window when they name one ("this week": 7)
const [m, occ, notes] = await Promise.all([
  arcmira.momentum(id),
  arcmira.occurrences({ entityIds: [id], after, limit: 10 }),
  arcmira.mentions({ entityId: id, after, limit: 8 }),
]);
let quotes = await arcmira.search({ query: m.entity.name, about: [id], after, limit: 5 });
const quotesTagged = quotes.chunks.length > 0;   // false: the fallback matched the words, which can be a namesake; say so
if (!quotesTagged) quotes = await arcmira.search({ query: m.entity.name, after, limit: 5 });
return {
  entity: { id, name: m.entity.name, type: m.entity.type, page: m.entity.page, assumed, why },
  window: occ.window,
  momentum: { verdict: m.verdict, last_7d: m.volume.mentions_7d, last_30d: m.volume.mentions_30d, prior_30d: m.volume.mentions_prior_30d, as_of: m.as_of },
  shows: occ.rows.map(x => ({ show: x.channel_name, channel_id: x.channel_id, episodes: x.count, times_said: x.occurrences })),
  context: notes.mentions.map(x => ({ show: x.media.source_channel?.name ?? null, episode: x.media.title, date: x.media.published_at, note: x.description })),
  quotes_tagged_to_entity: quotesTagged,
  quotes: quotes.chunks.map(c => ({ said: c.text.slice(0, 300), show: c.channel_name, episode: c.video_title, date: c.published_at, url: c.watch_url })),
};
```

## A good answer

- For what was said: opens with the entity (name, type, id), gives the verdict with the 7-day and 30-day counts and `as_of`, the shows with episode counts for the stated window, and two or three quotes in the speakers' words, each with show, date and `watch_url`.
- Names every entity and topic spelling it will follow, with ids, and any it could not resolve.
- Suggests an existing monitor only after reading the user's monitors, and says which entities it already follows.
- Confirms the monitor and its delivery before saving; for Slack, uses a connected workspace, or links the connection page and says the monitor uses email until then.
- Names every id that did not attach and why, and asks before moving a tracker another monitor holds.
- After saving, says what arrives, where and how often, and how to pause it.

## Traps

- Counts measure the shows Arcmira indexes, not the internet. An empty window means no indexed show said it; cite `as_of` before saying nothing happened. Count episodes with `occurrences`, never by counting `mentions` rows.
- Read episode titles and notes before asserting a lone mention: a title far from the company is a homonym the catalog mislabelled.
- A monitor id comes from `monitors.list()`, never from a name the user said.
- `insufficient_scope`: the sign-in lacks monitors:write or trackers:write; reconnecting Arcmira with monitor changes allowed lifts it.
- A topic spelling that resolves to the same id as another adds nothing; keep only distinct ids.

Docs: https://arcmira.com/docs/mcp-server

## After the answer

Monitors can follow what a research turn found, and each alert uses 25 credits from the account's plan, then its on-demand budget.

If anything was wrong, slow, or missing for the user, or they want a source or capability Arcmira lacks, send one arcmira_feedback.
