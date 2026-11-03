---
name: varg-video-prompting
description: >-
  How to prompt varg's video, image, voice and music models so shots come out right on the first or
  second take: the working loop (look bible, environment master, character sheets, approved stills,
  animate, QA), which model for which shot (Seedance 2.5, Kling 4, Veo 3.1, Wan 3, Nano Banana 2.1,
  GPT Image 2.5, ElevenLabs v4, Lyria, lip sync), prompt anatomy for video, stills and edits, what
  @image1, @video1 and @audio1 references copy, dialogue and voice rules, a frame and audio QA
  checklist, and gotchas from paid runs. Use when someone asks to "prompt Seedance", write a Kling or
  Veo prompt, pick a "varg video model" or asks "which model", does "image to video" or "video to
  video", needs a "consistent character" or location, makes "storyboard stills" or key frames, wants
  dialogue or lip sync, or asks why a clip looks like AI slop, drifted or ignored the prompt.
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
  openclaw:
    requires:
      anyBins:
        - curl
        - ffmpeg
    homepage: https://varg.ai
compatibility: >-
  Needs the varg MCP connection (https://mcp.varg.ai/mcp, OAuth sign-in) or a VARG_API_KEY for
  https://api.varg.ai/v2 (see the varg-ai skill). QA uses ffmpeg and ffprobe locally when
  available; otherwise the MCP analyze_video tool and the hosted ffmpeg tool.
allowed-tools: Bash(curl:*) Bash(ffmpeg:*) Bash(ffprobe:*) Bash(jq:*) Read Write Edit
---

# varg video prompting

This skill is what a team that makes video on varg every day learned the expensive way: which model to use for
which shot, how to write the prompt, what each reference actually copies, and how to check the result before
anyone sees it. It extends the basics in `varg-ai` (`references/prompting.md` has the shot, lens and light
vocabulary); it does not repeat them.

Calling the tools (sign-in, `call_tool`, jobs, uploads): [references/mcp-tools.md](references/mcp-tools.md).
Copy-paste prompts: [references/prompt-templates.md](references/prompt-templates.md). Per-model quirks:
[references/models.md](references/models.md). Real runs and what they taught: [references/examples.md](references/examples.md).

## 0. Five rules before any prompt

1. **Fix stills, not clips.** A 5 s Seedance 2.5 clip at 720p costs about as much as 25-35 Nano Banana stills.
   The video model keeps every fault of its first frame or reference. Approve stills, then animate.
2. **Every recurring thing gets a frozen text and a frozen image.** Character, place, prop and look each get one
   paragraph pasted word for word into every prompt, plus one approved image passed as a reference.
3. **The model draws what you name.** Similes become objects, "keep the top calm" becomes a dark band, "TV static"
   becomes grey mush, a prop in a reference shows up in the shot. Write only what should be visible.
4. **Text, logos, UI and numbers are never generated.** End every image and video prompt with a no-text line and
   draw all type in code afterwards (HyperFrames or the title and caption skills).
5. **Price first, one pilot, then the batch.** `estimate_cost` on one real request, run one clip of each kind,
   show it, wait for a go. Quote credits only, never money.

## 1. The working loop

Every step ends at a gate where the person looks at something cheap before anything expensive is made.

| Step | Make | Gate | Spend |
|---|---|---|---|
| 1. Brief | `brief.md`: format, length, platform, the one line to remember, references, budget ceiling in credits, the person's own words verbatim with dates | person confirms | 0 |
| 2. Look bible | one **look line** (medium, palette, lens, light quality, grain), one **identity paragraph** per character, one **place paragraph** per location, a banned list | person confirms the words | 0 |
| 3. Environment master | one wide establishing still per location, no hero action, layout written as numbered elements. If several cameras share a set and geometry matters, a 3D blockout render first (`threejs-animatic`, `varg-previz`) | person approves the plate | a few stills |
| 4. Character sheets | front, 3/4, profile, back + a large face crop on flat grey, no text; product or vehicle sheets with a person for scale (`varg-character-design`) | person approves | a few stills |
| 5. Approved stills | one still per beat from master + sheets, on a numbered board (`varg-mockups`); fix faults here with surgical edits | every still OK at full size | ~6-16 credits each |
| 6. Animate | one pilot per shot kind, then the batch; image-to-video from the approved still, or reference / video-to-video runs per location | pilot approved, batch quoted | the main cost |
| 7. QA | frame sheet + audio check per clip, against its still | every clip passes or is re-rolled | 0 (local) or ~6 per `analyze_video` |
| 8. Edit | cut, retime, lip-sync pass, text and graphics in code, loudness | person says ship it | lip-sync ~100 per shot |

Group shots by location: all coverage of one place comes from the same master and sheets, ideally one multi-shot
generation with hard cuts, cut back into the timeline afterwards. A retake of one broken shot is a short run of just
that shot, not the whole scene.

## 2. Which model for which shot

Credits are the public catalog's typical prices (`varg-ai` → `references/models.md`, October 2026); always confirm
with `estimate_cost`. Live list: `list_models` or `https://varg.ai/models/llms.txt`.

| Task | Model | Why | Credits / time |
|---|---|---|---|
| Hero shot with people; several shots of one place in one take; video-to-video from a previz | `seedance_2_5` | best faces and physical performance; ≤9 image, ≤3 video, ≤3 audio refs; 4-30 s; obeys timed hard cuts | ~210 per 5 s 720p, ~480 at 1080p; 480p drafts billed ~16/s in our runs; 3-5 min |
| Animate an approved still faithfully; start-frame to end-frame moves; long calm single moves | `kling_v4` | stays closest to the still (keeps everything in it, unwanted logos too); two files = start and end frame; native ambient audio | ~82 per 5 s 720p, ~123 at 1080p; 5-8 min per batch |
| Cheap motion test before paying for the hero model | `minimax_h3_max_turbo`, `kling_v4_flash`, or the hero model at 480p | same prompt, lower price; upgrade the winner | ~42 per 5 s |
| Best value text-to-video, lots of B-roll | `wan_3` | top text-to-video rank, 2-30 s, refs; audio only through its provider option | ~53 per 5 s 720p |
| Short shots that fit 4, 6 or 8 s, 16:9 or 9:16 only | `veo_3_1` (`_fast`, `_lite`) | strong image-to-video, first/last frame | ~105 silent, ~210 with audio per 5 s |
| Fastest top-tier clip, quick video edit | `omni_flash_1_1` | ~30 s generation, 3-10 s | ~53 |
| Many short clips for a fast-cut visualizer | `seedance_2_mini` | cheapest Seedance, 720p, 4-15 s, strict moderation | ~74 per 5 s |
| Sheets, masters, scene stills, most edits | `nano_banana_2_1` | ≤10 refs, holds identity, generates and edits | ~6 (1K), ~8 (2K), ~16 (4K) |
| Stills that must follow exact instructions or a blockout's geometry; dense text designs | `gpt_image_2_5` | #1 for text-to-image and edits; follows "mapping" instructions | several times a Nano Banana still, depends on quality tier: estimate |
| Extend a still to a new aspect ratio, keeping its pixels | `bria_fibo_edit_1_5_expand` | outpaint without redrawing the subject | estimate |
| Voice-over and character lines | `eleven_v4` (`eleven_v4_turbo` for drafts) | audio tags such as `[whispers]`, 90+ languages | ~84 / ~42 per line |
| Song with vocals | `lyria_3_5` | full songs, timestamped structure in the prompt | ~11 |
| Instrumental bed | `mureka_9_5` | instrumental only | ~25 |
| Lip-sync onto a generated clip | `sync_v3` (`sync_v2_pro`) | redraws only the mouth against the real voice | ~105 per short shot |
| Talking head from one still + audio | `veed_fabric_1_0`; long talks `minimax_h3_max_lipsync` | simplest path; lively but restrained on shouts | ~160-470; ~10-20 per s |
| Watch a clip and report what is in it | `analyze_video` (MCP) | timeline, transcript, on-screen text | ~6, same URL again is free |

Rules of thumb: Seedance for performance and multi-shot scenes, Kling 4 to move a frame you already love, a cheap
model to test motion, 480p or 720p for drafts, 1080p only for faces that stay on screen. More in
[references/models.md](references/models.md); for Kling-specific prompting use `kling-4-prompting`.

## 3. Prompt anatomy: video

Long, structured prompts (up to a few hundred words) worked on Seedance 2.5 when every sentence was a fact about the
frame. Kling 4 did best with a short director's prompt over strong key frames (`kling-4-prompting`). Write the blocks
in this order (full template in [references/prompt-templates.md](references/prompt-templates.md)):

1. **Reference roles**, one line each: `@image1 is the woman's character sheet: same face, short copper hair,
   green rain jacket.` For a previz or rough clip: `@video1 is a black-and-white grey-box previz. Copy from @video1
   ONLY the camera, the hard-cut timing and the blocking. Do not copy its look; the result must not look like @video1.`
2. **Winner rule** when refs disagree: `Where @image1 and @image2 differ in pose, light or setting, @image1 wins;
   @image2 only defines the person.`
3. **Counts and anatomy**: `Only one person in the room; every visible hand and sleeve belongs to her.`
   `She has exactly two arms.` `Her hands are empty: no phone, no card, no glowing object at any time.`
4. **Light of this run**: weather, time, practical lights. Never put light in the shared look line.
5. **Look line**, verbatim from the bible.
6. **Timed beats**: `3 shots, hard cuts:` then `1. 0.0-1.8 s. Medium close-up from the left: she ...`. Times are
   absolute from the clip start. One action per shot, a time for every event inside it (`at 0.9 s the door slams`).
7. **Camera**: one move per shot (push in, arc, crane). Never blend two moves in one shot.
8. **Sound**: either `No dialogue, no lip-sync.` plus the ambience you want, or the spoken line in quotes with its
   delivery (section 7).
9. **Frame**: `Full-bleed 9:16 frame, no borders, no letterbox.`
10. **Text ban**: `No text, letters, numbers, logos or UI anywhere in the frame.`

**Image-to-video from one approved still** (any model) is shorter, and describes only motion:

```
Animate this exact frame. Locked-off camera, no zoom. After a short beat <one action>; <secondary motion: wind in
the grass, haze in the light beams>. Keep <the face, the prop, the composition> exactly as in the image.
No cuts, no new objects, no text.
```

Timing that works: 4-11 s per run (short runs obey better and retake cheaply); a 30 s take is four beats with six
facts each (what, doing, where, camera, style, rules); spoken lines at about 2.5 words per second; generate a clip
to start one beat before its cut so a late take still covers it.

## 4. Prompt anatomy: stills

```
@Image1 is <character> sheet: match face, hair and outfit exactly.
@Image2 is the master shot of <place>: same camera direction, same <place>.
<Place paragraph, with the props that must not change spelled out by count and position.>
Create one new single image, <shot size + angle> of the same scene: <pose, expression, action>.
Exactly <N> people; <anatomy constraints>.
Full-bleed image filling the entire frame edge to edge, no borders, no letterbox.
<Look line>. No text, letters or logos.
```

- **Expressions go into the still.** Video models move what is there; they are bad at inventing a new face or
  fixing crossed eyes in motion.
- **Spell out every garment to the feet.** "Black high-neck bodysuit" became a leotard with bare legs; "long-sleeve
  flight suit with full-length trousers, black knee-high boots" fixed it.
- **Distinctive faces.** "Rugged, bald, stubble" men came out as recognisable actors; a stock "wise old man" (long
  silver hair, white beard, smooth skin) read as AI slop. Give an age as a number, one or two irregular features,
  real skin (pores, fine lines, slight redness), a film stock or camera, and check every face before animating.
- **Name the orientation in frame terms** for anything lying, leaning or crossing: "vertical in the frame,
  perpendicular to the road", not "lying on the road".
- Close-ups of a place always carry its master as a reference, never a fresh description.

## 5. Prompt anatomy: edits

The edit prompt says what stays, then the single change:

- **Change one thing**: `Keep the FIRST image pixel-identical in every respect: camera, <list>. Add only one thing:
  <the change>.`
- **Recast inside a finished still**: `Keep this exact image: same room, camera, light, pose, clothes. Replace ONLY
  the man with <identity paragraph>.` If the composition shifts, narrow it: `Edit the first image only by swapping
  the person's head and face. Do NOT change the camera, framing, crop, symmetry, pose or clothes.`
- **Blockout to finished still** (geometry held where an environment picture alone drifted): the blockout render is
  the FIRST file, then `Keep EXACTLY its camera position, lens, framing and perspective, and the position, size and
  orientation of every object. Do not add, remove or move any object. Mapping: grey blocks = <...>; the tall grey
  mannequin = the woman from the SECOND image; ...`. Give blockout people a head, arms and feet, or they come back
  as logs or rope bundles.
- **An action on a small unique prop is the hardest still.** "His fist slams the one orange button" failed three
  times in a row (a second orange button twice, a third hand once), even with the master as the first image and the
  fist asked to cover the button. After two failures stop paying: reframe so the action does not need the prop (an
  insert close-up, a cut-away), keep the best take, or fix it with a local crop-and-redraw edit.
- **Invented logos** on clothes and props: a separate pass, `Remove only the logos and brand marks; change nothing
  else.`
- **Outpainting** to a new aspect can clone people at the edges: `Only these two people, nobody else.`
- **A near-miss clip**: fix the still, then re-run from it, or edit the footage (video edit models in
  `varg-video-editing`). Do not regenerate the sheet to fix motion.

## 6. References: roles, counts and what copies over

- **One image = the first frame. Several images = references.** Reference mode re-draws the person: with a distant
  portrait (face about 280 px wide) the face came back soft and drifting. Give it a large, sharp face crop as its own
  ref, or, when the face must be exact, pass one approved close-up as the first frame and put the camera move in the
  prompt.
- **Number by media type, in `files` order**: the first image is `@image1`, the first video `@video1`, the first audio
  `@audio1`. Give each a role line that also says what it must not touch.
- **Stay within 1-8 images and 1-3 video or audio refs**, and pass only refs of what is in frame: a sheet that also
  shows a second character pulls that character into the shot; an exterior plate in an interior shot drags the
  exterior in. Crop modular sheets; pad crops to at least 300 px on the short side (a narrower crop was rejected).
- **A frame from the same film is the best style ref.** For a retake, grab a frame from an approved clip and add
  `@image2 is a frame from this same film: copy its drawing style, colours and set design.` This fixed a segment
  the reviewer called AI slop.
- **What video-to-video from a previz copies** (Seedance 2.5, 4 s, 480p):

| From `@video1` | Result |
|---|---|
| hard-cut timing | kept exactly |
| camera move (arc, push) | kept |
| blocking and action | kept |
| shot size | looser: a close-up came out as a medium shot, so frame one size tighter in the previz |
| the grey-box look | **copied** when no image refs were given (a mannequin became a toy-like person) |
| everything, once | a run came back as the previz itself, re-encoded; fixed by sending the ref in greyscale and saying "redraw every frame in full colour; the result must not look like @video1" |

  So every v2v run needs an image ref for every character and product in frame. A prop or pose in the reference
  clip gets copied too: remove it from the reference instead of forbidding it in words.
- **Audio refs are re-performed, not played.** Seedance re-voices a supplied line in a similar voice with its own
  timing (about 20% slower on a shout). Use `@audio1` to drive performance and timing, never as the final sound.
- Models refuse realistic real people as references; use consented actor photos or generated characters.

## 7. Dialogue, lip-sync and voices

- **Generate talking or singing shots with sound on.** Silent generations come back with barely moving mouths, and
  the lip-sync pass then has more to fix.
- **Line in the prompt**: `She leans in and whispers: "psst... wanna hear a secret?" A short pause. Then she shouts:
  "<line>"`, with delivery words (whispers, matter-of-factly, calling over wind). For no speech: `No dialogue, no
  lip-sync`, and name the ambience.
- **Keep the real voice** with one of two routes:
  1. Mute the clip, measure syllable onsets on both tracks (ffmpeg `astats` RMS at 10-20 ms), and retime the video
     piecewise (trim + `setpts` per segment) to the real audio. Body and lip timing then match well.
  2. Run `sync_v3` (or `sync_v2_pro`) on the shot exactly as it plays in the edit, with only that shot's own vocal
     slice. The output keeps the input length to the frame.
- **Choose lip-sync shots that can sync**: frontal or three-quarter faces, mouth clearly visible. In one pass of three
  shots, a three-quarter close-up whose teeth were shut the whole time came back opening on the vowels, while a
  profile close-up with clenched teeth barely changed and its credits were wasted.
- **For a big physical performance** (a shout, a sports-ad energy), Seedance gives far stronger body acting than an
  image-plus-audio talking-head model; do the body in Seedance, then lip-sync on top.
- **Voices**: pick with `search_voices` (by `intent` in words, or `filters`) and audition 2-3 takes yourself or with
  the person; choose by ear. If `eleven_v4` answers `voice_not_found` for a name or preset id, pass the raw ElevenLabs
  `voice_id`. Audio tags shape delivery: `[breathless whisper] ... [fierce shout] ...`, `[calm, slow, soft-spoken]`,
  `[pause]`. Transcribe each take (`whisper_large_v3`) and check brand words are pronounced cleanly.
- Keep one voice per character across the whole project, and freeze the approved take: reuse its file URL instead of
  regenerating, because a new take differs in length and breaks every retime and lip-sync built on the old one.

## 8. Music

- **The song is the clock.** Measure the beat grid on the real file and cut on downbeats (`varg-music-video`).
  Never trust the BPM you asked for. Same lyrics, same "112 BPM" prompt: ElevenLabs Music measured 112.3 BPM and
  50 s; Lyria came out near 97 BPM and 55 s, and the beat tracker first misread it as 129 (a triplet error) until a
  drum-stem check corrected it. Pick the song by ear, then measure it.
- **Lyria 3.5 ignores the `duration` field** (asked 20 s, got about 90 s) and exact rhythm instructions. Put the
  length and timestamped sections in the prompt text (`50-second ... [0:00-0:04] hook ... [0:46-0:50] outro. Song
  ends.`), add `Vocals from 0:00, no intro` if needed, then trim on the grid.
- Beds: genre, mood, instruments, tempo, energy arc in under ~40 words (`mureka_9_5`, or `instrumental: true` on
  `generate_music`). Describe the sound instead of naming people: ElevenLabs Music rejected a prompt that named a
  composer as copyrighted material.
- Never cut several separately generated sung clips into one song: each one sings a different melody.

## 9. QA checklist (every still and every clip)

Agents cannot watch video, but they can read frames and measure sound. Never ship a clip you have not checked.

**Stills**
1. Count people; exactly the people the shot names (an over-the-shoulder angle once drew a second pilot).
2. Every visible arm attaches to a body in frame and wears that character's sleeve.
3. Identity, outfit and age against the sheet; recurring props by count and position against the master.
4. Scale against the sheet (vehicle bigger than a person, product fits a hand).
5. No letterbox band, no drawn text or logos, no recognisable celebrity face.

**Clips**
1. Frame sheet: 8 frames across the clip in one image (`ffmpeg -i clip.mp4 -vf "fps=2,scale=320:-1,tile=4x2"
   -frames:v 1 sheet.jpg` for a 4 s clip; raise or lower `fps` with length), plus a frame at every intended cut.
   Compare with the approved still or the previz at the same times.
2. Pass-through check on v2v: does any frame look like the reference clip?
3. Extra or missing limbs, props that should not exist, faces drifting late in the clip (long clips drift more).
4. Where the cut or action really lands: models sometimes ignore "cut at 3.6 s". Write the measured in-points into
   the edit, not the requested ones.
5. Flash frames: scan `signalstats` YAVG for sudden spikes.
6. **Listen.** Check every clip's audio track even when you asked for none (see gotchas). `silencedetect` shows
   where speech sits; transcribe and diff against the script.
7. `ffprobe` duration and resolution match the request.

Artifacts up to about 6 frames can be cut out in the edit; anything longer, or anything the reviewer sees twice,
is a retake. Keep a jobs file (shot, job id, file URL, billed credits) the moment each job is submitted.

## 10. Gotchas (verified on paid runs)

**References and consistency**
- An environment image alone still drifted between cameras: a fork vanished, a person changed sides, gravel became
  asphalt. A 3D blockout render as the first file of a GPT Image edit held it.
- A shared look line that said "sunset outside" put sunset windows into an indoor shot. Look = style only.
- A recurring room rearranges itself unless its key props are written out in every prompt (count, colour, position).
- Kling 4 copies everything in the still, including a logo you did not want: clean the still first.
- Chaining from a drifted clip compounds the drift; re-anchor every shot on the original sheet and master.
- Once sheets are approved, never regenerate them to fix motion: change the motion prompt or the scene still.

**Prompt wording**
- In stylized looks, "TV static", "noise", "glitch" and "grain" were drawn as grey mush. Write "clean cel animation,
  crisp ink lines, flat colour, no noise, no static" and add those effects in post. Fine film grain on photoreal
  stills was harmless.
- "Keep the top fifth calm" (to leave room for text) drew a dark band. Say "full-bleed, no borders, no letterbox"
  and place text in the edit.
- "Do not copy its look" alone did not stop v2v copying a grey mannequin; only image refs did.
- Over-the-top effects ("hair explodes", "stadium lights blast on") looked cheap; restrained spray and rim light
  looked expensive.
- Image filters rejected "screaming", "about to be run over", "teeth bared, skin stretched"; the same moment phrased
  as tension or slapstick passed. Refused jobs are not charged; retry once, then rephrase, then change the still.
- Body-part slang in image prompts can stall a job for minutes; use neutral anatomy words and catalog phrasing
  (adult age as a number, each garment named).

**Video**
- Do not punch in digitally on generated footage: a 1.7x zoom on a 960 px clip turned to mush. Put the camera move in
  the prompt and generate at the resolution the frame needs.
- `audio: false` was not honoured on one Seedance route: the clip came back with a loud speech-like murmur. Also set
  the provider's own audio flag for the route that runs (listed on `https://varg.ai/models/seedance_2_5.md`), and
  strip audio in the edit (`-an`) for any clip that gets music or VO later.
- Seedance occasionally returns a pure white flash frame; scan before the edit.
- Estimates can be a ceiling far above the bill: Seedance 480p v2v was quoted at several times what it billed (about
  16 credits per second). Quote the estimate as the ceiling, report the billed cost with `get_job_cost`.
- In a parallel batch one Kling job sat "running" about 30 minutes while the rest took 6. After about 15 minutes
  submit a backup take and `cancel_job` the slow one. In our runs cancelled and failed jobs were not billed; confirm
  with `get_job_cost`.
- A provider outage shows up as every job on one route failing; try the same model id again later or a sibling
  model, and say so instead of retrying blind.
- The last frame for chaining: extract with `ffmpeg -sseof -1 -i clip.mp4 -update 1 last.png` (each frame of the
  last second overwrites the file, the last one stays); seeking to `duration - 0.04` can miss it because the
  container duration runs one frame past the last picture.

**Stills**
- GPT Image's default output (about 1088 px) showed artifacts on wide shots; ask for a larger size where the model
  schema allows (`get_tool("image", "gpt_image_2_5")`) and pick quality explicitly.
- With GPT Image, name references by content ("the woman in the face photo"); positional order is unreliable,
  except the blockout or master you call "the FIRST image".
- After any `provider_options` change, check the output's real pixel size and aspect: on a legacy Nano Banana
  route a resolution option made the requested aspect ratio be ignored.

**Audio and voices**
- A supplied voice is re-performed by Seedance, not played (section 6). Retime or lip-sync.
- Lip-sync on a profile or a shut mouth wastes credits (section 7).
- Music models do not respect exact durations or tempos (section 8).

**Operations**
- The hosted MCP cannot read local file paths: upload with `create_upload` and a `curl` PUT to its `proxy_url`, or
  `upload_file` with a public `url` (details in [references/mcp-tools.md](references/mcp-tools.md)).
- Download results with `curl`; the file host rejected Python's default user agent with 403.
- In zsh, `$V[x]` inside a string is an array subscript; write `${V}`.
- Keep unchanged prompts byte-identical between iterations: identical requests can be served from cache, and an
  extra space is a new paid generation.

## 11. References and related skills

| File | When |
|---|---|
| [references/prompt-templates.md](references/prompt-templates.md) | writing any prompt: bible lines, sheets, masters, scene stills, edits, i2v, multi-shot, v2v, retakes, dialogue, voice, music, lip-sync, ffmpeg helpers |
| [references/models.md](references/models.md) | choosing a model, durations, aspect limits, references, audio flags, quirks |
| [references/mcp-tools.md](references/mcp-tools.md) | connecting the varg MCP and calling it: `call_tool`, schemas, estimates, batches, jobs, uploads |
| [references/examples.md](references/examples.md) | real prompt, result and lesson from our own projects |

Related: `varg-ai` (setup, model catalog, basics), `varg-character-design` (sheets, realism, moderation-safe
wording), `varg-consistent-characters` (multi-scene ads with actors), `varg-previz` and `threejs-animatic` (3D
blocking, v2v packs), `varg-mockups` (still boards), `kling-4-prompting`, `varg-music-video`, `varg-video-editing`,
`how-to-make-ai-video` (find a ready skill for a format).
