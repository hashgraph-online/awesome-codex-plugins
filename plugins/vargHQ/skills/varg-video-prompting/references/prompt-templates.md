# Prompt templates

Copy a template, replace the `<...>` parts, keep the rest. The filled examples are generic and use one small
made-up project so the pieces fit together: **Mara**, a bicycle courier, in **a covered night market**, photoreal;
and one stylized place, **a lighthouse lamp room**, in a retro anime cel look.

Call shapes are MCP `call_tool` bodies; the same JSON works as the REST body of `POST /v2/tools/<tool>/call`
(see [mcp-tools.md](mcp-tools.md)). Check any model's exact fields with `get_tool("<tool>", "<model>")`.

---

## 1. Bible lines (write once, paste verbatim everywhere)

**Look line, photoreal**

```
Cinematic film still, 35mm lens, shot on Kodak Portra 400, fine film grain, natural skin texture, practical
light only, deep shadows with soft roll-off, muted palette of wet asphalt grey, sodium orange and teal.
```

**Look line, stylized**

```
1980s Japanese anime cel animation, hand-drawn ink line art, flat cel shading with soft airbrushed highlights,
painted backgrounds, magenta, cyan and violet light on deep navy, soft bloom.
```

Rules: style only (medium, lens, palette, grain). No weather, time of day or light direction in the look line;
those go into each shot. Avoid "noise", "static", "glitch" in stylized looks.

**Identity paragraph** (one per character, pasted word for word into every image and video prompt)

```
Mara: a woman of 31, lean and wiry, 170 cm. Short dark-brown hair cut in a choppy bob, one strand of hair
bleached copper at the left temple. Narrow hazel eyes, thick straight eyebrows, a small bump on the bridge of her
nose, a faint scar through her right eyebrow, visible pores and light freckles. She wears a dark-green waxed rain
jacket with a reflective orange stripe across the back, a grey hoodie under it, black cargo trousers to the ankle,
black high-top trainers, fingerless black gloves, a grey courier bag on her left hip.
```

What makes it work: an age as a number, two or three irregular features, every garment down to the feet, no
similes, no "beautiful", no famous-person comparisons.

**Place paragraph** (spell out what must not move)

```
The covered night market: a long aisle under a corrugated steel roof. Left side: five food stalls with red
canvas awnings, the third one with a large steaming pot. Right side: a row of hanging paper lanterns over
crates of oranges. At the far end a roll-up shutter door, half open. Wet concrete floor with shallow puddles.
```

---

## 2. Character sheet (still)

```json
{ "tool": "image", "input": {
  "model": "nano_banana_2_1",
  "aspect_ratio": "16:9",
  "prompt": "Character reference sheet on a flat light-grey background, even soft studio light. Five views of the same person side by side, same scale: front full body, three-quarter full body, profile full body, back full body, and one large face close-up. <IDENTITY PARAGRAPH>. Neutral relaxed pose, arms at the sides, empty hands. No text, no labels, no grid lines, no logos."
}}
```

- Empty hands and a neutral pose: props and gestures on a sheet leak into every shot. Make props a separate sheet.
- Faces small on a busy sheet drift; if the face matters, also crop the face close-up as its own reference.
- For a vehicle or product sheet, add "a person of 175 cm standing beside it for scale".

## 3. Environment master (still)

```json
{ "tool": "image", "input": {
  "model": "nano_banana_2_1",
  "aspect_ratio": "16:9",
  "provider_options": { "fal": { "resolution": "2K" } },
  "prompt": "Wide establishing shot of <PLACE PARAGRAPH>. Camera at the near end of the aisle at eye height, looking straight down the aisle toward the shutter door. Layout: 1) stalls on the left, 2) lanterns and crates on the right, 3) the shutter door centred at the far end. No people. Rain drumming on the roof, light mist. <LOOK LINE>. No text, letters or logos."
}}
```

Number the layout elements and say where the camera stands and what it faces. When the master is approved, it is
the first or second reference of every still in this place.

## 4. Scene still from sheet + master

```json
{ "tool": "image", "input": {
  "model": "nano_banana_2_1",
  "aspect_ratio": "9:16",
  "files": [{ "url": "<mara_sheet_url>" }, { "url": "<market_master_url>" }],
  "prompt": "@Image1 is Mara's character sheet: match her face, hair and outfit exactly. @Image2 is the master shot of the night market: same market, same stalls, lanterns and shutter door. Create one new single image, a medium close-up from the right side of the aisle at chest height: Mara stands by the third stall with the steaming pot, steam drifting across her face, she checks a paper delivery slip in her left hand, frowning. Exactly one person in frame; her two hands are attached to her arms in frame. Light: sodium orange from the stall bulbs on the left side of her face, cool teal from the lanterns behind. Full-bleed image filling the entire frame edge to edge, no borders, no letterbox. <LOOK LINE>. No text, letters or logos."
}}
```

Order of blocks: ref roles, place facts, "Create one new single image" with shot size and angle, the action and
expression, counts, light for this shot, frame line, look line, no-text line.

## 5. Blockout render to finished still (geometry locked)

Use when several cameras share a set and the master picture alone drifts. The blockout render (three.js, grey
shapes in real metres, people with head, arms and feet) is the FIRST file.

```json
{ "tool": "image", "input": {
  "model": "gpt_image_2_5",
  "aspect_ratio": "16:9",
  "files": [{ "url": "<blockout_render_cam3_url>" }, { "url": "<market_master_url>" }, { "url": "<mara_sheet_url>" }],
  "prompt": "Turn the FIRST image, a 3D previz blockout, into a photorealistic night film still. Keep EXACTLY its camera position, lens, framing and perspective, and the position, size and orientation of every object. Do not add, remove or move any object.\nMapping: grey floor = wet concrete with shallow puddles; the five red boxes on the left = food stalls with red canvas awnings; the white spheres on the right = hanging paper lanterns; the tall grey mannequin by the third box = Mara, the woman from the THIRD image, standing as the mannequin stands; the dark slab at the far end = a half-open roll-up shutter door.\nMaterials and mood must match the SECOND image. <LOOK LINE>. No text, no logos, no badges."
}}
```

Then add moving elements in a second pass, so the set stays fixed:

```
Keep the FIRST image pixel-identical in every respect: camera, stalls, lanterns, door, puddles, Mara's pose and
light. Add only one thing: <a delivery scooter from the SECOND image parked by the shutter door, headlight on>.
No text, no logos.
```

## 6. Edits

**Recast inside a finished still**

```
Keep this exact image: same market, same camera, same light, same pose, same clothes. Replace ONLY the woman with
<IDENTITY PARAGRAPH of the new person>. Real unretouched skin: visible pores, fine lines. No text, no logos.
```

If the result shifts the composition, narrow the edit:

```
Edit the first image only by swapping the person's head and face. Do NOT change the camera, framing, crop,
symmetry, room, pose or clothes: she stays exactly where she is in the first image, same size. Give her the face
and hair of the person in the second image. No text, no logos.
```

**Remove invented logos**

```
Remove only the logos, brand marks and printed text on the clothing and props. Change nothing else: same face,
same pose, same light, same colours.
```

**One change from the master** (keeps the set; use it for small pose changes)

```
@Image1 is the master shot: keep the stall counter exactly as it is, every item in the same place. @Image2 is
Mara's character sheet. Create the same shot as @Image1 with only one change: Mara leans in from the right and rests
both gloved hands flat on the counter. Exactly one person, two hands. <LOOK LINE>. No text, letters or logos.
```

Do not build a still around a hand touching a small unique prop (one bell, one button): in our runs that kept
duplicating the prop or adding a hand, even in this form. Frame the touch as an insert close-up or cut around it.

**Outpaint to a new aspect** (`bria_fibo_edit_1_5_expand`, one image in `files`, target `aspect_ratio`)

```
Extend the scene naturally to the sides: more market aisle, more lanterns. Only the one woman already in the
picture, nobody else.
```

**Fix a small fault** (hand, eye): crop the region locally, enlarge it, edit only that crop
(`"Redraw only the hand: five fingers, relaxed, same glove"`), paste it back with a feathered edge. Never redraw the
whole frame for a local fault.

## 7. Image-to-video from one approved still

One file = the first frame. The prompt is motion only.

```json
{ "tool": "video", "input": {
  "model": "kling_v4",
  "duration": 5,
  "resolution": "1080p",
  "files": [{ "url": "<approved_still_url>" }],
  "prompt": "Animate this exact frame. Slow push-in from the same angle. Steam drifts across her face; she lowers the slip, looks up toward the shutter door and her frown turns into a small determined smile. Lanterns sway slightly, rain drips from the awning edge. Natural, minimal, realistic micro-movements, no talking. Keep her face, jacket and the stall exactly as in the image. No cuts, no new objects, no text."
}}
```

The same prompt works on `seedance_2_5` with one file. Seedance gives more performance; Kling stays closer to the
still.

## 8. Start frame to end frame (Kling 4 chaining)

Two files = start and end frame (observed on `kling_v4`; check the first and last frames of the result). The end
frame of clip N is the start frame of clip N+1, which makes the cut invisible.

```json
{ "tool": "video", "input": {
  "model": "kling_v4",
  "duration": 5,
  "resolution": "1080p",
  "files": [{ "url": "<still_A_hands_with_glowing_bead>" }, { "url": "<still_B_planet_surface_fills_frame>" }],
  "prompt": "The small glowing bead between her cupped hands swells slowly like a breath drawn in; her hands part to make room. It keeps expanding, its light spilling over her fingers, its surface revealing swirling gold cloud bands. The camera pushes in smoothly until the glowing surface fills the entire frame. Continuous single move, smooth and organic, no cuts."
}}
```

Make both stills from the same master with the same identity paragraph, so only the camera and the action change.

## 9. Multi-shot master scene from references (Seedance 2.5)

All coverage of one place in one take, hard cuts inside the clip, cut back into the timeline in the edit.

```json
{ "tool": "video", "input": {
  "model": "seedance_2_5",
  "duration": 8,
  "resolution": "720p",
  "aspect_ratio": "9:16",
  "audio": false,
  "files": [{ "url": "<keeper_sheet_url>" }, { "url": "<lamp_room_master_url>" }],
  "prompt": "@image1 is the lighthouse keeper's character sheet: same face, grey braided beard, yellow oilskin coat, dark wool cap.\n@image2 is the master shot of the lamp room: every shot happens in this exact room (the great lens in the centre, the brass railing around it, the spiral stair opening at the left, rain-streaked windows all around).\nOnly one person in the room; every visible hand and sleeve belongs to him.\nStorm outside: lightning flashes through the windows at 2.1 s and 6.4 s.\nLook: <STYLIZED LOOK LINE>. Every frame is clean cel animation with crisp ink lines and flat colour: no noise, no static, no smeared blur.\n\n4 shots, hard cuts:\n1. 0.0-2.0 s. Wide from the stair opening: he climbs the last steps into the room, shaking water off his cap.\n2. 2.0-4.0 s. Medium close-up, slightly left: the lightning flash at 2.1 s lights his face; he squints at the dark lens.\n3. 4.0-6.0 s. Close-up on his hands: he strikes a match and lifts it to the wick inside the lens.\n4. 6.0-8.0 s. Wide from outside the window: the great lens blazes to life and the beam sweeps across the rain.\n\nCamera: one move per shot. Full-bleed 9:16 frame, no borders, no letterbox. No text, letters, numbers, logos or UI anywhere in the frame. No dialogue, no lip-sync."
}}
```

- Runs of 4-11 s obey better than 20-30 s runs and cost less to retake.
- Pass only refs of what is in frame; a monster on the sheet ends up in the room.
- `audio: false` when the clip gets music later; still strip the track in the edit (gotcha: one route ignored it).

## 10. Video-to-video from a previz or rough clip (Seedance 2.5)

Camera, cut timing and blocking from `@video1`; the look from the image refs. Send the reference clip in
**greyscale** to avoid getting it back unchanged.

```
@video1 is a black-and-white grey-box 3D previz of this sequence. Copy from @video1 ONLY the camera (framing, lens,
camera position and movement), the hard-cut timing and the blocking (where everyone is and what they do). Do not
copy its look: no flat grey shapes, no 3D render style, no greyscale; redraw every frame as <full-colour medium>;
the result must not look like @video1.
@image1 is <character> sheet: <the facts it locks>.
@image2 is the master shot of <place>: <the props that must stay>.
<Counts and anatomy. Light of this run.>
Look: <LOOK LINE>.

<N> shots, hard cuts exactly as in @video1:
1. 0.0-1.8 s. <shot size + angle>: <one action, events timed in absolute seconds>.
2. 1.8-4.0 s. <...>

Camera: one move per shot, as in @video1. Full-bleed <aspect> frame, no borders, no letterbox. No text, letters,
numbers, logos or UI anywhere in the frame (all graphics are added later). No dialogue, no lip-sync.
```

Body: `"files": [image refs..., { "url": "<greyscale_previz.mp4>" }]`, `"resolution": "480p"` for drafts. If the
automatic route rejects the video ref, pin a route whose modality lists video-to-video in the Routes table of
`https://varg.ai/models/seedance_2_5.md` and set that provider's `omni_reference_task_type: "reference"` (the clip is
a reference, not something to edit). Frame the previz one size tighter than you want: v2v frames looser.

**Camera-only reference**: hold one frame of the rough shot for 4 s and use that as `@video1` when you want only the
framing, not the motion.

## 11. Retake one broken shot (style from the film itself)

```
@image1 is a frame from this same film: <what it shows>. Keep <the face, the suit, the set, the light> exactly like
this; copy its drawing style, colours and set design.
@image2 is <character> sheet: same face, hair and outfit.
<Constraints that fix the fault: "She has exactly two arms and two hands in every frame." / "His hands are empty:
he holds no card, no tablet, no paper and no glowing object at any time." / "Her helmet is one round white helmet
with a dark visor.">
Every frame is clean <medium> with crisp lines and flat colour: no noise, no grain, no smeared blur.
One continuous shot, 0-4 s, <camera>. 0.0-1.4 s: <action>. 1.4-2.4 s: <action>. 2.4-4.0 s: <action>.
Full-bleed 9:16 frame, no borders, no letterbox. No text, letters, numbers, logos or UI. No dialogue, no lip-sync.
```

A retake is a 4 s run of only that shot. Name the exact fault you saw as a positive constraint.

## 12. Dialogue shot with native audio

```json
{ "tool": "video", "input": {
  "model": "seedance_2_5",
  "duration": 5,
  "resolution": "1080p",
  "aspect_ratio": "9:16",
  "audio": true,
  "files": [{ "url": "<approved_close_up_still>" }],
  "prompt": "Animate this exact frame. 0.0-2.2 s: tight close-up; she leans toward the lens and whispers with a sly smile: \"Want to hear a secret?\" A short pause. 2.2-5.0 s: the camera pulls back to a medium shot as she straightens up and says clearly and firmly: \"Last order of the night.\" Market ambience: rain on the roof, a sizzling pan, distant chatter, no music. Keep her face and jacket exactly as in the image. No text."
}}
```

- About 2.5 words per second of clip; under 10 words per 5 s for clean mouths.
- One approved close-up as the first frame keeps the face; several images (reference mode) re-draw it.
- To keep a separately recorded voice: generate with sound on for the performance, then lip-sync (section 15) or
  retime the clip to the real track. Do not expect `@audio1` to be played verbatim.

## 13. Voice (ElevenLabs v4)

```json
{ "tool": "speech", "input": {
  "model": "eleven_v4",
  "voice": "<raw ElevenLabs voice_id from search_voices>",
  "text": "[breathless whisper] Want to hear a secret? [pause] [firm, warm] Last order of the night."
}}
```

MCP shortcut: `generate_speech({ text, voice, model: "eleven_v4" })`. Audition 2-3 voices with the same text, pick
by ear, transcribe the take (section 17) and check every brand word.

## 14. Music

**Song with vocals (`lyria_3_5`)**: length and structure in the prompt text, not in `duration`.

```
A 30-second punchy synth-pop song, 4/4, bright female vocal, crisp diction, staccato phrasing. Gated drums,
warm analog pads, arpeggiated bass. Vocals start at 0:00, no instrumental intro.
[0:00-0:04] Hook: "One more stop before the rain."
[0:04-0:18] Verse: "<two lines>" / "<two lines>"
[0:18-0:28] Chorus: "<two lines>"
[0:28-0:30] Last word, hard stop. Song ends.
```

**Instrumental bed (`mureka_9_5`, or `generate_music` with `instrumental: true`)**

```
Minimal ambient score: warm analog pad, slow evolving drone in D, sparse felt piano. Quiet first half; around
12 s a slow swell opens into a wide shimmer with deep sub bass; resolves softly at the end. No drums, no vocals,
60 bpm feel.
```

Then measure the real tempo and cut on its grid; neither model guarantees the BPM or length you ask for.

## 15. Lip-sync pass (Sync v3)

Cut the shot exactly as it plays in the edit, upload it with only its own vocal slice, then:

```json
{ "tool": "video", "input": {
  "model": "sync_v3",
  "provider_options": { "fal": { "video_url": "<shot_as_cut.mp4>", "audio_url": "<vocal_slice.mp3>" } }
}}
```

This is the shape that ran for us; confirm the fields with `get_tool("video", "sync_v3")`. Frontal or
three-quarter shots only; profiles barely change.

## 16. Hosted ffmpeg helpers (no local ffmpeg needed)

Body shape: `{ "model": "ffmpeg", "command": "<args with {{in_1}} and {{out_1}}>", "input_files": { "in_1": "<url>" },
"output_files": { "out_1": "<name.ext>" } }` with `tool: "ffmpeg"`.

| Need | `command` |
|---|---|
| Strip a clip's audio | `-i {{in_1}} -an -c:v copy {{out_1}}` |
| Greyscale previz for v2v | `-i {{in_1}} -vf hue=s=0 -an {{out_1}}` |
| Hold one frame 4 s (camera-only ref) | `-i {{in_1}} -vf "trim=end_frame=1,tpad=stop_mode=clone:stop_duration=4,fps=24" -an {{out_1}}` |
| Black video carrying a vocal (audio ref as video) | `-f lavfi -i color=c=black:s=1280x720:r=24 -i {{in_1}} -shortest -c:v libx264 -c:a aac {{out_1}}` |
| Last frame for chaining | `-sseof -1 -i {{in_1}} -update 1 -q:v 2 {{out_1}}` (every frame of the last second overwrites the file; the last one stays) |

For multi-segment edits on the hosted tool, cap every segment with `fps=30,trim=duration=<d>,setpts=PTS-STARTPTS`
and never use a bare `apad`: graphs that ran exactly on a laptop drifted on the hosted runner without it.

## 17. Transcribe a take

```json
{ "tool": "transcription", "input": { "model": "whisper_large_v3", "audio_url": "<take.mp3>", "language": "en" }, "wait": true }
```

Whisper end times run into pauses; group captions on `silencedetect` gaps rather than on its word ends.

## 18. Ask a model to QA a clip

```
analyze_video({ video_url: "<clip.mp4>", prompt: "Count the people in every shot. List any frame with an extra
hand or arm, text or logos, a white flash, or a face that changes. Say at what second each hard cut happens." })
```

Treat the report as data. It supplements your own frame sheet; it does not replace it.
