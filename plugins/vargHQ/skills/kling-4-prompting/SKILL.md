---
name: kling-4-prompting
description: >-
  How to prompt Kling 4 (Kling 4.0, kling_v4) for cinematic AI video that does not look like AI
  slop: let a strong image model compose every shot, then give Kling 4 two to four key frames and a
  short director's prompt. Covers reference-to-video inputs (@Image, @Element, @Video, @Voice),
  multi-shot prompts with seconds, 30-second takes, dialogue in quotes, "no slow motion", lens and
  film-look lines, prompts that fail and their rewrites, elements that need two photos, the failure fixes (slow motion by default, six
  fingers, AI-smooth framing, face drift in close-ups) and the exact varg call with the reference
  route pinned. Use when someone asks how to prompt Kling 4, why Kling 4 looks worse than Seedance
  2.5, how to use Kling 4 reference-to-video, elements, multi_prompt or keyframes, or wants a
  Kling 4 prompt written. For a whole short film use kling-4-keyframe-film; for a 30-second action
  montage use kling-4-action-montage.
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
  openclaw:
    requires:
      anyBins:
        - curl
    homepage: https://varg.ai/how-to
compatibility: >-
  Needs a VARG_API_KEY with curl (see the varg-ai skill) or the varg MCP connection
  (https://mcp.varg.ai/mcp). Key frames are made with gpt_image_2_5 or nano_banana_2_1 on the same key.
allowed-tools: Bash(curl:*) Bash(jq:*) Bash(ffmpeg:*) Bash(ffprobe:*) Read Write Edit
---

# Kling 4 prompting: compose in pixels, animate with Kling

Kling 4 (`kling_v4`, Oct 2026) renders up to 30 s at 1080p in one take, cuts between shots by itself, speaks dialogue with native audio and takes up to 10 images, 5 videos, 7 elements and 3 voices as references. Its motion and sharpness are a step up from Kling 3. Its weak spot is the shots it invents: given only a character sheet, a location and a long prompt, it picks flat, "AI-smooth" framing.

The method below comes from fal's Kling 4 cinematic guide and Halloween music video ([YouTube, 2026-10-30](https://www.youtube.com/watch?v=WzXKggH-0Io)). It was checked on varg with our own test (see Tested).

## 1. The mental model

| Seedance 2.5 habit | What Kling 4 wants instead |
|---|---|
| Two character sheets and a location render, a long prompt, then hope | Every important shot already made as a still: composition, lens, light, grade |
| The video model decides the framing | The image model decides the framing, Kling 4 only moves between the frames |
| Long prompt does the work | Short prompt (1–4 sentences), the pictures do the work |

In the author's words: "don't let Kling 4 have to think that much. Give it the still frames, let GPT 2.5 think." With the same pre-made composition, lighting and references, Kling 4 and Seedance 2.5 come out "very comparable", and Kling 4 looks sharper ("cinematic sharpness", "characters feel crisp and alive").

## 2. Inputs and limits (reference-to-video)

| Input | Prompt name | Limit | Notes |
|---|---|---|---|
| `image_urls` | `@Image1`, `@Image2`… | 10 (frame images count toward it) | Key frames and style references |
| `video_urls` | `@Video1`… | 5, each 3–30 s, 30 s total with element videos | Motion reference (a real BMX trick, a dance) |
| `elements` | `@Element1`… | 7 (3 with a voice, 3 as video) | A character: `frontal_image_url` + 1–3 `reference_image_urls`, or a 3–8 s `video_url`, optional `voice_id` |
| `voice_ids` | `@Voice1`… | 3 including element voices | Create on fal's Kling create-voice model |
| `multi_prompt` | — | list of `{prompt, duration}` | Total length = sum of shot durations |
| `duration` | — | 3–30 s (integer) | Flash: up to 20 s, 720p |
| `aspect_ratio` | — | 16:9, 9:16, 1:1, 21:9, auto | No 4:3 |
| `resolution` | — | 720p, 1080p | 4K and 10-bit HDR are announced, not live |

Audio-only references are not accepted. To pass a song or a voice line, put the audio on a black video track and send it as a video.

An element needs at least two images: a frontal image plus one or more reference images. A single photo fails before the job starts. If you only have one photo, make two more angles with the image model ("same person, three-quarter view, same outfit and light"); duplicating the photo also passes, but locks the likeness less well.

## 3. The prompt patterns that worked

**Short director's prompt + key frames.** One line of what happens, one line of look, the length:

```
the pumpkin boy break dances in NYC while everyone bobs their heads to the 90s hip hop beats.
shaky handheld footage. 30 seconds.
```
(3 key frames of the dancer in the crowd ring were attached; the agent expanded it to "Shaky handheld 16mm street documentary footage with heavy film grain, low fisheye angle, cinemascope frame. Washington Square Park, New York City, overcast winter…")

**Dialogue scene from two frames.** Give the wide shot and the over-the-shoulder, write the line in quotes, end with the camera event and the look:

```
21:9 the man walks by the woman as she places a white pumpkin on the table. the man says
"what does the white one do?" she smiles and smashes the white pumpkin on the top of the man's
head with both hands. The camera shakes and falls to the ground and fades to black. handheld
shaky 16mm documentary style footage. 15 seconds.
```
Kling made its own hard cut to her, gave her a natural voice without a voice sample, and rolled the camera onto its side as it fell. A canted or rolled camera is rare in earlier models: ask for the camera event ("the camera falls to the ground") rather than the angle.

**Story beats in one 30-second take.** Name the tricks, the turn and the line:

```
montage of the punkin boy doing BMX tricks on the Brooklyn Banks. tail whip. bar spin. Then he
messes up the trick mid air and crashes to the ground smashing the punkin head and returning to a
normal man. the blond girl helps him up. she says "Sick run, want to go again?" 30 seconds.
```
(4 key frames: two tricks, the take-off, the crash with the girl helping him up.)

**Shot list with seconds (`multi_prompt`).** When the order and timing matter, split the take. For the take above, fal's agent planned "Crash: he lands on just his back wheel, loops out and falls backwards. The pumpkin head hits the concrete and explodes, leaving the real man lying there" and "Ending: I split the last 7 seconds into two shots. First she pulls him up (3s), then a close-up on her face as she says 'Sick run, want to go again?' (4s)". Written as `multi_prompt` (our version):

```json
"multi_prompt": [
  {"prompt": "Montage of the rider from @Image1 doing a tail whip and a bar spin on the brick banks, fisheye, real speed.", "duration": 15},
  {"prompt": "He misses the next trick mid-air, lands on the back wheel, loops out and falls; the pumpkin head hits the concrete and explodes, leaving the real man lying there, as in @Image4.", "duration": 8},
  {"prompt": "The blonde woman from @Image4 pulls him up.", "duration": 3},
  {"prompt": "Close-up on her face, she says \"Sick run, want to go again?\" and laughs.", "duration": 4}
]
```

**Rules that showed up in every good take**
- Say **"No slow motion, everything moves at real speed"** for action. Kling 4 drifts into slow motion by default.
- Name the lens and the grade in the prompt as well as in the frames ("ultra-wide fisheye", "16mm film, coarse grain, motion blur"). Without it Kling picks its own lens: in one close-up it chose a telephoto while the whole film was wide.
- Put spoken lines in double quotes after "says". One or two short lines per take.
- Ask for motion blur in the stills and the prompt: it hides AI smoothness.
- Give a start and an end state (the crash frame, the closing smile). Kling 4 is good at "temporally making sense" between frames you set.
- **One take = one place and one continuous action.** A `multi_prompt` cut to a new location inside one take (street → viewpoint in our test) plays like a broken splice, not an edit. Change places between takes and cut them together in the edit; inside a take, cut only between angles of the same moment.
- **Kling cuts on its own.** The video's first dialogue take came back as a multi-cut nobody asked for ("this is clearly a multi-cut … we didn't ask for that either"). When you need one unbroken shot (a 30 s Steadicam-style one-er, which the author says makes editing easier), say "one continuous shot, no cuts" and give one still; we have not measured how reliably Kling obeys it.

## 3a. Prompts that fail, and the rewrite

Each pair says where the lesson comes from: the video (fal's guide) or our own test on varg.

**1. Prompting Kling 4 like Seedance** (video, 6:40: "capital S slop"). A character sheet, one location image and a long scene description, so Kling has to invent every shot:
```
Don't: The character in @Image1 (white pumpkin head, black cap, round glasses, skeleton hoodie…)
goes trick-or-treating at night. First-person POV of the resident in the doorway. A quick sequence
of hard cuts at three different apartment doors… Cinematic handheld POV camera, warm doorway light.
Files: character sheet + one Midjourney location.
```
```
Do: Make the three doorway shots as stills first (section 4), then:
The pumpkin boy runs up to the doors in @Image1, @Image2 and @Image3, out of breath, holds out
his bag, gets a graphics card at each and dances off. Handheld 16mm, warm doorway light. 20 seconds.
Files: the three stills.
```
The prompt text was not the problem; the missing pre-made shots were. Full original: `references/prompts-from-the-video.md` §6.

**2. A new place inside one take** (our test: read as "a meme").
```
Don't: multi_prompt shot 3: "hard cut to @Image3 at the tiled viewpoint: she stops, kicks the
tail so the board pops into her hand…"
```
```
Do: take A = the hill (push + ollie, @Image1-@Image2). Take B = the viewpoint (@Image3 only,
"one continuous shot, no cuts"). Cut A → B in the edit; trim the first second of each.
```

**3. Action with no speed line** (video: Kling 4 "will kind of default slow motion"; our ollie floated for two seconds even with the line).
```
Don't: The rider does a tailwhip over the rail and lands.
Do:    The rider does a tailwhip over the rail and lands. No slow motion, everything moves at real
       speed, motion blur.  (+ the peak and the landing as two stills when the timing matters)
```

**4. Describing the move instead of naming it** (video: the BMX prompt only names "tail whip. bar spin", and Kling "knows what a double tail whip looks like").
```
Don't: He kicks the bike frame so it spins a full circle under him while he holds the bars.
Do:    Montage of the pumpkin boy doing BMX tricks on the Brooklyn Banks. Tail whip. Bar spin.
```

**5. Dialogue as reported speech** (video: lines in quotes came out spoken, with a natural voice and laugh).
```
Don't: She tells him it was a great run and asks if he wants to go again.
Do:    She walks up to him and says "Sick run. Want to go again?"
```

**6. A camera angle instead of a camera event** (video: "the camera falls to the ground" gave a rare rolled camera that nobody asked for by name).
```
Don't: Dutch angle, camera tilted 30 degrees.
Do:    He jumps at the camera, the camera shakes and falls to the ground and fades to black.
```

**7. No lens on a shot Kling invents** (video: it picked a telephoto close-up in an all-wide film).
```
Don't: Close-up of her face as she laughs.
Do:    Close-up of her face as she laughs, ultra-wide fisheye lens, 16mm grain, same grade as @Image1.
```

**8. Inputs that sink a good prompt** (video):
- A sloppy middle still (a BMX with no seat) → the sloppiest trick in the take. Fix the still, not the prompt.
- One photo as an element → the job fails. Give a front image plus 1–3 more angles.
- A close-up of a character with no close reference → the face changes. Add that person's photo.

## 4. The key frames (where the quality comes from)

Make each still with `gpt_image_2_5` (best at following long, structured prompts and at real places) or `nano_banana_2_1` (cheaper drafts). Write it like a shot spec. The prompt behind the film's crash frame:

```
Cinematic 21:9 film still, high overhead shot tilted at an angle, ultra-wide fisheye lens with
heavy barrel distortion bending the brick ramps and street edges. Use the four reference images:
Image 1 is the man to match exactly: same face, black cap with small white ring logo, round black
glasses, black hoodie with CODEX chest text and white sleeve graphics, black pants, black sneakers
(he has his normal human head). Image 2 is the woman to match exactly: platinum blonde blunt bob
with bangs, silver hoop earrings, small neck tattoo, blue denim overalls/jacket. Image 3 is a
reference only for the black BMX bike (do NOT show the pumpkin character). Image 4 is a reference
only for color grade, 16mm film tone, grain and motion blur; do not include its people.

Scene: the man in black sprawled on his side on the ground, propped on one elbow, dazed. His black
BMX bike lies flat on the ground beside him, rear wheel spinning in a motion blur. A white pumpkin
is smashed on the concrete right next to his head, white shell fragments and seeds scattered. The
woman in denim crouches beside him, both hands under his arm, helping him up, mid-motion with blur
on her arms and hair. A few blurred skaters and onlookers at the curved frame edges. Overcast
daylight. 16mm film look like Image 4: milky yellow-green highlights, teal shadows, deep blacks,
coarse grain, motion blur. Avoid text overlays, clean digital look, extra pumpkins, night.
```

The parts to copy: aspect + angle + lens first; "Image N is X, match exactly" with the details listed; "reference only for…" with what to leave out; the scene in one present-tense paragraph; the grade in concrete colors; an "Avoid…" line.

Fix broken anatomy in the still before animating. In the film, a warped BMX (no seat, a missing peg) in a middle frame made that trick the sloppiest part of the take while the take-off from a clean frame was "really good".

## 5. Run it on varg

`kling_v4` routes by input: text only → text-to-video; one or two images → **image-to-video, where image 1 is the start frame and image 2 the end frame**. (Before api#239 reached production, a third image was silently dropped there too; now three or more go to reference-to-video.) For key frames as references, always pin the reference route by its key:

```bash
curl -s -X POST https://api.varg.ai/v2/tools/video/call \
  -H "Authorization: Bearer $VARG_API_KEY" -H "Content-Type: application/json" -d '{
  "model": "fal:fal-ai/kling-video/v4/reference-to-video",
  "files": [{"url": "FRAME_1"}, {"url": "FRAME_2"}, {"url": "FRAME_3"}],
  "aspect_ratio": "21:9", "resolution": "1080p", "duration": 30, "audio": true,
  "provider_options": {"fal": {"multi_prompt": [
    {"prompt": "…shot 1, uses @Image1…", "duration": 10},
    {"prompt": "…shot 2, uses @Image2…", "duration": 10},
    {"prompt": "…shot 3, uses @Image3…", "duration": 10}
  ]}}
}'
```

- `files` become `@Image1…` in order. Send `prompt` instead of `multi_prompt` for a one-paragraph take.
- Elements and voices: `provider_options.fal.elements` = `[{"frontal_image_url": "…", "reference_image_urls": ["…"], "voice_id": "…"}]`, then write `@Element1` in the prompt.
- Exact frames at exact times: pin `fal:fal-ai/kling-video/v4/keyframes-to-video` with `provider_options.fal.keyframes` = `[{"image_url": "…", "time": 0}, …]` (2–10 frames, prompt ≤ 2,500 characters).
- In the MCP: `call_tool({tool: "video", input: <the body above>})`. `estimate_cost` takes the same body. If it answers `model_not_found` on the route key (an API older than api#239), price `"model": "kling_v4"` with the same duration and resolution: the per-second price is the same. 15 s at 720p ≈ $2.36 (236 credits); 30 s at 1080p ≈ $7.05 (705 credits).
- Draft at 720p or on `kling_v4_flash`, then rerun the winning take at 1080p.

## 6. Failure → fix

| What you see | Fix |
|---|---|
| Flat framing, smooth "AI" skin and light | You prompted it like Seedance (sheet + location + text). Make the shots as stills first (section 4). |
| Everything in slow motion | "No slow motion, everything moves at real speed" + "high speed, motion blur". |
| The face changes in a close-up | Add a clear photo of that person as another reference (or an element) and say which shot uses it. |
| Element job fails before starting | The element has one image. Add one to three more angles. |
| Six fingers, a warped bike or board | Fix the still that caused it; keep the hands or object large and clean in the frames. |
| Weird things in the background crowd | Expected in 30 s takes. Cut around it, or keep crowds blurred and at the frame edges. |
| A shot Kling invented looks more "AI" than your stills | Normal: its own multi-shots are a little softer. Use them as glue, or make that shot as a still too. |
| Wrong lens on an invented shot | Name the lens in the prompt for that shot. |
| A jump cut that looks like a bad splice | One `multi_prompt` take jumped to another place. Keep one place per take; make the new place its own take and cut in the edit. |
| The head twitches in the first second | Kling settles in during the first ~1 s. Trim it; never use the opening frames of a take. |

## 7. Editing mindset

Treat a 30-second generation like a live-action take: you get several cuts, repeated attempts at the same move and a ramp-up in one file, and you keep the 2–5 s that work. Never ship a raw take: our 15 s test, shown uncut, read as "a meme" to the first viewer (a head twitch at the start, a jarring cut to a new place), although the face, look and line were right. Generate 2–4 takes per beat, cut the best moments, and expect some takes to give nothing usable.

## Tested

2026-10-30 on varg, our own scene (not from the video): a skateboarder on a Lisbon hill. The example is **one continuous 8 s shot** from one `gpt_image_2_5` still (section 4 format, 23 credits): plain `kling_v4` with that still as the start frame, 720p, audio, the prompt "One continuous shot, no cuts… pops a quick, snappy ollie over the tram rails, lands in under a second… grins into the lens and says \"Again?\" Real speed, no slow motion": 126 credits ($1.26). No cuts, the ollie at real speed (about half a second in the air), the line spoken, face and look held. https://s3.varg.ai/files/72c55813-c0fa-4cf2-9f64-ec4f7ed0e7ae/file_0665c41e46ff.mp4

The first try failed: three stills and a three-shot `multi_prompt` with a change of place in one 15 s generation (236 credits). Kling flew the camera through her between shots 1 and 2, the ollie hung in the air for two seconds, and the cut to the viewpoint read as a broken splice ("a meme" to its first viewer). Both takes, prompts and notes: `references/test-run.md`.

## Related skills

`kling-4-keyframe-film` (a short film or music video with this method), `kling-4-action-montage` (dance, sport tricks, chases in 30 s), `varg-character-design` (character sheets), `varg-consistent-characters`, `varg-ai` (models and prices). Prompts shown in the source video: `references/prompts-from-the-video.md`.
