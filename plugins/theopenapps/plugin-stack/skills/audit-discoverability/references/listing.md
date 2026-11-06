# Listing words

## Prompts (step 1)

Take them in this order until you have 5-10:

1. The repo's issues and discussions, support threads and the user's own words, quoted as written.
2. Competitors' starter prompts, from the fields below.
3. Prompts you draft. Count these.

Leave the plugin's own listing out as a source, because prompts taken from it always pass. Prompts already in `.agents/plugin-stack.md` count as drafted unless the file names where they came from.

With fewer than half sourced, the report says: `Coverage is circular: <d> of <n> prompts were drafted.`

## Competitors (step 1)

3-5 listings that do the same job, each confirmed by the user. Take them from `.agents/plugin-stack.md` or the user, or find them:

1. `listings_search query="<1-3 nouns>" limit=10`. Words match one at a time, so a whole sentence returns mostly noise, and the first row can be the wrong app. Check the names.
2. `tags_get tag=<topic tag from a good hit> store=<store> limit=20`.

## Fields (steps 1 and 3)

The full copy is only in `listings_versions ref=<ref> latest=true`. `listings_get` and `charts_get` rows carry `short_description` alone.

| Store | Fields |
|---|---|
| ChatGPT | `data.listing[-1].data.{display_name,short_description,keywords}`; `data.detail[-1].data.release.interface.{short_description,long_description,default_prompts,category}` |
| Claude | `data.listing[-1].data.{name,one_liner,summary,description,categories,tool_names}` |
| Cursor | `data.listing[-1].data.{name,description}`; `data.detail[-1].data.keywords` |

With no listing yet, read the same words from the repo's manifest or draft copy.

## Coverage (step 3)

For each prompt, write what it asks for: the task, the object and any product it names. Read the listing's name, subtitle, long description, keywords and starter prompts. Covered means the listing states that task on that object, in those words or a plain synonym; name the field that does. Missed means anything else, including a job the listing only implies.

Mark each competitor the same way, and name those that cover a prompt the plugin misses.

`listings_search query="<words>"` shows a keyword match in OpenApps' catalogue. It's not the store's search and not an assistant's search, so mark coverage from the listing's own words and name it a proxy.

Neither ChatGPT's nor Claude's docs say which fields their directory search reads, so a prompt covered only by `keywords` gets the note `keywords only`.

Report line: `Covered <k> of <n> target prompts (proxy: the listing's own words). <d> of <n> prompts were drafted.`
