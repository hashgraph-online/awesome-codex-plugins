# Location references

A location reference proves that a real place of a stated type, decade and region exists, and shows it from ground
level. It does not prove the feeling: that comes from your words and from `style-boards.md`. A frame alone does not
prove the place or the decade either: the record does.

Check provenance first. People spotted AI worst on natural and urban landscapes in one large study ([Roca et al.
2025](https://arxiv.org/abs/2507.18640), `reported`), so your eye is weakest here.

## Read it

In this order. A frame can show objects, materials, weather and wear. Only the record can show where and when.

1. **Record.** Are place and decade known from the source? "Gary, Indiana, 1974" passes, "Urban street" does not.
2. **Dated objects.** Does anything visible contradict the decade? An LED billboard on a 1974 street does.
3. **Weather and time of day.** Do they match the scene?
4. **Signage.** Does it fit the stated place and language? Do not guess the place from it.
5. **Lived-in.** Patched wall, mismatched chairs. Pristine and empty is a warning.

## The path

Feeling → building type + decade + region → Commons category → ground level.

1. **Name the feeling.** Aesthetics Wiki API or CARI, as shown in `style-boards.md`.
2. **Convert it.** "Late-night, forgotten, fluorescent" becomes `diner` + `1970s` + `New Jersey`. This is a hypothesis.
   No validated dictionary exists.
3. **Find it.** Search Commons categories and HABS for the type, then walk the category with `search.py commons-cat`. Follow
   sibling decades. Read the author field of good hits (below).
4. **Take the address or coordinates** from the record.
5. **Go to ground level.** Mapillary with a small bbox, Flickr with `lat`, `lon`, `radius`, `geo_context`, or a person
   in Street View.
6. **Check a film-tested version.** TheFilmMap, then movie-locations for one page.
7. **Tag it.** `feed` only if CC0 or public domain with no identifiable person. CC BY and BY-SA are `words` unless a person
   clears them. `look` for Street View.

| Feeling (`our proposal`) | Type + decade + region | Query that was run | What came back (`tested 2026-11-03`) |
|---|---|---|---|
| Late-night, forgotten, fluorescent | Diner, 1970s, New Jersey | Commons category `diners New Jersey`. Files `diner New Jersey filetype:bitmap -incategory:"AI-generated images"` | "Category:Diners in New Jersey". 154 files, including "Skyline Diner New Jersey 1978 strong contrast.jpg" (CC BY-SA 4.0, so `words`) |
| The last morning at a working port | Fishing port, Galicia, no decade in the brief | Commons category `fishing ports Galicia` | "Category:Dársena de Oza", "Category:Fishing boats in Cambados" |
| A lifetime in one room, small town | Classroom, 1970s, United States | Commons category `classrooms 1970s`. HABS `schoolhouse` | "Category:Classrooms in the 1970s" and sibling decades. 111, "Millbrook Schoolhouse, Millbrook, Warren County, NJ" |
| Working alone after closing | Garage, 1970s, United States | Commons categories `auto mechanics`, `gas stations 1970s`. HABS `garage` | "Category:Automobile repair shops". "Category:Gas stations in the United States photographed in the 1970s". 1,223, first three ranch garages, so refine by town or type |

## The Commons category pattern

Licence per file, and it does most of the conversion for you.

```text
Category:<Things> in <country> photographed in the <decade>   Gas stations in the United States photographed in the 1970s
Category:<Things> in the <decade>                             Classrooms in the 1970s
Category:<Things> in <place>                                  Fishing boats in Cambados, Diners in New Jersey
```

```bash
python3 -I "$S/search.py" commons "gas stations 1970s" --categories --log search_log.jsonl    # find the category
python3 -I "$S/search.py" commons-cat "Category:Diners in New Jersey" --log search_log.jsonl  # walk it
```

`commons-cat` returns files with author, date, licence, original URL and size, plus subcategories. This walk was the
best route of the ad cold run: real Lisbon lettering and tile, with everything in one call. Raw API, on
`https://commons.wikimedia.org/w/api.php`, `tested 2026-11-03`, with `format=json` on each:

```text
Search files        ?action=query&list=search&srnamespace=6&srlimit=5&srsearch=diner+New+Jersey+filetype%3Abitmap+-incategory%3A%22AI-generated+images%22
Read licence, date  ?action=query&titles=File:<name>&prop=imageinfo&iiprop=extmetadata|url
```

**Read the author field of good hits.** Institutions upload whole collections, so ask a local archive by name. In the cold run
`"Biblioteca de Arte" azulejos` returned 10, 9 opened, all azulejo documentation from the Gulbenkian Art Library ("No
restrictions" on the hits read). It turned up through one author field, too late to use. Not checked: Arquivo Municipal de
Lisboa, Museu Nacional do Azulejo, Europeana.

**Some places only a person can find.** The inside of an old Portuguese tile shop, the thing that person loved, did not
turn up in 24 queries and 7 walks. Say so, and write the links: Google Images, Pinterest, Street View at the shop's
address.

Traps caught in testing:

- A decade category may hold no files. "Gas stations in the United States photographed in the 1970s" returned nothing
  with `cmtype=file`. Its members are years: "photographed in 1972", 1973, 1976, 1977, 1979. Walk without `cmtype`.
- Categories drift. "Category:Diners in New Jersey" also holds plates of food ("Rt. 1 Special"), and "Category:Diners in
  the United States" holds "Category:IHOP". Read the titles.
- Read `LicenseShortName` and `DateTimeOriginal` in `extmetadata` per file. A category never clears a licence.
- About 10 fast calls got "You are making too many requests to the API", and Commons returned 429 after about 30 calls
  with 3 to 4 s gaps in the cold run, as did `upload.wikimedia.org` on a file. `search.py` paces Commons at 3 s across
  processes. On a 429, wait what `Retry-After` says, or 60 s, try once more, then stop using that source for this run.

## Search it

Ranked. Results `tested 2026-11-03` unless marked.

| Source | Exact route | What came back | Access | Verdict |
|---|---|---|---|---|
| [Commons categories](https://commons.wikimedia.org/w/api.php?action=query&list=search&srsearch=gas+stations+1970s&srnamespace=14&srlimit=6&format=json) | `srsearch=gas stations 1970s`, `srnamespace=14` | 22 categories, sibling decades 1930s to 1990s | `agent` | Best. The pattern above does this almost directly |
| [LoC HABS](https://www.loc.gov/collections/historic-american-buildings-landscapes-and-engineering-records/?q=gas+station&fo=json&c=5) | `/collections/historic-american-buildings-landscapes-and-engineering-records/?q=<word>&fo=json`, 60 s timeout | `gas station` 150, `garage` 1,223, `schoolhouse` 111, `fish house` 97, `motel` 31. Exact addresses: "C.F. Forbes Gas Station, 195 North Raymond Avenue, Pasadena" | `agent` | Best for American buildings. US only |
| [TheFilmMap MCP](https://thefilmmap.com/mcp) | `python3 -I "$S/mcp_call.py" https://thefilmmap.com/mcp what_was_filmed_here '{"place":"Budapest","limit":3}'`. Also `where_was_it_filmed`, `locations_near` | "Budapest" 100 productions, with coordinates. It warns: "Which scene was shot where is not recorded and must not be inferred." | `agent` | Good. Keyless. Never name a scene from it |
| [Mapillary](https://www.mapillary.com/developer/api-documentation) | `GET https://graph.mapillary.com/images?access_token=$TOKEN&fields=id,thumb_1024_url&bbox=w,s,e,n`. Bbox "must be smaller than 0.01 degrees square". Filters `start_captured_at`, `is_pano` | Not run, a token is needed. [Terms](https://www.mapillary.com/terms): CC BY-SA, no re-identification or unblurring | `token` | Best street imagery. `words` until a person checks its commercial limit |
| [Flickr geo](https://www.flickr.com/services/api/flickr.photos.search.html) | `lat`, `lon`, `radius` (max 32 km), `geo_context` (1 indoors, 2 outdoors) plus another filter. Docs: "Geo queries require some sort of limiting agent" | Not run, a key is needed. Without a limit "we return only photos added in the last 12 hours" | `token` | Good |
| [Socks Studio](https://socks-studio.com/wp-json/wp/v2/posts?search=house&per_page=3&_fields=title,link), [Hidden Architecture](https://hiddenarchitecture.net/wp-json/wp/v2/posts?search=concrete&per_page=3&_fields=title,link) | `/wp-json/wp/v2/posts?search=<word>&per_page=3&_fields=title,link` | "Communal Living under One Roof: Plank Houses of the Pacific"; "Zagreb Post-Stadium" | `agent` | Good for unusual architecture |
| [Accidentally Wes Anderson](https://accidentallywesanderson.com/wp-json/wp/v2/posts?search=diner&per_page=3&_fields=title,link) | Same REST route | `search=diner` 1 | `agent` | Narrow and symmetric by design. That one look only |
| [Prelinger](https://archive.org/advancedsearch.php?q=collection%3Aprelinger+AND+%28diner+OR+%22lunch+counter%22%29&fl%5B%5D=identifier&fl%5B%5D=title&fl%5B%5D=year&rows=6&output=json) | `collection:prelinger AND (diner OR "lunch counter")` on Internet Archive `advancedsearch.php` | 81. `(classroom OR schoolteacher)` 234, noisy, including "Choosing a Classroom Film" (1963). `licenseurl` empty on most | `agent` | Good for period motion and streets. Check each licence |
| [movie-locations](https://www.movie-locations.com/movies/p/Paris-Texas.php) | `/movies/<letter>/<Title>.php` | 200. Robots disallow ClaudeBot, `use=reference` | `agent`, one page at a person's request | One-off lookups only |
| [Shorpy](https://www.shorpy.com/search/node/diner) | `/search/node/diner` | 200, 123 node links, result titles not parsed | `person` | Good for a person |
| Person-only | [Street View](https://developers.google.com/maps/documentation/streetview/policies), [Atlas Obscura](https://www.atlasobscura.com/search?q=abandoned+motel), [Dezeen](https://www.dezeen.com/), [ArchDaily](https://www.archdaily.com/search/projects/text/gas%20station), [British Pathé](https://www.britishpathe.com/) | Terms, off-topic results or blocks | `person` | `look` only. Links in `links.md`, never a fetch |

Street View's policy says you must not "pre-fetch, index, store, or cache" its content (excerpt). A person pans, nobody
keeps a copy, and it never goes into a model. Never unblur or try to re-identify anyone in Mapillary.

## Queries

| Bad | Good | Evidence |
|---|---|---|
| `moody liminal diner night cinematic` | `Category:Diners in the United States`, subcategories "by state", "by manufacturer" | `tested 2026-11-03` on the good string; the bad one is a pattern to avoid |
| `abandoned motel` on Atlas Obscura | HABS `motel` | `tested 2026-11-03`: off-topic results against 31 with addresses, such as "Rio Motel, 4810 Ocean Avenue, Wildwood, Cape May County, NJ". Mapillary at that address not run |
| `retro gas station` | `Category:Gas stations in the United States photographed in the 1970s` | `tested 2026-11-03` on the good string |
| `fishing village` on Are.na | Commons `fishing ports Galicia` | `tested 2026-11-03`: 8 weak channels against named places |

Subject words work on archives and fail on boards. Keep place searches on archives.

## Code vs generated

- **Generated.** The reference must prove real geometry and period detail. The output is words for the prompt, plus a
  `feed` plate only when it is CC0 or public domain with no identifiable person. A generated location that passes as a
  real, named place may need a label in the EU: the deep-fake definition covers "places" ([Article
  50](https://artificialintelligenceact.eu/article/50/), `reported`).
- **Code-made.** Your film republishes any plate it shows, so the licence must cover that, per file. CC BY-SA means
  attribution and share-alike. The output is the record for each plate: file, licence, date, address.

## Worked examples

Strings run on 2026-11-03 unless marked.

**"A Tuesday-night mechanic."** HABS `garage` → 1,223; the first three are ranch garages, so refine. Commons
"Category:Automobile repair shops" and the 1970s gas station category. Person link: Street View at the address.

**A Lisbon roastery, tile on the walls, one cold run.** Commons category walks gave real Lisbon signs and tile. HABS/HAER
`interior tile` gave stacked stock in a working tile works, in the wrong country: keep it for the stacks and say so.

## Reject if

- Place and decade are not stated by the source, and the location must be a real, named place. Otherwise mark them unknown and
  keep it as mood (`words`).
- A visible object contradicts the decade.
- Signage has the wrong script or language for the stated place.
- Pristine, empty, no wear.
- An identifiable person is in a plate tagged `feed`. Retag it `words`.
- You kept a copy of a Street View image.
- A claim about which scene was shot where, when the only source is a filming-location list.

Universal rejects: `never.md`.

## Judge it

Location O1 to O5 in `judge.md`, a draft and off by default. O1 is a record, core only when the location must be a real, named
place. O2 to O5 go to the LLM.
