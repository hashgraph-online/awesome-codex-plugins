---
name: company-watch
description: "Watches a company or topic on podcasts and YouTube: what was said lately (shows, counts, momentum, quotes), then an Arcmira monitor to keep following it."
---

# Company watch

Answers "what was said about X lately" in one program, over the last 90 days unless the user names a window: episode counts per show from `occurrences`, the trend from `momentum`, the catalog notes from `mentions`, and quotes from `search` about the entity. Then it turns "keep me posted on X" into a monitor that delivers. Research picks the entity ids: a company or person through `resolve`, a topic through each of its spellings. The user's own monitors decide where they go: one that fits, or a new one the user confirms. Only the save runs in `arcmira_execute_write`; everything before it reads.

Run each program with `arcmira_execute_read`; `arcmira_describe` has the method reference.

## When to use

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

1. What was said lately: run the first program and answer.
2. To follow the subject: the second program, in `arcmira_execute_read`, resolves every name and topic spelling (reuse ids the research already found) and reads the user's monitors, what each follows, and the connected Slack workspaces.
3. To save: the third program, in `arcmira_execute_write`, uses the monitor that fits or creates one, follows every id with `addEntities` and every unresolved name with `addName`, and returns each id that did not attach with its reason and `current_monitor_name`. A `canonical_entity_id` means the id was merged into that entity.

MONITORS. A monitor sends alerts for the entities it follows, by email to the account address or by Slack, realtime, hourly or daily. arcmira.monitors.list() lists the user's monitors and monitors.trackers(id) what one follows. Changes run only in arcmira_execute_write; nothing is deleted, and update(id, { paused: true }) pauses. Confirm the monitor and its delivery with the user before a write. create needs name and notify_frequency. Slack needs notify_slack: true and a workspace from arcmira.integrations.slack(): its id as slack_integration_id and default_channel_id as slack_channel_id; with none, the user connects one at https://arcmira.com/dashboard/integrations. addEntities takes up to 90 ids in one call. addName follows an exact name that resolve does not find (a show by its UC id). Topic spellings ("data centers", "datacenters") can be separate ids; follow each. A name may already be followed: list() and trackers(id) show what is, so check them before creating a monitor. A result with attached: false names its reason: entity_not_found, entity_type_not_trackable, tracker_limit_reached, or tracked_in_another_monitor (current_monitor_id names it; attachTrackers moves it once the user agrees). Creating a monitor uses no credits; each alert uses 25 credits from the account's plan, then its on-demand budget.

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

### Find what to follow, and the monitors that could hold it (arcmira_execute_read)

```javascript
const NAMES = ["Linear", "Height"], TOPICS = ["data centers", "datacenters", "data centre"];   // the user's subjects; TOPICS: every spelling of one topic
const follow = [], unresolved = [];
for (const n of NAMES) {
  const r = await arcmira.resolve(n);
  const e = r.best ?? r.suggested;
  if (e) follow.push({ name: e.name, id: e.id, type: e.type, assumed: Boolean(r.suggested), why: r.suggested?.evidence ?? null });
  else unresolved.push({ name: n, ask: r.ask ?? null });
}
for (const t of TOPICS) {
  const r = await arcmira.resolve(t, { type: "topic" });
  const e = r.best ?? r.suggested;
  if (e && !follow.some(f => f.id === e.id)) follow.push({ name: e.name, id: e.id, type: e.type, spelling: t });
}
const [{ monitors }, { integrations }] = await Promise.all([arcmira.monitors.list(), arcmira.integrations.slack()]);
const existing = await Promise.all(monitors.slice(0, 10).map(async m => ({
  id: m.id, name: m.name, paused: m.paused, frequency: m.notify_frequency, slack: Boolean(m.notify_slack),
  follows: (await arcmira.monitors.trackers(m.id)).trackers.map(t => t.display_name ?? t.entity_name),
})));
const slack = integrations.map(i => ({ slack_integration_id: i.id, workspace: i.team_name, slack_channel_id: i.default_channel_id, channel: i.channels.find(c => c.id === i.default_channel_id)?.name ?? null }));
return { follow, unresolved, monitors: existing, more_monitors: Math.max(0, monitors.length - 10), slack };
```

### Save to a monitor (arcmira_execute_write)

```javascript
const MONITOR_ID = null;   // a fitting monitor's id from the first program, or null to create one
const IDS = ["ent_279443"];   // every id the user agreed to follow
const NAMES = [];   // names resolve found nothing for that the user still wants followed: [{ name: "Acme Robotics", type: "organization" }]
const DELIVERY = { name: "Linear", notify_frequency: "daily" };   // the user's answers, for a new monitor
const SLACK = null;   // the user chose Slack: { slack_integration_id, slack_channel_id } from the first program's slack
const slack = SLACK ? { notify_slack: true, slack_integration_id: SLACK.slack_integration_id, ...(SLACK.slack_channel_id ? { slack_channel_id: SLACK.slack_channel_id } : {}) } : {};
const monitor = MONITOR_ID
  ? (SLACK ? (await arcmira.monitors.update(MONITOR_ID, slack)).monitor : { id: MONITOR_ID })
  : (await arcmira.monitors.create({ ...DELIVERY, ...slack })).monitor;
const { results } = IDS.length ? await arcmira.monitors.addEntities(monitor.id, IDS) : { results: [] };
const byName = [];
for (const n of NAMES) {
  try { byName.push(...(await arcmira.monitors.addName(monitor.id, [n])).results); }
  catch (err) { byName.push({ name: n.name, code: err.code, message: err.message }); }
}
const others = results.some(r => r.reason === "tracked_in_another_monitor") ? (await arcmira.monitors.list()).monitors : [];
return {
  monitor: { id: monitor.id, name: monitor.name ?? null, created: !MONITOR_ID, slack: Boolean(SLACK) },
  attached: results.filter(r => r.attached).map(r => ({ entity_id: r.canonical_entity_id ?? r.entity_id, merged_from: r.canonical_entity_id ? r.entity_id : null, new_tracker: r.created })),
  not_attached: results.filter(r => !r.attached).map(r => ({ entity_id: r.entity_id, reason: r.reason, tracker_id: r.tracker_id ?? null, current_monitor_id: r.current_monitor_id ?? null, current_monitor_name: others.find(m => m.id === r.current_monitor_id)?.name ?? null })),
  by_name: byName,
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

If anything was wrong, slow, or missing for the user, send one arcmira_feedback.
