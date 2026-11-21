# Palette references

A palette is real if you can name the frame it came from. It proves the colours and their shares in that frame, and nothing
about light, lens or subject.

**Hex is always extracted by code from a real frame. Never invent it, and never let an LLM write a hex list.** Weights
matter as much as hex: swatches alone lose the proportions that make a look.

## Read it

In this order. A frame shows colours and how much of the picture each one holds. It does not show how the look was made.

1. **Frames.** For the first board, take three named frames of candidates. After the pick, re-extract from the picked frame.
   For film, take 3 to 5 frames of one scene. One frame is fine for a painting or a still.
2. **Crop.** Remove letterbox bars and any scan border.
3. **Extract.** Run the LAB command below.
4. **Label.** Name each colour by role: shadow, midtone, highlight, one accent.
5. **Check**, `our proposal`. The accent covers little of the frame. Shadows are not pure `#000000` on film. Values fall
   on a smooth ramp from dark to light with the same colour cast. Invented palettes usually arrive with no weights at all.

## Extract it

`tested 2026-11-03` on FSA/OWI ["Guide at Little Norway, Blue Mounds,
Wis."](https://www.loc.gov/pictures/item/2017878934/?fo=json), the 487x640 `r.jpg`, "No known restrictions on
publication."

```bash
magick fsa.jpg -resize 400x400 -colorspace LAB -colors 6 -colorspace sRGB -format "%c" histogram:info: | sort -rn
```

```text
         68730: (31.0993,30.1996,19.1246) #1F1E13 srgb(12.1958%,11.843%,7.49985%)
         15394: (219.048,217.675,188.681) #DBDABD srgb(85.901%,85.3628%,73.9927%)
         14044: (92.2344,67.8232,44.8302) #5C442D srgb(36.1703%,26.5973%,17.5805%)
         10979: (185.577,150.441,102.213) #BA9666 srgb(72.7752%,58.9965%,40.0834%)
          9004: (155.936,103.014,66.756) #9C6743 srgb(61.1513%,40.3978%,26.1788%)
          3449: (120.08,133.787,106.24) #78866A srgb(47.0904%,52.4655%,41.6629%)
```

| Role | Hex | Share | Where it sits, read from the quantised frame |
|---|---|---|---|
| Shadow | `#1F1E13` | 56.5% | Background, vest |
| Midtone, low | `#5C442D` | 11.5% | Shaded side of the face |
| Midtone | `#9C6743` | 7.4% | Skin |
| Midtone, high | `#BA9666` | 9.0% | Lit skin |
| Highlight | `#DBDABD` | 12.7% | Shirt |
| Accent | `#78866A` | 2.8% | Hat, embroidery leaves |

The 5063x6657 master gave nearly the same six (`#201F14 #DBDABD #5C452D #B99664 #9D6641 #788668`), so a small file is enough
for colour even though it fails for grain.

What each step changes, `tested 2026-11-03`:

**Use LAB, not `palettegen`.** The same image through ffmpeg `palettegen` lost the green accent.

**Crop bars first.** We added black bars to this frame. `#000000` took 25,165 pixels and the accent vanished:
`#17160E #000000 #5C452E #DAD8BB #BA9666 #9B6844`. Trimming brought back the exact output above:

```bash
magick bars.png -fuzz 3% -trim +repage -resize 400x400 -colorspace LAB -colors 6 -colorspace sRGB -format "%c" histogram:info: | sort -rn
```

Check the size after a trim, as a dark frame can lose real edges. A scan border matters too: cropping it with
`-gravity center -crop 90%x92%+0+0 +repage` moved the darkest colour from 56.5% to 49.5%, and its hex only to `#211E14`.

**Use several frames on film.** Three frames 2 s apart from one scene of [To Enrich
Mankind](https://archive.org/details/ToEnrichMank) (1955, colour, public-domain `licenseurl`) changed the largest colour
from `#29211A` to `#655E51`. Stack them to get one palette:

```bash
magick f240.png f242.png f244.png -resize 400x400 -append -colorspace LAB -colors 6 -colorspace sRGB -format "%c" histogram:info: | sort -rn
```

**Crop onto a small accent.** The red embroidery on the FSA frame did not appear even at 16 colours. A crop on the object
did:

```bash
magick fsa.jpg -crop 24x16+410+478 +repage -colorspace LAB -colors 3 -colorspace sRGB -format "%c" histogram:info: | sort -rn
# 169 #693B2F, 136 #8C3831, 79 #879279
```

**Pictorial images lose their accents.** On [Simplon,
1928](https://commons.wikimedia.org/wiki/File:SBB_Historic_-_P_A05_0002en_-_The_electric_Simplon_Line_-_Switzerland.tif),
960 px, the LAB run gives two greys at 63% and no red locomotive, even at 16 colours. `-crop 200x100+340+980` onto the
locomotive gives `#923E21` and `#672A15`. Crop by coordinates, then check the crop by eye: it is easy to miss. Flat sheets
read well: `#1F2D2E` 37.2%, `#E2E2CB` 20.9%, `#166B99` 13.2% on a 1930 Giacometti (cold run on a coded film).

**A source's shares are the source's,** including shapes the film will not use. The film's mix is a decision. Label it:
`paper 70, ink 25, accent 5 (assumed)`.

## Code vs generated

Same palette, written two ways.

| | Code (HyperFrames, Remotion, three.js) | Generated (Seedance, Kling, Veo, Nano Banana) |
|---|---|---|
| Use | Exact hex, because the renderer obeys it literally | Attach the frame and describe the grade in words |
| The reference must prove | A named source frame, with shares you can check against | A frame you may feed, or words taken from a measured frame |
| Output | Tokens with role, share and source: `--accent: #78866A; /* 2.8%, LC-DIG-fsac-1a55005 */` | A role line and a grade sentence, loosely held |

**Generated.** Keep hex out of the prompt, and use it to judge the result (C1).

- If the frame is tagged `feed`, attach it with one role: `@Image1 defines colour and grade only. Do not copy subject,
  framing or light from @Image1.` The form is from [a post](https://x.com/AiwithBloodline/status/2115841225106604469),
  `reported`.
- If the frame is `words`, as this one is because it shows a real man, do not attach it. Describe it. Our wording, from the
  table above: "olive-black shadows, tan skin, cream highlights that keep their yellow, one muted green in the hat".
- Veo 3.1 takes "up to three images of a single person, character, or product" with no documented style type ([Vertex
  docs](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/video/use-reference-images-to-guide-video-generation),
  `reported`), so there the grade has to be words.
- If the grade must be exact, generate neutral and grade afterwards, in code, from the measured values.

Why:

- In our 48-still test (3 scenes × 2 models, two LLM judges, small) the hex line was obeyed best (89%), yet frames looked
  less like film with it: −0.67, 5 of 6 pairs, p = 0.03. That does not survive Holm correction, so it is suggestive only.
- "Prompting cannot deliver a grade. Measurement can."
  ([taste-distillation](https://github.com/affaan-m/ecc/blob/main/skills/taste-distillation/SKILL.md), `reported`, one
  project's claim, not reproduced).

**Rights.** Keep each frame's own tag. Taking hex from a work borrows a method rather than an image, so it is usually
the lowest risk, but we found no legal source for this, so it needs a person's call.

## Search it

Your own frames come first. The rest are for when no frame exists yet. What came back is `tested 2026-11-03`.

| Source | Real or generated | Exact route | What came back | Access | Verdict |
|---|---|---|---|---|---|
| Your candidates' frames, then the picked one | Real | Commands above | Six weighted hex | `agent` | Best |
| [LoC FSA/OWI](https://www.loc.gov/pictures/search/?q=woman&co=fsac&fo=json), [Met v1.1](https://collectionapi.metmuseum.org/public/collection/v1.1/search?q=poster&hasImages=true&isPublicDomain=true) | Real frames to measure | `co=fsac&q=`; `/v1.1/search` | 37 for `woman`; 9,263 IDs for `poster` | `agent` | Good when the look is a period |
| [Meditations in Color](https://meditationsincolor.com/directors/wes-anderson/) | Algorithmic reading of real posters | `/directors/{slug}/`, `/artists/{slug}/`, `/musicians/{slug}/`. Hex in static HTML, `/api/` disallowed | "16 film posters, 1996 to 2025. Palette: #51B9AD #212223 #F4F3F2 #FEC704 #131313 #93B52E #DEEBC3 #39654C" | `agent` | Best new find, for titles and key art more than grade |
| [Wada JSON](https://raw.githubusercontent.com/mattdesl/dictionary-of-colour-combinations/master/colors.json) | Historical book, 1933 | Group `colors.json` by `combinations` | 159 colours in 348 combinations, MIT. Combination 262 = `#da525d #ebd3a2 #b09f36 #437742` | `agent` | Best for a designed palette |
| [AIC API](https://api.artic.edu/api/v1/artworks/search?q=poster&fields=id,title,color,image_id,date_display,is_public_domain,artist_title&limit=3&query[term][is_public_domain]=true) | Measured from the work | `fields=color` | Zodiaque: h 40, l 44, s 56 | `agent` | Good, single dominant colour |
| [Wellcome images](https://api.wellcomecollection.org/catalogue/v2/images?query=poster&locations.license=cc0,pdm&color=d7372c&pageSize=3) | Real images by hex | `color=d7372c` | 85, then 82 on a second run. First a Royal Aquarium poster | `agent` | Good, hex to real image |
| [Lospec](https://lospec.com/palette-list) | Made by pixel artists | `/palette-list/{slug}.json` | 4,542 palettes. `sweetie-16.json` 16 hex, no `#` | `agent` | Pixel and 8-bit only |
| [Color Hunt](https://colorhunt.co/palettes/vintage), [Coolors](https://coolors.co/palettes/trending), Colormind, Huemint | Trend or generator | None | No frame provenance | n/a | Skip as evidence |
| Movies in Color, Screenmusings | Film-based | [403](https://www.moviesincolor.com/robots.txt), [Cloudflare 403](https://www.screenmusings.org/) | No open film-frame palette dataset turned up | `person`, `links.md`, never fetch | Links only |

Traps caught in testing:

- A Meditations in Color palette is a poster's, not a film's grade. Do not use it to grade a shot.
- AIC `color` is null on some works (La Gismonda) and reports a small share on others (Zodiaque 0.011). It is not a palette.
- Wada hex is converted from CMYK and the conversion is not exact, per an npm fork.
- Color Hunt calls an undocumented `POST /php/feed.php`. It is not a public API, so do not build on it.

## Queries

The left column is the feeling and was not run. The middle column was, `tested 2026-11-03`.

| Bad | Good | Where | What came back |
|---|---|---|---|
| warm cozy palette | Three named frames, the LAB command | Your frames | Six weighted hex, as above |
| cinematic teal and orange | `/directors/wes-anderson/`, for key art | Meditations in Color | 16 posters with hex |
| vintage palette | `co=fsac&q=woman`, then extract; Poster House `keyword=12674&decade=17431` | LoC; Poster House | 37; 343. `/palettes/vintage` is trend-driven |
| find images in this red | `color=d7372c` | Wellcome | 85, then 82 |

## Reject if

- You cannot name the frame or source that the hex came from.
- A hex list with no shares, or one an LLM wrote. A swatch-only site used as evidence.
- Bars or a scan border left in, with black leading the list. One frame standing in for a scene of a film.
- A second accent, or an accent over 10% of the frame, when you asked for one.
- One tint across all objects: skin, wall and sky should differ.
- A `words` frame attached to a generator.

Universal rejects: `never.md`.

## Judge it

Palette C1 to C5 in `judge.md`, a draft and off by default. C1 to C3 are code: `video-moodboard/scripts/palette.py
check` gives ΔE for C1, which is not core here. C4 and C5 go to the LLM. Never ask an LLM for exact hexes.
