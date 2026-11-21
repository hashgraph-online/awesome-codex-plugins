# How to write each line of the board

One section per line, in ranked order. Each has the rule, wording that works (with its source), what fails, the model
limit, what the vendor guides say, the tools to use, and a board line to copy. Every tip read from X, with links, is in
`dimensions-evidence.md`; every URL is in `links.md`.

Saves = X bookmarks on the cited post. All pages opened on 2026-11-03.

---

## 1. References

**Rule.** 3–5 references, each lending exactly one thing (light, palette, framing, texture, type or motion), each
with what it must not copy, and a rights badge: *feed* (CC0, licensed, our own) or *link-only*.

Works:
- "naming a style works way better than describing one"; without a reference the agent falls back to "centered
  text, gradient background, everything fading in" ([@rexan_wong](https://x.com/rexan_wong/status/2103707054108299437), 18,187 saves).
- Reverse-engineer a frame: feed it to Claude and ask for lens, lighting, colour temperature, composition, depth of
  field, then put the numbers on the board ([@starks_arq](https://x.com/starks_arq/status/2035367453711360340), 1,753 saves).
- "reverse-engineer the art direction: mood, typography, pacing, and WHY each animation exists. save it as a style
  bible" ([@0xMiraqle](https://x.com/0xMiraqle/status/2077199463278395732), 1,581 saves).
- Give each reference one role: "The reference image defines WHO the person is, not the pose, location, expression,
  clothing, lighting, or composition" ([@swiat_ai](https://x.com/swiat_ai/status/2100482637341012201)).

Fails: a one-line prompt and no references ("10 prompts in and it was not getting better. It was very, very bland.",
[@rameerez](https://x.com/rameerez/status/2015859121661059569), 2,101 saves); feeding a generator someone else's frame brings back their actor, set or logo.

Model side: newest multi-reference models open the prompt with reference roles: Kling 4.0 `[Asset Roles]`, MiniMax H3
"Reference asset instructions + Core concept + Shot-by-shot description", Seedance 2.5 asset referencing first
("Refer to Image 1 for lighting and filters"). Midjourney has native moodboards and `--sref`; Runway has Gen-4
References; Higgsfield Soul has moodboards.

Tools: FrameThrower MCP (4,326,755 frames, search by lens, shot size, colour), Refs MCP (4,422 films, free search),
Are.na MCP (the board container), Savee MCP (6M+, paid; terms forbid storing), Unsplash/Pexels/Met APIs (safe to
feed). Human-only: ShotDeck, FrameSet, Shot Cafe, Film-Grab, Eyecannndy. Full table: `links.md` §2.

Board line: `References: [1] FrameThrower frame, night street in sodium light -> LIGHT (not the actor) · feed: no`

---

## 2. Light

**Rule.** One named source, its direction, hardness and colour temperature, and what motivates it. Same light family
in every shot.

Works:
- "85mm. Hard key upper left. 3200K tungsten. 4:1 fill ratio." ([@starks_arq](https://x.com/starks_arq/status/2035367453711360340), 1,753 saves).
- One key 30–60° to one side, slightly above eye level; motivate every light with a window, lamp, monitor or
  streetlight; never evenly bright ([@beginnersblog1](https://x.com/beginnersblog1/status/2117355436789977462)).
- "light everything from one sun" ([@NEXUS_TO_NOVA](https://x.com/NEXUS_TO_NOVA/status/2117261732489925018)).
- UGC realism: "Natural window light only" ([@recap_david](https://x.com/recap_david/status/2021970126091039028), 2,168 saves).
- Character and product sheets: flat 18% grey background, shadowless light, so no light is baked into the identity
  ([@sirlifehacker](https://x.com/sirlifehacker/status/2115227821912281228)).
- Warm/cold contrast: a cold ambient base with warm pockets from practicals ([@zer0point_eth](https://x.com/zer0point_eth/status/2116832762912973220)).

Fails: "They look fake because nobody directed the light"; "random lighting, inconsistent style, plastic skin"
([@mikefutia](https://x.com/mikefutia/status/2027860561351135472), 4,141 saves); lit reference sheets → plastic characters.

Model side: Higgsfield: "one named source, one direction, one color", rule out a second sun or stray flare. Sora 2:
"Light determines mood as much as action or setting", "a single strong source creates sharp contrast and tension".
Veo examples: "rembrandt lighting on a portrait", "harsh fluorescent office lighting". Wan dictionary: light source
type (daylight, firelight, overcast), light type (soft, hard, side), time period. Kling: "Light and shadow are the
vital elements that imbue photographic works with soul".

Agent limit: vision models misread light in reference frames (ShotBench mean of 24 models: lighting condition 41.6%,
lighting type 57.5%). Write the light; confirm estimates with the person.

Tools: Poly Haven HDRIs (CC0, pick one that matches the scene light), set.a.light 3D (10,000+ setups, human),
StudioBinder lighting guide (vocabulary), Imagen light diagrammer.

Board line: `Light: one hard sodium streetlight high camera-left (~2000K key); cold blue fill from an advert panel camera-right; wet-pavement reflections; deep black shadows; no other sources.`

---

## 3. Subject lock

**Rule.** An identity block (face, hair, outfit with colour names, proportions, accessories) written once and
repeated in every shot, and a sheet (front, side, back, close-ups) on flat 18% grey with shadowless light, approved
before video.

Works:
- "if your character sheet is bad, you'll just waste tokens" ([@simonecanciello](https://x.com/simonecanciello/status/2111099437065855376), 2,624 saves).
- Lock outfit colours with muted, specific names so Seedance keeps them: "faded charcoal-grey sleeveless crop top,
  loose high-waisted light-wash jeans" ([@john_my07](https://x.com/john_my07/status/2071977017474789557), 21,231 saves).
- "the character lock that holds one face across every cut" ([@twoclipping](https://x.com/twoclipping/status/2073819471354192083), 4,803 saves).

Model side: all 14 guides cover the subject. Kling: subject, motion and setting are "the most fundamental". Seedance
2.0: "first lock in "who" is "doing what"". Luma Ray2 and Nano Banana start with the subject.

Skill: varg-character-design (https://github.com/vargHQ/skills/tree/main/varg-character-design).

Board line: `Subject: woman, 30, shoulder-length black hair, charcoal wool coat to mid-calf, red umbrella #C1272D; sheet on 18% grey, shadowless.`

---

## 4. Framing

**Rule.** Shot size, camera height and angle, lens in mm, where the subject sits and how much of the frame it fills,
and the aspect ratio. Unprompted models default to a medium shot.

Works:
- "Stop letting AI guess your camera angles"; call the subject a "tiny silhouette" to push the camera back
  ([@tetsuoai](https://x.com/tetsuoai/status/1997397799936139739), 9,884 saves).
- Numbers: "tilted 15-25°", logo at ~50% of frame height ([@zazzygfx](https://x.com/zazzygfx/status/2042690351526248917));
  "head from hair crown to chin occupying 50–60% of frame height" ([@VIBEQUIRKLABS](https://x.com/VIBEQUIRKLABS/status/2116168611773726743)).
- Direct the shot: INTENT → SUBJECT + ACTION → FRAME → OPTICS → CAMERA → PERFORMANCE → LIGHT → CONTINUITY
  ([@beginnersblog1](https://x.com/beginnersblog1/status/2105685837812007258), 1,921 saves).
- Front-load the non-negotiables: aspect ratio, medium, shot type ([@IamEmily2050](https://x.com/IamEmily2050/status/2018697592800981099), 2,677 saves).
- UGC: wide-angle, deep focus, handheld, slightly off-centre ([@mightyking](https://x.com/mightyking/status/2089299068514148655), 2,833 saves).

Fails: perfect symmetry reads as AI, keep "slightly uneven framing" ([@genuenci](https://x.com/genuenci/status/2088679915491074155));
vibe prompts with no shot, lens or camera position.

Our test: unusual angles failed most. Seedream met the top-down perfume framing 50% of the time and the straight-down
aerial 58%. Fix with a 3D blockout (threejs-animatic) or a reference frame.

Model side: Seedance 2.5 accepts shot size, movement and angle terms directly. GPT Image: call out placement
("subject centered with negative space on left"). Veo angle list: eye-level, low, high, bird's-eye, worm's-eye,
Dutch, close-up, extreme close-up, medium, full, wide. Wan: shot size, composition, focal length, camera angle.

Agent limit: framing is what vision models read best in films (64.1%), lens size worst (37.7%): always write the mm.

Tools: StudioBinder shot guide (50+ shot types), Veo prompt guide vocabulary, CineScale (shot sizes of 124 auteur
films), Shot Designer (blocking).

Board line: `Framing: wide, camera at knee height, 24mm, 16:9; she stands in the right third at 30% of frame height; dark empty space upper left.`

---

## 5. Palette

**Rule.** 3–5 colours as hex, taken from a reference frame (`scripts/palette.py extract`), each with a role
(shadows, highlights, one accent), one warm/cold contrast, what may not be saturated, and the grade in words.

Works:
- Sora 2: "Naming three to five colors helps keep the palette stable across shots".
- Hex for the big fields: "a vertical gradient #081d2c to #102348" ([@finnardley](https://x.com/finnardley/status/2114305886420086817), 5,291 saves);
  a named palette with roles: paper #EBE7E1, ink #1E1C1A, red #D7372C ([@finnardley](https://x.com/finnardley/status/2116010421740007894)).
- Grade for realism: "Drop contrast, push shadows up, add slight fade" ([@brendanhaze](https://x.com/brendanhaze/status/2031092943000346814), 1,716 saves).
- Take the grade from a real photo as colour-grading JSON ([@recap_david](https://x.com/recap_david/status/2023792981208429046)); match
  shots with Match Color or color-matcher ([@ciguleva](https://x.com/ciguleva/status/1994131108385214763)).
- One ink plus white space for stylised pieces ([@yanliudreamer](https://x.com/yanliudreamer/status/2093968800316293400), 10,649 saves).

Fails: leaving it to the model (Nano Banana Pro comes out grey and flat without a grade); invented palettes. In our
test the hex line was obeyed best (89%) but frames looked less like film with it (−0.67 film-likeness, 5 of 6 pairs).

Model side: colour is the easiest attribute for video models (T2V-CompBench: "color is the easiest to manage,
followed by texture"; VBench colour mean 85.66%), but a colour that must change during a shot fails about 80% of the
time (VBench-2.0). Higgsfield: colours and text "are the two details that drop out most often": name them.

Why it moves viewers: brightness and saturation set the mood more than hue (Valdez & Mehrabian 1994:
Pleasure = .69B + .22S, Arousal = −.31B + .60S).

Tools: Screenmusings Color Lab (film frames by dominant colour), Colormind and Huemint APIs (fill a palette from 1–2
locked colours; non-commercial), Timeline of Historical Film Colors (period processes), Coolors, Color Hunt.

Board line: `Palette: shadows teal #0F3B3F, highlights sodium orange #E07A2E, accent red #C1272D (umbrella only); nothing else saturated; low contrast, lifted blacks.`

---

## 6. Motion

**Rule.** Per shot: one named camera move, one subject action, start and end, duration. A reference clip when you
can. The average shot length for the cut.

Works:
- Sora 2: "Each shot should have one clear camera move and one clear subject action. Actions work best when
  described in beats or counts". Seedance 2.0: "Try to specify only 1 type of camera movement in a single shot."
- Name the move: push-in, pull-back, pan, tilt, tracking, orbit, crane, dolly zoom, FPV, handheld
  ([@beginnersblog1](https://x.com/beginnersblog1/status/2065759796104761770), 2,269 saves).
- Timestamped beats: "0-4s: [Medium Wide]" ([@techhalla](https://x.com/techhalla/status/2083389002552664385), 2,537 saves).
- One move with a duration: "The object slowly flips horizontally over 5 seconds" ([@hewarsaber](https://x.com/hewarsaber/status/1911052503686262917), 2,960 saves).
- Copy motion from a clip: "keep the same movements, camera quality and audio" ([@simonecanciello](https://x.com/simonecanciello/status/2116268465463976312), 4,032 saves).
- Short-form pace: "keep a new image or motion every 2 seconds" ([@gregisenberg](https://x.com/gregisenberg/status/1977828256750403927), 4,534 saves).
- Generate short clips and cut them yourself ([@_VVSVS](https://x.com/_VVSVS/status/2090813096310784160)).

Fails: "smooth cinematic movement"; several moves in one shot; fights and multi-person action come out stiff.

Model side: prompted camera moves land about half the time (VBench mean 49.58%; Sora 27.16%, Kling 1.6 61.73%,
Veo 3 54.94%). EvalCrafter: "All methods cannot perform camera motion control directly using text prompt." Use the
model's camera presets or parameters (Kling camera_control, Higgsfield presets) or a motion reference. MiniMax: an
orbit is "truck left + pan right". For image-to-video, every vendor says prompt motion only.

Pace: average Hollywood shot length fell below 4 s after 2000 (Cutting 2011).

Tools: Higgsfield camera controls (50+ presets), Kling camera control parameters, CameraBench (150,000+ labelled
camera moves), Eyecannndy (techniques, human-only), Motionographer.

Board line: `Motion: shot 1, 4 s: slow push-in from wide to medium; she lowers the umbrella at 2 s; rain in motion-blurred streaks. Average shot 2.5 s.`

---

## 7. Texture

**Rule.** One capture medium (film stock, device or era) and its physical flaws; skin detail for people; grain and
one compression pass in post.

Works:
- "Blurred and slightly halated streetlights" on 35mm analog ([@xmliisu](https://x.com/xmliisu/status/1993152669150822852), 15,976 saves).
- "Raw friend-recorded early-2000s consumer DV footage" as the first style line ([@kingofdairyque](https://x.com/kingofdairyque/status/2096833375369929039), 4,208 saves).
- "add 2-3% film grain", export 1080p, one compression round ([@knoxtwts](https://x.com/knoxtwts/status/2028840621423644728), 5,763 saves).
- Skin: visible pores, uneven texture, asymmetry, "Subtle phone-camera grain" ([@recap_david](https://x.com/recap_david/status/2021970126091039028), 2,168 saves);
  fix skin at the image stage before animating ([@twoshados](https://x.com/twoshados/status/2056052193476727183), 4,135 saves).
- Stylised: "soft clay with fingerprints, lumpy edges, stop-motion at 12 fps" ([@m4lkxx](https://x.com/m4lkxx/status/2116893154322284929)).

Fails: "photorealistic 8k", flawless skin, perfect symmetry; grain on a look that should stay clean.

Our test: the smallest lift of the six (+31 points): models already added a film look half the time when the rest of
the board was cinematic.

Model side: Kling 4.0 rejects "Premium look" for "fine matte grain is visible on the surface". Higgsfield: "Close
with the visual reference, a film stock, a grain level, a color grade". Sora 2 example: "fine grain; subtle halation
on speculars; no gate weave". Midjourney names only a medium, never a stock.

Tools: Kodak motion-picture stock pages (Vision3 200T, 250D, 500T…), filmdev.org (5,629 stock recipes with photos),
FilmConvert and Dehancer (emulation in post), ambientCG and Poly Haven (CC0 materials).

Board line: `Texture: Kodak Vision3 500T 35mm, fine grain, halation around every light, slightly soft, no digital sharpening; +2% grain in post.`

---

## 8. Type

**Rule.** Font family, weight, size, hex, position, case and tracking on the board; the text itself set in code
(HyperFrames, Remotion) over the footage. Let a model draw text only for one short quoted word.

Works:
- "one clean UI font (Geist)" ([@twoclipping](https://x.com/twoclipping/status/2103273003555402193), 21,166 saves).
- "NO generic fonts (Inter, Roboto, Arial, system-ui)" ([@cloudxdev](https://x.com/cloudxdev/status/2002526815022190985), 4,322 saves).
- Serif italic display + light sans body, both by name: "Instrument Serif (italic) — headings" ([@viktoroddy](https://x.com/viktoroddy/status/2035366371530617238), 3,775 saves).
- Captions from word timings (faster-whisper), not from the video model ([@flxrnc](https://x.com/flxrnc/status/2117318336837017846), 3,213 saves).
- Pin graphics to the world, not the screen, when the camera moves ([@tetsuoai](https://x.com/tetsuoai/status/2115277212824019367)).

Fails: default fonts and purple gradients; all-caps wide-tracked labels and gradient text read as AI; asking the
video model for subtitles.

Model side: exact text is the weakest skill of video models (best T2VTextBench score 0.37; Sora-2 keeps exact text in
0.671 of layouts, Veo 3.1 in 0.416, references 0.940). GPT Image: "Put literal text in quotes or ALL CAPS and specify
typography details (font style, size, color, placement)". Pika: write "No other text". Veo: to prevent text, avoid
quotation marks. Kling 4.0 and Seedance 2.0 accept font size, alignment, timing and position for subtitles.

Tools: Google Fonts (1,959 families, metadata without key), Fontshare (100 free families), Fonts In Use (35,008
documented uses), Typewolf, Art of the Title, title-design skill.

Board line: `Type: LAST BUS, Barlow Condensed 700, #FFFFFF, 48 px, tracking +200, lower left x 96 y 960; set in code.`

---

## 9. Sound

**Rule.** One line each for voice, music and room tone; generate the voice separately and lock the audio before
animating so the model does not change body movement to fit it.

Works: "You've made it look right. We'll make it sound right." ([@MireloAI](https://x.com/MireloAI/status/2110360787780800611), 4,303 saves);
"If your AI characters sound fake, the fix is almost always in how you write and DIRECT the dialogue in your prompt"
([@second_bassoon](https://x.com/second_bassoon/status/2117307653320007954), 4,472 saves).

Model side: Veo, Sora 2, Kling, Seedance, Hailuo, Wan, Pika and Higgsfield give audio advice; Runway video and Luma
do not.

Board line: `Sound: rain on the shelter roof, distant traffic, no music until the bus arrives.`
