---
name: varg-music-video
description: >-
  Directs an AI music video or a song-driven promo end to end on varg, the way the most-watched
  AI music videos are made: measure the song (beat grid, word timings), pitch the concept, cast
  and lock character references, storyboard every cut on a downbeat, approve stills before paying
  for video, generate Seedance 2.5 shots, run a mandatory lip-sync pass, draw lyrics and graphics
  in code, run review rounds and master for each platform. Use when someone asks for a music
  video, a clip for my song, a video for a track, a lyric video with AI footage, a singing
  character, an AI artist or band video, slopcore, or a launch video cut to a song. Not for a
  one-off generated song or single clip (use varg-ai), shot planning and 3D camera blocking only
  (use varg-previz), a talking character without music (use varg-character-keynote or
  varg-podcast-video), or a typography-only lyric video with no generated footage (use a
  HyperFrames music-to-video skill).
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
  openclaw:
    homepage: https://varg.ai
compatibility: >-
  Generation needs the varg MCP connection (https://mcp.varg.ai/mcp) or a VARG_API_KEY (see the
  varg-ai skill). Song analysis uses local tools when available: ffmpeg, Python with Demucs and a
  beat tracker. Code-drawn lyrics and graphics need HyperFrames (Node 22 + ffmpeg) or Remotion.
allowed-tools: Bash(curl:*) Bash(ffmpeg:*) Bash(ffprobe:*) Bash(python3:*) Bash(bun:*) Bash(npx:*) Read Write Edit
---

# Music video director

This skill encodes the workflow that the most-watched AI music videos on X in 2026 actually use (sources at the end): a long slopcore guide written after four viral videos, a character series with a 20M-view video, a Suno → Seedance thread, a Seedance 2.5 reference-bible guide, and a restyle-a-reference-video breakdown.

It is written as a **capability pipeline**. Each step names the capability it needs and the tool that provides it: a varg model or tool where one exists, otherwise an outside tool marked **Outside varg**. **Do not drop a step because varg lacks a tool for it.** Use the outside tool, tell the user what it needs, or stop at that gate.

Generation (images, video, voice, music, lip-sync, transcription, ffmpeg) runs on varg: the varg MCP server (`https://mcp.varg.ai/mcp`) or the `varg-ai` skill (REST at `https://api.varg.ai/v2`). Read `varg-ai` for sign-in and model details.

The agent is the crew; the user is the director. Every phase ends at a gate where the user looks at something and says yes before more credits are spent.

---

## 0. Non-negotiables (what every good creator converged on)

1. **The song is the clock.** Measure every beat and every sung word before making a single picture. Every cut and every lyric hangs off those numbers.
2. **Cuts land on downbeats. Always.** A cut that misses the "one" feels sloppy even to viewers who can't say why. The edit script must refuse off-grid cuts.
3. **Fix stills, not clips.** A still costs a few credits; a clip costs tens to hundreds, and the video model keeps every fault in the still. If two takes miss the same thing, stop paying for takes and change the still.
4. **Everything is video.** A slow zoom on a still reads as a slideshow. Budget for real clips.
5. **Video models never draw text.** End every video prompt with "No text, letters or logos." All lyrics, titles, UI, scoreboards and labels are drawn in code on top of the footage.
6. **Seedance re-sings your line in its own timing.** Every singing or talking shot gets a dedicated lip-sync pass against the real vocal. It costs less than one retake.
7. **Few singing shots.** Decide the count in the storyboard and keep it small: 8 of 93 shots in one viral video, 2 in another.
8. **Pilot, quote, "Go".** Run one clip of each shot kind, show the result and an exact price in credits, and wait for the user to type go. Every batch has a spending ceiling.
9. **When the user criticizes something, make it better.** Never remove a feature because of a complaint; ask before cutting anything.
10. **Write the user's own words into the brief verbatim.** Every later agent reads them.

**First video ever?** Do the best 30 seconds of the song (usually the first chorus), about 8 shots, one lead character, at most one singing shot, and a hard credit ceiling agreed up front (see section 12).

---

## 1. Measure the song (gate: timing proof)

**Input.** The WAV/MP3 plus the lyric sheet. If there is no song yet, see section 1a.

**Steps.**

1. **Split stems** into vocals, drums, bass and other.
   - **Outside varg:** Demucs (`pip install demucs`, then `demucs <song>`), run locally.
2. **Fit a beat grid to the kick drum.**
   - Sanity-check the BPM against the drum stem: a half-time or double-time read (80 instead of 120) puts every cut in the wrong place.
   - If a song has drops, build the grid in **sections that reset on the first kick after each drop**; a single grid drifts.
   - Record downbeats, bars, sections and drops.
   - **Outside varg:** a beat tracker such as librosa or madmom on the drum stem.
3. **Get word timings.**
   - Run Whisper on the **vocal stem**, with the lyric sheet passed as the prompt.
   - Align the lyric sheet to what Whisper heard, giving a start and end for every sung word.
   - Whisper folds pauses into the next word, so **move each word start to the vocal onset** (where the vocal stem gets loud).
   - varg: the `transcription` tool returns word-level timestamps (`whisper_large_v3`, or `groq_whisper_large_v3_turbo` for speed); upload the stem with `POST /v2/files` first. **Outside varg:** forced alignment to the lyric sheet and onset correction (a forced aligner such as WhisperX, plus an onset detector on the vocal stem).
4. **Render a timing proof.**
   - A plain video in which each word lights up at its measured time over a visible beat/bar counter, with the master audio.
   - The user watches it on headphones; iterate until they say it's perfect, then **freeze the numbers**.
   - It takes minutes; never skip it.
   - Build it with the same code-graphics engine as section 8 (HyperFrames or Remotion).

**Output: `songmap.json`.**

```json
{
  "bpm": 98, "grid_segments": [{ "from": 0.0, "bpm": 98, "first_downbeat": 0.21 }],
  "beats": [0.21, 0.82, ...], "downbeats": [0.21, 2.66, ...],
  "sections": [{ "name": "chorus1", "start": 42.1, "end": 61.7 }],
  "drops": [61.7],
  "words": [{ "w": "light", "start": 44.02, "end": 44.51, "line": 12 }],
  "lines": [{ "i": 12, "text": "I keep on waiting for the light", "start": 43.4, "end": 45.9 }],
  "duration": 229.4, "stems": { "vocals": "...", "drums": "..." }
}
```

### 1a. No song yet

The creators' default:
1. Lyrics: written with an LLM by the director.
2. Song: Suno, where the artist's persona voice lives. **Outside varg:** Suno (persona voice and stem export).

On varg:
- `lyria_3_5`: full song with vocals, up to ~3 min; timestamped structure in the prompt; ≤1000 characters.
- `eleven_music_v2_5`: songs with vocals, 3 s to 10 min.

State an exact BPM and structure in the prompt either way.

Keep one voice per artist across songs. For spoken lines, creators prefer Fish Audio clones for acting quality, or generate the lines in Suno so speech and singing share one voice. On varg, spoken lines use ElevenLabs (`eleven_v4`, voice clones supported).

---

## 2. Pitch the concept and the lyric surfaces (gate: brief approved)

1. **Pitch in a few sentences.** Write down the joke or the feeling of the song. Let the agent pitch 2–3 concepts and the user react.
2. **Give every lyric a home**, a surface that belongs to the world of the song. Examples:
   - a nutrition label for the chorus
   - a code review
   - a trading screen
   - phone texts
   - a mission-control HUD
   - hand-painted shop signs
3. **Straight-face rule for funny songs.** The graphics present the joke as real information, the way a label or news ticker would.
4. **Write the production brief** to `brief.md`. It holds:
   - the concept
   - the lyric surfaces
   - the look: palette, era, lens
   - a **banned list** (e.g. decorative shadows, gradients, emoji, lens flares, glitch effects)
   - the user's own direction **quoted verbatim**

   Every agent reads the brief before touching anything.

---

## 3. Cast and build the bible (gate: casting test picked)

1. **Casting test.** Generate the same 3–4 scenes three ways, side by side: model A with refs, model B without refs, model B with refs. Pick one look for the whole video.
   - Creators' choice of image model:
     - GPT Image for instruction accuracy
     - Nano Banana for realism and real materials
     - Midjourney for stylized or cinematic looks, with a locked `--sref` code
   - On varg: `gpt_image_2_5`, `nano_banana_2_1`, `soul` (Higgsfield character styles). **Outside varg:** Midjourney.
2. **Identity text.** One paragraph describing the character's face and body, pasted **word for word** into every image and video prompt. Models read every word literally:
   - "long loose strands across her face" put hair over her eyes in 27 stills
   - the simile "like a microphone" put a real microphone in three of four pictures
   - So: no similes, no ambiguous hair or wardrobe phrases.
3. **Reference sheets** for anything that appears more than once: front, side, back, three-quarter and full body, on a blank background.
4. **The bible.** One page per recurring character, place and prop. Each page holds the identity text, the locked style, the sheets, and the prompts that worked.
   - Recurring rooms get a fixed description pasted into every prompt; furniture otherwise rearranges itself between shots.
   - Name screen positions explicitly ("Mia on the left, Jo on the right") when two characters share a frame.
   - After every session the agent writes a short note on what worked and updates the index.
   - Keep it as files in the project (`bible/<name>.md` + the sheet URLs); varg presets can hold reusable prompt settings.
5. **Lock the references.** Once locked, never regenerate them to fix motion. Fix the motion prompt instead; a new image undoes the consistency work.

---

## 4. Storyboard as data, on the grid (gate: storyboard approved)

`storyboard.json`, one entry per shot:

```json
{ "id": "s034", "section": "chorus1", "start_bar": 41, "bars": 1,
  "start": 42.1, "end": 44.55, "kind": "singing",
  "lyric": "I keep on waiting for the light", "lyric_surface": "nutrition_label",
  "picture": "...", "graphics": "...", "camera": "slow push-in",
  "refs": ["lead_sheet", "diner_plate"], "resolution": "1080p" }
```

Rules:
- **One shot per lyric line, plus the instrumental moments.**
- **Every cut sits on a downbeat**: `start` and `end` come from `songmap.downbeats`, never from line starts. A singer rarely starts a line on the "one"; in one draft only 21 of 74 line-start cuts were on a downbeat.
- **Three shot kinds:**

  | Kind | Inputs | Mode |
  |---|---|---|
  | **singing** | approved still + a **clean vocal slice containing only the words sung on camera** | reference-to-video |
  | **motion** | still + the song itself, so the action lands on the beat; nobody sings | reference-to-video |
  | **insert** | silent; the still is the exact first frame | image-to-video (easiest to get right) |

- Spoken-dialogue scenes last a **whole number of bars**, so the music drops back in on the beat.
- Each clip is generated to start **one beat before** its shot, so a slightly late take still covers the cut.
- Choreography: pair one dance move with one cut, not a continuous take.
- Mark the singing-shot count and get it approved.

For camera blocking and a 3D animatic before any spend, hand the storyboard to `varg-previz`.

---

## 5. Stills first (gate: every still approved at full size)

1. Generate one still (plate) per shot from the bible references.
2. **Review board.** Show every shot in order with its lyric and chosen still.
   - The user can click to see it full size, flag it, and type a note.
   - The comment box doubles as the director's channel: in one video a throwaway comment on a still became the finale.
   - Archive notes between rounds so each round starts empty.
   - Build it as a small web page per project (in Claude, an Artifact with a shared database works), reachable from a phone.
3. **Strict check at full size**: hands, face identity, wardrobe, extra limbs, stray text.
   - In one run, only 3 of 60 Midjourney people-stills passed a strict check.
   - The same shots re-shot in GPT Image: 36 passed, 24 had minor faults, none failed.
4. **Surgical fixes, never whole-image redraws.**
   - Crop the bad region (hand, eyes), enlarge the crop, have the edit model redraw only that, and paste it back with a feathered edge.
   - On varg: the edit models (`nano_banana_2_1` or `gpt_image_2_5` with the crop in `files`). The crop, enlarge and feathered paste are local image steps (ffmpeg or ImageMagick).
5. **Expressions go into the still.** Video models move what's there; they are bad at inventing a new expression. Fixing crossed eyes in the still cost a few credits; three video takes trying to fix them in motion all failed.
6. Safety refusals: change the still (e.g. add bystanders), not the wording. Refused takes are not charged.

---

## 6. Clips (gate: pilot + quote + "Go")

**Model.** Seedance 2.5 is the consensus main model:
- up to 30 s per generation
- native audio
- multimodal references

On varg:
- `seedance_2_5` (PiAPI, BytePlus and fal routes; spec at `https://varg.ai/models/seedance_2_5.md`)
- reference mode: pin `fal:bytedance/seedance-2.5/reference-to-video`, or use `@image1` / `@audio1` tags in the prompt on the PiAPI routes

**Resolution.** 720p for wides and quick cuts; 1080p for faces that stay on screen (it costs roughly twice as much).

**Prompt structure** (every clip):
1. Place, who is in it, and what each of them wants.
2. The action as **timestamped beats**. Timestamps come straight from `songmap.words`, so a word in the prompt sits where that word sits in the song.
3. Camera: **one move per beat**. Never blend an orbit with a dolly.
4. Look: the locked palette and lens.
5. Rules. Always end with "No text, letters or logos."

**Six details per beat:** what's in it, what it's doing, where, how the camera moves, the style, and the rules.

**A 30 s generation is four beats, not one paragraph:** 0–6 set the scene, 6–14 build, 14–24 the turn or big moment, 24–30 the ending. Write the six details for each beat, inside one prompt, with timestamps.

**Reference roles.**
- Tag every reference (`@Image1`, `@Video1`, `@Audio1`) and state **what it controls and what it must not touch**, e.g. "@Video1 defines motion and pacing only; do not use its person, clothing or scene."
- Stay within **1–8 images and 1–5 video/audio refs**. Stability drops above that, whatever the ceiling says.

**Audio references.**
- **Singing shots:**
  - Pass the clean vocal slice. The "blank video" method, a black video carrying the audio, works as an audio reference.
  - **Also write the lyrics into the prompt** ("…she sings: 'waiting for light'"), then add "Use the exact audio from @Video1."
  - On varg the `ffmpeg` tool makes both (MCP `call_tool` with tool `ffmpeg`, or `POST /v2/ffmpeg`). A blank video from a vocal slice:

    ```json
    { "model": "ffmpeg",
      "command": "-f lavfi -i color=c=black:s=1280x720:r=24 -i {{in_1}} -shortest -c:v libx264 -c:a aac {{out_1}}",
      "input_files": { "in_1": "<vocal slice URL>" },
      "output_files": { "out_1": "blank.mp4" } }
    ```
- **Motion shots:** pass the song so the motion lands on the beat, and write "no lipsync, no dialogue".
- **Anything with a speaking or singing character:** generate **with sound on** (`"audio": true`). Silent generations come back with barely moving mouths.

**Run order.**
1. **Pilot**: one clip of each kind.
2. Show it with an exact quote, e.g. "46 clips, 219 s, ≈ N credits", from `estimate_cost` (MCP) or `POST /v2/estimate`.
3. Wait for "Go".
4. Check the balance (`check_balance`) before big runs; a balance hitting zero mid-batch stalls everything.

Keep a running total of billed credits per project (`get_job_cost` per job) against the agreed ceiling, and stop at the ceiling.

**Near-miss clips.** Edit the footage instead of regenerating, e.g. adding missing jet engines to a clip from a corrected still.
- On varg: `seedance_2_5` and `kling_v4` edit modes, `omni_flash_1_1` edit, `grok_imagine_edit`, `minimax_h3_max_insert`, and `id_v2v` (restyle from an edited first frame, keeping motion), the closest to edit-from-still. **Outside varg:** Runway Aleph.

**Very short v2v shots.** Slow the source to half speed before the swap and speed it back up after; otherwise the model invents motion past the end.

---

## 7. Lip sync (mandatory pass)

What goes wrong: Seedance re-performs the line, so a take can look great and still sit half a second off the recording. Checks that compare Seedance's own soundtrack, or only mouth openness, pass while viewers still see bad sync. One creator took a finished video down after five of six comments said the lip sync was off.

Do this for every singing and talking shot:
1. Cut the shot **exactly as it plays in the final edit**.
2. Pair it with **only that shot's own vocal** (the stem slice).
3. Run a dedicated lip-sync model. Creators use Sync's lipsync-2-pro.
   - On varg: `sync_v2_pro` or `sync_v3` (video + audio in `files`).
4. Optional, for hero shots: make several takes, transcribe each take's own audio, measure each word's offset from the song, keep the best take, and time-warp it per word before the lip-sync pass. **Outside varg:** the take scorer and per-word time-warp are local scripts (transcription on varg, ffmpeg `setpts` per segment).
5. QA what the lips are shaping, not only whether the mouth opens.
   - On varg: `analyze_video` with a focused prompt on p/b/m closures, plus the user's eyes. **Outside varg:** a SyncNet/LSE-style lip-sync score.

Staging that helps sync: medium close-ups, simple clear phoneme shapes, and the vocal delivery written into the prompt ("crisp diction, open vowels, staccato phrasing"). Avoid whispered or mumbled delivery.

---

## 8. Lyrics and graphics in code, then the cut

**Graphics engine.**
- A headless-browser engine (HTML/Canvas) draws every frame at the target resolution.
- **Every frame depends only on song time, never on the previous frame.** That lets sections render in parallel: a 4-minute 1080p film renders in about a minute across 8 workers.
- Each song section is one file whose scenes know their start, their end, and how to draw themselves at time *t*.
- Sections can be farmed out to subagents, each allowed to edit only its own file and forbidden to generate or buy anything.
- **Use HyperFrames** (HTML compositions rendered frame-exact from timeline time; the `hyperframes` skill) or Remotion. varg's own `<Captions>` / `<Title>` / `<Overlay>` cover simple subtitles only, not lyric surfaces.

**Lyric gate.** An automated check that every sung word is on screen at the moment it is sung, readable on a phone. It must print **N of N** before anything ships. Write it as a script that reads `songmap.words` and the composition's text timings.

**Graphics rules.**
- Lyrics are type straight on the picture. **Never put solid boards over faces.**
- Camera shake only on the kick. Reacting to every sound hides the character.
- Chopped vocal stutters can become cuts or jumps in the picture.

**Assembly.**
- The master track is the only music. Generated clip audio is muted, except deliberate diegetic or dialogue moments.
- Hard cuts on downbeats. No soft crossfades in beat-driven sections.
- Keep 30 fps. **Do not RIFE-interpolate to 60**: it smears fast whips.
- Upscale soft or murky shots (creators use SeedVR2; on varg: `seedvr_video` or `topaz_video`).
- The edit script **rejects any cut that is not on a downbeat** and any total that does not equal the song duration.

---

## 9. Review rounds (repeat until "ship it")

- **Review page.** Each draft goes on a page with a player per scene and a comment box under every shot. The agent reads the notes from the page, fixes them, and posts the next draft. Creators report 3–7 rounds and 60–100 notes per video.
- **Takes tracker.** Track every take of every slot (one creator had 122 takes for 12 slots). A player stitches the current best take of each slot into "the cut so far".
- **Phone access.** Serve the page through a tunnel or a hosted link so the director can approve from a phone.

Build both on the same review page as section 5 (in Claude, an Artifact with a shared database holds notes and takes).

---

## 10. Finish like you mean to post it

- **First frame:** the star is on screen in frame 1; feeds show it before play.
- **Handle in the picture:** a faint handle (e.g. "X: @name") in the frame, because reposts strip captions.
- **Flash-frame scan:** check every frame of every clip for sudden brightness spikes; Seedance occasionally makes a pure white frame. Use ffmpeg `signalstats` (locally, or through varg's `ffmpeg` tool) and flag frames whose `YAVG` jumps.
- **Loudness:** master at about −14 LUFS through a limiter at **−1 dBTP**; platform compression pushes −0.2 dB peaks over the ceiling. ffmpeg `loudnorm=I=-14:TP=-1:LRA=11`, locally or through varg's `ffmpeg` tool.
- **Vertical versions are re-laid out, not cropped.**
  - Use 15–30 s sections at 1080×1920 built from the same clips.
  - Re-place the type clear of the app UI safe zones; a 16:9 frame dropped into 9:16 leaves the lyrics unreadable.
- **Rights:** register an own song with the distributor before the video spreads; expect Content ID claims on someone else's song. Label AI content where platforms require it.

---

## 11. Alternate routes

- **One-shot generators**: Slop Cannon (slop.cc), OiiOii, Flova, Kling's one-minute MV mode, and `pixverse_vibemv` on varg (a whole song, 10 s to 6 min, in one of 15 styles). Fast and cheap, good for drafts and memes. Creators report a quality ceiling on pacing, camera sense and lip sync compared with the directed pipeline above.
- **Restyle a reference video** ("make this, but about X"):
  1. Measure the original: score every frame for hard cuts, zooms, flashes and grayscale stretches (ffmpeg `select='gt(scene,0.35)'` and `signalstats`; `analyze_video` on varg for a coarse pass).
  2. Turn it into slots. Each slot gets a verdict: swap the person / render fresh / replace.
  3. Swap the person with v2v, using a character sheet plus start and end frames. On varg: `wan_3` reference-to-video, `minimax_h3_max_recast`.
  4. Keep the original song mix whole.
  5. Redraw all text in code.
- **Single sung hook (≤30 s, no fixed master):** one Seedance 2.5 generation with the lyrics in the prompt and native audio. Fine for a teaser. Never cut several of these into one song, because each one sings a different melody.

---

## 12. Budget reality

Quote every amount in credits from `estimate_cost` / `POST /v2/estimate`, never in money. Creators' reported spend, as proportions:

- Almost all the credits go to video generation; stills, voices and lip sync are small change.
- Seedance 2.5 is billed per second and per resolution: about 210 credits per 5 s at 720p and about 480 at 1080p (varg catalog, October 2026; confirm with the estimate).
- **A 4-minute song, one shot per lyric line, no dialogue:** plan for roughly 2–3× the credits of generating the song's full length once at the chosen resolution (handles, pilots, retakes). Dialogue roughly doubles that, and about a third of clip spend goes to post-review fixes.
- The pilot is one clip of each kind; stills for a whole video and the lip-sync pass are each a small fraction of the clip spend.
- **First 30-second video:** agree a hard ceiling of about 2–3× one pass of those 30 seconds, and stop there.

---

## 13. Tools by capability

| Capability | On varg | Outside varg |
|---|---|---|
| Stem separation | — | Demucs |
| Beat grid / downbeats / sectional reset / BPM sanity | — | librosa, madmom |
| Word timings, lyric forced alignment, onset correction | `transcription` (`whisper_large_v3`, `groq_whisper_large_v3_turbo`) for raw word timings | a forced aligner (e.g. WhisperX) + onset detection |
| Agent "ears" (describe a take or a mix, check cuts against sound) | — | an audio-understanding model |
| Song with vocals | `lyria_3_5`, `eleven_music_v2_5` | Suno (persona voice, stems) |
| Spoken lines, voice clone | `eleven_v4` | Fish Audio |
| Stills | `gpt_image_2_5`, `nano_banana_2_1`, `soul` | Midjourney (`--sref` lock) |
| Surgical crop → redraw → feather-paste | edit models (`nano_banana_2_1`, `gpt_image_2_5`) | ImageMagick / ffmpeg for crop and paste |
| Seedance 2.5 i2v and reference-to-video with audio refs | `seedance_2_5` routes | — |
| Blank-video audio ref, slicing, trims | `ffmpeg`, `trim` tools | local ffmpeg |
| Edit an existing clip from a corrected still | `id_v2v`, `seedance_2_5` / `kling_v4` edit, `omni_flash_1_1` edit, `grok_imagine_edit` | Runway Aleph |
| Lip-sync redraw | `sync_v2_pro`, `sync_v3` | — |
| Take scoring + per-word time-warp; lip-sync score | `transcription`, `analyze_video` (coarse) | local scripts, SyncNet/LSE |
| Time-driven code graphics + parallel render + lyric gate | `Captions` / `Title` / `Overlay` (simple only) | HyperFrames, Remotion |
| Downbeat-only cut validation | — | the edit script |
| Review board / takes tracker / phone review | — | a project web page (Claude Artifact with a database) |
| Pricing gate, pilot, ceiling | `estimate_cost`, `check_balance`, `get_job_cost` | a running total kept by the agent |
| Flash-frame scan, loudness mastering | `ffmpeg` tool (`signalstats`, `loudnorm`) | local ffmpeg |
| Upscale soft shots | `seedvr_video`, `topaz_video` | — |
| v2v person swap / recast | `wan_3`, `minimax_h3_max_recast` | — |
| Reference-video cut/flash detection | `analyze_video` (coarse) | ffmpeg scene detection |
| Project bible (characters, places, props, prompts that worked) | presets | project files |

## Related skills

`varg-ai` (sign-in, models, single generations, cloud render), `varg-previz` (story structure, 3D camera blocking, Seedance video-to-video packs), `hyperframes` (lyrics and graphics drawn in code, final assembly), `media-download` (pull a reference video or audio by link), `video-skills` (find a skill for another format).

---

Sources (public posts on X, 2026):
- @obie, "slopcore in 7000 words" (github.com/obie/slopcore)
- @anabology, the Claudia videos and their making-of
- @Framer_X, Suno → Seedance thread
- @EXM7777, Seedance 2.5 guide
- @zealcaiden, restyle breakdown (github.com/aimvgg/claude-video-editing-skills)
- Higgsfield's open-sourced Originals prompts
