# After it's live

## Countries

`listings_get ref=<ref>` gives `data.app.availability[].{region,status,as_of,reason}`: `listed` or `not_listed` per country. Only rows with `reason: complete` count. A country with no row, or one `meta.coverage` names as dark, is unknown, not unlisted.

Signed out, availability has the United States alone. The reach tags on the same answer still say which side the app is on, and they're derived from every country: `worldwide` is listed in every country with data, `geo-restricted` is missing in some. With either tag, print it and name signing in once to get the countries.

Don't wait for missing countries to fill in by themselves: many new apps carry `geo-restricted`, and some stay listed in very few countries. The store doesn't publish why an app is missing in a country, so name the countries and leave the reason out.

## What gets apps delisted

```
tags_get tag=delisted store=chatgpt limit=200
```

`data.tag.n` is how many ChatGPT apps are delisted now, and `data.related[].{id,label,n,lift}` lists the tags they carry more often than apps at large: a lift of 1.5 means half again as often. Set the app's job tags, from `listings_get`, against that list, and print the lift and `n` of each one it shares. A lift of 1.5 or more with n of 30 or more is a pattern. The same lift with n under 30 is a lean. A lift under 1.5 is no signal. Word the app's risk only as pattern, lean or no signal, with no level such as low or moderate. Delisted rows lose their category, so `category` is empty on them: match by tag.

Each row's `mcp_status` is the server's status now. Count `error`, `dead` and `blocked` among the delisted rows, then the store's share: `tags_get tag=mcp-down store=chatgpt limit=1` gives `data.tag.n`, every ChatGPT app whose server is down, blocked or erroring, and `stores_get` the store's size. A down server can follow the delisting as easily as cause it, so word it as company, not cause.

Then the app's own server: `mcp_toolset_get app=<ref>` gives `data.servers[].{url,status,checked_at}`. Print `checked_at`, because it's the last check, and `null` means not checked yet. No servers is a finding on its own: OpenApps found no MCP URL for the listing.

## Whether they come back

```
changes_list store=chatgpt types=delisted since=-90d limit=200
```

Each event has `t`, `app` and `before.listed_at`, the last day it was seen listed. An app is back when it's no longer among the `tags_get tag=delisted` rows, or `listings_get` shows a `listed` country after the event's `t`. Count the events and the returns, and print the window from the earliest event's `t`, because `data.since` can start before OpenApps recorded any.

Signed out this answer holds back every event outside a chart's top 100 and starts 7 days back, so it can come back empty with `data.held` above zero: print `Degraded: delistings outside the top 100 need a free account` and use the tag read alone. Returns have been rare, so don't plan on one. Run the same read with `store=claude` for a Claude app.

## Your app was delisted or rejected

```
changes_list store=chatgpt apps=<ref> types=delisted,mcp_status_change,toolset_change,listing_change since=-30d
```

Passing `apps` reads the app's own events on every plan. Put them in date order with the server's `status` and `checked_at`, so the user sees what changed before the delisting. `mcp_status_change` can return no rows, so take the status from `mcp_toolset_get` and don't read an empty answer as a healthy server.

Then check what the store reviews, in this order: the server answers `tools/list` from a client with no stored credentials; sign-in works in a clean browser session; the tools still match what the listing promises. Name what you ran and what it returned. The store's own email, if any, decides: hand its reasons to `submit-plugin`.
