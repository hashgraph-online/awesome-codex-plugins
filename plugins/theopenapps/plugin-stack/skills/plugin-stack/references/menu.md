# Menu

If the file names competitors, first run `changes_list store=<store> apps=<refs> since=-7d limit=20` once per store. Skip icon and url changes, which are often re-hosted files or trailing slashes. Any other event earns `watch-competitors` a place in the picks, whatever Runs says. Cite the event and its date.

Take the first two or three rows that apply. Fewer than two apply: add the skill with the oldest line under Runs.

| State | Suggest |
|---|---|
| Submitted and not live yet, or delisted, no `track-launch` line in 7 days | `track-launch` |
| Nothing built yet, or no category picked, no `find-opening` line | `find-opening` |
| No listing, no `submit-plugin` line under Runs | `submit-plugin` |
| Live less than 30 days, no `track-launch` line | `track-launch` |
| Live, no `optimize-listing` line in 30 days | `optimize-listing` |
| No `audit-discoverability` line in 30 days | `audit-discoverability` |
| Widgets in the repo or a store that shows them, no `design-widgets` line | `design-widgets` |
| No `watch-competitors` line in 7 days | `watch-competitors` |

A suggested skill missing from your skills: give `npx skills add theopenapps/plugin-stack --skill <name>` in place of running it. Once the user picks, invoke that skill by name.
