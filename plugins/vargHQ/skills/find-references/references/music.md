# Music references

An agent cannot hear. Everything it finds is on target by metadata and curator fit only, so a person chooses. A good
music reference proves era, instruments, a tempo range and what the music does in the scene. It does not prove the track
fits the picture, and nothing an agent reads can prove that. Never say you heard a track.

This file finds and frames the reference. To make the sound, with the cue sheet, beats, mix and checks, use the
`video-sound` skill.

## Read it

Write the cue brief before any search. Supervisors start from story. Randall Poster: "Sometimes music is the motor that
drives the story forward. Sometimes it is a moment of emphasis or a moment of clarification"
([WIPO](https://www.wipo.int/en/web/wipo-magazine/articles/music-and-the-movies-an-interview-with-randall-poster-39133)).
Thomas Golubić: "Not using music is as powerful as using music"
([AwardsDaily](https://www.awardsdaily.com/2019/08/28/better-call-saul-music-supervisor-thomas-golubic-on-storytelling-with-songs)).
So ask first whether it needs music at all. With temp love, find out what they love and "guide the client toward
something fresh" ([Soundstripe](https://www.soundstripe.com/blogs/how-to-avoid-temp-love)).

`our proposal`, built from those quotes and [Swell's brief
fields](https://swellmusicsound.com/learn-more/how-to-brief-a-music-supervisor-for-your-ad-campaign/):

```text
scene and beat:     what happens, what the viewer must feel (not what they see)
job of the music:   motor / emphasis / clarification / irony / none
world:              whose music is this? on-screen source or score?
enters / leaves:    timecode, and what happens in the silence before it
tempo and feel:     BPM range, straight or swung, driving or floating
instruments:        3 to 5, plus "no X" lines
era and production: decade, place, recording texture
lyric or not:       instrumental under any voice; if lyric, what the words may say
reference + why:    track, the 3 attributes borrowed, what to ignore
NOT:                what it must not be
route and rights:   license / generate / silence; platform, length, budget
```

Then work in this order:

1. Search each source in its own words (below). Log failed queries and show them: a zero means the wrong words, not no
   music.
2. Shortlist with reasons. Hand over several options, not one. Brienne Rose sends "ten ideas for one scene"
   ([Vice](https://www.vice.com/en/article/music-supervisor-brienne-rose-on-how-to-choose-the-perfect-music-for-tv/)).
3. The person listens against picture, picks, and fills in `reference + why`.
4. License it, or generate from the card with no names.

## Search it

Use three vocabularies. Databases want catalogue words, libraries want filter words, generators want attribute
sentences. In our three worked briefs, the first useful query was an era or function query, and mood adjectives returned
the least useful results or none.

| Kind | Wants | Worked | Failed, `tested 2026-11-03` |
|---|---|---|---|
| Databases | Genre, style, tag, year | `tag:"library music"`, `style=Berlin-School`, `year=1976` | `tag:"felt piano"` gave 0 on MusicBrainz |
| Sound and library search | Sound words, instrument, BPM, duration | `room tone`, `bottle pump`; `felt piano` found loops on Openverse | Adding `category=music` on Openverse gave 0, because Freesound rows have a null category |
| Generators | Attribute sentences | "1976 analog step sequencer, 16th notes at 120 BPM" | Names, and `epic`; see below |

**A silent empty is a vocabulary failure.** `tested`: Discogs `q=library+music&style=Library+Music&decade=1970` returned
HTTP 200 with 0 items and no error, because "Library Music" is not a style. `decade=1970` also did not restrict the
year: `style=Soundtrack&decade=1970&type=master` returned 34,977 items whose first rows were dated 2014, 2017 and 2023.
Use `year=`.

`tested 2026-11-03`. Reference tracks are `look`: a person listens, nobody keeps copies, and only the attributes travel
as `words`. `scripts/search.py` wraps `musicbrainz`, `listenbrainz`, `discogs` and `openverse-audio`.

| Source | Exact call | What came back | Access | Verdict |
|---|---|---|---|---|
| ListenBrainz | `https://api.listenbrainz.org/1/lb-radio/tags?tag=library%20music&operator=and&pop_begin=0&pop_end=100&count=6`, then `https://api.listenbrainz.org/1/metadata/recording/?recording_mbids=<ids>&inc=artist` | Alan Hawkshaw "Lost Spirit", Roger Roger "Lightly Amusing" | `agent`. `/1/explore/lb-radio` is `token`: "Due to bad actors and AI scrapers" | Best for similarity |
| MusicBrainz | `https://musicbrainz.org/ws/2/release-group?query=tag:"library music" AND firstreleasedate:[1970 TO 1979]&fmt=json&limit=5` (URL-encode it) | Count 7: "Condizione umana", "Metal Sunrise", "Genti e Paesi del mondo". [Genre list](https://musicbrainz.org/ws/2/genre/all?fmt=txt) 2,222 lines | `agent`, [1 request/s](https://musicbrainz.org/doc/MusicBrainz_API/Rate_Limiting) with an identifying user agent | Best for era and vocabulary. Artist tag search is noisy: `tag:"dream pop" AND country:GB` led with Coldplay |
| Discogs API | `https://api.discogs.com/database/search?style=Berlin-School&type=master&year=1976&per_page=5` | Tangerine Dream "Stratosfear", Klaus Schulze "Moondawn" | `agent`, keyless today, 25/min. API only: the website is 403 and its developer terms are unread | Best for era and style |
| NTS | `https://www.nts.live/api/v2/search?q=library%20music&version=2&offset=0&limit=3&types[]=episode`, then `https://www.nts.live/api/v2/shows/guests/episodes/la-dimostrazione-9th-november-2018/tracklist` | "La Dimostrazione: Highlights from the CAM Library", 6 tracks | `agent`, undocumented | Best curated tracklists |
| Are.na | `https://api.are.na/v2/search/channels?q=library%20music&per=8` | "LIBRARY SOUNDS" 147 blocks, "Bruton Music" 21 | `agent`, targeted lookups only | Human taste, the Pinterest for sound |
| [Bandcamp Daily](https://daily.bandcamp.com/lists/library-music-album-guide) | Web search limited to `daily.bandcamp.com` | Library music primer. Separate from bandcamp.com, and robots leaves articles open | `agent` | Good expert lists |
| [Openverse audio](https://api.openverse.org/v1/audio/?q=room+tone&license_type=commercial,modification&page_size=4) | `q=room+tone&license_type=commercial,modification` | CC0 room tones. `bottle pump` 14. Calls took up to 41 s, so set a 60 s timeout | `agent`. Rights for audio used as an asset: CC0 or BY is `feed` after you check `license` | Room tone and effects |

Scene-level song data has no agent path. MusicBrainz `secondarytype:soundtrack AND releasegroup:"Baby Driver"` and
Wikipedia work at film level only.

**Person only: write these in `links.md` as links, and never fetch them.** An HTTP 200 is not permission; robots rules
and terms are. Access `person`, rights `look`.

- [Rate Your Music](https://rateyourmusic.com/robots.txt): "prohibits any kind of automated means".
- Every Noise at Once: robots disallow named AI bots, and it has been [frozen since a December 2023
  layoff](https://techcrunch.com/2024/02/12/every-noise-shut-down-spotify-layoffs).
- Bandcamp tag and discover pages: robots disallow ClaudeBot, GPTBot and CCBot by name. It is the [best human source for
  non-AI music](https://djmag.com/news/bandcamp-bans-ai-generated-music), given its AI ban since January 13, 2026.
- Music-Map, Gnoosic, Tunefind, WhatSong, WhoSampled, Radiooooo, [Cosine.club](https://cosine.club/), YouTube Audio
  Library.

## Licence traps

These rules are for audio used as an asset. They replace the CC BY default in `SKILL.md`, which is for images and video.

- **CC BY-ND under video is out.** CC law says music synced in timed relation with a moving image is an adaptation ([CC
  BY-ND 4.0](https://creativecommons.org/licenses/by-nd/4.0/legalcode.en)). `tested`: Openverse
  `license_type=commercial` still returned BY-ND and `commercial,modification` still returned BY-SA. Filter again on
  `license`, and keep CC0 and CC BY.
- **Deezer and Last.fm are non-commercial.** Deezer: "strictly limited for a non-commercial purpose"
  ([terms](https://developers.deezer.com/termsofuse)). Last.fm: "solely for non-commercial purposes"
  ([terms](https://www.last.fm/api/tos)). So `artist/<id>/related` is for private research only, even though `tested`
  "Cocteau Twins" returned Slowdive and The Sundays.
- **Do not download iTunes or other store previews, to analyse them or for anything else.** Apple says previews must be
  "streamed only, and not downloaded, saved, cached, or synchronized with video"
  ([Apple](https://performance-partners.apple.com/search-api)). Deezer forbids bypassing its measures to download. This
  rules out running audio models on previews.
- **A trending TikTok song is [not automatically
  cleared](https://www.soundstripe.com/blogs/tiktok-music-library-explained)** for ads.
- **Every asset gets a row:** source URL, licence, whether credit is needed, platforms it may run on. No row, no use
  (`our proposal`).

Asset routes. Terms are `reported`, as read on the linked pages:

| Route | Agent access | AI terms | Verdict |
|---|---|---|---|
| [Epidemic Sound MCP](https://www.epidemicsound.com/tools/mcp/) | `token`. Official, beta. Endpoint 401 without auth, not tested. "Search by mood, BPM, genre, key, instrument, or a reference track" | "No separate AI licensing". Silent on training. Its [blog](https://www.epidemicsound.com/blog/mcp-server/) conflicts on whether search needs a subscription | Best for agents |
| [Artlist](https://help-center.artlist.io/media/w5mglb2w/current-pro-license-permitting-assets-in-ai-clean-01042026.pdf) | `person` downloads | Assets may be AI inputs but not train models, and not with community AI services. Output stays an Asset | Best written terms |
| [TikTok CML](https://ads.tiktok.com/help/article/how-to-use-the-commercial-music-library) | `person` | "global music library of 1 million songs" | Best for TikTok ads only |
| Openverse, CC0 or CC BY only | `agent`, keyless | See the BY-ND trap above | Good for effects |
| [Sonniss GDC](https://sonniss.com/gdc-bundle-license) | `person`, bundle download | "personal and commercial projects"; training banned | Good for effects |
| [De Wolfe](https://dewolfemusic.com/page/US_Licensing_Info) | Search not tested | Owns its masters per its site. Terms unread | Route to real vintage library cues |

## Voice

A voiceover needs a voice reference as much as a music cue. Write one casting line before anything else: age, region, texture,
pace. Then hand it to `video-sound`, which renders the hardest lines in 3 to 5 candidates for a person to pick
(`references/voice.md` there). An agent cannot hear these either. Clone only a voice you have the right to use.

## Measure it

Analyse only audio you have rights to: your own file, a licensed download, or CC. If a person cannot supply a file, the
person listens and fills the card. You may add a [SongBPM](https://songbpm.com/@max-richter/on-the-nature-of-daylight)
number, marked unverified.

`scripts/sound.py measure` and `beats` in `video-sound` do the measuring.

**Report tempo as a range with its half and double, never as one number.** On one CC0 piano file ([Freesound
112071](https://cdn.freesound.org/previews/112/112071_682033-hq.mp3)), `tested 2026-11-03`, librosa read 172.3 BPM and
Essentia 165.2. On a known track, Deezer's field gave 117.45 and SongBPM gave 85 with "double-time at 170". Mark ambient
pieces "no reliable BPM" and describe the pulse in words: "floating, no percussion until 0:18". librosa
([ISC](https://github.com/librosa/librosa)) is the safer default in anything shipped: Essentia is ["Affero GPLv3, for
non-commercial applications"](https://essentia.upf.edu/licensing_information.html).

## Queries

Bad to good. Prompts are `our proposal`, run through no model. Database queries are `tested 2026-11-03`.

| Bad | Good for a generator or brief | Good for a database (count) |
|---|---|---|
| `epic` | "sparse felt piano, tape hiss, 62 BPM, no percussion until 0:18, 1970s Italian library music" | `style=Modern+Classical&q=piano&year=2015` (63) |
| `retro` | "1976 analog step sequencer, 16th notes at 120 BPM, no drums until bar 9, dark filter sweep" | `style=Berlin-School&type=master&year=1976` (5) |
| `70s crime` | "1972 Rhodes, wah guitar, dry tight drums, flute stabs, 98 BPM, library-music mix" | `tag:"library music" AND firstreleasedate:[1970 TO 1979]` (7) |
| `library music` | As above | Not `style=Library+Music` (0, silent). MusicBrainz tag, or Discogs `q=KPM` (5,880) |
| `upbeat corporate` | "handclaps on 2 and 4 from a real room, nylon guitar, 104 BPM, no ukulele, no whistle" | Library filter on instrument and BPM |
| `dark` | "low drone at 40 Hz, distant metal scrape, no melody, no pulse" | MusicBrainz genre `dark ambient` (in the list) |
| `fun TikTok music` | "no music, room tone from a small kitchen, one bottle pump at the reveal" | Openverse `room tone`, `bottle pump` (14) |

Picture to sound: warm palettes suggest organic instruments, fast cuts quicker tempos, and "not all beach scenes need steel
drums" ([Audio Network](https://blog.audionetwork.com/the-edit/music/how-to-build-a-music-brief-from-a-mood-board), a seller's
practitioner advice with no validating study).

Worked briefs, every query run `tested 2026-11-03`. Nothing was heard, and a person picks at the end of each.

| Brief | First useful query | Came back | Route |
|---|---|---|---|
| 40 s AI teaser, Milan 1974, night heist. Job: motor | MusicBrainz `tag:"library music" AND firstreleasedate:[1970 TO 1979]` | Umiliani "Genti e Paesi del mondo" (1975), Peymont and Braen "Paese sotto inchiesta" (1971) | License real library cues, or generate from the card |
| 30 s HyperFrames launch, cuts on the bar, 120 BPM. Job: motor | Discogs `style=Berlin-School&type=master&year=1976` | Schulze "Moondawn", Göttsching "New Age Of Earth" | Generate, then measure and make the stop in the edit |
| 25 s UGC skincare ad, a voice leads. Job: none | Openverse `room tone`, `bottle pump` | "Room Tone Apartment Small Bachelor" (CC0, 46 s), "Squirt Bottle x3" (CC0, 5.9 s) | Room tone and one pump, or a quiet TikTok CML bed |

## Borrow or never

Not legal advice. Prompt from the reference card only, and run a name check before sending: the prompt must hold none of
the reference's artist, song, album, label or lyrics.

**Borrow:** tempo, meter, instrumentation, recording era, arrangement order, dynamic shape, mix texture.

**Never borrow:** melody, hook, lyrics, a recognisable voice, a signature riff, an artist's or song's name.

| Source, `reported` | What it says |
|---|---|
| [*Midler v. Ford*](https://static.case.law/f2d/849/cases/0460-01.json) | When "a distinctive voice of a professional singer is widely known and is deliberately imitated in order to sell a product", the sellers commit a tort in California |
| [Munich court, GEMA v. Suno](https://www.musicbusinessworldwide.com/suno-infringed-copyright-in-gema-case-german-court-rules) | Ruled against Suno on July 31, 2026, first instance and appealable |
| [ElevenLabs Music Terms](https://elevenlabs.io/music-terms) | Bans "any artist's real name or stage name" by contract. Audio Reference "is designed for music you've made yourself" ([docs](https://elevenlabs.io/docs/overview/capabilities/music)) |
| [Suno help](https://help.suno.com/en/articles/3198209) | Prompts with well-known names "may not generate" |

## Code vs generated

**Code-made video.** The reference must prove a tempo range and a bar grid you can cut on. The output is a cue brief, a
picked track or bed, and a beat map from `video-sound`. Music models keep tempo, not structure: 0 of 3 made the planned
stop in our paid tests, per the `video-sound` skill. So make stops and exact lengths in the edit.

**Generated video.** The reference must prove attributes you can say in words. The output is an attribute sentence with
no names. Lyria takes `120 BPM`, keys and bracketed structure
([guide](https://aistudio.google.com/docs/lyria-prompt-guide)). Do not upload a track you do not own or license.

## Reject if

- The prompt or the card holds an artist, song, album or label name, or the person hears the reference in the output.
- The track came from a store preview or a person-only site that an agent fetched.
- It is CC BY-ND or BY-NC under commercial video, or it has no licence row.
- It is a trending song in a business TikTok, unconfirmed in the Commercial Music Library for that region.
- Tempo is one number from one tool. Ambient is given a BPM.
- The whole description is `epic`, `cinematic`, `inspiring`, `corporate` or `upbeat`.
- A stock instrument stands in for a mood, such as ukulele and whistle for happy.
- Music starts on frame one by habit, with nobody having decided where it enters.

Universal rejects: [`never.md`](never.md).

## Judge it

Music A1 to A6 in [`judge.md`](judge.md), a draft and off by default. A1 to A3 are code, A4 needs the record, A5 is a text
question with no image, and A6 is always a person.
