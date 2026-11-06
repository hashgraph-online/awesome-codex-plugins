# Texture references

A texture reference proves that one named material or process leaves these marks at pixel level. It proves nothing about
subject, grade or lens. Keep one only with a label from the caption, tags or record, native pixels, no preset, and a date
before the flood of generated images. A record naming the material ("azulejo") is enough for a material. A stock label is
needed only for film.

## Name the process, not the feeling

"A prompt that says '1980s' gets a pastiche; one that says 'matte plastic, saturated primaries against beige, chunky
rounded shapes, CRT glow' gets the decade"
([layer-art-direction](https://github.com/layerai/skills/blob/main/plugins/layer/skills/layer-art-direction/SKILL.md),
`reported`). Search works the same way: replace the feeling with the process, then with a stock, camera or printer name.

| Feeling | Process | What it does (`reported`; starred ones from search summaries only) | Look here |
|---|---|---|---|
| dreamy glow | Halation | "white, red, or orange halos around bright points of light", usually red because the red-sensitive layer is farthest from the lens ([Analog Cafe](https://www.analog.cafe/r/halation-in-film-photography-i3q4)). Sources conflict on where the light reflects | Edges of practical lights |
| gritty, filmic | Film grain | Strength depends on brightness, so it is not white noise: `Y' = Y + f(Y) * GL` in AV1 ([Norkin](https://norkin.org/research/film_grain/)\*) | Midtone patch against deep shadow and clipped highlight |
| old projector wobble | Gate weave, jitter | Weave is lateral, side to side. Jitter is vertical ([Sprocket School](https://www.sprocketschool.org/wiki/On_Screen_Troubleshooting)\*) | Frame-to-frame offset in a static shot |
| VHS vibe | Head switching, tracking noise | "commonly seen at the bottom of video display during VHS playback" ([A/V Artifact Atlas](https://avartifactatlas.com/artifacts/head_switching_noise.html)) | Bottom lines of the frame |
| Y2K flash | CCD blooming, hard clipping | Overflow from full wells spills into neighbouring photosites ([Evident](https://evidentscientific.com/en/microscope-resource/knowledge-hub/digital-imaging/concepts/blooming)\*). Nikon D1 series had "a serious highlight problem" ([Ken Rockwell](https://kenrockwell.com/nikon/d1xpits.htm)\*) | Strong lights, sky, flash hot spots |
| Polaroid feel | Instant film pod | Rollers break a pod and spread reagent between negative and positive sheet ([Wikipedia](https://en.wikipedia.org/wiki/Instant_film)) | Edge and corner chemistry |
| home movie | Super 8 | Amateur format, 18 frames per second ([Wikipedia](https://en.wikipedia.org/wiki/Super_8_film)) | Cadence and motion in clips |
| zine, riso poster | Risograph | Soy ink, spot colours, listed errors: roller marks, misregistration, needle marks, smudges ([Wikipedia](https://en.wikipedia.org/wiki/Risograph)) | Colour layer offset, flat ink fields |
| retro print | Halftone | Combining screens can cause moiré ([Wikipedia](https://en.wikipedia.org/wiki/Halftone)) | Dot shape under magnification |

Naming the stock beats naming the flaw (`tested 2026-11-03`). Openverse CC0 or PDM `halation` returned 3 unrelated hits, and
`kodachrome` hit the cap of 240. Flickr `unretouched,portrait` led with a photo tagged
`aigenerated aiart generativeai digitalart`, and `portra160,portrait` led with a large-format Sinar portrait.

## Read it

In this order. A frame shows marks. It does not show the process name, the grade or the lens.

1. **Label.** Take the material or process from the caption, tags or record. Never name a stock from pixels.
2. **Size.** Long edge under 1,000 px, or an upscale: cannot tell. A search result's `image` is often a thumbnail (960
   wide on a landscape Commons file, one cold run), so this is the one job that fetches `original`. Check `bytes` first:
   one poster's TIF is 272 MB. Else find the larger file or hand over a link.
3. **Preset.** Reject tags such as `vsco`, `preset`, `filter`, `lightroom`, and any emulation if you asked for the real
   thing.
4. **Date.** Prefer images taken before 2022: `date_taken` in the feed, `max_taken_date=2021-12-31` in the API. `our
   proposal`.
5. **Crop.** Run the test below and read the row for the process you claim.
6. **Motion.** Gate weave, cadence and head-switching jitter need consecutive frames. One frame cannot prove them.

## The 100% crop test

```bash
magick in.jpg -auto-orient -gravity center -crop 512x512+0+0 +repage crop100.png
```

This never resamples. View it 1:1. `tested 2026-11-03`:

- On a 5063x6657 master scan it returned 512x512 of real detail: single hairs and pores.
- On a 487x640 `r.jpg` it returned 487x512 with no warning. Check the output size: that file is too small for grain.
- The centre may miss what you claim. Aim it with `-auto-orient -crop 512x512+X+Y +repage` and no `-gravity`. Keep
  `-auto-orient`: on a phone original (raw 4032x3024, orientation RightTop) an offset crop without it landed on plain
  wall (one cold run).
- For a clip: `ffmpeg -ss 240 -i film.mp4 -frames:v 1 frame.png`. A 480 px access copy proves nothing about grain.

| Claim | Pass at 100% | Fail |
|---|---|---|
| Film grain | Clumps vary with brightness, weakest in clipped highlights and deep blacks; slight colour variation; no repeat | Same strength everywhere, single-pixel noise, visible tile, grain on top of smooth plastic detail |
| Halation | A red or orange fringe only where a very bright source meets dark, falling off smoothly | White glow on every edge, or bloom on dim objects |
| Gate weave | Whole frame drifts, mostly sideways, a pixel or two | Only the subject moves, or a regular sine wave |
| VHS | Damage at the bottom lines, colour smear wider than luma detail, horizontal line displacement | Scanlines and RGB split with sharp luma underneath |
| CCD | Hard clipped highlights, chroma noise in shadows, JPEG blocks, EXIF or caption naming the camera | Soft film-like rolloff under a "digicam" label |
| Polaroid | Uneven chemistry near edges, soft detail | A clean border frame over a sharp digital image |
| Risograph | Flat spot-ink fields, consistent colour layer offset, screen pattern | Offset applied per object or letter |
| Halftone | Dots follow tone with a consistent screen angle, moiré only where screens combine | Same dot size in all tones, or dots that break at edges in a generated scene |
| Paper | Fibres and tooth run under the ink and show through thin ink | Texture multiplied flat over the top |
| Skin | Pores vary by zone, fine hair, broken specular on nose and forehead, neighbouring hair and fabric equally sharp | Even pores or none, sharp hair next to smooth skin |

The pass and fail columns are craft knowledge plus the sourced definitions above. No authority covers all of them, and
nobody has measured how reliable they are for agents.

If everything looks soft at 100%, the file is an upscale or a downscale and proves nothing about grain. One exception we
saw: the master scan above looks gently soft at 100%, yet hairs and pores separate. Keep a file like that.

**Measure grain against brightness.** Read flat patches in shadow, midtone and highlight:
`magick in.tif -crop 64x64+X+Y +repage -colorspace Gray -format "%[fx:mean] %[fx:standard_deviation]\n" info:`.
`tested 2026-11-03` on the master in the worked example, flattest tenth of 48 px tiles per brightness band from 0 to 1 in
steps of 0.1, SD on 0 to 255: 0.90, 0.76, 2.64, 4.83, 4.44, 3.48, 3.33, 1.86, 1.66, 0.95. It agrees with the Film grain row.
It is one scan, with pores inflating the midtones, and not a study.

## Search it

What came back is `tested 2026-11-03`. Ranked.

| Source | Exact route | What came back | Access | Rights | Verdict |
|---|---|---|---|---|---|
| [Flickr public feed](https://www.flickr.com/services/feeds/docs/photos_public/) | `photos_public.gne?tags=cinestill800t&format=json&nojsoncallback=1`, add `tagmode=all` for two tags | 20 each for `cinestill800t`, `digicam`, `ccdcamera`, `superia400`, `polaroid600`, `riso,risograph`. Newest first. Image 240x159, no licence field | `agent`, the public feed only: [robots](https://www.flickr.com/robots.txt) set `*` to `Disallow: /` | `words` | Best first hop, but only leads: stock words, at 240 px, with no licence. Too small to crop |
| [Flickr `photos.search`](https://www.flickr.com/services/api/flickr.photos.search.html) | `text=%22portra%20400%22%20-aigenerated%20-aiart%20-midjourney`, `max_taken_date=2021-12-31`, `extras=url_o,tags,license,date_taken`, `per_page=30`. Add `license=4,5,7,8,9,10,11,12` for commercial reuse | Not run, key needed. [Terms](https://www.flickr.com/services/api/tos/): at most 30 photos per page, no long-term caching | `token` | `feed` only for a CC0 or public-domain [licence ID](https://www.flickr.com/services/api/flickr.photos.licenses.getInfo.html) with no person. CC BY and BY-SA `words` unless a person clears them | Best once a person creates a key |
| Commons categories, `search.py commons-cat` (`location.md`) | Walk from `Category:<material> in <place>` | One cold run: real Lisbon tile with author, date, EXIF and licence in one call. Commons `azulejo craquelure` 0, `jute sack coffee` 5 | `agent` | Per file: CC0 or public domain with no person `feed`; CC BY and BY-SA `words` | Best for real materials in place |
| [Internet Archive](https://archive.org/advancedsearch.php?q=collection%3Avhsvault&fl[]=identifier&fl[]=title&rows=5&output=json) | `collection:vhsvault`; `collection:home_movies`; `subject:"super 8" AND mediatype:movies`; `collection:zines AND subject:punk` | 126,295; 1,898; 587; 8,033 | `agent` | Per item. `feed` only with a public-domain `licenseurl` and no person | Best for moving flaws |
| [LoC FSA/OWI](https://www.loc.gov/pictures/search/?q=woman&co=fsac&fo=json) | `co=fsac`, `q=` a real subject, `fo=json` | 37 for `woman`, 1,616 whole. `r.jpg` 487x640; `u.tif` 101,113,476 bytes. Collection and item HTML returned 403, so stay on JSON | `agent` | "No known restrictions on publication." `feed` with no person, else `words` | Best real colour-film object |
| [A/V Artifact Atlas](https://www.avartifactatlas.com/artifacts/head_switching_noise.html) | `/artifacts/{name}.html` | Named flaw, cause, examples | `agent` | `words`, [CC BY-NC-SA](https://www.avartifactatlas.com/copyrights.html) | Best for VHS words. Not an asset |
| [Analogue Shop](https://analogueshop.com/pages/film-stock-samples) | `/pages/shot-on-{stock-name}`; some slugs break the pattern | 90 entries across 23 brands. Captions name the camera. Images did not extract. One 429 with `Retry-After: 60`: wait that long, try once more, then stop using it for this run | `agent` for captions, `person` for images | `look` | Best human stock gallery |
| [Filmtypes](https://www.filmtypes.com/films), [The Darkroom](https://thedarkroom.com/film-index/) | Facets for grain, contrast, saturation | 53 stocks; about 97 rows | `agent` | `words` | Good for choosing a stock. Check credits on samples |
| [ambientCG](https://ambientcg.com/api/v2/full_json?type=Material&q=paper&limit=10&include=downloadData,tagData), [Poly Haven](https://api.polyhaven.com/categories/textures) | `q=paper`; `assets?t=textures&c=fabric`, or list `t=textures` and filter locally | ambientCG `paper` 10, `fabric` 106, `rust` 58. Poly Haven 869 textures, `c=fabric` 43, skin 0, film 0, plaster 150, concrete 192 | `agent` | `feed`, CC0, check each | Best CC0 materials. Clean surfaces, thin for skin and film, no hand-painted tile (one cold run) |
| [Openverse](https://api.openverse.org/v1/images/?q=risograph&page_size=5) | `q` of one or two words, `license=cc0,pdm` | See Queries. Slow runs hit HTTP 500 and timeouts | `agent`, unstable | The uploader's claim: check the landing page | Good for CC0 print. Never the only source for a job. You may fetch an image URL it returns, even on a Flickr host: one file for a reference you keep, since Openverse points to it |
| Person-only | [filmdev.org](https://filmdev.org/robots.txt), [Camera-wiki](https://camera-wiki.org/robots.txt), [Lomography](https://www.lomography.com/films) | Robots disallow Claude crawlers on the first two; Lomography 403. Never fetch | `person`, `links.md` | `look` | filmdev is the only site tying stock to developer |

**Print comes from archives.** `search.py links --job texture` lists film-stock sites only, so it is no route for print.
Read poster and print records in Commons, LoC and Internet Archive, and keep the label rule: a record that does not say
lithograph leaves the process unknown (cold run on a coded film).

Traps caught in testing:

- A count of 20 on the Flickr feed is its page size, and 240 on Openverse is its cap. Neither tells you depth.
- `q=kodachrome` in FSA/OWI returned 1, because the word is rarely in the record. Search a real subject instead.
- Openverse `film grain` returned "abstract art of a black hole, solid shapes..." under PDM. Generated images carry open
  marks.
- `subject:"super 8" AND mediatype:movies` includes a Funny or Die video. Home movies hold real private people: `words`,
  avoid faces.

**Skin.** Open libraries hold nothing usable: Poly Haven 0, ambientCG one false hit (Leather008), Openverse CC0 or PDM
`skin pores macro` 0 (`tested 2026-11-03`). Martin Schoeller is the clearest named standard, with "faces become topography"
([National Portrait Gallery, Australia](https://portrait.gov.au/exhibitions/martin-schoeller-2010), `reported`, search
summary). Real skin is a real person, so it stays `words`.

## Queries

The left column is the feeling, run only where the result says so. The middle column was run, `tested 2026-11-03`, for
what the search returns and not as a prompt.

| Bad | Good | Where | What came back |
|---|---|---|---|
| vintage film look | `superia400`; `kodakgold200,halation` | Flickr feed | 20; 1 |
| Kodachrome look | `co=fsac`, `q=woman` | LoC | 37. `q=kodachrome` 1 |
| home movie, nostalgic | `collection:home_movies`; `subject:"super 8" AND mediatype:movies` | Internet Archive | 1,898; 587 |
| VHS vibe | `collection:vhsvault`; `subject:analog AND subject:vhs AND mediatype:movies` | Internet Archive | 126,295; 1,539. Openverse `vhs screenshot` 0 |
| grungy zine, xerox | `collection:zines AND subject:punk` | Internet Archive | 8,033. Openverse `xerox zine` 0, `photocopy texture` 1 |
| retro print, `halftone dots newspaper` | `halftone print` | Openverse, `license=cc0,pdm` | 137 against 0 |
| aged paper | `q=paper`; `paper texture` with `license=cc0,pdm` | ambientCG; Openverse | 10, with Paper003 tagged `creased`; "Paper texture on a fading poster" (CC0) |
| natural skin, `unretouched,portrait` | `portra160,portrait`; `freckles,film` | Flickr feed | 20 each. The bad one led with an AI-tagged image |

Worked example, "1940s Kodachrome look", `tested 2026-11-03`. A real man, so tag it `words`: judge against it, never feed
it.

```bash
curl -s "https://www.loc.gov/pictures/search/?q=kodachrome&co=fsac&fo=json"   # 1 hit, "Guide at Little Norway, Blue Mounds, Wis."
curl -s "https://www.loc.gov/pictures/item/2017878934/?fo=json"
# item.rights_information  No known restrictions on publication.
# item.notes               "Minnesota Farmer, Kodachrome, 1940" and "FSA" on transparency jacket.
# resources[0].larger      https://tile.loc.gov/storage-services/master/pnp/fsac/1a55000/1a55000/1a55005u.tif
magick 1a55005u.tif -auto-orient -gravity center -crop 512x512+0+0 +repage crop100.png     # in 5063x6657, out 512x512
```

## Code vs generated

**Code (HyperFrames, Remotion, three.js).** The reference must prove the file is real and licensed. Output: file,
licence, blend mode, strength by brightness. Real files beat prompts: a `u.tif` crop with no person in it, a CC0 map, or
the HyperFrames `grain-overlay` block (`npx hyperframes add grain-overlay`, install not run). Grain packs spread widely
on X ([9,185 bookmarks](https://x.com/BandicootDesign/status/1969178516089385209)), with licences unverified, so read
before shipping.

If you synthesise grain, scale it by brightness and add spatial correlation. Even noise is the failure: ffmpeg's
`noise=c0s=14:c0f=t+u` measured SD 0.018 on flat greys at 25, 50 and 75%. This one is `our proposal`:

```bash
magick in.png \( +clone -fill gray50 -colorize 100 -seed 11 -attenuate 0.6 +noise Gaussian -colorspace Gray -blur 0x0.7 \) \
  -compose Overlay -composite out.png
```

`tested 2026-11-03` on flat greys at 3, 25, 50, 75 and 97%: SD 0.0008, 0.0068, 0.0134, 0.0068, 0.0008. That is a
triangle, not a measured stock curve, and luma only. Change `-seed` every frame or it reads as a tile.

**Generated (Seedance, Kling, Veo, Nano Banana).** The reference must prove the words name marks a model can make, and any
fed image must be `feed`. Output: one line of process words, or a neutral close-up with one role, in the form `@ImageN
defines X only. Do not copy Y, Z from @ImageN.` ([post](https://x.com/AiwithBloodline/status/2115841225106604469),
`reported`). Do not overspend here: in our 48-still test (3 scenes × 2 models, two LLM judges, small) the texture line
gained +0.33 film-likeness (p = 0.39), which is no clear effect.

## Reject if

- No material or process label in the caption, tags or record, or only a guess from pixels.
- A preset tag, an emulation when you asked for the real thing, or AI tags.
- Long edge under 1,000 px, an upscale, or soft at 100% with no fine detail.
- Grain with the same strength in shadow, midtone and highlight, or a visible tile.
- An open licence you did not check on the landing page.
- An identifiable person in a reference tagged `feed`. Retag it `words`.

Universal rejects: `never.md`.

## Judge it

Texture T1 to T4 in `judge.md`. T2 and T3 start in code. Never ask an LLM to name a film stock from pixels.
