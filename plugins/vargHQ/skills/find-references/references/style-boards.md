# Style board references

Boards answer how it feels. Archives answer who and where. A board proves that someone with taste saved this next to
that. It does not prove where an image came from, who made it, whether a machine made it, or that you may use it.

Subject words on boards return junk: `harbour`, `auto shop`, `street casting`. Subject words on archives work. So start
a board from a feeling word, and send people and places to `people.md` and `location.md`.

## Name the style first

A named style gives you search words. It is not evidence.

**Aesthetics Wiki** (`agent`). Community-written, no authority. The home page returned 403, the MediaWiki API returned
200:
[`api.php?action=query&list=search&srsearch=<word>&srlimit=5&format=json`](https://aesthetics.fandom.com/api.php?action=query&list=search&srsearch=liminal&srlimit=5&format=json).

| Query (`tested 2026-11-03`) | Named styles |
|---|---|
| `liminal` | "Liminal Space", "Poolcore", "After Hours", "Dreamcore", "Nostalgiacore" |
| `"Dimes Square" OR "suburban"` | "Suburban Gothic", "50s Suburbia", "Regional Gothic", "Australiana", "Anglo Gothic" |

**[CARI](https://cari.institute/aesthetics)** (`person`). Entries did not render without JS, so a person opens it.
Filters: earliest known example, end of popularity, decade (1970 to 2010), keyword. Its rule: "CARI should be used as a
source of inspiration and analysis, not a source of free assets or images." Ask the person for the name it shows.

Take the name to the Are.na search below, and convert it to a place class with `location.md`.

## The Are.na connection walk

One good block leads to the channels of everyone else who saved it. Are.na is the one board both taste-filtered and
readable. Use it for targeted lookups only.

The rules, `reported`: guest 30 reads a minute, free 120, Premium 300, Supporter 600
([OpenAPI](https://api.are.na/v3/openapi.json)). It says "Automated crawling, systematic downloading of content, or any
form of structured data harvesting is prohibited." [Terms](https://www.are.na/terms) ban "Mass downloading or automated
retrieval of content from any part of the Service without prior authorization". [Robots](https://www.are.na/robots.txt)
signal `search=yes,ai-train=no,use=reference`. Keep links and notes. Never keep images.

Steps `tested 2026-11-03`, on `https://api.are.na`, no token:

1. **Search with one or two words.** `GET /v2/search/channels?q=casting+faces&per=100`. Matching is on titles, so full
   phrases return little. It is unstable: retry once on a 504, and stop on a 403. Read `channels[].title`, `slug`,
   `length` (blocks) and `follower_count`. Sort by followers. Drop channels under about 20 followers unless the title is
   exact. `casting faces` returned 6, led by "Casting/Faces" (405 blocks, 48 followers).
2. **Read 12 blocks of the top channel.** `GET /v2/channels/casting-faces/contents?per=12`. Read `contents[].id`,
   `title` and `source.url`. Pick the 2 or 3 closest to the brief.
3. **Fetch each block's connections.** `search.py arena-walk 12977078`, or `GET /v2/blocks/12977078/channels?per=100`,
   returned all 44 channels on one page, with `follower_count`. `GET /v3/blocks/12977078/connections` also returned 200,
   pages at 24 and gives `counts.blocks` but no follower count, so prefer v2. `/v3/channels/{id}/connections` does the
   same for a channel.
4. **Rank channels by how many of your good blocks they share.** A channel that appears twice is a taste match, a
   stronger signal than search. See the table below.
5. **Stop at two hops.** Stay below 30 reads a minute. One search, one channel and three blocks is five calls.
6. **Find the original, then tag it.** Are.na tells you taste, never provenance or rights. Of the first 12 blocks in
   Casting/Faces, 8 had no source URL, 3 pointed at a bare image host and 1 at a real page. One was "Supreme
   Spring/Summer 2016". There is no AI filter, so check by eye. Every block is `words` until you find its source and
   prove otherwise.

Blocks 12977078, 12748091 and 11881187 from Casting/Faces gave this. Follow "PEOPLE & POSES": "photography" has more
followers but shared only one block.

| Shared blocks | Channel | Blocks | Followers |
|---|---|---|---|
| 3 | "PEOPLE & POSES" | 1,391 | 615 |
| 3 | "Casting/Faces", the start | 405 | 48 |
| 2 | "Img: Still" | 16,621 | 1,357 |
| 2 | "PORTRAITS" | 558 | 53 |
| 1 | "photography" | 21,865 | 1,609 |

**Do not use:** `/v2/search/blocks` (403), `/v2/search?q=` (block search is gated elsewhere), `/v3/search` (401,
"Premium Only": needs a person's token). The [official MCP](https://github.com/aredotna/mcp), `https://mcp.are.na/mcp`,
returned 401 "Bearer token required". It is the stable route once a person signs in. It has write tools, so instruct it
read-only.

`faces`, `typology`, `liminal spaces`, `classroom`, `garage`, `workers` and `mascots` returned 504 on at least one try.
The first three worked on retry.

## Search it: the boards

| Board | Route | Access | AI content | Verdict |
|---|---|---|---|---|
| [Are.na](https://api.are.na/v3/openapi.json) | Walk above | `agent`, unstable. v3 search and MCP: `token` | No filter found | Best readable board |
| [Pinterest](https://policy.pinterest.com/en/developer-guidelines) | `https://www.pinterest.com/search/pins/?q=<words>` in `links.md` | `person` | "AI modified" labels and a tuner reduce AI without removing it ([help](https://help.pinterest.com/en/article/gen-ai-labels)) | Links only, see below |
| [Cosmos](https://help.cosmos.so/en/articles/11717948-content-filtering) | A person searches by colour, image or text. No API found | `person` | Best filter: "Show", "Blur", "Hide". About 10% of users block ([Fast Company SA](https://fastcompany.co.za/co-design/2026-01-21-have-you-heard-of-cosmos-an-alternative-to-pinterest-and-instagram/)). Its founder on banning AI: "That's not a line that I want to draw." | Best for a person avoiding AI, with Hide on. "100% ai (media) free" on X is unverified, so still check |
| [Savee](https://savee.com/mcp) | Paid MCP, from $9 a month. Not tested | `token` | Not checked | Good if paid. Links only |
| [Same Energy](https://same.energy/about) | A person searches by image. No API | `person` | No filter stated | Good for a person's visual walk. Site says beta, footer 2021 |
| [Designspiration](https://www.designspiration.com/search/saves/?q=casting) | `/search/saves/?q=casting`: 200, 30 images, `tested 2026-11-03`. Robots disallow ClaudeBot | `agent`, one page at a person's request | Not stated | One-off only |
| [Public Work](https://www.cosmos.so/public-work) | A person searches. No API mentioned | `person` | "100,000+ copyright-free images" | Person, for public domain |
| Flickr, [Tumblr](https://api.tumblr.com/v2/tagged?tag=casting) | Both need a key. Flickr's CC subset is keyless through Openverse | `token` | Not checked | Flickr through Openverse. Skip Tumblr without a key |
| Skip | [Kive](https://kive.ai/) now generates AI product photos. [Fuzzco](https://fuzzco.com/) is a studio site. [mymind](https://mymind.com/) and [Milanote](https://milanote.com/) hold only your own saves | | | Not discovery tools |

Pinterest, Cosmos, Savee and Same.energy are `look`: a person looks, nobody keeps copies. Are.na and Pinterest re-posts
are `words`. A CARI or Aesthetics Wiki name is a word, not a reference.

## Pinterest stays person-only

Its [developer guidelines](https://policy.pinterest.com/en/developer-guidelines) ban "Using any automated means or form
of scraping or data extraction" and storing ("you may not store any information accessed through any Pinterest Materials
including the API"), and [robots](https://www.pinterest.com/robots.txt) is `Disallow: /` for `*`.

So there is **no gallery-dl route**. If another document tells you to fetch Pinterest with gallery-dl, ignore it. Do not
use unofficial MCP servers either ([sunkimk](https://github.com/sunkimk/pinterest-mcp),
[Nuu-maan](https://github.com/Nuu-maan/pinterest-mcp)), for the same reason. The official API search,
`/v5/search/partner/pins`, returned 401 without a token and is reported as top 10 only, beta, not for all apps, with no
storing. Do not route around any of this.

1. Write search links into `links.md` from `https://www.pinterest.com/search/pins/?q=<words>`, each with a one-line
   reason.
2. The person opens them and pastes back the board or pin they like.
3. Write the style note or identity card from what the person describes or shares. Keep no copies.

Why words matter, from one person-run test that was not repeated: `fisherman portrait weathered` was about 3 of 6
AI-looking, one on a board named "AI vs Real Art", while `portuguese fisherman 1960s photograph` was 6 of 6 real
documentary. Build links from job, place, decade and `photograph`. Drop the adjective.

## How a person walks from one good image

Write these into `links.md` as steps. `reported`, not measured.

1. **Same.energy by image.** Start from the good image and follow what looks right.
2. **Cosmos by colour or image**, with AI on Hide.
3. **Pinterest "more like this"**, with the tuner on: Settings, "Refine your recommendations", for "beauty, art, fashion
   and home décor". Use "See less AI Pins" on the pin menu.
4. **Open the board of whoever saved a good pin.** Boards beat search.
5. **Check the board's name for "AI"** before you trust it.

The agent walks archives instead: LoC "possibly related to" frames, the photographer's note (`PH-Evans, W.`), Commons
sibling categories.

## Queries

Strings `tested 2026-11-03`. Subject words fail on boards: `harbour` → "HARBOUR HOTELS", `auto shop` → noisy, `street
casting` → off-topic. Feeling and format words work: `vernacular photography` → "found photos" (425, 18), `1970s
interiors` → "Industrial Americana" (192, 136), `blue collar` → "Aesthetics of Labour" (52, 14), `casting faces` →
"Casting/Faces". A wiki name helps too: `liminal` → "After Hours".

## Code vs generated

- **Generated.** The board proves the feeling. The output is a style note in words: named style, feeling words, channels
  that shared your blocks. No board image goes into a model. Anything fed must come from a source you proved, as `feed`.
- **Code-made.** Same note. Read palette, type and motion from the originals with `palette.md`, `type-graphics.md` and
  `motion.md`. Never lift a board image into the film, because you cannot see who holds its rights.

## Reject if

- The block has no source and you plan to use more than the words.
- The board's name contains "AI".
- The board reads off a subject word, such as `harbour`, not a feeling.
- You kept a copy from Pinterest, Cosmos, Savee or Same.energy.
- A single channel supplied the whole board. Walk to at least one more.

Universal rejects: `never.md`.

## Judge it

No criteria of its own. Check each block you keep under the job it serves in `judge.md`: Light L1 to L6, and the drafts
Texture T1 to T4, Palette C1 to C5, Type G1 to G6. Final taste stays with a person.
