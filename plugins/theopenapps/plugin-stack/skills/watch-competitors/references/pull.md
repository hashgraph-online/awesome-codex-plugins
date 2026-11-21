Window: from the date of the last `watch-competitors` line under Runs, else 7 days back. Signed out the reach is 7 days, with an account 30, on Pro everything, with chart events to 90. Read `data.since` on each `changes_list` answer. If it's later than the date you asked for, history stopped there: say "covers from <data.since>, not since last run".

Call `listings_ranks_current`, `listings_metrics` and `mcp_toolset_get` once per ref. Rank series come one listing at a time and you compare them yourself, except on Pro (`meta.tier` is `plus`), where one call takes them all. `changes_list store=<store> apps=<refs> since=<window>` takes all of a store's refs in one call, and its `listing_change` rows carry the before and after copy.

## Calls

`<window>` is the date from the Runs line. With no Runs line, use `-7d` without asking.

Group the refs by store and make this call once per store, following `meta.next_cursor` with `cursor`. Its `featuring_enter` and `featuring_exit` rows are the featuring record.

```
changes_list store=<store> apps=<refs> since=<window> types=listing_change,rank_move,chart_enter,chart_exit,featuring_enter,featuring_exit,toolset_change,mcp_status_change,metric_change,delisted limit=20
```

Then per ref:

| Call | Read |
|---|---|
| `listings_get ref=<ref>` | `data.app.url`: the plugin's link. Skip it for a ref whose `url` you hold from a search or `changes_list` row |
| `listings_ranks_current ref=<ref>` | `data.charts[].{chart,title,primary,url}`: today's position on each chart, and `url` is the chart's |
| `listings_ranks_history ref=<ref> from=<window>` | `data.series[].{chart,points[].{t,position}}`: position at the window's start and end. On Pro make one call per store with `apps=<the other refs>`, and `data.series[].app` says whose each is |
| `listings_metrics ref=<ref>` | Claude and Cursor refs only: `data.metrics[].{name,basis,value,points}` |
| `mcp_toolset_get app=<ref> diff_from=<window>` | `data.servers[].{status,checked_at,diff.{added,removed,changed}}` |
| `listings_versions ref=<ref>` | Competitors only: the records named under Copy |

Each ref costs several calls, so keep the list short on a low plan.

## Ranks

For each chart two or more refs share, sort them by position at the window's start and at its end. A ref gains when it passes another ref in the set. A chart with one ref gives a position and no comparison, and each store's ranks stand alone.

Raw position moves with the whole list. When one app jumps, the others slide a place while their order among themselves holds.

Date a move from its `rank_move` row (`t`, `chart`, `before`, `after`), or from the series point where no row exists.

## Metrics

ChatGPT publishes none, so print a dash and estimate nothing. Not every Claude listing has installs: print what the listing has with its `basis`, and compare two refs only on a metric they share. Take the change over the window from `points`, because `prev` is only the value the latest one replaced.

## Tools

Print `checked_at` beside each toolset, because a snapshot can predate the window. It's the last check, changed or not, and `null` means not checked yet. Word an empty diff as "no tool change seen, checked <date>".

For a competitor known only by its server URL, use `mcp_toolset_get server=<url> diff_from=<window>` and state the gaps in ranks, metrics and featuring.

## Copy

Copy edits are `description`, `keywords` and `name`, with before and after. On ChatGPT `description` is the 30-character subtitle. On Pro a copy change older than 7 days also has `rank_impact.{chart,before,after}`: print it as timing beside the change, never as its effect.

Report `publisher` changes too, because they can mean a sale or a move to another company. State the change itself, because a sale and a tidied company name arrive as the same event.

Report `category` when the values differ as a set. Hide `icon` and `url` changes unless the user asks, since ChatGPT icon ids change with no visible edit. Some `category` events only reorder the array, and some `url` events are a trailing slash.

Long descriptions and starter prompts raise no events. For each competitor, diff the records in `listings_versions ref=<ref>`: on ChatGPT `data.detail[].data.release.interface.{long_description,default_prompts}`, on Claude and Cursor `data.listing[].data.description`. Going oldest first, a record with `seen_since` inside the window whose fields differ from the record before it is a rewrite. A new record can leave these fields untouched, so compare the fields.

## The table

One row per ref: the plugin linked by its own `url`, not the chart's; its position on the chart most of the set shares, as of `meta.as_of`; its position there at the window's start; metric with basis, or a dash; featuring entered or left, with dates; tools added and removed, with `checked_at`. Today's positions are the dated baseline for the next run.
