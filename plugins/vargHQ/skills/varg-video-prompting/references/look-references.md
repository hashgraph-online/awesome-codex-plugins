# Look references: where to find them and how to use them

Without specific references an agent picks the safe, middle version of every look, and the film looks like every
other AI video. "Most AI videos look cheap because nobody gives the AI a real film reference"
(https://x.com/ScaleWthAI/status/2111821935021863254). People often cannot describe the look they want either; a
few real frames give both sides the words. This step comes before the look bible (step 2 of the working loop).

The full version, with one query pack per job, light first, a never board and a judge benched for bias, is the
`find-references` skill. Turning the chosen references into a checked board (ranked lines, hex taken from a
reference, test stills scored line by line, 450+ source links) is the `video-moodboard` skill.

## Where to look

| Source | What it is good for |
|---|---|
| [Film-Grab](https://film-grab.com) | free stills from whole films, browsable by title; a post recommending it was saved 5,828 times (https://x.com/miso1278/status/2084635891981750518) |
| [ShotDeck](https://shotdeck.com) | paid, with a trial; film frames filtered by colour, light, camera angle and location, and some shots list the camera and lens (https://x.com/tkz_aiart/status/2111805365730095182) |
| [Shot Cafe](https://shot.cafe) | free reference shots for a kind of scene |
| Eyecannndy | names for visual techniques, when you can see an effect but cannot name it |
| Pinterest | curated boards: search `<film> still`, `<director> color palette`, `<decade> film grain`, `<character> cosplay`, `<genre> lighting` |
| [Godly](https://godly.website), [CTA Gallery](https://cta.gallery) | web and UI motion, for product and interface pieces (https://x.com/VullnetAdemaj/status/2116916867923161110) |

## How to search

- **Name the feeling, not the subject.** "Lonely, sodium-lit, wet" finds a look; "night market" finds stock photos.
- **Search by attribute**: colour, light direction, lens, camera angle, decade, film stock.
- **Go to the specific, recognisable edge on purpose**: one famous scene, one iconic costume, one named animation
  style. The middle of a search is the average you are trying to avoid.
- **Skip the obvious first pick.** When the agent proposes references (films and the scene, styles, designers),
  it drops the first one that comes to mind and offers the less obvious ones. The person verifies by looking at the
  frames; never trust a reference that nobody has opened.
- **Borrow the look, not the content**: palette, framing, lens, light, texture and motion; never characters,
  actors, logos or recognisable people.

## refs.md

One entry per frame, with what it lends:

```
## refs.md
1. <film or source, scene, link>: palette (deep teal shadows, one sodium-orange accent); framing (centred, wide
   negative space above the head); light (single hard source from frame left).
2. <...>: texture (fine grain, slight halation on highlights); motion (slow lateral dolly, no handheld).
```

## From refs to the look bible

- Write the **look line** from what the refs lend (medium, palette with the accent named, lens, light quality,
  grain), in words. The look line is what goes into every prompt.
- Add a **Never** list of 5 things this look would never do (for example: no lens flares, no handheld shake, no glossy
  plastic skin, no saturated blue sky, no slow-motion hair flips). It stops later prompts drifting back to the
  average. "Feed 4-5 inspo edits to Claude and tell it to make a skill out of it" is the same idea at a larger scale
  (https://x.com/alexgoughcooper/status/2115076988327076296).
- Use found frames to write the words and to judge stills against them, not as generation references: whatever
  sits in a reference comes back in the shot (SKILL.md section 6), including someone else's actor, set or logo.
  Once you have approved stills, frames from your own film are the style reference.
- To show the person the frames with their "take" lines and the Never list, put them on a reference board
  (`varg-mockups`, which has the same source list) before any still is generated.
