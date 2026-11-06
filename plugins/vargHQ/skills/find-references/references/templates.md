# File templates

## brief.json

Mark each field `said`, `assumed` or `asked`.

```json
{
  "idea":    {"v": "what the viewer should believe afterwards", "from": "said"},
  "feeling": {"v": "quiet, earned; not cosy", "from": "assumed"},
  "method":  {"v": "coded | generated | hybrid | filmed", "from": "asked"},
  "medium":  {"v": "live action | 3D | 2D | type-led | photo-based", "from": "assumed"},
  "and the rest": {"v": "subject, world, audience, platform, constraints, loves, hates: same shape"}
}
```

Assume out loud when you must: 9:16 and 15 s for ads, 16:9 and 45 s for launch films, nothing licensed.

## queries.md

```
## Light (floor: 6 queries, 3 sources; stop when two in a row add nothing new)
Want: a tired office worker at night, alone
Visible words: one distant source, small pool, surroundings fall to dark, cold ambient
L  commons   "fluorescent" office night
L  polyhaven night,artificial,indoor
N  met       Edward Hopper (--artist)   -> words only if not public domain
A  rijks     kaarslicht (--type painting), only if the light is candlelight
C  framethrower lighting:fluorescent, time_of_day:night; "one tube over a desk, the rest of the room dark"  (skip with no semantic engine)
X  filter afterwards: flat even light, no visible source

## Control: the whole brief, one query
<one plain sentence>
```

Log every result in `search_log.jsonl` (`search.py --log`). A silent zero is a finding: change the vocabulary and note it.

## Want card

One per job, in `want/<job>.txt`, frozen before you see candidates. Values only, no praise words. Changing it later makes a
new version and reads are repeated.

```
job: light | direction: any | hardness: soft (assumed) | source: practical, street lamp or window |
colour: warm key, cold fill | shadow side: near black
```

Freeze only values the person gave or the brief implies. Anything you had to invent is marked `assumed`, and it cannot be
core: if you invented the side, write `direction: any`, and the judge skips L2. The person's words outrank the card.

## refs.md

One job card per kept candidate. The number is the file's number: `board.py` numbers the board separately, after
shuffling. Mark `Pick: yes` when the person picks. An image that truly does two jobs gets two cards, each with its own
do-not-copy line.

```
## 07 · light · Met — Holy Family with Saint Anne, French painter, early 17th century
Link: https://www.metmuseum.org/art/collection/search/436344
File: refs/light/07-light-met.jpg
What I see: one low candle, faces lit from below, background falling to black.
Lends: light only. One source low in frame, hard shadows upward, <n> stops of contrast (frame_light.py).
Must not copy: the figures, the costumes, the painted surface.
Rights: words for now (public domain, so legally feed; feed only after a test frame)
Provenance: HUMAN-PROVEN (held by the Met)
Found by: met "candlelight" medium=Paintings, rank <r> of 6
```

Write only what you measured.

For a person:

```
## 11 · people · Library of Congress — "New Orleans garage mechanic", Walker Evans
Link: https://www.loc.gov/item/2017762251/
What I see: <only what is visible>
Lends: words for the identity card only: <bones, work marks, carriage>. Trait counted once of the three needed.
Must not copy: this man's face. Never fed to a model.
Rights: words (public domain clears copyright, not likeness)
Provenance: HUMAN-PROVEN (held by the Library of Congress)
```

## never.md

```
Reject if <something a stranger can check>. Check on: frame | clip | code | text.
Prompt as: <the positive wording, because negatives backfire in most models>.
Found: <URL, date, count in what the obvious search reached>, or: the person's stated hate.
```

## links.md

```
## Night exteriors, sodium light
Why a person: these libraries forbid bots, and I may not open them.
- Film-Grab: https://film-grab.com/?s=sodium+street — stills from whole films; look for one hard lamp and dark ground
- Pinterest: https://www.pinterest.com/search/pins/?q=sodium+street+1970s+photograph — turn the AI tuner on
Drop 1 to 3 frames in refs/ and tell me which. Anything you drop counts as a reference, tagged look or words.
```

Build these with `python3 -I "$S/search.py" links "<words>" --job light`. Say what you could not find, and put that first.

## board.json and board.html

Three candidates per job. `board.py` builds one self-contained page: grouped by job, shuffled, numbered after shuffling, no
scores, with a keep or reject button and a note per candidate, and a "Copy my picks" button that gives JSON. Do not use the
`varg-mockups` board for this: it is a storyboard template.

```bash
python3 -I "$S/board.py" board.json board.html --seed 7
```

```json
{"title": "Lisbon roastery ad",
 "jobs": [{"job": "light", "want": "one window, frame left, room falls to dark",
           "candidates": [{"file": "refs/light/02-light-met.jpg", "title": "The Visit, Pieter de Hooch",
                           "link": "https://www.metmuseum.org/art/collection/search/436678",
                           "lends": "light only: one window, frame left",
                           "must_not_copy": "the figures, the costumes, the painted surface",
                           "rights": "words", "provenance": "HUMAN-PROVEN"}]}]}
```

A candidate takes `file` (relative to `board.json`, so keep the images beside it) or `url`. Audio and video get a
player. A `look` reference takes `link` alone, with no `file` or `url`, because nobody keeps it and `url` would hotlink it:
its card says "No image. Open the link." Show the judge's evidence only after the person chooses. Paste the picks back into
`refs.md`.

## ideas.md (only if asked)

```
## 3 · <title> (stretch)
Pitch: <one line>
Built from: 07 (light) + 12 (motion) + 03 (type)
Look: <medium>, <palette with the accent named>, <lens class>, <light in numbers>, <texture>, <motion>
First shot: <one sentence>
Risk: <what could make it slop>; <any rights question>
```

Spread: close to what works now, stretches, wild. No two share a main reference.

## From picks to the next step

**Generated:** one role line per fed reference.

```
@Image1 defines the light only: one low source, shadows rising. Do not copy the figures or the painted surface.
```

**Coded:** two files. With nobody there to pick, head both PROVISIONAL. The values below are from the cold run on a coded
film.

`DESIGN.md`: every value is labelled measured, record, by eye or assumed, with its source frame.

```
Type: Archivo, variable 100 to 900 (record: Fontsource, OFL-1.1). tnum present (measured: latin 400 file). Display 120 px at 1080p (assumed).
Palette: --ink #1F2D2E, 37.2% of the source (measured: SBB Historic P A02 0021de, crop 96%). Film mix: paper 70, ink 25, accent 5 (assumed).
Grid: title left margin 2.7% (by eye: Wyss, about 1930, on the 10% grid).
Light: none in the coded part. The one still, in words: one desk lamp frame right, 6.9 stops (measured: Myers 1939, inside the border).
Motion: everything holds 1.5 s, then one thing jumps in 2 to 3 frames at 25 fps (measured: Zürich clock). Stagger: none measured.
```

`timing.md`: one row per beat. Whole-film structure rarely comes from a reference, so beats are usually assumed, and that is
fine if labelled. The primitives inside them can be measured.

```
| Beat | Seconds | Frames at 25 | What moves first | Ease | Source |
|---|---|---|---|---|---|
| One invoice line sets itself | 0.0-6.0 | 0-150 | the first figure, cut in | none, 4 frames | beat assumed; reveal measured: Trick or Treat |
| Hold | 6.0-7.5 | 150-188 | nothing | n/a | beat assumed; hold measured: Zürich clock |
| The one still | 19.5-24.0 | 488-600 | hard cut, 0 frames | n/a | beat assumed |
```
