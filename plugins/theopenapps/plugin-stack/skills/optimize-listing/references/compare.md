# Comparing a listing

## Finding the listing

`listings_search` matches single words, so the first row is often another plugin. Accept a row as the user's own only when its `name` matches exactly. Its `linked` holds the same plugin's refs in other stores.

## Choosing competitors

Competitors the user named, or that `.agents/plugin-stack.md` lists, skip this search.

Pick 3-5 by job, not category. Take the job tag from a good `listings_search` hit, then `tags_get tag=<tag> store=<store> limit=20`; the rows are in `data.top`. Search with 1-3 nouns from what the plugin does (`listings_search query="<noun>" limit=10`), because a whole sentence pulls noise. Job tags come first in a row's `tags`, ahead of the `for-*`, `cap-*` and `kind-*` entries. The user confirms the pick.

Add the category top only when the category is under 200 apps. The size is `data.total` in `charts_get store=<store> chart=<chart> limit=20`, and the store file names the charts.

Report rank as position of `data.total`, read fresh each run. The position is the last point of each series in `listings_ranks_history ref=<ref>`, and on Pro (`meta.tier` is `plus`) one call with `apps=<up to 9 other refs>` reads the whole set. Totals move fast.

## Reading copy

Read copy with `listings_versions ref=<ref> latest=true`, last array element. `listings_get` and `charts_get` give only the subtitle; their `listing` is `{}`. Budget one `versions` call per competitor.

| Listing | Paths |
|---|---|
| ChatGPT | `data.listing[-1].data.{display_name,keywords}`; `data.detail[-1].data.release.interface.{short_description,long_description,default_prompts,category,capabilities,screenshot_urls}`; `data.detail[-1].data.release.skills` |
| Claude connector | `data.listing[-1].data.{name,one_liner,summary,description,categories,tool_names,verified_tier}` |
| Claude plugin | `data.listing[-1].data.{name,summary,description,taxonomy,verified_tier}` |
| Cursor Marketplace | `data.listing[-1].data.{displayName,description,curatedCategoryKeys,tags}` |
| cursor.directory | `data.listing[-1].data.{name,description}`; `data.detail[-1].data.{keywords,plugin_components}` |

## Reading rewrites

There is no category filter and events have no category field. Run `changes_list store=<store> types=listing_change since=-7d apps=<up to 10 refs>`, one call per 10 of the competitors and chart rows. Keep `field` in description, keywords, name, category. Drop icon, url and publisher. Drop edits that differ only by case, a trailing slash or array order. On ChatGPT `description` is the 30-character subtitle.

Long descriptions and starter prompts never appear as events: to see them, diff `detail` records from `listings_versions`.

An empty result is normal, so say so.

If the competitors show no rewrites, page `changes_list store=<store> types=listing_change since=-7d` with `cursor` and keep events whose `best.chart` or `tags` match. `best.chart` reads `category:featured` for Popular apps and `popularity` on Claude, so match tags there. State how many events you read.

Quote each rewrite's `before`, `after` and `t` with its `url`. A rewrite, the plugin's own included, shows what someone chose to say and nothing about whether it worked, so rank moves around it stay out of the verdict.

## Giving a verdict

Each row of the store file's table is one field. Put the plugin's value beside each competitor's, then mark the field `keep` or `change` and name the listings behind the verdict.

Mark `change` when:

- the value breaks the store's limit or preflight
- the copy leaves out the job a target prompt asks for, or claims a job the plugin doesn't do
- a word from a target prompt appears in competitors' copy, the plugin can honor it, and the plugin's copy lacks it (a keyword gap)
- a target word from words.md is missing from the field the store file places it in
- competitors with the same job sit in another category, and the plugin fits there too

Everything else is `keep`. A field the store doesn't show can't change what a reader sees, so it stays unless a rule fails.

Hold each `change` to the rules above, even when every top app fills the field. Show the counter-example from the user's own competitors when one exists.

Target prompts come from the user's words, issues or support threads first, then competitors' starter prompts. Prompts drawn from the plugin's own listing make the gap check circular. Say how many you drafted yourself.
