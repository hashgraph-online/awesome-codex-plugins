# SERP snapshot format (`rank-monitor --features`)

> **Script location.** If your host does not set `${CLAUDE_PLUGIN_ROOT}`, the scripts are in this plugin's `scripts/` folder, next to `skills/`. Run them with Python 3.10 or newer: `python`, or `python3` where `python` is not found (macOS, many Linux systems).

Search Console reports positions for a verified property, not the SERP-feature layout of each query. Any SERP API or rank tracker can export that layout. Save one export per check as a CSV file or a JSON array, then validate it:

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/serp-snapshot.py" --file snapshot.csv --brand-domain example.com
```

The script reads only the file you name. It makes no network request, reads no API key and contains no provider code, so the export can come from any tool. Exit 0 means every row is valid; exit 1 lists every bad row, marks the file `refused` and gives no summary (fix the export, do not use a partly valid file); exit 2 means the file could not be read.

## Columns

One row per query, country and language. Column names are case-insensitive; extra columns are ignored and listed in `ignored_columns`.

| Column | Required | Values |
|---|---|---|
| `query` | yes | the search query, as tracked |
| `gl` | no | 2-letter country code (`us`, `gb`, `in`) |
| `hl` | no | language code (`en`, `en-GB`, `pt-BR`) |
| `position` | no | the brand's organic position, a whole number of 1 or more; empty when the brand does not rank in the results checked |
| `ai_overview_present` | no | `true` / `false` |
| `ai_overview_cited` | no | `true` / `false`: the brand is cited in the AI Overview (only when one is present) |
| `paa_present` | no | `true` / `false`: a People Also Ask box appears |
| `featured_snippet_owner` | no | the domain that owns the featured snippet (a URL is reduced to its domain); empty when there is none |

Booleans accept `true`/`false`, `yes`/`no`, `y`/`n` and `1`/`0`. An empty boolean means the export did not report that feature, which is different from `false`. The same query in another country or language is a separate row; the same query, `gl` and `hl` twice is an error.

## Example (CSV)

```
query,gl,hl,position,ai_overview_present,ai_overview_cited,paa_present,featured_snippet_owner
best trail shoes,us,en,3,true,false,true,rival.com
trail shoe sizing,us,en,,true,true,false,example.com
waterproof trail shoes,gb,en-GB,12,false,,true,
```

## What the script returns

- `rows`: each row normalised (lower-case `gl`, `-` in `hl`, the snippet owner as a bare domain). With `--brand-domain`, each row also gets `brand_owns_featured_snippet` (the brand's domain or any subdomain of it).
- `summary` (only when every row is valid): queries, how many rank, AI Overviews present and citing the brand, People Also Ask boxes, featured snippets, and (with `--brand-domain`) snippets the brand owns.
- `errors`: every problem, each naming its row and column.

## How the skill uses it

Save each validated snapshot with the monitoring run. Diff it against the previous one for features gained or lost, AI Overview citations won or lost, and featured-snippet ownership changes. Say which queries' flags came from a snapshot file and which from a connected rank tracker or manual observation. A snapshot covers only the queries in it: do not extend its counts to queries it did not include.

Volume note: a monthly check of 40 queries is 40 rows, so 480 rows a year. Cost depends only on the provider you export from.
