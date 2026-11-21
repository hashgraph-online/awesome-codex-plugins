# References and a moodboard (before the story)

Without specific references an agent picks the safe, middle version of every choice, and the film looks like every
other AI film. "Most AI videos look cheap because nobody gives the AI a real film reference"
(https://x.com/ScaleWthAI/status/2111821935021863254). People often cannot name the look they want either ("I don't
have the language!", https://x.com/trq212/status/2115641110710419752), so pictures come first and words are written
from them.

Output of this step: `refs.md` (the frames and what each one gives) and `moodboard.md` (the look in words). Both are
free. The previz stays grey-box; the moodboard sets the look of the anchors (step 5) and the Seedance prompts (step 8).
The `video-moodboard` skill builds this board in ranked order (from a 48-still test and 6,086 X posts), draws it as
`board.html` and checks it on test stills before any video.

## Where to look

| source | what it is good for |
|---|---|
| [Film-Grab](https://film-grab.com) | free film stills, browse a whole film frame by frame (a post recommending it got 5,828 bookmarks, https://x.com/miso1278/status/2084635891981750518) |
| [ShotDeck](https://shotdeck.com) | paid (2-week trial); filter film frames by colour, light, camera angle and location; some shots list camera and lens (https://x.com/tkz_aiart/status/2111805365730095182) |
| [Shot Cafe](https://shot.cafe) | free; reference shots for one kind of scene |
| Eyecannndy | names of visual techniques, so you can say what a move or effect is called |
| Pinterest | curated boards; search "[film] still", "[director] color palette", "[decade] film grain", "[character] cosplay", "[genre] lighting" |
| [Godly](https://godly.website), [CTA Gallery](https://cta.gallery) | web and UI motion, for product promos with screens (https://x.com/VullnetAdemaj/status/2116916867923161110) |

## How to search

- **Name the feeling, not the subject.** "lonely, late, humming fridge light", not "man in kitchen".
- **Search by attribute**: one colour, one light direction, one lens, one framing, one texture at a time.
- **Go to the specific edge on purpose.** One famous scene, one iconic costume, one named animation style beats a
  general genre. The middle is what the model does by default; the reference exists to pull it off the middle.
- **Borrow the look, not the IP.** Take palette, framing, lens, light and texture; never characters, logos or a
  recognisable scene recreated shot for shot. Write the look into the moodboard in words; the film still stays on
  the board and does not go into a generation request.
- **Claude proposes, the person looks.** Suggest 5-8 references (film + scene, a style, a designer), skip the obvious
  first pick, and say where to find each frame. The person checks by looking at the frames and keeps 3-5 from one
  aesthetic.

## refs.md

One row per kept frame. The "take" column is what makes it a reference instead of a mood:

| # | source (film, scene, link) | shots it serves | take |
|---|---|---|---|
| r1 | Film X, the diner at night, Film-Grab link | s01-s04 | palette (teal walls, one red sign), hard top light, wide lens at eye level |
| r2 | Film Y, the chase, ShotDeck link | s09-s12 | handheld at knee height, motion blur on the background only |

Tie every frame to shots; a reference no shot uses is cut. `treatment.md` keeps the short list and
`storyboard.json` may carry `film_ref` per shot.

## moodboard.md

```markdown
# Moodboard: <title>
Palette: #0E2A33 (base), #1F5560, #E8DCC4 (skin/practical light), #D7262E (accent, only on the sign and the scarf)
Light: hard top light, practicals in frame, black shadows that keep detail, no fill from the camera side
Framing: wide lens at eye level, subject off centre, lots of ceiling; close-ups only on the turn
Texture: 35 mm grain, slight halation on practicals, no sharpening
Type: one condensed sans, white, lower third only (drawn in code)
Motion: slow lateral dolly, one whip pan per act, no drone moves
Never:
1. no orange-and-teal blockbuster grade
2. no lens flares
3. no slow-motion
4. no centred symmetrical framing
5. no glossy plastic skin
```

The "Never" list (5 things this look would never do) stops the work drifting back to average across many
generations; copy the relevant lines into anchor and run prompts. A moodboard can also become a reusable skill: "feed
4-5 inspo edits to Claude and tell it to make a skill out of it"
(https://x.com/alexgoughcooper/status/2115076988327076296).

Show the board (frames + moodboard.md) to the person and get a yes before the story is written. Changing the look
later is cheap only until the anchors exist.
