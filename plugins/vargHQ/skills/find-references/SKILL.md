---
name: find-references
description: >-
  Find real, human-made references before anything is made, for AI image, video and music and for video made with
  code. Turns a request into one query pack per job (light first if generated; type, motion and palette first if
  coded; then framing, people, location, texture, music, and a "never" board of what must not appear), searches each
  source in its own words, opens everything it keeps, proves who made it, measures what code can measure, checks light
  with an LLM judge, and hands a person three candidates per job. Use when someone says "find references", "reference
  board", "what should this look like", "lighting reference", "framing reference", "texture reference", "font
  reference", "motion reference", "casting reference", "music reference", "moodboard references", "make it not look
  like AI", "avoid slop", "rank these references", or starts a video with no look yet. Not for writing the look from
  chosen references (video-moodboard, varg-video-prompting), building the cast (character-passport) or downloading one
  known link (media-download).
license: MIT
metadata:
  author: vargHQ
  version: "2.0.0"
  openclaw:
    requires:
      anyBins:
        - python3
        - curl
    homepage: https://github.com/vargHQ/skills/tree/main/find-references
compatibility: >-
  Works in any agent with a shell and web access. scripts/search.py needs only Python 3 and reaches 22 open sources with
  no key. frame_light.py needs ffmpeg. motion_read.py needs ffmpeg and uv. judge.py and the palette commands need
  ImageMagick; judge.py read uses the person's own logged-in claude or codex CLI, with no API key. OCR needs tesseract.
  FrameThrower, Refs Pro, Are.na v3, Flickr's API, Mapillary and Epidemic Sound need the person's own account. No varg
  credits are used.
allowed-tools: Bash(python3:*) Bash(curl:*) Bash(ffmpeg:*) Bash(ffprobe:*) Bash(magick:*) Bash(uv:*) Bash(tesseract:*) WebFetch WebSearch Read Write Edit
---

# Find references

Without a reference an agent falls back to its default look: "centered text, gradient background, everything fading in"
(https://x.com/rexan_wong/status/2103707054108299437). Adding more words does not fix it. Three facts shape this skill:

- **No library searches by ratio, shadow edge or Kelvin.** Search with words a cataloguer would use, then measure what
  you find. A spec and a query are different things.
- **Machines read light and taste badly** (`references/evidence.md`). A judge answers literal questions about what is
  visible, and nothing else.
- **The best libraries forbid bots.** Film-Grab, ShotDeck, Pinterest, Instagram, Rate Your Music and Bandcamp's pages are
  for people. The agent reads open archives and writes links for the person.

So each part does what it can do. **Code owns facts in pixels and timing. Records own who made it and the rights. The
LLM owns literal yes/no checks and the shortlist. A named person owns meaning and the final pick.**

**Some things only a person can find.** In the cold run on an ad (`tested 2026-11-03`), no open source returned the
inside of an old Portuguese tile shop, the thing that person loved most. Finding that out early and writing the link is a
good result. Say so plainly, and do not pass off something near it as the thing.

## Read and run

Read this file and `references/queries.md`. Then read only the job files this piece needs. Every rule that matters for
the whole run is in this file. Job files hold routes, traps and queries.

Run from the project folder. Call scripts by absolute path. Never write into the skill folder. Use `-I` when a folder
holds downloads, which is nearly every folder here, so the commands below all have it.

```bash
S=<skill folder>/scripts     # absolute path
python3 -I "$S/search.py" sources
```

| Script | Does | Needs |
|---|---|---|
| `search.py` | 22 open sources, person-only links, fusion, the search log | Python 3 |
| `board.py` | the board page | Python 3 |
| `sun.py` | sunrise, sunset, sun altitude and azimuth | Python 3 |
| `ai_marker.py`, `hdri_light.py`, `mcp_call.py` | AI marker scan; light in an HDRI; any MCP tool with no client | Python 3 |
| `frame_light.py` | bright side, contrast, colour | ffmpeg |
| `motion_read.py` | cuts, holds, camera, elements, scale | ffmpeg and uv, in the `uv run` form below |
| `judge.py` | blind, read, enforce, aggregate, pairs, rank | `magick`. `read` and `pairs` use the person's logged-in `claude` or `codex` CLI |

## What you come back with

```
brief.json        the request as 11 fields, each marked said, assumed or asked
queries.md        one query pack per job, plus the whole-brief control query
search_log.jsonl  source, exact query, status, rank and count for each search
never.md          reject-if tests, with a positive translation for prompts
want/<job>.txt    one want card per job, frozen before you look
refs/<job>/       every frame or clip you opened and kept, named NN-job-source.ext
refs.md           one job card per kept candidate; picks are marked when the person picks
links.md          searches only a person may open, with a one-line reason each
board.html        three candidates per job, shuffled, no scores, for the person to pick
DESIGN.md         coded only: hex, type, grid, motion, each value labelled measured, record, by eye or assumed
timing.md         coded only: beat, seconds, frames, what moves first, ease, source
```

For a coded piece the picks become numbers in those two files. With nobody there to pick, write them from the first passers
and head them PROVISIONAL. For a generated piece the picks become role lines and words. See `references/templates.md`.

## The jobs

**Priority depends on the method.** Generated: light first, because people and machines both read it badly. Coded: type,
motion and palette first, and light only where a shot has it (a 3D scene, a single still, an HDRI). Change the order to fit
the piece, and say so in `queries.md`. Run only the jobs a piece needs: People only with a cast or one generated person,
Characters only with a cast. Queries and sources are a floor to start from, not a limit.

| Job | What the reference proves | Queries, sources | Agent starts with | Person gets links to | Read |
|---|---|---|---|---|---|
| **Never** | what the default looks like, so it can be rejected | 2, 2 | Refs obvious query; generated: Commons `deepcat:`; coded: Impeccable | Meta Ad Library and TikTok Creative Center for ads; Kagi `ai:only`, r/aislop | `references/never.md` |
| **Light** | one source, a side, a hardness, and why it is there | 6, 3 | Deakins site, Met by artist, Commons, LoC; Poly Haven for code | Film-Grab, ShotDeck | `references/light.md` |
| **Framing** | shot size, height, angle, where the subject sits | 4, 2 to 3 | Met, Commons, ShotOnWhat | Film-Grab, Shot Cafe, Frame Set | `references/framing.md` |
| **People** | who this person is, apart from pose, place, expression, clothes | 4, 2 to 3 | LoC FSA/OWI, Commons | Flickr group 100 Strangers, ShotDeck | `references/people.md` |
| **Characters** | shape language and how a non-human moves | 2, 2 | Sakugabooru metadata, Are.na | ArtStation | `references/characters.md` |
| **Location** | a real place, decade and region | 3, 2 | Commons categories, LoC HABS, TheFilmMap MCP | Street View, Atlas Obscura | `references/location.md` |
| **Texture** | one named material or process, at pixel level | 2 to 3, 2 | Commons, LoC, ambientCG; Flickr feed for leads | filmdev.org, Camera-wiki, Lomography | `references/texture.md` |
| **Palette** | colours and proportions from a named frame | 2, 2 | your candidates' frames, Wada JSON, Meditations in Color | Movies in Color, Screenmusings | `references/palette.md` |
| **Type, graphics** | a real use of a named typeface, or its class, in a year | 2 to 3, 2 | Fonts In Use numbered paths, Art of the Title, Poster House, a Commons category of the genre's posters | Fonts In Use search | `references/type-graphics.md` |
| **Motion** | timing you can measure and rebuild | 3, 2 | Refs, Commons `filetype:video` for clips you may process, Sakugabooru metadata, Motionographer | whatships films, Instagram Reels, Meta Ad Library, TikTok Creative Center, Ads of the World, Vimeo Staff Picks | `references/motion.md` |
| **Music, voice** | tempo, instruments, era, for a person to hear. Voice: a casting line (age, region, texture, pace), and `video-sound` casts candidates | 3, 2 | Discogs, MusicBrainz, ListenBrainz, NTS | Rate Your Music, Bandcamp pages | `references/music.md` |

Style is not a job. It comes from a board (`references/style-boards.md`), which answers how a piece should feel; archives
answer who and where. A style you cannot break into these jobs is a mood, not a reference.

## Rules

1. **Brief before search.** The output of this step is a written description of light and staging. Images are how you get
   there. Roger Deakins produces "sketches of possible shots and staging as well as detailed diagrams for lighting"
   (https://www.rogerdeakins.com/?p=215049).
2. **One job per card.** Say what it lends and what it must not copy. An image may have two cards if it truly does two
   jobs, each with its own do-not-copy line. Everything else in the image leaks: "Any asset you pass as a reference, even
   if you're not explicitly prompting for it, will still influence the output"
   (https://x.com/henrydaubrez/status/2037554793850499369).
3. **Open what you keep.** Keyword hits lie: of two Met hits for `candlelight`, one has a single low candle and one has no
   candle at all. Write one line saying only what you can see. Delete what you could not open.
4. **Prove who made it before judging pixels.** People and detectors both fail at spotting AI, and curated AI is the worst
   case. Sort sources by when the collection closed. Give each reference one label (`references/never.md`):
   **HUMAN-PROVEN** (a verified film title or a named archive or museum as holder, or a named author plus a date before
   2022 plus a body of work or credits), **LIKELY HUMAN** (a named author or a date, with nothing against), **UNKNOWN**
   (nothing proven: mood only, no measurements, no feeding) or **AI** (a marker, or the maker says so: never board only).
   "No AI marker" and "the detector says human" are never a pass.
5. **Respect access.** Every source is `agent`, `token`, `person` or `dead` (`references/sources.md`). Never fetch a
   person-only site, not even to check a link. Never spoof a user agent, sign in for someone or download store previews.
   - **401, 403 and a bot wall are final.** Stop and write the link in `links.md`.
   - **A 429 means slow down.** Wait what `Retry-After` says, or 60 s, try once more, then stop using that source for this
     run.
   - A server error (500, 504) gets one retry.
6. **Tag every reference `feed`, `words` or `look`.**
   - `feed` may go to a generator: yours, licensed for this use, CC0 or public domain, and no identifiable person.
   - `words` is read and described. CC BY and BY-SA are `words` by default; a person may clear them for feeding.
   - `look` is seen by a person, and nobody keeps a copy.
   - **Any identifiable real person is `words`, even in a public-domain photo.** Copyright and likeness are separate rights.
   - A public-domain painting is legally `feed`, but start from words: whether paint texture comes back is untested, so
     feed one only after a test frame.
   - Audio used as an asset has its own licence rules in `references/music.md`.
7. **Feed a model far fewer references than it accepts: 1 to 5, each with a role.** `@Image1 defines the light only. Do not
   copy the room, the person or the colours from @Image1.` Scores fell as reference count rose in the benchmarks we found.
   Keep identity sheets flatly lit so the light reference can work (`references/queries.md`).
8. **Never ask a judge for what it cannot perceive.** Lens, film stock, ratios and exact hex come from records or code.
   Report "these three pass the checks", never "the best" (`references/judge.md`).
9. **Borrow one step sideways.** Skip the first famous name that comes to mind. Take the same job from another field:
   candlelight from a painting, a 9:16 composition from a hanging scroll. Never pass a director's or artist's name to a
   generator: pass measurements.
10. **Copy numbers as the source shows them.** Never round up or invent a film, scene, post or tag. Say what you could not
    reach, what the search actually returned, and which expected things it did not confirm.

## Step by step

### 0. Write the brief

`brief.json`: idea (what the viewer should believe afterwards), feeling (two adjectives and one opposite), subject, world
(place and decade), medium, audience, platform (aspect ratio, length), method (coded, generated, hybrid, filmed),
constraints, loves, hates. Mark each `said`, `assumed` or `asked`.

Ask at most two questions: what they hate, and the method if you cannot infer it. Assume the rest out loud. Also ask for
real assets (product, UI, founder, brand), which does not count as a question: real material beats any reference. If the
request is vague, show three territories and ask one question: `references/queries.md`.

### 1. Run the obvious search, and ban what repeats

Search the plainest words (`coffee`, `coffee ad`). Say what the results actually show, and name what they share.

```bash
python3 -I "$S/search.py" refs '{"query":"coffee","ai_made":false,"limit":8}' --log search_log.jsonl
```

Refs may not show the obvious thing: in the cold run 17 of 48 cards were about coffee, and 9 of those were Nespresso. Mark
anything you expected and could not confirm. For ads, the real picture of a category is in Meta Ad Library and TikTok
Creative Center, which are person-only, so write those links.

Write `never.md` from the search you ran and from the person's stated hates. Each entry is a test a stranger can check, on
a frame, a clip or a text as fits. At intake, drop a reference only if what matches a never test is what it lends: a
painting that shows people drinking can still lend only light. Details: `references/never.md`.

### 2. Write one query pack per job

Each pack has up to five slots, shaped for the engine that reads it: L literal, C caption (skip it if you have no semantic
engine), N named, A adjacent, X excluded. `references/queries.md` has the slots, a bad-to-good table per job and the
feeling table. Add one whole-brief control query.

- Keyword sources want one or two catalogue words. A silent zero usually means the wrong vocabulary: open one good result,
  read its tags and reuse them.
- Never write "no X" into a semantic query. Filter afterwards.
- Search in the place's own words and in English: both, since neither always wins (`references/light.md`). Read the author
  field of good Commons hits: institutions upload whole collections. Ask a local archive by name.
- **Stop a job when two queries in a row add nothing new.** The floors in the table do not cap you: Light took 26 queries on
  a hard brief in the cold run, and that is fine.
- Palette needs no first search of its own. For the first board, extract from three named frames of candidates. After the
  pick, re-extract from the picked frame.

### 3. Search, and write the links

```bash
python3 -I "$S/search.py" met "Georges de La Tour" --artist --public-domain --medium Paintings --log search_log.jsonl > light-1.json
python3 -I "$S/search.py" commons '"low key" portrait' --log search_log.jsonl > light-2.json
python3 -I "$S/search.py" commons-cat "Category:Diners in New Jersey" --log search_log.jsonl > location-1.json
python3 -I "$S/search.py" loc "mechanic" --collection fsa-owi-black-and-white-negatives --log search_log.jsonl > people-1.json
python3 -I "$S/search.py" links "sodium street night" --job light     # that job's person-only links, nothing is fetched
```

- Retrieve 10 to 20 a query and 30 to 60 candidates a job at most.
- Every call prints JSON with a `status`: `ok`, `error`, `blocked` or `rate_limited`, and anything but `ok` exits 1.
  `search.py` paces itself across processes, handles a 429 as rule 5 says, and logs every outcome. Add a row by hand for
  anything you fetch another way (WebFetch, curl, `mcp_call.py`), including silent zeros and blocks.
- `image` is often a sized copy, and `original` can be a 272 MB TIF (cold run on a coded film). Check `width`, `height` and
  `bytes` first. Use a sized copy for layout and palette (`--width 1920` on `commons` and `commons-cat` sets Commons
  `iiurlwidth`), and the original only for a 100% texture check.
- The best route of the cold run was a Commons category walk, with author, date, EXIF and licence in one call. Which source
  to use for which job is in each job's file. Who may read what is in `references/sources.md`.
- Connect what the person has an account for: FrameThrower is the only library with a filter for what lights a frame
  (`references/light.md`).

### 4. Fuse, open, prove

Fusion merges duplicates and rank across queries. It does not cut by maker: one pick per maker happens only at the
shortlist, after opening. Across different sources few items overlap (6 of 119 in the cold run), so read the top of each
query too.

```bash
python3 -I "$S/search.py" fuse light-1.json light-2.json light-3.json --limit 20
```

Open every candidate you keep and write what you can see. Then prove provenance from records: a named maker and date, a
holding archive, or an oldest copy. Run `python3 -I "$S/ai_marker.py" refs/` on what you download: a hit rejects, and a
miss proves nothing, because any re-encode erases the marker.

### 5. Measure, then judge

Write a **want card** per job in `want/<job>.txt` before you look at candidates, with values only and no praise words:

```
job: light | direction: any | hardness: soft (assumed) | source: window or practical lamp | shadow side: near black
```

- Freeze only values the person gave or the brief implies.
- Anything you had to invent is marked `assumed`, and it cannot be core. If you invented a side, write `direction: any`, and
  the judge skips L2. It also skips a question whose value says `(assumed)`.
- The person's words outrank your card. A reference that fits the brief and fails an assumed value goes to the person with
  a note.

Every kept candidate passes the gates, for every job: opened, provenance, source allowed, rights, identity safety, no
duplicate (`references/judge.md`). Then measure. Gates, code and the person are usually enough.

```bash
python3 -I "$S/frame_light.py" refs/light/07-light-met.jpg       # bright side, contrast in stops, highlight and shadow colour
uv run --no-project --python 3.12 --with scenedetect --with opencv-python python -I "$S/motion_read.py" cuts refs/motion/12-motion-archive.mp4
```

**Generated: judge Light by default, and only if more than 3 candidates survive the gates. Coded: usually no judge,**
since the answers come from records and code. Run one only on a generated still's light, when more than 3 candidates
survive. We have not run the demographic swap, so for light prefer frames without people, and a person confirms the rest.
For other jobs the criteria tables are a draft, off by default. On a small budget: Light only, 2 reads per family. Ask
binary questions about visible things only, with labels stripped and order shuffled, then take the best few to pairs in
both orders. No API key: `read` uses the person's own logged-in `claude` or `codex` CLI.

```bash
C="$S/../assets/criteria/light.json"
python3 -I "$S/judge.py" blind refs/ blinded/                    # no metadata, random ids, never upscales, ledger kept apart
python3 -I "$S/judge.py" read blinded/light --family claude --want want/light.txt --criteria "$C" --reads 3 --out reads.jsonl
python3 -I "$S/judge.py" read blinded/light --family codex --want want/light.txt --criteria "$C" --reads 3 --out reads.jsonl
python3 -I "$S/judge.py" enforce reads.jsonl --criteria "$C" > enforced.jsonl
python3 -I "$S/judge.py" aggregate enforced.jsonl --criteria "$C" > shortlist.json
```

Pairs, prompts, criteria and the budget rules are in `references/judge.md`. What we measured on this judge is in
`references/judge-evidence.md`. It is weakest on rooms with no face, so a person looks at anything the checks rank low that
fits the brief.

### 6. The person picks

Put three candidates per job on the board, grouped by job, shuffled, with no scores until they choose. Reference lists
ranked in one column raise fixation ([Chan et al. 2024](https://arxiv.org/abs/2401.11022)), so do not make one.

```bash
python3 -I "$S/board.py" board.json board.html --seed 7          # input shape in references/templates.md
```

`board.py` numbers candidates after shuffling. A `look` reference goes on as a link with no image. Do not use
`varg-mockups` for this: it is a storyboard template. If nobody is there, name the first passer per job and say so.

Close the loop for one or two rounds. Picks go to "more like this": FrameThrower `/similar`, the Are.na connection walk
(`python3 -I "$S/search.py" arena-walk <block>`), a person's Google Lens. Rejects go to `never.md` with the reason.

### 7. Write the job cards

One per kept candidate, in `refs.md` (template in `references/templates.md`). Mark the picks when the person picks.

```
id · job · URL · maker · year · what I see · lends (one thing, with numbers from a measurement or record) ·
must not copy · rights (feed | words | look) · provenance label · query and rank that found it
```

Then pass on. Generated: the look comes next, in `video-moodboard`. Coded: `DESIGN.md` and `timing.md` go to `hyperframes`,
`code-to-video-previz`, `kinetic-type-art` or `motion-formats`. Anyone who recurs: `character-passport`.

### Optional: what people save this week, and ten ideas

When the piece rides a trend, search X for the format (`references/experts.md`). If the person asks for visual ideas, write
up to ten in `ideas.md`, each built from two or more references of different jobs (`references/templates.md`).

## For code, and for generation

| | Coded (HyperFrames, Remotion, three.js) | Generated (Seedance, Kling, Veo, Nano Banana) |
|---|---|---|
| Light | none on a flat film. Where a shot has it: HDRI choice, key angle, shadow softness, glow values | real-looking source: direction, hardness, colour |
| Framing | grid, margins, scale ratios, safe zones | shot size, lens, staging |
| Texture | noise, grain shader, PBR maps | material words, or a neutral close-up reference |
| Palette | exact hex and contrast | named colours and a chosen frame, loosely held |
| Type | exact licensed font, tracking, size in px | avoid in frame; overlay in code |
| Motion | seconds per beat, ease curve, what moves first, stagger | camera verb, subject action, cut rate |
| Rights question | shipped fonts, textures, code licences, any generated person | every fed image |
| Output | `DESIGN.md` plus `timing.md` | role lines plus a look description |

Hybrid is often the answer: generate plates, and set type and data in code.

## Done when

- `brief.json` exists, with each field marked, and `queries.md` shows a pack for each job this piece needs.
- `never.md` has tests from a search you ran and from the person's stated hates, each one a stranger could check.
- `refs.md` has a job card per kept candidate, with what you saw, one job, what not to copy, rights and provenance.
- `search_log.jsonl` records each search, including silent zeros and blocks.
- `links.md` lists the searches only a person may open, and says what you could not find.
- `board.html` shows three candidates per job, and the person has picked, or you said why not.
- Coded: `DESIGN.md` and `timing.md` exist, with every value labelled measured, record, by eye or assumed.
- If a generated person appears in an ad, you flagged possible disclosure (New York, EU Article 50(4)) for the person to
  decide.
- No person-only site was fetched, no real person's face was fed, and nothing in any file was invented.

## Reference files

Claims in these files carry a label: `tested 2026-11-03` (run that day), `reported` (read, not reproduced), `our proposal`
(a synthesis nobody has validated).

| File | Use it for |
|---|---|
| `references/queries.md` | **always**: from a request to query packs, fusion, the feeling table, one worked brief |
| `references/light.md` | **the priority job for generated work**: read light, search it, verify it |
| `references/framing.md`, `texture.md`, `palette.md`, `type-graphics.md`, `motion.md` | one job each |
| `references/people.md`, `characters.md`, `location.md`, `style-boards.md`, `music.md` | one job each |
| `references/never.md` | never board, dated tells, keeping slop out, provenance labels |
| `references/judge.md` | the judge protocol, commands and criteria |
| `references/judge-evidence.md` | our bench, published bias findings, the prompts as tested, how to test your own judge |
| `references/sources.md` | who may read what, person-run link templates, unstable endpoints |
| `references/experts.md` | who to learn from per job, how to search X, MCP servers that exist |
| `references/evidence.md` | what is measured, what is only our proposal, what nobody has tested |
| `references/templates.md` | file templates: brief, want card, job card, never, links, board input, ideas, `DESIGN.md`, `timing.md` |
| `references/goal-prompt.md` | the whole skill as one prompt to paste after `/goal` or into any agent, and short prompts per job |

Judge questions per job: `assets/criteria/`.

## Related skills

- `video-moodboard`: turns chosen references into a checked board. It is the next step for generated work.
- `hyperframes`, `code-to-video-previz`, `kinetic-type-art`, `motion-formats`: the next step for coded work, from
  `DESIGN.md` and `timing.md`.
- `character-passport`: builds the cast once the identity card is written, for anyone who recurs. Not for one still.
- `video-sound`: makes the sound once the music reference is picked, and casts voice candidates.
- `media-judge`: judges finished takes. This skill judges references.
- `how-to-make-ai-video`: the whole ten-step film. This skill is its step 1.
- varg how to, for existing guides and skills on a format: `curl -s "https://varg.ai/how-to/api/search?q=coffee+ad"`. It
  returns how-to guides and skills to install, not references.
