# Framing references

A framing reference proves where the camera stood and how much of the frame the subject takes: shot size, camera height,
angle, the side with the empty space. It lends framing only, not light or set. It does not prove the lens in mm.

Size and angle can be filtered and read fairly well. Lens is the weak point. Mean across 24 vision models: shot framing
64.1, shot size 53.3, camera angle 45.6, composition 43.0, lens size 37.7 ([ShotBench](https://arxiv.org/html/2506.21356),
older models). So look the lens up, and read the rest as measurements, not adjectives.

## Read it

Same order on every frame. Put a 10% grid over it first, so that you count cells instead of guessing. The grid is `our
proposal`; `tested 2026-11-03` on the Vermeer below.

```
$ ffmpeg -i frame.jpg -vf "drawgrid=w=iw/10:h=ih/10:t=1:c=white@0.4" grid.jpg
```

| # | Measure | What it gives | Cannot tell when |
|---|---|---|---|
| 1 | Where the frame cuts the body or object, plus subject height as % of frame height | Shot size. A chest cut is a medium close-up | No person or object of known size |
| 2 | Top of head to frame edge, as % | Headroom | No head in frame |
| 3 | Which side has the empty space, relative to the look | Lead room or short side | Subject looks into the lens |
| 4 | Horizon height, or where standing eye lines converge | Camera height | No horizon or verticals |
| 5 | Subject's centre: left, middle or right third | Composition: `Center, Left heavy, Right heavy, Short side` | No clear subject |
| 6 | Foreground between camera and subject | Depth: a soft door frame, or a subject flat against a wall | Subject fills the frame |
| 7 | Lens: look it up, else a class only | "wide, close to the subject" or "long, far away" | Almost always, for an exact number |

No source we opened maps a shot size to a percentage. Record the number and the crop point, then choose the label.

One agent's reading of Vermeer's
[Young Woman with a Water Pitcher](https://images.metmuseum.org/CRDImages/ep/web-large/DP353257.jpg), `tested 2026-11-03`,
no person confirmed it:

```
Size: full figure, top of the headdress at 21% and the hem at 98% of frame height, so 77% tall. Headroom: 21%. Look: frame
left, into the window side, so lead room. Centre: middle third. Height: no horizon; the tabletop shows, so above the table,
otherwise unknown. Foreground: table and basin, frame right. Lens: unknown, it is a painting.
```

**Brightness is a cheap check on weight.** [`frame_light.py`](../scripts/frame_light.py), run from the project folder
with `S=<skill folder>/scripts`, says where the brightness sits and gives `source_size` for aspect. It is not a
composition reading: it only tells you that a take has flipped or shifted the weight of its reference. `our proposal`.

**The camera decides what the key is.** For code, [`hdri_light.py`](../scripts/hdri_light.py) gives the key's position
in the map. With the camera facing the map's centre, azimuth 0 is a backlight, ±90 a side light, and 180 comes from
behind the camera. Plain geometry, not measured: move the camera, then re-measure a render.

### The lens

1. **Look it up.** [ShotOnWhat](https://shotonwhat.com/sicario-2015) lists "Zeiss Master Prime Lenses" for Sicario,
   `tested 2026-11-03`.
2. **Otherwise state a class.** Wide lenses "stretch space, exaggerate distance" and may "distort spaces or people's faces
   in an unnatural, exaggerated way, especially as the lens gets closer to the subject". Telephoto lenses "compress space
   and offer a much tighter field of view" ([In Depth Cine](https://www.indepthcine.com/videos/focal-length)). Write
   what you see, not why.
3. **Never read an exact number from one frame.** It is "practically impossible unless we know the dimension of each
   object in the scene and it's distance from the camera"
   ([forum, snippet only](https://groups.google.com/g/maya_he3d/c/MfRzeROZC2U)). The mm on your board is a decision, not a
   reading.
4. **Anamorphic needs its tells:** "Out-of-focus highlights render as vertical ovals rather than circles", and "Point
   sources streak into horizontal flares" ([FrameThrower](https://framethrower.ai/style/anamorphic)). A 2.39:1 frame alone
   proves nothing: Sicario is 2.39:1 on Master Primes (`reported`, snippet only).

**Rule breaking needs a reason.** Tod Campbell: "We would try to build our story within our composition and let that tell
the story" ([The Credits](https://www.motionpictures.org/2017/04/mr-robots-cinematographer-season-threes-wild-ride/)), and
on a lonely frame, "putting him at the bottom of the corner of the frame makes it so there's no place for him to go". "A
dirty single keeps a sliver of the scene partner", and "Strong films break each of these — but as decisions, not
accidents" ([FrameThrower](https://framethrower.ai/style/guide/composition-in-film)). Write the reason beside the board
line.

**9:16 has its own craft.** Hao (Hunter) Deng: "I often use centered compositions to highlight a character's loneliness or
sense of pressure" and "hallways, stairs, and doorframes help create vertical layers"
([Flanelle](https://flanellemag.com/?p=104790)). "Generally, you are framing a little bit looser than you might typically
do" ([Definition](https://online.bright-publishing.com/view/581062653/29/)). Do not crop a 16:9 reference to prove a tall
frame: look where tall is native, such as hanging scrolls.

**A portrait sheet in a 16:9 film lends its grid, not a crop.** The crop test applies only if you use the frame itself. Read
`width` and `height` across a category to find the wide sheets: in `Category:SBB Historic - Plakate`, 3 of 48 are landscape,
`tested 2026-11-03`. A grid carries as ratios and positions by eye, labelled so in `DESIGN.md`.

## Search it

Results are `tested 2026-11-03` unless marked. Prefer facets and image similarity to sentences here: text embeddings
"behave as bags of concepts", weak on pose and viewpoint ([VisRet](https://arxiv.org/abs/2505.20291)).

| Vocabulary | Shot size | Angle | Lens or composition |
|---|---|---|---|
| [FrameThrower films](https://framethrower.ai/api/v1/openapi.json), read from the spec | `shot_type`: `medium, closeup, wide, fullbody, establishing` | `camera_angle`: `eye_level, high_angle, low_angle, top_down, overhead, worms_eye, dutch_angle, pov, birds_eye` | `lens`: `anamorphic, spherical, vintage_soft`. `depth_of_field`: `shallow, deep, rack_focus, medium` |
| [FrameThrower commercials](https://framethrower.ai/api/v1/openapi.json), read from the spec | `shot_size`: `extreme_closeup, closeup, medium_closeup, medium, medium_wide, full, wide, extreme_wide, insert` | `camera_angle`: `eye_level, low_angle, high_angle, overhead, aerial, pov, worms_eye, dutch` | None |
| [ShotBench](https://arxiv.org/html/2506.21356), use as answer lists | `Wide, Close Up, Extreme Wide, Medium Close Up, Medium Wide, Medium, Extreme Close Up` | `Aerial, Overhead, Low angle, High angle, Dutch angle` | `Long Lens, Wide, Ultra Wide&Fisheye, Medium`. `Center, Balanced, Symmetrical, Right heavy, Left heavy, Short side` |
| [Open style pages](https://framethrower.ai/style) | `/style/close-up, wide-shot, establishing-shot, two-shot` | `/style/low-angle, high-angle, dutch-angle, overhead-shot, over-the-shoulder` | `/style/anamorphic, shallow-depth-of-field, deep-focus, vintage-lenses` |

| Source | Exact route | What came back | Access | Rights | Verdict |
|---|---|---|---|---|---|
| FrameThrower search | `POST https://framethrower.ai/api/v1/search` with the facets above, then `POST /api/v1/similar` with `frameId` | Not tested: 401 without a token | token | `words` | Best if the person pays. Size and angle filter, similar frames |
| FrameThrower open pages | [`/style/low-angle`](https://framethrower.ai/style/low-angle), [`/film/sicario-2015`](https://framethrower.ai/film/sicario-2015) | 200. Sicario "leans on medium shots (38% of the sample) and wide compositions (29%)" | agent | `words` | Good free route for words and a film's habits |
| [ShotOnWhat](https://shotonwhat.com/sicario-2015) | `https://shotonwhat.com/<film-year>` | 200, "Zeiss Master Prime Lenses" | agent | `words` | Best for lens. Look it up first |
| [Met hanging scrolls](https://metmuseum.github.io) | `https://collectionapi.metmuseum.org/public/collection/v1.1/search?q=hanging%20scroll&medium=Paintings&geoLocation=China&hasImages=true` | 906. Of the first 20 objects, 17 public domain with an image. The small image may include the mount, and can be narrower than 9:16 (233x623, one cold run) | agent | Legally `feed` after the object check, but start from words | Best open route for tall framing |
| Met still life | `?q=still%20life&medium=Paintings&hasImages=true&dateBegin=1600&dateEnd=1800` on the same path | 87 | agent | Legally `feed` after the object check, but start from words | Good for object framing and light together |
| [LoC FSA/OWI colour](https://www.loc.gov/collections/fsa-owi-color-photographs/?q=night&fo=json&c=3) | `?q=night&fo=json&c=3`, then `https://www.loc.gov/item/<id>/?fo=json` for `rights_advisory` | 25; `window` 18; `kitchen` 1 | agent | People `words` | Best open documentary framing. Small |
| Internet Archive | `https://archive.org/advancedsearch.php?q=title:storyboard+AND+mediatype:texts&fl=identifier&rows=10&output=json` | 161, including TV boards | agent | `words` | Good: framing grammar with no light in the way |
| [Hitchcock Zone](https://hitchcockwiki.com/wiki/Hitchcock_Gallery:_storyboards) | Storyboard gallery | Not opened | person | `look` | Link it, unchecked |
| Person-only | film-grab.com, shotdeck.com, [Frame Set](https://intercom.help/frame-set/en/articles/5683324-filtered-search) ("Frame size", "Aspect ratio", "Number of people") | Never fetched | person | `look` | Write links in `links.md`. Frames the person drops in are `words` |

| Trap caught in testing | Do this |
|---|---|
| Met Walker Evans with `isPublicDomain=true` counts 9,191. Of 30 objects tried, 21 opened with no public-domain image and 9 answered 404. At offset 1000 the API answered 403 | Do not trust a count. Open objects at `.../public/collection/v1/objects/<id>`. Stop at the 403. For open documentary use LoC |
| `q=pillar print&hasImages=true` gives 1,139, including a cotton "Pillar print textile" | Add `medium=Prints&isPublicDomain=true`: 744, and the first one opened was a print |
| Commons `storyboard film` gives 111,135 noisy hits | Skip that search. A category walk works better: `Category:Shop signs in Lisbon` gave a frontal tall frame (one cold run) |
| FrameThrower's [developers page](https://framethrower.ai/developers) shows `extreme-close-up`, which the spec does not have. Films and commercials use different words (`dutch_angle` against `dutch`) | Read the spec. Use each endpoint's own words |

## Queries

| Source | Bad | Good | Result |
|---|---|---|---|
| Met | `vertical video composition` | `q=hanging scroll&medium=Paintings&geoLocation=China&hasImages=true` | 906 |
| Met | `q=pillar print&hasImages=true` | `q=pillar print&medium=Prints&hasImages=true&isPublicDomain=true` | 1,139 with textiles against 744 |
| Met | `composition` | `q=still life&medium=Paintings&hasImages=true&dateBegin=1600&dateEnd=1800` | 87 |
| FrameThrower | `cinematic wide shot alone` | `{"query":"a woman alone under one streetlamp at a bus stop, the street behind falls dark","lighting":"streetlamp","time_of_day":"night","setting":"exterior","shot_type":"wide","visual_style":"live_action"}` | Not tested |
| FrameThrower | `extreme-close-up` | `{"shot_type":"closeup","camera_angle":"high_angle"}` on films, `{"shot_size":"extreme_closeup"}` on commercials | Not tested |
| Any vision model | "what lens is this, in mm?" | ShotOnWhat first, then "wide, close" or "long, far" | Mean 37.7% on lens |

Feeling to framing: the table in `queries.md`. No measurement of Dutch angle as unease turned up.

## Code vs generated

| | Generated (Seedance, Kling, Veo, Nano Banana) | Code (HyperFrames, Remotion, three.js) |
|---|---|---|
| Must prove | Shot size, lens class, staging, in words a model follows | Grid, margins, scale ratios, safe zones, in numbers |
| Output | `Wide, camera at eye level, 28mm decided; she sits in the bottom-right third at 25% of frame height; empty shelter above.` | `Close-up, slightly low angle, centred, bottle at 60% of frame height, 85mm decided`, then set the camera and measure a render |
| UGC | `Medium, phone at chest height, wide lens, slightly off-centre, handheld.` | Not applicable |
| Check | One test take: compare crop points and thirds with the board | Render a frame on the grid. FrameThrower's `depthUrl` might help match staging, not tested |

Nothing above was generated or rendered, so nobody has shown a model follows these lines. Check a tall crop before you
commit. This keeps the centre: 599x465 became 262x465, `tested 2026-11-03`. A frame already narrower than 9:16 keeps its
width: the 233x623 scroll became 232x622. Then look at whether the head survived.

```
$ ffmpeg -i frame.jpg -vf "crop=min(iw\,ih*9/16):ih" tall.jpg
```

## Reject if

`our proposal`, and see `never.md` for the universal tests.

- It has no person, object of known size, horizon or verticals, and you need size or height from it.
- The source is a crop or a re-cut, so the frame edges you are reading are not the original's. A search result's `image` is
  usually a sized copy of the whole frame, which is fine for layout. Check `bytes` before you fetch `original`.
- A lens claim rests on aspect ratio, a label or a vision model alone.
- A broken rule has no reason you can write beside it.
- You use the frame itself, and the subject box does not survive a crop to the target aspect.

## Judge it

Use Framing F1 to F5 in `judge.md`. Lens stays out of the LLM's job: use records or a person.
