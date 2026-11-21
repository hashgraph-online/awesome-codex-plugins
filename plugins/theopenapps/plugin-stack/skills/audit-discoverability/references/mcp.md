# MCP

The server is `https://theopenapps.com/mcp`. To sign in, the user connects `https://theopenapps.com/mcp/account` in its place.

| Operation | Tool |
|---|---|
| `changes_list`, `charts_get`, `listings_search`, `market_get`, `mcp_toolset_get`, `new_list`, `stores_get`, `tags_get` | The same name, with the same parameters |
| `listings_get`, `listings_metrics`, `listings_ranks_current`, `listings_tools` | `listings_profile` with `apps=[<ref>]`; one call covers all four |
| `listings_ranks_history` | None: date moves from the `rank_move` rows of `changes_list` |
| `listings_versions latest=true`, `listings_widgets` | `listings_copy app=<ref>` |
| `charts_regions_get`, `listings_list`, `tags_tree`, older `listings_versions` records | None |

`listings_profile` answers with `data.profiles[].{app,ranks,metrics,tools}`, so the `listings_get` fields a skill names are under `app`, and its `data.charts`, `data.metrics` and `data.servers` paths are under `ranks`, `metrics` and `tools`.

`listings_copy` answers with the same fields on every store: `data.copy.{name,subtitle,description,keywords,categories,prompts,capabilities,tools}`, and `data.widgets[].{tool,title,image}`. Where a skill names a `listings_versions` path for current copy, read these instead.

With no tool for an operation, call it through `references/api.md` if you can fetch a URL. Otherwise add `Degraded: <operation> isn't on the MCP server, so <what is missing>`. A rewrite of a long description or starter prompts needs older `listings_versions` records.

`stores_get` ends with `account:`, the plan you're reading at, and any answer adds a `budget:` line once little is left.

## Show it

When `show` is in your tool list, end a chart, list or app answer with one `show` call, which draws the widget in the chat: `show tool=charts_get arguments={store,chart,limit}`. A `next: show` line in an answer gives the arguments. The host may ask the user to allow it. It draws for the user and adds no data, so read the rows first.

## Output

Text answers hold a few columns, plus lines for the date, the plan and any cut. Set `response_format=detailed` when a skill names a field or path: `structuredContent` then holds the whole `{ data, meta }`. A long answer is trimmed with a `next_cursor`, so pass it as `cursor`.
