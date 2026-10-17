---
name: cron-and-intervals
description: Use when building a val that runs on a schedule — periodic jobs, recurring tasks, polling, cron jobs, monitoring, alerting. Covers the interval handler signature, cron expressions, the UTC timezone constraint, and the `lastRunAt` pattern for detecting new items since the previous run.
triggers: [cron, interval, scheduled, schedule, recurring, periodic, timer, poll, polling, job, daily, hourly]
---

# Cron / Interval Vals

Interval vals (`fileType: "interval"`) run on a recurring schedule defined by a cron expression. Use them for polling external APIs, sending reminders, running cleanups, generating reports, or any work that should happen on a clock rather than in response to a request.

## Basic handler

```ts
// Learn more: https://docs.val.town/vals/cron/
export default async function (interval: Interval) {
  // interval.lastRunAt: Date | undefined
  console.log(interval);
}
```

The file must have an `export` — `export default` for the handler.

## Timezone

**Cron expressions run in UTC.** Convert any human-readable schedule (e.g. "9am Eastern") to UTC before writing the cron expression. Daylight savings is not handled — pick a UTC time that's close enough year-round.

## The `lastRunAt` pattern

`interval.lastRunAt` is the timestamp of the previous successful run (or `undefined` on the first run). Use it to fetch only items created since the last run, instead of re-scanning everything:

```ts
export default async function (interval: Interval) {
  const since = interval.lastRunAt ?? new Date(Date.now() - 24 * 60 * 60 * 1000);
  const newItems = await fetchItemsSince(since);
  for (const item of newItems) {
    await handle(item);
  }
}
```

This makes the val idempotent against missed runs and avoids reprocessing.

## Reading and updating the schedule

- `read_interval_settings` — fetch the current cron expression and active state of an interval file.
- `write_interval_settings` — change the cron expression or pause/resume an interval.

## When to skip a template

For simple scheduled jobs, create a new val with a single `interval`-type file directly — no template needed. Templates are for more complex shapes (dashboards, AI agents, webhook + UI combos).

## Verifying changes

After editing an interval val, use `run_file` to invoke the handler manually instead of waiting for the next scheduled run.
