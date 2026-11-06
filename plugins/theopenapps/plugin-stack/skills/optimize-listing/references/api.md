# API

The base URL is `https://theopenapps.com/v1`. Every read is a GET and works without a key. To read at the user's plan, send `Authorization: Bearer <key>`, using a developer key from their OpenApps account.

| Operation | Path |
|---|---|
| `changes_list` | `/changes` |
| `charts_get` | `/charts/{store}/{chart}` |
| `charts_regions_get` | `/charts/{store}/{chart}/regions` |
| `listings_search` | `/listings` |
| `listings_list` | `/listings/list` |
| `listings_get` | `/listings/{store}/{id}` |
| `listings_metrics`, `_tools`, `_versions`, `_widgets` | `/listings/{store}/{id}/metrics`, and so on |
| `listings_ranks_current` | `/listings/{store}/{id}/ranks/current` |
| `listings_ranks_history` | `/listings/{store}/{id}/ranks` |
| `market_get` | `/market` |
| `mcp_toolset_get` | `/mcp/toolsets` |
| `new_list` | `/new` |
| `stores_get` | `/stores` |
| `tags_get` | `/tags/{tag}` |
| `tags_tree` | `/tags` |

A ref fills `{store}/{id}`: `chatgpt:kiwi-com` is `/listings/chatgpt/kiwi-com`. Every other parameter is a query string, such as `/changes?store=chatgpt&since=-7d&limit=20`. For the rest, read one path from `/v1/openapi.json`, which is about 190 KB in all.

Answers are always the whole JSON, about ten times the size of the rows a list needs, so keep `limit` small.

A cut returns 200. Not found is 404, budget spent is 429 and busy is 503. The `x-openapps-budget` header says what's left: `calls-hour=264, calls-day=894, rows-day=4470`.
