# Light references

A light reference proves one thing: this source, from this side, with this edge, can make this picture. You can point to
the shadow and to what made it. It lends light only, never the actor, wardrobe or set. It does not prove the lamp, the
on-set ratio or the true Kelvin.

On generated work light gets the most search: a floor of 6 queries and 3 sources (`our proposal`), and a hard brief took
26 in the ad cold run. On coded work it comes only where a shot has it, and one still does not earn the floor
(`queries.md`). Machines read it badly: a mean of 24 vision models scored 41.6% on lighting condition and 57.5% on
lighting type ([ShotBench](https://arxiv.org/html/2506.21356), older models, no 2026 rerun found), and in our 48-still
test two judges agreed least on light (κ = 0.46). Treat your own reading as one weak witness, then measure it.

## Read it

Same order on every frame. Crop first: eyes, nose and chin, one shadow edge, the brightest surface. Ask one closed
question per crop, write the evidence before the answer, allow "unknown". The questions are `our proposal`: nobody has
tested whether crops or two reads raise accuracy.

| # | Look at | What it tells you | Closed question |
|---|---|---|---|
| 1 | Cast shadows | "What direction is the light coming from?" "The shadows will tell you" ([Hobby](https://strobist.blogspot.com/2006/04/reverse-engineering-other-shooters.html)). Sun: length = height / tan(altitude), so about 9.5× the object at 6°, 4× at 14°, 1.4× at 36°, 0.5× at 62° | Shadows fall: left, right, toward camera, away, none visible, unknown |
| 2 | Nose and chin | Start "assessing the shadows under the model's nose and chin" ([McKim](https://fstoppers.com/how-to-read-light-in-photography-part-2)). Short, straight down: in front, a little above the eyes. Long, no catchlights: far above. Going up: below the eyes. No direction: highly diffused | Nose shadow: left, right, up, down, none visible, unknown |
| 3 | Catchlights | Reveal "a lot about the frontal lighting" (Hobby). Retouching or shadow can remove them (`reported`, snippet only), then use skin highlights | Eye reflection: position, shape, none, unknown |
| 4 | Number of sources | Several shadow directions mean several sources. Reverse-engineer only the key first (Hobby, snippet only) | Shadow directions: 1, 2, 3+, unknown |
| 5 | Falloff | Fast falloff suggests a near source, a small lit area a snoot or grid (Hobby). "By controlling the size and placement of the light you can control the way the light will fall" ([Deakins](https://www.rogerdeakins.com/forums/topic/lighting-a-dark-corridor/)) | Across one wall or floor: fast, slow, even, unknown |
| 6 | Shadow edge | A hard or smooth transition shows hardness. Size and distance set it: "Further away and larger" ([Deakins](https://www.rogerdeakins.com/forums/topic/how-to-create-a-believable-dawn-interior-in-a-tiny-location/), on a dawn interior) | Name one edge: crisp, gradual, no edge, unknown |
| 7 | Ratio in stops | Lit against shadow side of one surface. Each stop doubles: 1 = 2:1, 2 = 4:1, 3 = 8:1 ([Wandering DP](https://wanderingdp.com/cinematography/cinematography-school-lighting-ratios-101/)). Write stops, since Kodak's 3:1 counts "main plus fill illumination and fill illumination alone" ([snippet only](https://www.scantips.com/lights/kodakgraycard.pdf)) | Measure it, do not guess |
| 8 | Colour | Apparent colour of highlights and shadows, on a neutral surface. A gel or a grade may have set it | Warm, neutral, cool, unknown |
| 9 | Motivation | What here could make this light? It can be fiction: in The Conformist "the light is not coming from the window at all, it's coming from above the set" ([ProVideo Coalition](https://www.provideocoalition.com/helpful-ways-for-cinematographers-to-get-a-grip-on-lighting-part-3/)) | Source: visible, implied, none, unknown |

**No face in the frame?** Skip rows 2 and 3. Read the wall or floor nearest the source, and the shadows of furniture.

**A frame can show** side, height, hardness, relative contrast and apparent colour. **It cannot show** the lamp model,
whether a strobe fired, the fixture mix, the on-set ratio or true Kelvin. Deakins: "The LED panels were sometimes 60% of
the overall light and at other times they added very little" ([forum](https://www.rogerdeakins.com/?p=216504)), and he
gels to the story's colour ([Jesse James](https://www.rogerdeakins.com/jesse-james-x-3/)). Answer "unknown" to those every
time. Use "Rembrandt" or "loop" only as a label a person has confirmed.

**Keep it**, `our proposal`, only if (1) a shadow edge is visible on a surface whose shape you understand, and (2) you can
point to the source or a clear reason for it. Value rises if you can state side, height, hardness and rough ratio in one
line, if a setup is published (plan, ASC article, gear list: the strongest kind), if subject and scale match the shot
(skin to skin, product to product), and if it is real capture. Since AI images appeared you cannot tell whether an image
is safe to study light from ([yutorikoubo](https://x.com/yutorikoubo/status/2051506121362534756), 781,939 views).

**Write the reading with its evidence.** One agent's reading of Vermeer's
[Young Woman with a Water Pitcher](https://images.metmuseum.org/CRDImages/ep/web-large/DP353257.jpg), `tested 2026-11-03`,
no person confirmed it:

```
Key: frame left, from the window (visible), above eye level (forehead brightest, nose shadow soft, down and frame right).
Catchlights: none, eyes lowered. Sources: 1. Edge: gradual, no crisp edge on the face. Contrast: forehead 1.3 stops, cheek
0.9 stops, wall 1.2 stops (measured, two crops each). Colour: wall warmer by the window (measured). Confidence: medium.
```

## Measure it

Run [`frame_light.py`](../scripts/frame_light.py) from the project folder, with `S=<skill folder>/scripts`. It needs ffmpeg
and nothing else.

```
$ python3 -I "$S/frame_light.py" DP353257.jpg
{"file": "DP353257.jpg", "left_mid_right": [0.125, 0.101, 0.071], "top_mid_bottom": [0.141, 0.115, 0.041], "bright_side":
"left", "lr_ratio": 1.75, "contrast_stops": 4.9, "p5": 0.009, "p50": 0.063, "p95": 0.265, "clip_high_pct": 0.0,
"pct_below_half_grey": 59, "highlight_k": 5060, "shadow_k": 8019, "source_size": "555x624"}
```

**Crop film borders first.** It measures whatever is in the frame. On one [LoC
negative](https://www.loc.gov/item/2017745253/) with its rebate and sprocket holes in frame, `p50` read 0.051 on the whole
frame and 0.195 inside the border (`tested 2026-11-03`, cold run on a coded film; 0.159 to 0.191 on our own crops). Use
`--crop`, or trim.

Brighter on the left, and the window is on the left, so measurement and eye agree. It measures the frame as graded, and
reflectance as well as light, so **`lr_ratio` is not a key-to-fill ratio**. `shadow_k` 8019 is her blue skirt, not the
light. Same script: Caravaggio's [The Musicians](https://images.metmuseum.org/CRDImages/ep/web-large/DP-687-001.jpg)
6.1 stops, 73% under half grey; La Tour's
[The Fortune-Teller](https://images.metmuseum.org/CRDImages/ep/web-large/DP-14286-015.jpg) 4.5 stops, `lr_ratio` 1.05, so
`even`. For video add `--at 12.5`.

To get closer to a ratio, crop twice on one material and take log2 of the two `p50` values, `our proposal`. On this wall
`--crop 80:60:90:30` (W:H:X:Y, by the window) gave `"p50": 0.322` and `--crop 80:70:430:260` (far side) gave `"p50": 0.139`,
so log2(0.322 / 0.139) = 1.2 stops.

For captured light in a 3D scene, run [`hdri_light.py`](../scripts/hdri_light.py). No dependency; it reads Radiance `.hdr`.
An HDRI and `sun.py` are for 3D and exteriors only: for a desk at night, `night,artificial,indoor` returned Christmas Photo
Studio and Concrete Tunnel (cold run on a coded film).

```
$ curl -s -A "your-agent/1.0" -O https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/1k/cobblestone_street_night_1k.hdr
$ python3 -I "$S/hdri_light.py" cobblestone_street_night_1k.hdr
{"file": "cobblestone_street_night_1k.hdr", "size": "1024x512", "key_azimuth_map_deg": 0.6, "key_altitude_deg": 14.4,
"key_k": 3143, "top_energy_share": 0.78, "key_vs_opposite_ratio": 3.63, "key_vs_opposite_stops": 1.86, "range_stops": 24.1}
```

| HDRI, `tested 2026-11-03` | `evs_cap` | Altitude | Key colour | Key vs opposite half | Top 0.1% energy | Range | Read as |
|---|---|---|---|---|---|---|---|
| `bloem_olive_house` | 22 | 47.6° | 6533 K | 3.77 stops | 0.90 | 25.2 | Hard high sun |
| `cobblestone_street_night` | 18 | 14.4° | 3143 K | 1.86 stops | 0.78 | 24.1 | One dominant warm lamp |
| `brown_photostudio_02` | 15 | 37.7° | 6213 K | 1.95 stops | 0.10 | 13.3 | Large window, soft |
| `studio_small_08` | 17 | 19.2° | 7193 K | 0.73 stops | 0.11 | 12.8 | Soft, wrapping |
| `aarfontein_pan` | 12 | 3.8° | 3400 K | 0.89 stops | 0.06 | 11.6 | Sun likely clipped: not a hard-light reference |

Across 13 maps, hard sources read 0.65 to 0.90 and soft ones 0.05 to 0.11, a small sample. Check `evs_cap` and
`range_stops` first: `aarfontein_pan` is tagged clear and high contrast and its text says "Unclipped", yet it ranges
11.6 stops against 21.5 to 26.9 on seven other clear-sky maps. `key_azimuth_map_deg` is no compass bearing: eight
clear-sky maps all sit at 35.9° to 36.3°, so they seem rotated to a common position.

## Verify it

1. **Look up first.** ASC, American Cinematographer spec sheets, ShotOnWhat, Deakins' site. Record conflicts.
2. **Measure pixels** with the commands above.
3. **Read it as above,** crop by crop, evidence first, "unknown" allowed. Never answer a fixture, a strobe or a true Kelvin.
4. **Read twice,** with a different crop or model such as ShotVL. If they disagree, write "unknown" or ask a person.
5. **Round trip.** Render the rig or generate one test frame, then run `--compare`. Its tolerance is unvalidated.
6. **Check the take.** Reject shadows in two directions, or a face lit from a side no source explains.
7. **For a hero shot, ask a person.** Eyes alone prove little: "the human visual system is generally insensitive to
   lighting inconsistencies" ([Farid](https://arxiv.org/html/2207.13744)).

```
$ python3 -I "$S/frame_light.py" --compare DP353257.jpg mirror.jpg   # both frames, then this line. Exit code 1 = outside
{"same_bright_side": false, "contrast_delta_stops": 0.0, "highlight_delta_k": 10, "within_tolerance": false, "tolerance":
"our proposal, not validated: same bright side, within 1 stop, within 500 K"}
```

That is a mirrored copy, a test of the script. No real take or render has been through this loop yet.

## Search it

**Split the spec first.** No library lets anyone search by ratio, shadow edge or Kelvin. Visible words go in the search
box, numbers go on the board. `single practical tungsten lamp, 4:1 ratio, hard falloff, interior night` becomes filters
`lighting: practical`, `setting: interior`, `time_of_day: night`; the sentence `one bare lamp lights half of her face, the
room falls to black`; and the board line `4:1 (2 stops), hard edge, warm`.

**For any brief, search cheapest proof first:** time and place (`sun.py`, exteriors), a measurable real source (Poly
Haven, 3D), film frames, then paintings. The table ranks sources by what they are worth. Results are `tested 2026-11-03`
unless marked.

**Search local words and English, both.** `lampelys` on Commons returned 92,978 with noise, and `Harriet Backer lamplight`
found the painting (cold run on a coded film). Dutch `kaarslicht` beat `candlelight`.

**Light words match captions, not light.** In the ad cold run, Rijksmuseum by Dutch word, Met by light word, Commons by
light phrase and LoC by "early morning" found no window-lit room for a dawn brief. Named artists on the Met worked, and a
subject word did: `interior tile` in LoC HABS found a real tile works in dark rooms, the best single find of that run.

```bash
python3 -I "$S/sun.py" --lat 38.72 --lon -9.14 --date 2026-11-03 --time 08:30     # UTC. Sunrise, sunset, altitude, azimuth
```

| Source | Exact route | What came back | Access | Rights | Verdict |
|---|---|---|---|---|---|
| [Deakins](https://www.rogerdeakins.com/jesse-james-x-3/) | `https://www.rogerdeakins.com/?s=window+light`, then read only his replies | 200, forum topics. [Some threads](https://www.rogerdeakins.com/forums/topic/advice-for-lighting/) have no reply from him | agent | `words` | Best to learn a setup: his plan, frames and words. Never feed the frames |
| [FrameThrower](https://framethrower.ai/api/v1/openapi.json) | `POST https://framethrower.ai/api/v1/search`, facets below | Not tested: 401 without a token | token | `words` | Only library found with a filter for what lights the frame. Best if the person pays |
| FrameThrower open pages | [`/style/window-light`](https://framethrower.ai/style/window-light), [`/film/sicario-2015`](https://framethrower.ai/film/sicario-2015) | Definition, 24 example frames, named films; "keeps 45% of it in soft, low-key light" | agent | `words` | Good free way to find film names and words |
| [Poly Haven](https://api.polyhaven.com/assets?t=hdris) | `search.py polyhaven "night,artificial,outdoor,high" --asset hdris` filters `attributes` | `night + artificial + outdoor + high contrast` 15; `sunset + clear + outdoor` 58; tag `softbox` + high contrast 4 | agent | `feed`, CC0 | Best for code and previz |
| [Met v1.1](https://metmuseum.github.io) | `https://collectionapi.metmuseum.org/public/collection/v1.1/search?q=Georges%20de%20La%20Tour&artistOrCulture=true&hasImages=true&isPublicDomain=true&medium=Paintings` | 3. Vermeer 6, Caravaggio 6, Rembrandt 43 | agent | Legally `feed` after the object check, but start from words: feed a painting only after a test frame. Named sitter `words` | Best open light, by artist more than by light word |
| [Rijksmuseum](https://data.rijksmuseum.nl/docs/search) | [`/search/collection?description=kaarslicht&type=painting`](https://data.rijksmuseum.nl/search/collection?description=kaarslicht&type=painting), then `https://id.rijksmuseum.nl/<id>` with `Accept: application/ld+json`. Three calls to reach an image: the record, then its `shows`, then `digitally_shown_by`, whose `access_point` is the file | 10, against `candlelight` 3. `maanlicht` 12, `venster` 55. `venster` usually means a window in the description, often a niche behind a sitter | agent | `words` until the object shows a public domain mark (one opened did; SK-A-2321 had no `subject_to` on its record or digital object, one cold run) | Good for candlelight, where Dutch worked best. `dageraad`, `ochtend` and `venster` gave 19 opened records with no window-lit room (one cold run) |
| [Commons API](https://commons.wikimedia.org/w/api.php) | `action=query&list=search&srnamespace=6&format=json&srsearch=filetype:bitmap incategory:"Rembrandt lighting" -deepcat:"AI-generated images"` | 13, top hits named sitters. Bare `chiaroscuro` 19,808 with dahlias and cosplay | agent | `words` for people, else per file | Best free photographic route |
| [LoC FSA/OWI colour](https://www.loc.gov/collections/fsa-owi-color-photographs/?q=night&fo=json&c=3) | `?q=night&fo=json&c=3`, then `https://www.loc.gov/item/<id>/?fo=json` | 25; `window` 18; `kitchen` 1 | agent | Read `rights_advisory` (one read "No known restrictions on publication"); people `words` | Good for real practical light. Small |
| [AIC](https://api.artic.edu/api/v1/artworks/search?q=Edward%20Hopper%20Nighthawks&fields=id,title,artist_title,image_id,is_public_domain) | Known artist or title | Nighthawks found, `is_public_domain: false`. `candlelight` with filters 687, mostly unrelated | agent | Per object. Hopper `words` | Good for titles, skip for light words |
| [NGA open data](https://github.com/NationalGalleryOfArt/opendata) | Download `objects.csv`, `published_images.csv`, filter yourself | Has "Imitator of Johannes Vermeer" rows, so filter attribution | agent | `feed` where `openaccess` is set | Good, slower |
| [Lantern](https://lantern.mediahist.org/catalog.json?q=%22low+key%22+lighting) | `catalog.json?q="low key" lighting` | 98,880 with excerpts, first hit American Cinematographer 1961 | agent | `words` | Good for period words and checking a reading. Read the excerpt, the count is broad |
| [`sun.py`](../scripts/sun.py) | `--lat 38.72 --lon -9.14 --date 2026-11-03 --time 08:30`, times in UTC. NOAA formula, standard library, azimuth clockwise from north | Altitude 14.0°, azimuth 122.9°, shadow 4.0× height. Lisbon sunrise 07:05 UTC, azimuth 108.8°, the same as [SunCalc](https://github.com/mourner/suncalc) 2.1.1 | agent | Data | Best for sun height and direction |
| Person-only | film-grab.com, shotdeck.com (`逆光` backlight, `ローキー` low key, [@ksd_illust](https://x.com/ksd_illust/status/2099998194906087701)), [Frame Set](https://intercom.help/frame-set/en/articles/5683324-filtered-search), [William Nguyen's 3D head](https://x.com/teacup_art/status/1274119275998072834), Google `"practical light" film still before:2022-11-30` | Never fetched. Film-Grab and ShotDeck named by 11 and 10 independent authors on X | person | `look` | Write links in `links.md`. Frames the person drops in are `words` |

| FrameThrower facet, read from the [spec](https://framethrower.ai/api/v1/openapi.json) `tested 2026-11-03` | Values |
|---|---|
| `lighting` | `sun, window, moonlight, practical, neon, fluorescent, firelight, candlelight, streetlamp, screen_glow, headlight, lightning` |
| `time_of_day` | `night, day, interior_indeterminate, golden_hour, dusk, blue_hour, dawn, overcast` |
| `setting`, `visual_style` | `interior, exterior, both`. `live_action` keeps out `cg_photorealistic`; also `noir, documentary` |
| `POST /api/v1/commercials/shots/search` | Other words. `lighting`: `natural, high_key, low_key, silhouette, chiaroscuro`. `setting` adds `studio_void, virtual_cg` |
| `POST /api/v1/similar` | After one good frame, instead of rewriting words: `frameId`, `mode: visual` or `color` |
| Open `/style/<slug>` | `chiaroscuro, hard-light, soft-light, high-key-lighting, low-key-lighting, natural-light, window-light, practical-lighting, neon-lighting, candlelight, silhouette, golden-hour, blue-hour, night-scenes` |

| Trap caught in testing | Do this |
|---|---|
| FrameThrower's docs disagree. `POST /browse` has no `lighting`, nor does the MCP's `find_by_craft` | Read the spec. Use REST for film light |
| `enhance` is on by default (recall@10 0.72 raw, 0.88 enhanced) and may soften a precise line | Run key queries both ways |
| Its labels can be wrong: the [Sicario page](https://framethrower.ai/film/sicario-2015) says "Anamorphic glass shapes the frame", [ShotOnWhat](https://shotonwhat.com/sicario-2015) lists Zeiss Master Primes | Treat labels as hints. Record the conflict |
| Its terms: "never ingest them in bulk", and one frame "isn't prohibited, but it isn't licensed or endorsed either" ([intended use](https://framethrower.ai/legal/intended-use)). Free credit reads 200 credits on the [developers page](https://framethrower.ai/developers), $2 in the [MCP repo](https://github.com/framethrower-ai/framethrower-mcp), 2,000 in [an X post](https://x.com/happy_modeling/status/2102023504246030642) | One frame at a time, as `words`. Check the person's account |
| Poly Haven `whitebalance` has a median of 5400 for sunset and midday alike. Words `candle` and `sodium` return 0 | Ignore it. Filter `attributes`, then measure. Candle lives in paintings |
| The Met's public-domain filter leaks: Hopper returned 26, yet [366204](https://www.metmuseum.org/art/collection/search/366204) reads `isPublicDomain: false`. `v1/search` is retired and `v1.1/objects` answers Not Found | Search on v1.1, then open each object at `.../public/collection/v1/objects/<id>` |
| `search.py met --artist` is loose. `Georges de La Tour` with no medium returned 4, including Maurice Quentin de La Tour. `Emanuel de Witte` returned De Witte Starre Manufactory (5) and Peter Candid (4) in the top 10 (one cold run) | Add `--medium Paintings`, and read the maker of every hit |
| No dawn value. Poly Haven `time_of_day` has none, and sunrise + indoor returned 0. FrameThrower's open `/style` list has no dawn page, and `/style/blue-hour` defines blue hour as "after sunset" (one cold run) | Get height and direction from `sun.py`, then write words. The token route has `time_of_day: dawn` |
| MovieStillsDB is publicity stills, not the film's own light. cinematography.com, CineD and r/cinematography answered 403 | Skip the first. The other three are person-only |
| Gurney's robots disallows `/search`. His *Color and Light* recurs in 6+ posts on why light looks as it does | Reach gurneyjourney.blogspot.com through its sitemap or `site:` |

## Queries

| Source | Bad | Good | Result |
|---|---|---|---|
| FrameThrower | `moody lighting` | `{"query":"one bedside lamp lights half of her face, the rest of the room falls to black","lighting":"practical","time_of_day":"night","setting":"interior","visual_style":"live_action"}` | Not tested |
| FT commercials | `premium perfume shot` | `{"query":"bottle on black, thin rim light along the glass edge","shot_size":"closeup","lighting":"low_key","industry":"Beauty & Personal care","setting":"studio_void","product_visible":true,"awarded":true}` | Not tested |
| Poly Haven | `candle`, `sodium` in description | `attributes`: `night`, `artificial`, `outdoor`, `high` | 0 against 15 |
| Rijksmuseum | `description=candlelight` | `description=kaarslicht&type=painting` | 3 against 10 |
| Commons | `chiaroscuro` | `incategory:"Rembrandt lighting"` | 19,808 noisy against 13 |

Feeling to visible words. A convention from teaching sources and prompt guides, with no experiment behind it. A chosen
frame overrides it.

| Feeling | Visible light words | Board numbers | FrameThrower filters, not tested |
|---|---|---|---|
| Lonely | One distant source, a small pool, surroundings fall to dark, cold ambient | Key to shadow 3+ stops (8:1+), background 2+ stops under | `lighting: streetlamp` or `moonlight`, `time_of_day: night` |
| Tense | Single hard source, shadow edge across the eyes, top or side, unwell colour | 3 to 4+ stops, hard edge | `lighting: fluorescent` or `practical`, `visual_style: noir` |
| Tender | Large soft window from one side, shadow wraps, warm | 1 to 2 stops (2:1 to 4:1) | `lighting: window`, `setting: interior`, `shot_type: closeup` |
| Nostalgic | Low sun through a curtain or haze, warm highlights, lifted blacks | Low contrast, altitude under 10° | `time_of_day: golden_hour`, `lighting: window`, `era: 1970s` |
| Luxury | Big controlled soft sources, clean black, a defined edge line | Low key but soft, background 3+ stops under | Commercials: `lighting: low_key`, `setting: studio_void`, `awarded: true` |
| Documentary truth | Only what the location has, uneven, mixed colour left uncorrected | Unset, measure after | `visual_style: documentary`, `lighting: practical` |

## Code vs generated

For generation a reference must prove a sentence, the right to use the image, and that the model obeys. For code it must
prove numbers you can set in a rig and re-measure. Nothing below was generated or rendered, so obedience is unproven.

| Must prove | Generated (Seedance, Kling, Veo, Nano Banana) | Code (three.js, HyperFrames, Remotion) |
|---|---|---|
| Direction | Words: "from camera left, above eye level" | Azimuth, altitude. Turn the map with [`environmentRotation`](https://threejs.org/docs/pages/Scene.html), then re-measure |
| Hardness | Words plus a reference with a visible shadow edge | Hard: `SpotLight` with low `penumbra`. Soft: env map, larger `shadow.radius`. `RectAreaLight` has "no shadow support" ([docs](https://threejs.org/docs/pages/RectAreaLight.html)) |
| Ratio | Words: "the far side of the face falls 2 stops" | Light intensity ratio = 2^stops, `environmentIntensity` as fill |
| Colour | One named colour plus one warm/cold contrast | Convert K to RGB yourself: three.js has [no Kelvin helper](https://threejs.org/docs/pages/Color.html) |
| Motivation | Name the visible source in the prompt | A visible emissive practical at the light's position |
| Rights | Feed only `feed`. Everything else stays words | CC0, plus "Powered by Poly Haven" if a product uses the live API |

**Generated output:** a board line, plus one role line if a `feed` image exists. "Refer to Image 1 for lighting and
filters" is the documented Seedance form ([BytePlus](https://docs.byteplus.com/en/docs/ModelArk/seedance-2-5-prompt-guide)).
Veo 3.1 has no documented style type, so there it becomes words. Whether a painting gives its light without its painted
texture is unknown: test one take. Adherence falls when references "carry a salient state of the controlled attribute",
most for light and wind ([VIF-Bench](https://arxiv.org/html/2609.37709), adjacent models), so feed identity references lit
flat ([@sirlifehacker](https://x.com/sirlifehacker/status/2115227821912281228) uses 18% grey).

**Code output:** numbers. `HDRI cobblestone_street_night, evs_cap 18; altitude 14.4°, 3143 K, 1.86 stops, share 0.78; key
frame left; SpotLight added for the hard edge; one tone mapping for every shot.`

| Brief | Time or real light | Board light line | Fed or words |
|---|---|---|---|
| Generated: a night-shift nurse waits alone for the first bus in Lisbon | Sunrise azimuth 108.8°. `cobblestone_street_night` | `One high streetlamp camera-left, hard, warm; 3 stops key to shadow; bus shelter and street 2+ stops under; cold pre-dawn sky as the only fill; no second shadow.` | Words. Nighthawks lends "a lit island in a dark street", never fed |
| Code: a perfume launch, dark studio, one bottle | Tag `softbox` + high contrast: `story_studio_05`, `wooden_studio_10`. Neighbour `studio_kontrast_03`: 6428 K, 1.33 stops, share 0.05 | `Big soft overhead strip, thin rim along the glass edge, background 3+ stops under, neutral white; no stray reflections.` | Numbers. Lower `environmentIntensity` until the background measures 3 stops under |
| Generated: a woman drinks coffee in her Lisbon kitchen at 8:30, tender and true | 08:30 UTC altitude 14.0°, azimuth 122.9°, shadows about 4× object height. Decide direct sun or sky | `Natural window light only, window camera-left, soft sky with no direct sun, no fill; far side of the face falls about 2 stops; warm kitchen, cool window; shadows visible on the table.` | Words first. The Vermeer is legally `feed`: after a test frame, `Refer to Image 1 for lighting only.` |

## Reject if

- No shadow edge on a surface you understand, or no source and no reason for the light.
- The caption or tag supplies the light but the frame does not show it.
- It has no author, date or source, or it could be generated. See `never.md`.
- A clear-sky HDRI has a range far below its peers or a low `evs_cap`, and you wanted hard sun.
- The reading needs a lamp model, a strobe, an on-set ratio or a true Kelvin to hold.
- You asked for near black and `p5` is above 0.03, or `clip_high_pct` is above 2. Example limits: set yours per job.

## Judge it

On generated work Light is the one job judged by default: L1 to L6 in `judge.md`, if more than 3 candidates survive the
gates. On coded work, and on frames with people, read Scope there. `frame_light.py` supplies L4 (`p5`, `p95`,
`clip_high_pct`, `source_size`). A person owns L6.
