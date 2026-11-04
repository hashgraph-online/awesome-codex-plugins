---
name: find-references
description: >-
  Find real references for a video before anything is made, then turn them into ten visual ideas. The agent
  goes through seven sources in order (varg how to, X from the last 7 days, Refs, FrameThrower, the film-still
  libraries, Pinterest and Are.na, YouTube) and comes back with four kinds of reference: style (palette, light,
  texture, type), film (framing, lens, camera move), pop culture (moments people recognize) and trends (what
  people saved this week, with the numbers). It writes refs.md, trends.md, links.md and ideas.md and builds one
  board to pick from. Use when someone says "find references", "reference board", "what should this look like",
  "give me visual ideas", "moodboard references", "make it not look like AI", or starts a video with no look yet.
  Not for writing the look bible from chosen references (varg-video-prompting) or for downloading one known link
  (media-download).
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
  openclaw:
    requires:
      anyBins:
        - curl
        - python3
    homepage: https://github.com/vargHQ/skills/tree/main/find-references
compatibility: >-
  Works in any agent with a shell and web access. Refs search is free with no key: connect it as MCP or call it
  with scripts/mcp_call.py (Python 3, standard library); its frame sheets and blueprints need Refs Pro.
  FrameThrower needs a FrameThrower account (OAuth sign-in, $2 free credit, then pay per use), so connect it as
  MCP. X needs an X MCP or API; without one the agent falls back to web search and says so. Pinterest images need
  gallery-dl (via the media-download skill), YouTube clips need yt-dlp. No varg credits are used.
allowed-tools: Bash(curl:*) Bash(python3:*) Bash(yt-dlp:*) Bash(gallery-dl:*) Bash(ffprobe:*) Read Write Edit
---

# Find references

Without a reference the agent falls back to its default look: "centered text, gradient background, everything
fading in" (https://x.com/rexan_wong/status/2103707054108299437, 18K bookmarks). "Most AI videos look cheap
because nobody gives the AI a real film reference" (https://x.com/ScaleWthAI/status/2111821935021863254). A search
that stays in the middle finds the same average. This skill sends the agent to seven places, in a fixed order,
for four kinds of reference, and makes it show what it found before anyone writes a prompt.

## What you come back with

Four kinds of reference ("atoms"). Each kept reference is one of them:

| Atom | What it lends | Minimum |
|---|---|---|
| **Style** | palette, light quality, texture and grain, type, grade | 3 |
| **Film** | framing, lens, camera move, cut, staging | 3 |
| **Pop culture** | a moment people recognize: a music video, an anime opening, a game cinematic, an iconic costume, an era, an ad everyone remembers | 2 |
| **Trend** | what people saved this week in this format, with likes, bookmarks, views and date | 3 |

Then **ten visual ideas**, each built from at least two references of different kinds.

Files, all in the project folder:

```
brief.md      the brief in 6 lines
refs/         every frame or clip the agent actually opened, named NN-atom-source.ext
refs.md       one entry per kept reference (template in references/templates.md)
trends.md     the trend posts with their numbers
links.md      search links for the sites only a person may open
ideas.md      the ten visual ideas
board.html    everything numbered on one page, to pick from
```

## Rules

1. **Open every reference you keep.** Never describe a frame you did not see, and never invent a film, a scene or
   a post. If a source is out of reach, write what you could not open.
2. **Respect the sites that block bots.** Film-Grab, Shot Cafe, Eyecannndy, ShotDeck and Film Vibes forbid
   crawling and automated use (robots.txt, Cloudflare, terms). Never fetch them. Build search links for the
   person in `links.md`; frames the person drops into `refs/` count as references.
3. **Borrow the look, not the content.** Palette, framing, lens, light, texture and motion. Never actors,
   characters, logos, recognizable people or "in the style of" a living filmmaker.
4. **Found frames are for words and for judging, not for feeding a generator.** Whatever sits in a reference
   image comes back in the shot, including someone else's actor, set or logo. Feed a model only frames the person
   owns or licensed, and later your own approved stills.
5. **Skip the first, obvious pick.** For every idea, drop what comes to mind first and look one step further
   (for a sci-fi look, not Blade Runner). The middle of a search is the average you are trying to avoid.
6. **Give every reference one job** and say what it must not copy: "The reference image defines WHO the person
   is, not the pose, location, expression, clothing, lighting, or composition"
   (https://x.com/swiat_ai/status/2100482637341012201).
7. **Numbers come from the source.** Copy likes, bookmarks, views, installs and dates as the source shows them;
   never round them up or guess them. Bookmarks show usefulness better than likes.

## Step by step

### 0. Brief

Write `brief.md` in six lines: what the video is, who it is for, where it plays (platform, aspect ratio), length,
the brand or product, and taste (one or two things the person loves, one thing they hate). If the person already
gave references, they go first in `refs/` and every search starts from them. If the brief is missing a line, ask
once, then go on with a stated assumption.

Turn the brief into search words: name the feeling, not the subject ("lonely, sodium-lit, wet" finds a look,
"night market" finds stock photos), and add attributes (color, light direction, lens, decade, film stock, shot
size, mood).

### 1. varg how to: what already worked

Search the catalog for the format and the look. It returns style cards, tutorials and prompt cards taken from
viral posts, with their bookmarks and views.

```bash
curl -s "https://varg.ai/how-to/api/search?q=<format and look in plain words>"
```

Or `search_how_to` on the varg how to MCP, or `vargai search "<query>"`. Run 3 to 5 searches, not 50. Search
results carry no numbers: open the 2 or 3 cards closest to the brief (add `.md` to the card's link) and copy their
installs, GitHub stars or, for prompt cards, the bookmarks and views of the post they came from. Keep them as
style or trend atoms.

### 2. X, the last 7 days: what people save now

Search for the format, the look and the tools, newest week only, and rank by bookmarks:

```
<format or look> since:<date 7 days ago> min_faves:100 -filter:retweets
<model or tool> prompt since:<date 7 days ago> min_faves:50
```

X has no sort by bookmarks: filter with `min_faves:` and rank by bookmarks yourself. Ask for 10 to 20 posts per
search, not 100: posts often carry whole prompts and long results get cut off. Read the top posts; the prompt is
in the post, its link or the author's first reply. Watch the video before you keep a post: the text and the clip
do not always match. For each kept post write a line in
`trends.md`: link, author and followers, date, likes, bookmarks, views, and the look or format in one line.
Posts with far more bookmarks than the author's following suggests, and bait hooks, are suspect: keep them only
when nothing else shows the same trend.

Use an X MCP or the X API if one is connected. Without one, search the web for `site:x.com <query>`, keep only
posts you could open, and write in `trends.md` that X search was not available.

Extra trend sources when they fit: the Civitai MCP (what AI looks are popular this week, with prompts; needs a
Civitai key), TikTok Creative Center and the Meta Ad Library for ads (see `varg-ad-library-remix`).

### 3. Refs: films like this one, measured

Refs (https://refs.video) holds 4,000+ launch films, product demos, explainers, motion pieces, teasers and UGC
ads, each taken apart shot by shot (cut map, pacing, palette, type, voice, music). Searching is free with no key
and returns short cards: title, maker, length, aspect, summary, thumbnail and a link that plays the film.

- `search_videos` with the brief in plain words (filters: category, aspect, seconds, platform, brand).
- Look at the thumbnails and open the 2 or 3 best on refs.video or their original post.
- With Refs Pro: `get_frames` for labelled frame sheets and `get_blueprint` for the beats, shot list and style
  guide of the one you keep. Without Pro, say which films you could only see as cards.

Connect it as MCP (`claude mcp add --transport http refs https://refs.video/mcp`) or call it with the script:

```bash
python3 scripts/mcp_call.py https://refs.video/mcp search_videos '{"query":"founder-led launch film under 60 s","limit":8}'
```

Films play from their original posts and stay their makers'. Do not download or bulk-export them.

### 4. FrameThrower: film frames, ads and animation

FrameThrower (https://framethrower.ai) is a cinematography library indexed frame by frame, with credits. It needs
a FrameThrower account: connect it as MCP and sign in once (`claude mcp add --transport http framethrower
https://framethrower.ai/api/mcp`, then `/mcp` to authenticate); new accounts get $2 of credit, then it is pay per
use. It covers three of the four atoms:

- **Film:** `search_frames` by concept, mood or color; `find_by_craft` by lens, shot size, visual style, setting,
  time of day, director or years; `find_similar` for "more like #2".
- **Ads:** `search_commercials` and `search_commercial_shots` by idea or by what is in the frame.
- **Pop culture:** `search_animation_frames` and `find_animation_titles` (anime and Western animation).

Example call: `find_by_craft` with `{"lens": "anamorphic", "time_of_day": "night", "limit": 8}`. Use the frames to
see and name the look. They are someone else's films: rule 4 applies. If FrameThrower is not connected, say so
and lean on step 5 for film atoms.

### 5. Film-still libraries: links for the person

These are the best human libraries and they forbid bots. Write searches into `links.md`, grouped by what to look
for, and ask the person to open them and drop 1 to 3 frames each into `refs/`:

| Site | Link pattern | Good for |
|---|---|---|
| Film-Grab | `https://film-grab.com/?s=<query>` | full sets of stills from one film; lens, stock and process words |
| Shot Cafe | `https://shot.cafe/tag/<tag>` (spaces as `%20`) | shot type, light, day or night, interior or exterior |
| Eyecannndy | `https://eyecannndy.com/technique/<slug>` | the name of a technique you can see but cannot name |
| ShotDeck | `https://shotdeck.com` (search needs a login) | color, light, camera angle, location; shot cards list palette, lens, lighting and film stock |

Never fetch these pages, not even to check a link.

### 6. Pinterest and Are.na: curated boards

People have already curated costumes, grades, posters, sets, cosplay and eras. Search by attribute, not subject:
`<film> still`, `<director> color palette`, `<decade> film grain`, `<character> cosplay`, `<genre> lighting`.

- Pinterest images: the `media-download` skill (`scripts/pinterest.sh -n 8 -o refs "<query 1>" "<query 2>"`,
  gallery-dl underneath, run through uvx if it is not installed). Its `references/pinterest-presets.md` has ready
  query sets. Saved files are not named by pin, so link the search page as the source.
- Are.na: the Are.na MCP (`https://mcp.are.na/mcp`) or its API to search channels and read the person's boards; it
  can hold the final board. Its image files refuse direct downloads: put the channels in `links.md` and do not
  work around the block.

### 7. YouTube: motion and pop culture

Music videos, trailers, title sequences, game cinematics, anime openings and ads people remember. Search, watch
the 2 or 3 best, and note the timestamps of the moments you would borrow. Pull a 5 to 15 second clip with yt-dlp
(`media-download`'s `video.sh`) only where motion or pacing matters, and keep it for reference.

### 8. Board and picks

Put every candidate on one page, numbered, with its atom, its source link and one line on what it lends: use the
`varg-mockups` board (`templates/board.html`) or a plain HTML contact sheet. Aim for 20 to 30 candidates. Keep the
12 or more that are strongest and most different from each other, covering every atom at its minimum. When the
person is present, let them pick; otherwise pick yourself and say why.

### 9. refs.md

One entry per kept reference, in the format in `references/templates.md`: number, atom, source and link, what it
lends (palette with named colors, framing, light direction and hardness, lens, texture, motion), its one job and
what it must not copy.

### 10. Ten visual ideas

Write `ideas.md`. Each idea:

- a title and a one-line pitch
- the references it combines, by number, from at least two different atoms
- the look line: medium, palette with the accent named, lens, light, grain, motion
- the first shot in one sentence
- why now: the trend post it rides, with its numbers; use a different trend for each idea where you can (wild
  ideas may have none)
- the risk: what could make it slop, and any rights question

Spread them: 3 close to what is working this week, 4 stretches, 3 wild. No two ideas share the same main
reference. None may fall back to centered text, a gradient background and everything fading in. Add the ideas to
the board and stop there: the person picks one or two, and the look bible comes next (`varg-video-prompting`,
look line plus a Never list).

## Done when

- `refs.md` has 12 or more references the agent or the person opened: 3+ style, 3+ film, 2+ pop culture and 3+
  trends from the last 7 days with their numbers.
- Every entry has a source link, what it lends, one job and a do-not-copy line.
- `links.md` lists the searches only a person may open.
- `ideas.md` has 10 ideas, each from 2+ references of different atoms, spread 3 / 4 / 3.
- `board.html` shows every reference and idea, numbered, with sources.
- Nothing in any file was invented, and no blocked site was fetched.

## The same thing as one prompt

`references/goal-prompt.md` holds this skill as one prompt to paste after `/goal` in Claude Code (or as a task in
any agent). `references/sources.md` has the seven sources in detail: tools, queries and what each one may be used
for.

## Related skills

- `media-download`: Pinterest images and YouTube or X clips for steps 6 and 7.
- `varg-mockups`: the review board for steps 8 and 10.
- `varg-video-prompting`: the look bible and Never list once the person picks an idea; its
  `references/look-references.md` is the short version of this skill.
- `how-to-make-ai-video`: the whole ten-step film; this skill is its step 1.
