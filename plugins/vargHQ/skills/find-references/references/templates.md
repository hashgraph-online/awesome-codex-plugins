# File templates

## brief.md

```
What:      <the video in one line>
For:       <who watches, what they care about>
Plays on:  <platform, aspect ratio>
Length:    <seconds>
Brand:     <name, product, anything fixed: logo, colors, fonts>
Taste:     loves <1-2 things>; hates <1 thing>
```

## refs.md

One entry per kept reference. Number them in the order they appear on the board.

```
## 07 · film · FrameThrower — <film title> (<year>), dir. <director>, DP <DP>
Link: <url to the frame or page>
File: refs/07-film-framethrower.jpg (or "opened in the browser, not saved")
Lends: palette — deep teal shadows, one sodium-orange accent; framing — centered, wide headroom; light — single hard
source from frame left; lens — anamorphic, oval bokeh; texture — fine grain; motion — slow lateral dolly
Job: sets palette and light for the night scenes
Do not copy: the actor, the costume, the street signs, the film's text
```

For a trend, add the numbers exactly as the post shows them:

```
## 11 · trend · X — @<author> (<followers> followers), <date>
Link: https://x.com/<author>/status/<id>
Numbers: <likes> likes · <bookmarks> bookmarks · <views> views
Lends: <the look or format in one line>
Job: proves the format is being saved this week
Do not copy: the creator's characters and words
```

## trends.md

```
| # | Post | Author (followers) | Date | Likes | Bookmarks | Views | The look or format |
|---|------|--------------------|------|-------|-----------|-------|--------------------|
```

Add one line at the top on how X was searched (X MCP, X API, or web search fallback) and anything you could not see.

## links.md

Searches for the sites only a person may open, grouped by what to look for:

```
## Night exteriors, sodium light
- Film-Grab — search "anamorphic night": https://film-grab.com/?s=anamorphic%20night
- Shot Cafe — tag: night: https://shot.cafe/tag/night
- Eyecannndy — technique: dolly zoom: https://eyecannndy.com/technique/dolly-zoom
Drop 1-3 frames from each into refs/ and tell me which ones.
```

## ideas.md

```
## 3 · <title> (stretch)
Pitch: <one line>
Built from: 07 (film) + 12 (pop culture) + 11 (trend)
Look line: <medium>, <palette with the accent named>, <lens>, <light>, <grain>, <motion>
First shot: <one sentence>
Why now: <trend post link> — <likes> likes, <bookmarks> bookmarks, <date>
Risk: <what could make it slop>; <any rights question>
```

Ten ideas: 3 close to what is working this week, 4 stretches, 3 wild. No two share the same main reference.

## board.html

One page, every candidate numbered, with its atom, a thumbnail or link, the source under it and one line on what it
lends; the ten ideas below with the reference numbers they combine. The `varg-mockups` board
(`templates/board.html`) does this with approve / reject and a note per frame.
