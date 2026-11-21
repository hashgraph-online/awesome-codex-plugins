# Sources: who may read what

Access decides the workflow before quality does. The best taste sites are person-only, so the agent writes links for the
person instead of pretending it can browse them. Every source is one of four kinds:

- `agent`: open API or readable pages. The agent may call it.
- `token`: needs a key or sign-in from the person. The agent never signs in for them.
- `person`: the agent writes the link in `links.md` and a person opens it. Never fetch it, not even to check a link.
- `dead`: skip.

Rules for every call: reading one page on a person's request differs from training or bulk harvest, and several sites
allow the first and forbid the second through `Content-Signal: search=yes,ai-train=no,use=reference`. Cap reads, pace to
crawl delays, identify the agent honestly, and never mirror.

- **401, 403, a captcha or a Cloudflare challenge are final:** blocked for this agent, not down for people. Stop and write
  the link.
- **A 429 means slow down.** Wait what `Retry-After` says, or 60 s, try once more, then stop using that source for this run.
- **A server error (500, 504) gets one retry.**

`search.py` does the waiting: it paces per host across processes (1.1 s, and 3 s on Commons and upload.wikimedia.org) and
returns status `blocked` or `rate_limited`. Which source to start with for each job is in the table in `SKILL.md`. Queries,
traps and verdicts are in the job file.

## Every source by access

| Access | Sources |
|---|---|
| `agent`, tested 2026-11-03 | Light and framing: Met v1.1, Rijksmuseum, AIC, NGA data, LoC JSON, Commons API, Internet Archive search, Poly Haven, Lantern, ShotOnWhat, Deakins site, Wandering DP, Cooke site search. Texture and palette: Flickr feed, ambientCG, Wellcome, Wada JSON, Meditations in Color. Type: Fonts In Use facets, Art of the Title, Poster House REST, Google Fonts CSV, Fontsource, Logobook, People's Graphic Design Archive. Motion: Refs search, LottieFiles GraphQL (undocumented), Sakugabooru metadata, Motionographer, Stash, three.js JSON, GitHub, whatships. Location: TheFilmMap MCP, Socks Studio, Hidden Architecture, Aesthetics Wiki API. Music: MusicBrainz, ListenBrainz (part), Discogs API, NTS (undocumented), Mixcloud, Bandcamp Daily articles |
| `agent`, unstable | Are.na v2, Openverse. See the endpoint table below |
| `agent`, our own | varg how to: guides and skills, not references |
| `token`, tested 2026-11-03 | X, through an X MCP or the X API. Rules in `experts.md` |
| `token`, not tested | FrameThrower, Are.na v3 and MCP, Flickr API, Mapillary, Unsplash, Pexels, YouTube Data API, Freesound API, Epidemic MCP, Savee MCP, Refs Pro, Mobbin, Refero |
| `person` | **Instagram and Reels**, Pinterest, Film-Grab, ShotDeck, Shot Cafe, Eyecannndy, Film Vibes, Frame Set, Flim, Google Images, Bing, Yandex, TinEye, Cosmos, Same.energy, [Vimeo Staff Picks](https://vimeo.com/channels/staffpicks), [filmdev.org](https://filmdev.org/robots.txt), [Camera-wiki](https://camera-wiki.org/robots.txt), Lomography, Movies in Color, Screenmusings, ArtStation, Dribbble, CodePen, Codrops site, Shadertoy, Video Static, Ads of the World, Meta Ad Library, TikTok Creative Center, Reddit, Atlas Obscura, Street View, Rate Your Music, Every Noise, Bandcamp pages, Music-Map, Gnoosic, Tunefind, WhatSong, WhoSampled, Radiooooo, Cosine.club, YouTube Audio Library, Pixabay, Free Music Archive, Uppbeat |
| `dead` | Maroofy (HTTP 402), Kive (now generates), appmotion.design (404), Living Lines Library, ccdphotos.com (parked), Spotify features for new apps, Udio downloads. Temporarily out: Letterform Archive Online, Graphics Atlas, Velvetyne (strike page) |

Why the film libraries are `person`, from our review on 2026-10-26: Shot Cafe's `robots.txt` disallows ClaudeBot and its
terms are personal and non-commercial. Film-Grab's operator rejects AI and bots. Eyecannndy's Cloudflare answers
automation with 403, and its clips are excerpts of others' work. ShotDeck and Film Vibes are subscriber products with
login-only search, restricted to reference, internal or non-commercial use. Instagram and Reels were not fetched: we treat
them as `person`, because they need a login.

## Cross-job sources and setup

**Refs** (`agent` for search, `token` for Pro). How do films like this cut, pace and look?

```bash
python3 -I "$S/search.py" refs '{"query":"kinetic type","category":"motion","ai_made":false,"limit":8}' --log search_log.jsonl
claude mcp add --transport http refs https://refs.video/mcp     # optional, if you want it as a client tool
```

`tested 2026-11-03`, with cold-run facts marked:

- **Reach.** Keyless, up to 8 short cards, 30 searches an hour. `limit` above 8 returns 8, and `limit:50` fails. `offset` is
  capped at 40: offset 48 repeats the page at 40. So keyless reach is 48 unique.
- **Filters.** `category` (`launch`, `demo`, `explainers`, `motion`, `interactive`, `films`, `teaser`, `ugc`), `aspect`,
  `min_seconds`, `max_seconds`, `ai_made`, `made_with`, `brand`, `ugc_format`, `industry`, `platform`, `min_days_running`,
  `sort`, `offset`. Use short keywords.
- **`ai_made` and `made_with`.** Its own schema: `ai_made` true = "made with AI/code (Claude, Remotion, three.js)", false =
  human-made. So `false` removes code-made films and `true` mixes code with generated. For a coded piece use `made_with`:
  `{"query":"launch","made_with":"hyperframes"}` 3, `"made_with":"remotion","max_seconds":60` 4.
- **Thumbnails.** A thumbnail URL on a result card is part of the result: open a few, to read what a card shows, and tag
  them `look`. Do not keep them, ship them or walk through a host's images from there. On the board such a film is a `link`
  with no image.
- **No clip.** Cards give a summary and a thumbnail, so nothing is measurable from Refs alone. Find the film's own public
  page, and a person watches.
- **Locked.** Keyless cards can say `locked: library` ($6 a month per Refs' note), and in the ad cold run 89 of 89 did. A
  person who clicks a Refs link on the board may meet a paywall, so say so. Full cards need a free account. Frame sheets and
  blueprints need Pro.

**FrameThrower** (`token`, not tested, 401 without one). Which real frames have this light, lens or mood? Which ads and
animation?

```bash
claude mcp add --transport http framethrower https://framethrower.ai/api/mcp   # then /mcp to sign in
```

For film light use REST, `POST /api/v1/search` with `lighting`. Read the [OpenAPI
spec](https://framethrower.ai/api/v1/openapi.json) first, because its docs disagree. Open without a token,
`tested 2026-11-03`: [`/style/window-light`](https://framethrower.ai/style/window-light) gives a definition, 24 example
frames and named films. Traps and terms are in `light.md`.

**Are.na** (`agent`, unstable, or `token` for the stable route). What have people already curated for this look?

```bash
claude mcp add --transport http --scope user arena https://mcp.are.na/mcp   # then /mcp to sign in
```

The official [MCP](https://github.com/aredotna/mcp) has write tools such as `searchAndConnect`, so instruct read-only
use. The connection walk is in `style-boards.md`.

**X** (`token`). What are people saving this week? Use an X MCP or the X API. Without one, web search `site:x.com`, keep
only posts you could open and say X search was not available. Rules in `experts.md`.

**YouTube** (`token`, not tested). Which moments, music videos, trailers and title sequences do people remember?
`search.list` with the person's key: `q` with minus and pipe operators, `publishedBefore`, `videoDuration`,
`videoLicense`, `relevanceLanguage` ([docs](https://developers.google.com/youtube/v3/docs/search/list)). A person
watches and notes timestamps. A 5 to 15 s study clip only when the person asks for it, through `media-download`
(`video.sh`, yt-dlp). Tag it `words`. Never ship it.

**Pinterest** (`person`). Rules are in `style-boards.md`. Tag finds `look`. Give the person attribute words:
`<film> still`, `<director> color palette`, `<decade> film grain`, `<genre> lighting`.

**varg how to** (`agent`, free, a few searches). What already worked for this format? It returns how-to guides and skills
to install, not references. `curl -s "https://varg.ai/how-to/api/search?q=<format and look in plain words>"`, or
`search_how_to` on the varg how to MCP, or `vargai search "<words>"`.

## Person-run links

Write these into `links.md`, one line of reason per link, or run `python3 -I "$S/search.py" links "<words>" --job
light`. The job is one of `light`, `framing`, `people`, `location`, `texture`, `type`, `motion`, `style`, `music` or
`provenance`. With no job it lists every group, each row marked with its job. Nothing here is fetched or was tested, so
never promise a link works. Where we cannot build a link we trust, use the site's home page and name what to look for.

```
https://www.google.com/search?udm=2&q=<words>+before:2022-11-30&tbs=itp:photo
https://noai.duckduckgo.com/?q=<words>&iax=images&ia=images
https://yandex.com/images/search?text=<words>
https://www.pinterest.com/search/pins/?q=<words>
https://fontsinuse.com/search?terms=<words>
https://film-grab.com/?s=<words>
https://shot.cafe                            home page, plus the tag to look for
https://eyecannndy.com                       home page, plus the technique's name
https://shotdeck.com                         search needs a login
https://www.instagram.com/reels/             needs a login
https://www.facebook.com/ads/library/        what a category really runs
https://ads.tiktok.com/business/creativecenter/inspiration/topads/pc/en
https://www.adsoftheworld.com/
```

Provenance check for anything web-found, person-run: TinEye sorted by oldest, then Google Lens, then Yandex if it shows
a face or Eastern Europe. What that proves is in `never.md`. One exception invites assistants:
[whatships](https://whatships.com). Its robots.txt allows assistant fetchers, and `/search-index.json` returned 2,908
entries (2,786 videos, 109 tools, 13 studios), `tested 2026-11-03`. Its [`llms.txt`](https://whatships.com/llms.txt) lists
"downloading videos as a CDN" as not a fit: link a film, a person watches, and nobody processes its clips.

## Exact endpoints where access is unstable

Everything here was observed on 2026-11-03. Treat it as a snapshot and expect it to change.

| Source | Endpoint | Observed on 2026-11-03 | Do |
|---|---|---|---|
| **Are.na** | [`GET /v2/search/channels`](https://api.are.na/v2/search/channels?q=casting+faces&per=10) | 200 on most calls. Intermittent 504s on `faces`, `typology`, `liminal spaces`, `classroom`, `garage`, `workers`, `mascots`; the first three succeeded on retry. A 403 was also recorded that day | Unstable. Retry a 504 once. Stop on 403 |
| | Everything else, and the rules | See `style-boards.md`. Guest 30 reads a minute, and its terms ban harvesting | Targeted lookups only |
| **Openverse** | [`/v1/images/?q=low%20key%20portrait&page_size=5`](https://api.openverse.org/v1/images/?q=low%20key%20portrait&page_size=5) | 240 results, top 5 all Flickr. Robots disallow generic crawlers on this path | Pace, identify the agent. You may fetch an image URL it returns: one file for a reference you keep |
| | [`/v1/images/?q=fisherman+portrait&category=photograph&page_size=8`](https://api.openverse.org/v1/images/?q=fisherman+portrait&category=photograph&page_size=8) | 87, with 3 of 14 calls HTTP 500. A 504 was also recorded that day | Retry once |
| | `/v1/images/` with `burlap` | HTTP 500, then no response on later calls | Keep a fallback |
| | `/v1/images/` from one network | Failed every time: one HTTP 500, then timeouts at 30, 45 and 60 s, while `/v1/images/stats/` returned 200 | Never the sole source for a job |
| | `/v1/audio/` | Worked. Headers `anon_burst: 20/min`, `anon_sustained: 200/day`. 18 to 41 s per call | 60 s timeout. `result_count` caps at 240 |
| **Fonts In Use** | `/search?terms=`, `/search/advanced`, and the numbered paths | See `type-graphics.md` | `person` for search, `agent` at a paced rate for numbered paths |

Also check per call. **Met:** `isPublicDomain=true` leaks: Hopper returned 26 with it, yet
[366204](https://www.metmuseum.org/art/collection/search/366204) reads PD False, so check each object.
**Screenmusings:** Cloudflare 403 that day, so `person`. **MusicBrainz:** good for era search, IDs and credits, noisy
for discovery: `tag:"dream pop" AND country:GB` returned Coldplay first.

MCP servers that exist, and how to spot a bulk-published one, are in `experts.md`.
