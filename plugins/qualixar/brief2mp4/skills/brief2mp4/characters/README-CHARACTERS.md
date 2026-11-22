# The character kit

A brief that says "two characters talk, walk or fight" needs characters that hold poses, move between them, blink, and move their mouths in time with a voice. The kit gives you that without any dependency: a rig that runs in a HyperFrames page, on a canvas or in Node, a pose and cycle library, a character file format, and art-form skins so the same character can be paper, anime or something else. A character stays recognisable across skins because every skin draws the same parts.

Everything is plain JavaScript and JSON. Nothing is fetched at render time.

## Files

| File | What it is |
|---|---|
| `rig.js` | `B2M.pose(character, track, t [, opts])`: the transform of every part at time `t`. A pure function of its inputs |
| `poses.js` | 15 named poses, the cycles (walk, run, wave, laugh, breath) and the nine mouth shapes |
| `shapes.js` | Turns shape records into paths; path tools for skins; the lip-sync mouth drawings |
| `render.js` | `B2M.layout(...)` gives a display list; `drawCanvas` and `createSVG` draw it |
| `skins.js`, `skins-extra.js` | The six skins (`B2M.SKINS`) |
| `stage.js`, `stage.html` | A 2D stage: backdrop, cast, captions; the page that plays a scene |
| `sheet.js`, `sheet.html` | The character sheet page |
| `cast/*.json` | The starter cast: `child`, `adult`, `crow`, `tomato` |
| `schema/character.schema.json`, `validate.py` | The format, and a standard-library validator |
| `image-demo/` | A robot rigged from PNG part images that a script draws: the worked example for your own art |

Scripts next to the skill's others: `scripts/lipsync.py` (mouth track), `scripts/standin_voice.py` (a preview voice from word timings), `scripts/character_sheet.py` (a PNG sheet), `scripts/character_project.py` (a scene, or the 2D-in-3D starter, to a HyperFrames project), `scripts/build_character_docs.py` (keeps the tables below in step with the code). `schema/scene.schema.json` and `validate_scene.py` check a scene file. The runnable example is `examples/09-story-characters/`.

In a page, load the scripts in this order: `poses.js`, `rig.js`, `shapes.js`, `render.js`, `skins.js`, `skins-extra.js`, `stage.js`. In Node, `require("<kit>/index.js")` loads them all. `character_project.py` copies the runtime into a HyperFrames project and inlines the cast as `characters/cast.js`.

## The starter cast

A child, an adult man in a kurta and dhoti-style outline (culturally neutral, no real person), a crow (a folded wing lying along the body, tip to the tail), and a tomato chef (an object character). Each is drawn from the same part list, in a three-quarter side view facing right, so poses, a walk and a fight read; each has a front-facing head drawing for close-ups, an anime redraw of the eyes, hair or crest, hard shadow shapes for the cel skin, and the hands, arms or wings it needs for open palms, pointing and a raised arm. The child holds a kite, the man a sword, the chef a ladle (`props: ["prop_kite"]` in a track). The crow's beak is a jaw that opens with the mouth shape.

## Look at a character first

```bash
python3 scripts/character_sheet.py --character child --skin all --out sheets/
python3 scripts/character_sheet.py --file my-art/hero.json --skin paper-cutout --out sheets/
```

Each sheet is a 1920x1080 PNG: the standing view, the front view close-up (if the character has one), six poses and the nine mouth shapes. Look at it before you build a scene. It is also the quickest way to check that a character still reads in every skin, and a source for thumbnails. One call renders every sheet through one HyperFrames snapshot run; it needs Node and, once, the network for GSAP.

## The pose function

```js
const posed = B2M.pose(child, track, t, { steps: skin.steps, smooth: !skin.steps });
const items = B2M.layout(child, skin, posed, { x: 600, y: 900, scale: 1.2 });   // feet at (600, 900)
B2M.drawCanvas(ctx, items);                                                    // or B2M.createSVG(document, parent, 1920, 1080).update(items)
```

It reads no clock and no unseeded randomness. Blinks and talk gestures come from a seeded hash of (character id, time bucket), so the same frame renders the same on every run. Call it from the paused GSAP timeline the way `references/threejs.md` shows.

A **track** is what one character does. It is a list of keys, or an object with any of these parts (every one is optional):

```js
{ keys:   [{ t: 0, pose: "idle" }, { t: 1.2, pose: "wave", ease: "out", mouth: "AI" }],   // which pose, from when
  move:   [{ t: 0, x: 300, facing: "right" }, { t: 4, x: 900, walk: true }],     // where it stands: absolute pixels; walk: true walks there
  layers: [{ cycle: "walk", from: 0, to: 4, steps: 8 }, { cycle: "talk", from: 4, to: 9 }],
  visemes: [{ t: 4.1, v: "AI" }, { t: 4.3, v: "rest" }],            // the lip-sync track (scripts/lipsync.py)
  props: ["prop_kite"], view: "front", fx: { speedLines: [[2, 3]] } }
```

Times are seconds. Between two keys the rig eases from one pose to the next; the ease on a key shapes the move **into** that key. Outside the first and last key it holds the nearest pose.

**Where a character stands.** `move` keys hold **absolute** positions in scene pixels: `x` is across the frame from the left edge (the middle of a 1920-wide frame is 960) and `y`, if you give one, is the y of its feet on screen. Without a `y` a character stands on the ground top (`ground`), so its feet are never hidden in the ground band; a `y` below the bottom of the frame is an error. Between keys the character glides. To walk, put `"walk": true` on the key the character walks **to**: the walk cycle then plays between the two keys at the speed that matches the distance, so the feet never slide, the glide is steady (the key's `ease` is ignored) and the character turns to face the way it walks unless a key says `facing`. You never need to work out a speed. (A walk that needs more than 12 drawings a second looks like a run; `character_project.py` warns and you give it more time or less distance.) A key that leaves out `x` or `y` keeps the character's home position, the `x` and `y` of its cast entry; with no `move` at all it simply stands at home. `move` positions are never added to the cast `x`.

**Which way it faces.** `facing: "left"` or `"right"` on a move key turns the character from that key on (`flip: -1` or `1` is the older spelling and still works); `facing` on the cast entry sets the way it faces before any key. Characters are drawn facing right. In a conversation, **speakers usually face each other**: the one on the left faces right and the one on the right faces left. A character that answers with its back turned reads as a mistake; `character_project.py` warns when it sees it.

**Mouths.** A character that is not speaking keeps a closed mouth, so a listener never looks as if they are talking: the pose can still smile or frown, but a mouth shape appears only when the track asks for it. Give a key `mouth: "AI"` to hold that shape from the key until the next one, or set `poseMouths: true` on the track to let each pose show its own mouth (open for surprise, wide for a laugh). Spoken words come from `visemes`.

### Poses

Joint angles are degrees. For arms, hands and legs a positive angle swings the limb forward, the way the character faces; for the torso, head, brows and feet it turns clockwise on screen. `lift` moves the whole body up or down as a fraction of leg length, so one pose fits a child and an adult. These are all the names a key's `pose` can take:

<!-- BEGIN generated: poses -->
| Pose | What it shows |
|---|---|
| `idle` | standing, arms loose, a slight breath |
| `wave` | near arm raised high behind the head, open palm (add the wave cycle to move the wrist) |
| `point` | near arm straight out in front, one finger pointing |
| `sit` | seated: thighs forward, knees bent, the body drops by 46% of the leg length |
| `run-ready` | a crouched start, leaning forward, arms bent |
| `jump` | in the air: arms up, knees tucked, the body lifts by 28% of the leg length |
| `surprised` | leaning back, arms out, eyes and brows wide |
| `sad` | head and shoulders down, brows tilted, a frown |
| `laugh` | leaning back, eyes squeezed shut, a wide smile (add the laugh cycle to shake) |
| `think` | a hand at the chin, eyes looking up |
| `fight-ready` | a low guard, near arm and far arm up, brows down |
| `bow` | bending forward from the waist, eyes closed, a small smile |
| `strike` | a lunge: front leg out, near arm thrown forward |
| `hurt` | thrown back, arms flung, eyes squeezed, a frown |
| `cheer` | both arms up, a wide smile, a small hop |
<!-- END generated: poses -->

### Cycles hold drawings

A cycle is a short loop of drawings added to the pose while a `layers` entry is active: `{ "cycle": "walk", "from": 0, "to": 4, "steps": 8 }`. `steps` is the number of new drawings per second: a walk has 8 drawings, so at `steps: 8` one stride takes a second. Handmade skins pass `steps: 12` to `pose` (line art 10), so nothing changes more than that many times a second whatever the cycles say. A smooth skin passes `smooth: true` and the cycles blend. To keep a walking character's feet planted, move it at `B2M.strideSpeed(character, "walk", steps) * scale` pixels a second. A layer fades in and out over `fade` seconds (default 0.1) and `amp` scales it.

<!-- BEGIN generated: cycles -->
| Cycle (a `layers` entry) | Drawings | Default steps a second | What it does |
|---|---|---|---|
| `walk` | 8 | 8 | legs swing, arms swing the other way, the body bobs; keep feet planted by moving at B2M.strideSpeed(character, "walk", steps) |
| `run` | 6 | 12 | a faster, longer stride with bent arms and a lean; the body leaves the ground between steps |
| `wave` | 2 | 5 | the wrist tips one way, then the other (two held drawings); use after a pose that raises an arm |
| `laugh` | 4 | 8 | the shoulders and head shake |
| `breath` | 8 | 4 | a slow rise and fall of the chest; always on unless the track sets breath: false |
| `talk` |  |  | a layer with no drawings of its own: head nods and small arm gestures while the mouth speaks, 7 beats a second (rate) |
| `blink` |  |  | not a layer: every character blinks every 2.5 to 5.5 s, from a seeded hash; the track sets blink: false to stop it |
<!-- END generated: cycles -->

### Mouth shapes

Nine shapes, the same for every character; a track's `visemes` and a key's `mouth` use these names. `scripts/lipsync.py` picks them from the words.

<!-- BEGIN generated: mouths -->
| Mouth shape (`v` in a viseme track, `mouth` on a key) | What it looks like |
|---|---|
| `rest` | closed mouth (a smile or frown comes from the pose) |
| `AI` | wide open (ah, i, my) |
| `E` | wide, teeth showing (ee, eh) |
| `O` | round and open (oh, ow) |
| `U` | small and round (oo, w) |
| `MBP` | lips pressed together (m, b, p) |
| `FV` | top teeth on the lower lip (f, v) |
| `L` | tongue up behind the teeth (l, th) |
| `etc` | half open, teeth showing (every other consonant) |
<!-- END generated: mouths -->

### Eases

<!-- BEGIN generated: eases -->
| Ease | Feel |
|---|---|
| `linear` | constant speed |
| `in` | starts slow, ends fast |
| `out` | starts fast, settles slowly (for arrivals) |
| `inOut` | slow at both ends (the default) |
| `sine` | a gentle inOut |
| `backOut` | overshoots a little, then settles |
| `hold` | stays on the earlier pose until the key time, then snaps |
<!-- END generated: eases -->

## Skins

A skin is a style map plus hooks: `shape(ctx)` turns one shape into drawing primitives, `character(ctx)` adds primitives for the whole figure, `sky(ctx)` and `foreground(ctx)` style the stage. All wobble is seeded by the shape and the drawing number. Each skin follows the rules of its page in `references/art-forms/`.

| Skin | Look |
|---|---|
| `line-art` | Strokes only, one weight, the line boils 10 times a second; the ground's colour inside a shape only hides lines behind it |
| `paper-cutout` | Flat fills, a thin lighter cut edge, paper grain, a tight shadow under each layer, edges that wobble on every held drawing |
| `shadow-puppet` | A flat black leather profile: one silhouette per part, props and the chef hat included, with a readable edge (nose, lips and chin, the moustache, a flared hem, cuffs, fingers) and at most an eye hole cut out. No brows, painted mouth, pupils or patterns, and no front view (a `view: "front"` track is drawn in profile and the sheet leaves the front cell out). The mouth is a **hinged jaw** cut as its own leather piece: it swings open with the mouth shape (shut for `rest` and `MBP`, widest for `AI` and `O`) and uncovers a gap of light, so lip sync shows in this skin too. Rods run from the torso and hands to the **bottom of the frame on purpose**: that is how a puppet is held. The stage uses the screen's own tones: a glowing backlight, mid-tone hills, a mid-brown ground, black scenery, and set shapes with `role: "light"` (sun, moon, lamp, fire) stay light, so nothing black vanishes into the ground and the sun is not a hole |
| `cel-shaded` | The anime redesign: parts with an `anime` variant are redrawn (large eyes with two highlights, hair with a shine band, a tick for a nose), hard shadow shapes (`role: "cel"`) in a tinted tone, an ink outline sized to each shape, speed lines on a jump, a run, or `fx.speedLines`. How spiky the hair is comes from the character file: `"spikes": 0.35` (0 calm to 1 spiky, default 0.6) blends the two outlines of any hair shape that has a `calm` set of points |
| `motion-comic` | Flat colour with a bold ink line, halftone dots for shadow, a panel border and a yellow caption box that carries the spoken line |
| `flat-explainer` | Clean flat vector: fills only, smooth motion, no outline and no shadow |

The handmade skins pass `steps: 12` (line art 10) to `pose`, so nothing changes more than that many times a second. The smooth skins pass `smooth: true` and cycles blend.

## Variants: one part, several drawings

A part can carry `variants`, each replacing the part's own `shapes`, `image`, `pivot`, `mouth` or `z`. Which one draws is decided, in this order, by the pose (`variants: { handN: "open" }`: an open palm for a wave, a pointing finger for a point), then the view and skin together (`front+anime`), then the view (`front`: a close-up that faces the camera, set with `track.view`), then the skin (`anime`). The child uses them for hands, a raised arm that draws over the head (`over`), the front-facing head, and the anime eyes and hair.

## The character format

```json
{ "id": "child", "palette": { "skin": "#f0b48a", "ink": "#231b2a" },
  "proportions": { "height": 232, "legLength": 78 },
  "parts": [
    { "id": "hip", "parent": null, "pivot": [0, -78], "z": 10, "shapes": [ ... ] },
    { "id": "legN_up", "parent": "hip", "pivot": [0, -78], "z": 10, "shapes": [ ... ] } ] }
```

Everything is drawn in one rest-pose coordinate system: feet on `y = 0`, the character facing `+x`, up is negative `y`. A part's `pivot` is where it hinges, in that same system; its children hang from it. Standard part ids are `hip` (the root), `torso`, `head`, `eyeN`, `eyeF`, `pupilN`, `pupilF`, `browN`, `browF`, `mouth`, `armN_up`, `armN_lo`, `handN`, the same with `F` for the far side, `legN_up`, `legN_lo`, `footN`, and props such as `prop_kite` (`"prop": true`, drawn only when the track lists them). `N` is the near side, `F` the far side. A pose that names a joint the character does not have skips it.

Shapes are `path` (absolute `M L C Q Z` only, so skins can wobble every point), `ellipse`, `circle`, `capsule` (a tapered limb), `rect` and `poly` (straight or a smooth curve through the points). `fill` and `stroke` name palette keys. `role` is `base`, `detail`, `hole`, `line`, `mouth` or `cel`. Validate with `python3 characters/validate.py cast/child.json`.

The mouth part has a `mouth` block: `lips` (drawn from the nine-shape table, `size` scales it), `jaw` (a lower jaw that rotates open) or `images` (below).

## Words, lip sync and a stand-in voice

Lip sync starts from the time of each spoken word. The file is a list of `{"text", "start", "end"}`, seconds from the start of the voice track:

```json
[
  { "text": "Hey",   "start": 3.45, "end": 3.70 },
  { "text": "crow,", "start": 3.78, "end": 4.12 },
  { "text": "that",  "start": 4.45, "end": 4.68 }
]
```

That is what `npx hyperframes transcribe voice.wav` writes (the word list, with an `id` on each word, which is ignored): point `lipsync.py` or a track's `visemesFrom.words` at the file it writes (`transcript.json` in the project folder; the command prints the path). Other speech tools usually give the same facts under other names, and `lipsync.py` reads the common ones: a list, an object `{"words": [...]}`, or `{"segments": [{"words": [...]}]}`, with `text` or `word`, and `start` and `end`. Anything else needs a few lines to convert it to the list above. Put one speaker's whole voice track in one file and cut it per character with `from` and `to`.

```bash
python3 scripts/lipsync.py words.json --fps 30                        # -> [{ "t": 3.45, "v": "etc" }, { "t": 3.5, "v": "E" }, ...]
python3 scripts/lipsync.py words.json --from 3.3 --to 6 --out kid.json   # one speaker's words
python3 scripts/lipsync.py --wav voice.wav                           # no timestamps: open, half-open, closed from loudness
```

Put the result in a track as `visemes`, or let a scene do it (`visemesFrom`, below). Words become shapes by letter rules with a small exceptions table, spread over the word's time in proportion to how long each sound takes. The mouth closes in any pause longer than 150 ms, no shape is held for less than one frame at `--fps`, and every key sits on the frame grid. `--lang hi` reads romanised Hindi (aa, ee, oo, kh, bh), and Devanagari is read letter by letter in any `--lang` (vowel signs to `AI`, `E`, `O` or `U`, प ब भ म to `MBP`, फ व to `FV`, ल to `L`, the rest to `etc`; the inherent a is dropped at the end of a word). Both are a best-effort mapping, approximate by nature, and meant for a mouth that looks right, not a phonetic transcript. Accented Latin letters are folded (café reads as cafe). A word with no letters the rules know is named on stderr and left out; if no word gives a shape the command exits with an error and suggests `--wav`. Words that overlap, as speech-to-text often gives them, are cut at the next word's start, and the words may come in any order. The picture follows the voice: never stretch the audio to fit the mouth.

**No recording yet?** `scripts/standin_voice.py` turns a words file into a WAV so you can preview the timing, the captions and the loudness:

```bash
python3 scripts/standin_voice.py words.json voice.wav --seconds 14
bash scripts/finish.sh --in raw.mp4 --out final.mp4 --seconds 14 --audio voice.wav
```

The WAV is a buzz that swells with each word and follows the mouth shapes (open vowels loud, closed lips quiet). It is not speech. Record or generate the real voice, run `npx hyperframes transcribe` on it, replace `words.json` and render again.

## A scene

`stage.js` composes a frame: a backdrop in the skin's style, the cast, captions. A scene file names it all, and the same file renders in any skin:

```bash
python3 scripts/character_project.py --scene scene.json --skin cel-shaded --out project/
npx hyperframes render project -o raw.mp4 --quality delivery --fps 30
bash scripts/finish.sh --in raw.mp4 --out final.mp4 --seconds 14 --audio voice.wav
```

`character_project.py` checks the scene against `schema/scene.schema.json` first. Every problem names the field and says what is allowed (`scene.cast[1].track.keys[2].pose: 'wavee' is not allowed. Allowed: idle, wave, ...`), and nothing is built until they are fixed. It also stops with an error when a cast member is fully outside the frame for more than half a second (naming the character and the times; set `allowOffscreen: true` on the cast entry if that is meant), and warns when two speakers face away from each other. `python3 characters/validate_scene.py scene.json` runs the first check alone.

**Your own characters.** A character file of your own (SVG-style shapes or PNG part images, see "Bring your own art") joins a scene with `--character-file`, once for each file: `python3 scripts/character_project.py --scene scene.json --character-file hero.json --character-file villain.json --out project/`. Each file is validated (a picture must be a real PNG or WebP inside the file's folder) and its pictures are inlined, then the scene's `cast[].character` can be the file's `id`. An id that is already in the starter cast is refused.

Here is a complete scene with every field. The `//` notes are for reading; real JSON has no comments. It is valid as written, apart from the words file, which must sit next to the scene.

```jsonc
{
  "$schema": "schema/scene.schema.json",       // optional; lets an editor check the file
  "width": 1920, "height": 1080,               // frame size in pixels
  "fps": 30,                                   // frames a second; used for lip-sync timing (default 30)
  "duration": 14,                              // seconds
  "skin": "paper-cutout",                      // line-art | paper-cutout | shadow-puppet | cel-shaded | motion-comic | flat-explainer
  "ground": 900,                               // the y where feet stand; cast entries default to it
  "palette": {                                 // backdrop colours, #rrggbb. Every skin restyles them
    "sky": "#f6d7a7", "ground": "#8a9a52",     // required
    "hill1": "#d98a5a", "hill2": "#b26a43",    // the usual hill colours
    "sun": "#ffd166", "kite": "#e5484d"        // any name a shape below uses
  },
  "hills": [                                   // silhouettes behind the cast, back to front
    { "fill": "hill1", "pts": [[0, 650], [620, 630], [1380, 620], [1920, 600]] },   // fill: a palette key; pts: the ridge line, left to right (the shape closes at the bottom of the frame)
    { "fill": "hill2", "pts": [[0, 760], [760, 750], [1560, 745], [1920, 705]] }
  ],
  "set": [                                     // extra shapes: the sun, a rock, a kite. Same records as a character's shapes
    { "type": "circle", "c": [1560, 250], "r": 90, "fill": "sun", "layer": "back", "role": "light" },   // layer "back" draws behind the hills; "front" (default) on the ground, behind the cast. role "light" (sun, moon, lamp, fire) stays light in shadow-puppet
    { "type": "ellipse", "c": [420, 915], "r": [48, 22], "fill": "kite", "rot": 0 },        // r: [rx, ry]; rot in degrees
    { "type": "rect", "x": 100, "y": 880, "w": 60, "h": 40, "r": 6, "fill": "kite" },       // x, y: top-left; r: corner radius
    { "type": "poly", "pts": [[1130, 852], [1172, 892], [1130, 934], [1088, 892]], "smooth": false, "closed": true, "fill": "kite", "role": "base", "shade": true },
    { "type": "path", "d": "M1130 934 Q1110 962 1138 980", "fill": null, "stroke": "kite", "sw": 6, "role": "line" },   // d: absolute M L C Q Z only; a line has fill null and a stroke colour (palette key) and width sw
    { "type": "capsule", "a": [200, 870], "b": [260, 870], "ra": 10, "rb": 6, "fill": "kite" }   // a tapered rounded bar from a to b with radii ra and rb
  ],
  "cast": [
    {
      "id": "kid",                             // your name for this entry; unique
      "character": "child",                    // child | adult | crow | tomato (files in characters/cast/)
      "x": 560, "y": 900,                      // where it stands: pixels from the left; y of the feet (default: ground)
      "scale": 1.9,                            // 1 is the drawn size; the child is 232 units tall, so 1.9 gives about 440 px
      "facing": "right",                       // left | right at the start ("flip": 1 or -1 is the older spelling)
      "allowOffscreen": false,                 // true if it may be out of the frame for over half a second
      "track": {
        "keys": [                              // a pose from `t` on; ease shapes the move into the key
          { "t": 0, "pose": "idle" },
          { "t": 3.3, "pose": "point", "ease": "out", "mouth": "rest" }      // mouth: hold this shape from here (optional)
        ],
        "move": [                              // absolute pixel positions; a missing x or y keeps the cast x or y
          { "t": 0, "x": -200, "facing": "right" },
          { "t": 3.0, "x": 560, "walk": true, "ease": "linear" }   // walk: true walks here from the key before, feet planted
        ],
        "layers": [                            // cycles added to the pose between from and to
          { "cycle": "walk", "from": 0, "to": 3, "steps": 8, "fade": 0.1, "amp": 1, "smooth": false },
          { "cycle": "talk", "from": 3.4, "to": 5.9, "rate": 7 }
        ],
        "visemesFrom": { "words": "words.json", "from": 3.3, "to": 6, "lang": "en" },   // the lip-sync track, built from the words that start between from and to (lang: en or hi)
        "visemes": [],                         // or give the mouth keys yourself: [{ "t": 3.5, "v": "E" }]
        "blink": true, "breath": true,         // both on by default; false to stop
        "poseMouths": false,                   // true: each pose shows its own mouth (see Mouths)
        "view": "side",                        // side | front (a close-up that faces the camera)
        "steps": 12,                           // only when you call B2M.pose yourself; the skin's steps win in a scene
        "props": ["prop_kite"],                // child: prop_kite; adult: prop_sword; tomato: prop_ladle
        "fx": { "speedLines": [[1, 2]] }       // time ranges for anime speed lines (cel-shaded skin)
      }
    },
    {
      "id": "chef", "character": "tomato", "x": 1400, "scale": 1.2, "flip": -1,   // flip -1 is the same as facing left
      "track": [ { "t": 0, "pose": "idle" }, { "t": 5, "pose": "laugh" } ]     // a bare list of keys is a track too
    }
  ],
  "captions": [                                // on screen from `from` to `to`; wrapped to the frame and scaled with it, at the bottom of the safe zone or the top when a character stands there; captions that overlap in time are stacked; motion-comic shows them in its caption box
    { "from": 3.45, "to": 5.95, "text": "Hey crow, that is my kite!" }
  ]
}
```

Captions are sized for the short side of the frame (40 px at 1080) and wrapped to fit; on a 9:16 frame they stay inside the platform's vertical safe zone. `character_project.py` warns when one needs more than two lines.

Set shapes take the fields of their type: `circle` (`c`, `r`), `ellipse` (`c`, `r` as `[rx, ry]`, `rot`), `rect` (`x`, `y`, `w`, `h`, `r`), `poly` (`pts`, `smooth`, `closed`), `path` (`d`), `capsule` (`a`, `b`, `ra`, `rb`). All of them take `fill` and `stroke` (palette keys or `null`), `sw` (stroke width), `role` (`base`, `detail`, `hole`, `line`, `light`), `layer` and `shade` (`false` stops the cel skin's two-tone). A `hole` is drawn in the paper colour. In the shadow-puppet skin the backdrop uses the skin's own screen tones (the palette colours are ignored there), set shapes are black leather, and `light` ones stay light.

`examples/09-story-characters/` is a working scene: a 14-second story with a walk, a point, two spoken lines, a laugh and a wave, built once and rendered as paper cut-out and as anime.

### Characters in a 3D set

```bash
python3 scripts/character_project.py --stage3d --cast child,crow --seconds 6 --out project/
```

`templates/threejs/characters-stage.html` puts each character on its own canvas, uses that canvas as the texture of a plane that faces the camera, and stands the planes in a Three.js set: a ground, four trees, a rock, a hut, a sun and a camera that moves. The frame is deterministic like the 2D stage. Edit the `ACTORS` list for who stands where and what they do.

## Recipes

Each recipe is a track you can paste into a cast entry (they are checked against the scene schema by a test). Positions are absolute pixels; the ground is at `y: 900` and the frame is 1920 wide.

### Recipe: walk in and stop

```json
{ "keys": [{ "t": 0, "pose": "idle" }, { "t": 3, "pose": "point", "ease": "out" }],
  "move": [{ "t": 0, "x": -150 }, { "t": 3, "x": 560, "walk": true }] }
```

It starts off the left edge, walks to x = 560 with its feet planted, faces right because it walks right, and points as it stops. A character may be off screen for up to half a second.

### Recipe: land on a perch

```json
{ "keys": [{ "t": 0, "pose": "idle" }, { "t": 0.3, "pose": "jump", "ease": "out" }, { "t": 1.1, "pose": "idle", "ease": "in" }],
  "move": [{ "t": 0, "x": 1300, "y": 900 }, { "t": 0.3, "x": 1300, "y": 900 }, { "t": 1.1, "x": 1380, "y": 700, "ease": "out" }] }
```

`y` is the y of the feet, so a perch whose top is at y = 700 is where the feet end up. Draw the perch as a `set` shape with its top at 700. The jump pose lifts the body while the move rises; the idle pose at the end is the landing.

### Recipe: jump off and leave

```json
{ "keys": [{ "t": 0, "pose": "idle" }, { "t": 0.2, "pose": "jump", "ease": "out" }, { "t": 0.9, "pose": "idle", "ease": "in" }],
  "move": [{ "t": 0, "x": 1380, "y": 700 }, { "t": 0.9, "x": 1450, "y": 900, "ease": "in" }, { "t": 3.4, "x": 2300, "y": 900, "walk": true }] }
```

It drops to the ground and walks out to the right. A character that stays outside the frame for more than half a second is an error, so end the scene within half a second of the exit, or set `allowOffscreen: true` on the cast entry.

### Recipe: turn to face

```json
{ "keys": [{ "t": 0, "pose": "idle" }, { "t": 2, "pose": "surprised", "ease": "out" }, { "t": 3, "pose": "idle" }],
  "move": [{ "t": 0, "facing": "right" }, { "t": 2, "facing": "left" }] }
```

A key's `facing` holds until the next key, and a key with no `x` or `y` keeps the character where it stands. Turn when the other speaker starts, so the two face each other.

## Known limits

- The cast is in a side view; a character that turns to face the camera mid-scene uses the front drawing for a close-up only (`view: "front"`), not a continuous turn.
- Skins style vector shapes. A part picture is drawn as it is, with a drop shadow in the paper skin only.
- Lip sync is letter rules, not a speech model: it is right for the mouth and wrong for pronunciation, and Hindi is approximate.
- The walk and run are side-view cycles; stairs, slopes and turning on the spot are not built in.
- A crow's beak and a robot's picture mouth open by amount, so some shapes (`rest` and `MBP`) look alike there.
- Shadow puppets are jointless in the tradition; here they keep the rig's joints. The skin makes the look, not the movement.

## Bring your own art: image parts

A part can show a PNG or WebP picture instead of vector shapes. That way art from any image model or drawing app can be rigged and animated. Prepare it like this:

1. **One image per part.** Cut the head, torso, upper arm, lower arm, hand, thigh, shin and foot into separate files, plus the eyes and brows if they should move. Keep the far arm and far leg as their own pictures (darker is fine).
2. **Transparent background**, 8-bit RGBA, saved as PNG or WebP. Trim extra margin, but keep the part whole: the overlap where a limb tucks under the body must be drawn, or a gap shows when the joint turns.
3. **The same scale for every part.** Pick one size for the character (the demo is 226 units tall at 2 pixels per unit) and size every picture to it. Draw at twice the size you will show, so it stays sharp at 1080p and 4K.
4. **A pivot for every part.** Write each picture's rectangle in the shared coordinate system (`image: { "src", "x", "y", "w", "h" }`, `y = 0` at the feet, facing right) and set the part's `pivot` to the joint, in the same coordinates. Read both off your drawing app: the top-left of the layer, and the point the joint turns about.
5. **Mouth shapes as separate images.** Draw nine, one per shape: `rest`, `AI`, `E`, `O`, `U`, `MBP`, `FV`, `L`, `etc`. Use `"mouth": { "kind": "images", "images": { "rest": { ... }, "AI": { ... } } }`; `rest` is required and stands in for any missing shape.
6. **Set parents and order.** `parent` links each part to the one it hangs from; `z` is the draw order (far limbs lowest, the head and near arm above the torso).

`src` is a path relative to the character file, or a `data:image/png;base64,` URI. `scripts/character_project.py` inlines pictures as data URIs when it builds a page, so a render needs no file. Run `validate.py` on the file: it checks that every picture exists, is a PNG or WebP, and that an image mouth has `rest`. Then render a sheet with `character_sheet.py --file`, and put the character in a scene with `character_project.py --character-file`.

`image-demo/make_tin_bot.py` is a complete example: it draws every part and every mouth with the Python standard library and writes `tin-bot.json`. Run it, open the sheet, and swap its pictures for yours. Skins style vector shapes; a picture is drawn as it is, with a drop shadow in the paper skin. For a flat silhouette or an ink outline, prepare the picture that way.
