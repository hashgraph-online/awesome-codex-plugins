# Follow and save to a monitor

MONITORS. A monitor sends alerts for the entities it follows, by email to the account address or by Slack, realtime, hourly or daily. arcmira.monitors.list() lists the user's monitors, monitors.trackers(id) what one follows and monitors.alerts(id) the alerts it sent, each with the video_id to read. Changes run only in arcmira_execute_write; nothing is deleted, and update(id, { paused: true }) pauses. Confirm the monitor and its delivery with the user before a write. create needs name and notify_frequency. Slack needs notify_slack: true and a workspace from arcmira.integrations.slack(): its id as slack_integration_id and default_channel_id as slack_channel_id; with none, the user connects one at https://arcmira.com/dashboard/integrations. addEntities takes up to 90 ids in one call. addName follows an exact name that resolve does not find (a show by its UC id). Topic spellings ("data centers", "datacenters") can be separate ids; follow each. A name may already be followed: list() and trackers(id) show what is, so check them before creating a monitor. A result with attached: false names its reason: entity_not_found, entity_type_not_trackable, tracker_limit_reached, or tracked_in_another_monitor (current_monitor_id names it; attachTrackers moves it once the user agrees). Creating a monitor uses no credits; each alert uses 25 credits from the account's plan, then its on-demand budget.

Pass each block as one program to the tool its title names, with the names swapped for the user's.

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
