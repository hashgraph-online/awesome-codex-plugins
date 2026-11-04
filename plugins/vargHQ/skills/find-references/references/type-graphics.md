# Type and graphics references

A type reference proves that a real designer made a real thing with this typeface for this audience and year. A pretty
specimen proves nothing about use. A graphics reference proves a system, shown across several items, so prefer manuals and
identity sets to a single logo.

## Read it

Five questions, in this order. A frame can show case, serif class, width, weight and hierarchy. Only a record can name the
typeface, so never take a name from a model's guess. If no source names it, keep the classes and leave the name unknown.
Lettered posters often name no typeface: unknown is the normal outcome there, and no failure.

1. Is the typeface named and credited?
2. Is there a year?
3. Is it a photo or scan of a real object, not a mockup?
4. Does it match the format? A poster does not prove a lower third.
5. Is there hierarchy, or only one big word?

## Fonts In Use: numbered paths only

> **`/search` is person-only. Never fetch `/search` or `/search/advanced`.** [Robots](https://fontsinuse.com/robots.txt) write
> `Disallow /search` without a colon, so honour the intent. To search by word, put
> `https://fontsinuse.com/search?terms=<words>` in `links.md` for a person to open.

Everything below is `agent`, at a paced rate: ClaudeBot gets a crawl delay of 1 and `*` gets 10. GPTBot is disallowed
from `/`, so an agent fetching under that name hands over links. The terms pages returned 500, so they stay unread.
Pictures are others' work, so tag them `words`. `tested 2026-11-03`: All 35,008, Staff Picks 6,402.

| Path | Pattern | IDs that work |
|---|---|---|
| Format | `/in/2/formats/{id}/{slug}` | [film-video 15](https://fontsinuse.com/in/2/formats/15/film-video) (1,192 uses, 249 staff picks), posters-flyers 12 (6,213), branding-identity 9 (9,288), books 6 (7,126), packaging 4, advertising 5, album-art 72, ephemera 73, magazines-periodicals 11, signs 7, social-media 59, web 3 |
| Topic | `/in/1/topics/{id}/{slug}` | film-and-television 70, music 43, fashion-apparel 24, technology 32, food-beverage 30, sports 42, activism 41 |
| Typeface | `/typefaces/{id}/{slug}` | `/typefaces/76/akzidenz-grotesk`, `/typefaces/65/adobe-caslon`, `/typefaces/1297/aktiv-grotesk` |
| Tag | `/tags/{id}/{slug}` | `/tags/242/science-fiction`, `/tags/4673/b-movies` |
| Set | `/sets/{id}/{slug}` | `/sets/684/1970s`, `/sets/5784/retro-futurism`, `/sets/7292/eurostile-1` |
| Use | `/uses/{id}/{slug}` | [`/uses/46227/the-terminator-1984-movie-logo-and-opening-cr`](https://fontsinuse.com/uses/46227/the-terminator-1984-movie-logo-and-opening-cr) |
| Feed | Append `.rss` | `/in/2/formats/12/posters-flyers.rss` |

- **The ID decides the page.** `/typefaces/13/helvetica` opened Farao FTN. Take IDs from a page's sidebar. Never guess one.
- **These fail:** `/formats` and `/topics` 500, `/uses?terms=format:film-tv` 500.
- **There is no decade filter, no combined topic and format URL, and no sort URL.**
- **For a combination, use a web search limited to the domain.** `Eurostile science fiction film titles 1970s` with
  `allowed_domains: fontsinuse.com` returned the science-fiction tag, the Eurostile and 1970s sets, and uses such as
  [Solaris (1972) Polish poster](https://fontsinuse.com/uses/46111/solaris-1972-polish-movie-poster) (Disco),
  [The Terminator](https://fontsinuse.com/uses/46227/the-terminator-1984-movie-logo-and-opening-cr) (Eurostile) and
  [Star Wars crawl](https://fontsinuse.com/uses/49364/star-wars-opening-crawl-and-titles) (Trade Gothic Bold No. 2).

## Search it

What came back is `tested 2026-11-03`. All of it is inspiration: `words`, or `look` where a person views it.

| Source | Exact route | What came back | Access | Verdict |
|---|---|---|---|---|
| Fonts In Use | Above | 1,192 film and video uses | `agent`; `/search` is `person` | Best. Typeface, year and real format in one record |
| [Art of the Title](https://www.artofthetitle.com/style/1970s/) | `/style/{slug}/`, `/title/{slug}/`, `/designer/{slug}/`, `/search.do?q=kinetic` | `live-action` 553, `1960s` 135, `1970s` 92, `stop-motion` 43, `hand-lettering` 8. `search.do` 13 title links. 404: `kinetic-typography`, `typography`, `animated`, `collage`, `minimal`, `/search/?q=` | `agent` | Best for title design. No typeface data, so pair with Fonts In Use |
| [Poster House](https://collection.posterhouse.org/wp-json/wp/v2/poster?keyword=12674&decade=17431&per_page=3&_fields=title,link) | REST `poster?keyword=12674&decade=17431`, `search=`, `country=`. Get a keyword's ID from [`/wp/v2/keyword?search=railway`](https://collection.posterhouse.org/wp-json/wp/v2/keyword?search=railway&_fields=id,name,count) | `x-wp-total: 343` film posters from the 1970s. `railway` is keyword 12702, count 99, and with `country=12842` gives 1, where `search=railway&country=12842` gives 0. Records hold no image, so open `link`. Terms unread | `agent` | Best open poster index. Filter by keyword ID, not `search=` |
| [Commons category of a genre's posters](https://commons.wikimedia.org/wiki/Category:SBB_Historic_-_Plakate) | `search.py commons-cat "Category:SBB Historic - Plakate"`. Find names with `search.py commons "Swiss railway posters" --categories` | 48 files, mostly 1880s to 1930s, 47 CC0, master TIFs, author and date in one call. Fonts In Use returned 0 on SBB, twice (cold run on a coded film) | `agent` | Best when the love is a genre of posters. Records name no typeface: classes only |
| [Internet Archive](https://archive.org/advancedsearch.php?q=identifier%3ALFAID%2A&fl[]=identifier&fl[]=title&rows=60&output=json) | `identifier:LFAID*`; `identifier:lfatype*`; `title:"graphic standards manual"` | 54 manuals (Mobil, Air Canada, IBM); 280 specimens; 9. Many `stream_only`: a person views them, nobody downloads | `agent` for metadata, `person` for pages | Best way in while [Letterform Archive Online](https://oa.letterformarchive.org/) is offline |
| [Typeset In The Future](https://typesetinthefuture.com/2016/06/19/bladerunner/) | `/YYYY/MM/DD/slug/` | Film-by-film type study | `agent` | Best for sci-fi |
| [People's Graphic Design Archive](https://peoplesgdarchive.org/?order=artwork-date), [Logobook](https://logobook.com/?s=bird) | `/?order=artwork-date`; `/?s=`, `/nature/birds/` | Poster 2,876 items; `?s=bird` 58 on page. Logobook shows no years | `agent` | Good |
| Person-only | [Ads of the World](http://www.adsoftheworld.com/robots.txt), [D&AD search](https://www.dandad.org/en/d-ad-awards-archive) (`/search/` ruled out by robots; `/work/d-ad-awards-archive` reads as text, see `motion.md`) | Never fetch | `person`, `links.md` | Links only |

Traps caught in testing:

- Keep the phrase and the field. `title:(type specimen)` drew in biology papers, and `subject:"type specimen"` (460) let one
  through as well. `identifier:lfatype*` stayed on specimens in the hits we read.
- Openverse `graphic standards manual` returned 27, first a NASA 1975 manual marked PDM by a Flickr user. That mark is the
  uploader's own statement. `design manual 1970` returned 26, led by an Olivetti typewriter.
- An open licence on a logo file grants no trademark use. Simple Icons warns that CC0 on the project does not "imply
  that all icons within the project are also CC0"
  ([disclaimer](https://raw.githubusercontent.com/simple-icons/simple-icons/develop/DISCLAIMER.md)).

## Genre names beat mood words

Pick a font by genre name, not by feeling. In the [Google Fonts tag
CSV](https://raw.githubusercontent.com/google/fonts/main/tags/all/families.csv) (34,354 rows, 74 tags) the mood tag
returns costume fonts and the genre tags return something specific.

| Tag | Rows | What the command below prints, `tested 2026-11-03` |
|---|---|---|
| `/Expressive/Vintage` (mood) | 1,884 | Jim Nightshade, Tangerine, Smokum, Monsieur La Doulaise, Mea Culpa, Luxurious Script, Cinzel, Uncial Antiqua. A noisy set |
| `/Theme/Woodtype` | 40 | Rye, Rubik Dirt, Gravitas One, Arbutus, Sancreek, Notable, Asset, Plaster |
| `/Slab/Clarendon` | 21 | Special Elite, Pridi, Orelega One, Moul, Montagu Slab, Crete Round, Besley, Ultra |
| `/Theme/Techno` | 105 | Zen Dots, WDXL Lubrifont TC, WDXL Lubrifont SC, WDXL Lubrifont JP N, Turret Road, Syne Mono, Space Mono, Space Grotesk |
| `/Theme/Distressed` | 61 | Special Elite, Rubik Lines, Rubik Iso, Rubik Glitch Pop, Rubik Gemstones, Rubik Distressed, Rubik Dirt, Road Rage |
| `/Sans/Grotesque` | 118 | Strichpunkt Sans, Staatliches, Squada One, Special Gothic Expanded One, Special Gothic Condensed One, Special Gothic, Six Caps, Shippori Antique B1. Noisy: display faces in the top tie |
| `/Sans/Neo Grotesque` | 126 | Zalando Sans SemiExpanded, Zalando Sans Expanded, Zalando Sans, Yantramanav, Vazirmatn, Ubuntu Sans Mono, Ubuntu Mono, Ubuntu Condensed |

Many families tie at the top weight (45 at 100 in `/Sans/Grotesque`, 52 in `/Sans/Neo Grotesque`), and the command sorts a
tie by name, so the first names are not better than the next. Read the whole tie.

```bash
curl -s https://raw.githubusercontent.com/google/fonts/main/tags/all/families.csv -o families.csv
python3 -I -c "import csv,sys; r=[x for x in csv.reader(open('families.csv',encoding='utf-8')) if x[2]==sys.argv[1]]; r.sort(key=lambda x:(int(x[3]),x[0]),reverse=True); print(len(r), list(dict.fromkeys(x[0] for x in r))[:8])" /Theme/Woodtype
# 40 ['Rye', 'Rubik Dirt', 'Gravitas One', 'Arbutus', 'Sancreek', 'Notable', 'Asset', 'Plaster']
```

Parse it as CSV. Rows such as `Cabin,"wdth,wght@75,400",/Expressive/Vintage,20` hold commas, so `awk -F,` counted 1,832
where the true count is 1,884, and `sort -t, -k4` misordered the top.

A genre is not a pass. Road Rage, in `/Theme/Distressed`, is named as "the apparent default font" for text in AI images
([@AriOnnaDX, 13,864 likes](https://x.com/AriOnnaDX/status/2117646394060132844)), so check any pick against `never.md`.

**Two different lists.** `never.md` names no replacement fonts, because a published list becomes the next tell.
`DESIGN.md` names the one font you picked for this piece. That is a decision, not a list.

**From a reference to one font**, `our proposal`:

1. **Real use.** Akzidenz-Grotesk on Fonts In Use tells you what was used, and it is no licence.
2. **Class.** Take the class as a tag: `/Sans/Neo Grotesque` here, or the right tag for your class. `/Sans/Grotesque` is
   noisy.
3. **Three candidates** from the tie, each with a licence and a file from the sources below.
4. **What the piece needs:** tabular figures for an invoice, diacritics or Cyrillic for translators, the weights you will
   set.
5. **A person compares by eye**, the three against the reference.

```bash
curl -s -o archivo-latin-400.woff2 https://cdn.jsdelivr.net/fontsource/fonts/archivo@5.3.0/latin-400-normal.woff2
uv run --no-project --python 3.12 --with fonttools --with brotli python -I -c "
import sys
from fontTools.ttLib import TTFont
for path in sys.argv[2:]:
    font = TTFont(path)
    tags = {r.FeatureTag for r in font['GSUB'].table.FeatureList.FeatureRecord} if 'GSUB' in font else set()
    print(path, 'tnum' if 'tnum' in tags else 'no tnum', 'missing:', ''.join(c for c in sys.argv[1] if ord(c) not in font.getBestCmap()) or 'none')
" "0123456789.,€ßéčłя" *.woff2
# archivo-latin-400.woff2 tnum missing: čłя
# archivo-latin-ext-400.woff2 no tnum missing: 0123456789.,€ßéя
# libre-franklin-latin-400.woff2 no tnum missing: čłя
```

`tested 2026-11-03`. WOFF2 needs `--with brotli`: without it fontTools stops at `No module named brotli`. Fontsource ships
one file per subset, so check each subset you will ship: `č` is in `latin-ext`, and a `no tnum` may be the subset's. To
ask about the family, read the master: [Libre
Franklin's](https://raw.githubusercontent.com/google/fonts/main/ofl/librefranklin/LibreFranklin%5Bwght%5D.ttf) has no
`tnum` either, so the family has none.

## Fonts you can load in code

Read the licence on each family before you ship it. We did no legal review. `tested 2026-11-03`.

| Source | Route | What came back | Licence evidence | Verdict |
|---|---|---|---|---|
| [Fontsource](https://api.fontsource.org/v1/fonts) | `/v1/fonts`, `/v1/fonts/{id}`, `?category=display&subsets=latin` | 2,103 families, 1,984 Google and 119 others (Bagnard, Bluu Next, Redaction, Cooper Hewitt, Metropolis, Ostrich Sans, Chunk Five, League Mono, Uncut Sans, Iosevka, Fusion Pixel). Display in Latin 480 | `license` field: OFL-1.1 2,059, Apache-2.0 36, UFL-1.0 5, CC0-1.0 1, mit 1, Unlicense 1 | Best. A licence per family and a direct file URL |
| [Google Fonts metadata](https://fonts.google.com/metadata/fonts), tag CSV | `metadata/fonts`, CSV above | 1,959 families with no key. Sans Serif 722, Display 474, Handwriting 358, Serif 354, Monospace 51. The [Developer API](https://www.googleapis.com/webfonts/v1/webfonts?sort=trending) returned 403 with no key | Check through Fontsource's `license` field | Best for choosing by genre |
| [Fontshare](https://api.fontshare.com/v2/fonts?limit=2) | `/v2/fonts?limit=100` | 100 families | `license_type` field, for example `itf_ffl`. Read it | Good |
| [UNCUT.wtf](https://uncut.wtf/) | Browse | "currently 163 typefaces": Sans 66, Serif 27, Monospace 23, Display 47 | States "free for commercial use" | Good, read each |
| [Font Squirrel](https://www.fontsquirrel.com/api/classifications) | `/api/classifications` | JSON on the first call, non-JSON on a later one | Not read | Unstable |
| [Collletttivo](https://www.collletttivo.it/typefaces), [Open Foundry](https://open-foundry.com/), [Font Library](https://fontlibrary.org/), [League of Moveable Type](https://www.theleagueofmoveabletype.com/), [Omnibus-Type](https://www.omnibus-type.com/) | Browse | Loaded, not tested | Not read | Try after the above |
| [Velvetyne](https://velvetyne.fr/greve/) | n/a | Every URL redirects to a strike notice | n/a | Out for now |

```bash
curl -s https://api.fontsource.org/v1/fonts/bagnard
# license OFL-1.1, type other, weights [400]
# variants["400"].normal.latin.url.woff2:
# https://cdn.jsdelivr.net/fontsource/fonts/bagnard@5.3.0/latin-400-normal.woff2  (200, font/woff2, 7,428 bytes)
```

Logos as SVG: [Simple Icons](https://github.com/simple-icons/simple-icons), [svgl](https://github.com/pheralb/svgl)
(`https://api.svgl.app?search=vercel` returned light, dark and wordmark URLs). Trademarks remain with their owners.

## Queries

The left column is the feeling. It was not run. The middle column was, `tested 2026-11-03`, for what the search returns.

| Bad | Good | Where | What came back |
|---|---|---|---|
| cool retro font | `/sets/684/1970s`, then the typefaces it credits | Fonts In Use | Found via domain search |
| sci-fi title | `/tags/242/science-fiction`, `/sets/5784/retro-futurism`, a Typeset In The Future film | Fonts In Use, TITF | Eurostile, Disco, Trade Gothic |
| movie poster type | `/in/2/formats/12/posters-flyers`; `keyword=12674&decade=17431` | Fonts In Use; Poster House | 6,213; 343 |
| film titles | `/in/2/formats/15/film-video`; `/style/1970s/` | Fonts In Use; Art of the Title | 1,192; 92 |
| kinetic type | `/style/type-over-scene/`, `/style/main-title/`, `/search.do?q=kinetic` | Art of the Title | 200, 200, 13 title links. `/style/kinetic-typography/` 404 |
| Swiss style | `/typefaces/76/akzidenz-grotesk`; Poster House country 12842, then `keyword=12702` for railway | Fonts In Use; Poster House | Live; 176, sorted by upload date, then 1 |
| old-timey; grunge; futuristic | `/Theme/Woodtype`; `/Theme/Distressed`; `/Theme/Techno` | Google Fonts CSV | Rye, Sancreek; Special Elite, Rubik Distressed; Zen Dots, Space Grotesk |
| corporate 70s look | `identifier:LFAID*`; `title:"graphic standards manual"` | Internet Archive | 54; 9 |

## Code vs generated

- **Code.** The reference must prove the typeface or its class, the year, the format, and a font you may ship. Output in
  `DESIGN.md`: font file, licence, what the piece needed from it, tracking, size, position, contrast.
- **Generated.** The reference proves layout and hierarchy only. Output: where the text will sit, so the plate leaves room.
  Models fail on exact text: our stills read ASCENST for ASCENT. So generate the plate, and set the words in code.

## Reject if

- No typeface named by a source, unless you keep classes only and say so.
- No year, or a template mockup instead of a real object.
- The wrong format for the piece, one big word with no hierarchy, or a specimen with no use.
- A single logo offered as proof of a system.
- A shipped font whose licence you have not read, or a logo used as a mark because its file has an open licence.
- Words rendered by a generator.

Universal rejects: `never.md`.

## Judge it

Type G1 to G6 in `judge.md`, a draft and off by default. G1, G4 and G5 are code, and G1 applies only to your own set type
or a take, never a found sign. G2 is the record, G3 goes to the LLM, G6 to the LLM with the record.
