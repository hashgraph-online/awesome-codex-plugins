# Case study: a 99 s anime music video, with scripts

What one finished video taught, step by step: "I Don't Wanna Pick", 99 s, 36 shots, 9:16, 133.8 BPM, 1980s anime
cel look, nine rounds of director notes. The main pipeline is in `SKILL.md`; this page adds the file formats, the
scripts and the fixes that worked on a real project.

## The scripts

Four small scripts live in the code2video template of the same name
([vargHQ/code2video-templates/varg-music-video](https://github.com/vargHQ/code2video-templates/tree/master/varg-music-video)):

```bash
git clone --depth 1 https://github.com/vargHQ/code2video-templates
S=code2video-templates/varg-music-video/scripts
python3 $S/songmap.py assets/song.mp3 --lyrics lyrics.txt --out songmap.json    # librosa (+ faster-whisper for words)
python3 $S/rough_cut.py storyboard.json place.json renders/cut.mp4 --clips out/ --audio assets/song.mp3
bash $S/contact_sheet.sh renders/cut.mp4 qa/cut.jpg 2                             # timestamped QA sheet
bash $S/tg_export.sh renders/final_v1.mp4                                         # small copy for Telegram/chat
```

| script | does |
|---|---|
| `songmap.py` | song → `songmap.json`: tempo fitted by the best phase in every 8 s window, `beat_track` held to it, 4/4 bar phase = the beat with the most onset energy, optional faster-whisper word timings with the lyrics as the prompt. `--bpm` when the generator tells you the tempo (then only the phase is fitted); `--start/--end` for a window of a longer track |
| `rough_cut.py` | storyboard + `place.json` → a frame-exact cut with the song; segments, slow-mo, freeze frames, tints; warns when a segment needs more source than the clip has |
| `contact_sheet.sh` | `<video> <out.jpg> [fps] [cols] [width] [start] [dur]`: one image of timestamped frames, to look at every generation and render |
| `tg_export.sh` | H.264 CRF 24, max 3 Mbit/s, faststart: ≈38 MB for 99 s at 1080×1920; add `720` as the second argument for ≈15–18 MB |

## Song map

- librosa alone read 129.2 BPM for a 133.8 BPM track (3.5 % off), which puts every later cut in the wrong place.
  Pass the generator's BPM when you have it.
- AI songs sit on a fixed tempo, but the phase can jump between sections; that is why the fit runs per window.
- Sections and drops are written in by hand (by ear or from the energy curve). The drop is where the story turns.
- Whisper often folds an instrumental intro into the first word: check the first word of every line against the
  vocal stem and fix it by hand. Keep a small overrides table for director notes like "the word 'into' is long".
- Using a window of a longer track: store the window in `songmap.json` and shift every time to 0.
- At 133.8 BPM a beat is 0.448 s and a bar 1.794 s. Most shots were one bar, big moments two bars, inserts half a bar.
- Frame-exact: a shot `start..end` gets `round(end*fps) - round(start*fps)` frames, so rounding never drifts.
- If the edit must breathe (a hero beat before a reveal), move a whole beat from one shot to its neighbour and
  shift every graphic that keyed off the old boundary.

## Story in five moves (fits 30 s to 3 min)

| move | where in the song | what it was in this video |
|---|---|---|
| Hook (≤ 2 s) | first bar | extreme close-up of the hero, an impact on beat 2 |
| Problem | verse | everything breaks: providers die, keys expire, 50 tabs, a giant "503" monster |
| Dream / turn | pre-chorus | he closes his eyes and dreams of "all the models" walking a runway |
| Payoff | drop / chorus | the agent orb ignites, one call, the squadron attacks together |
| Climax + callback | bridge / last chorus | into the monster's mouth, a sax solo, a 2001-style stargate, then a calm cockpit and a wink |

- Every lyric line gets a **literal** picture plus a graphic: "How do I call Seedance?" → a gloved fist hits a
  console button labelled SEEDANCE that fails with ✕ 503. The model draws the action; code draws the words.
- Abstract things named in the lyrics become objects: a router becomes a ring of logos, providers become lanes.
- Keep recurring markers: the same crack in the canopy, the orange orb, colour = side (red enemy, brand orange ours).
- For a longer arc use the Hero's Journey in the `varg-previz` skill (`references/story-structure.md`).

Storyboard fields used here, next to the ones in `SKILL.md` section 4: `scene` (location + light state: shots of
one scene are generated together even when they are not adjacent), `action` (the text for the video model, one
action, absolute times), `overlay` (what code draws: text, logos, UI; never in `picture`) and `source`
(`gen`, `reuse` for a clip from an earlier version, `code` for a shot made only in code). Keep a short
`treatment.md` (logline, the five moves with times, colour script, references) next to `brief.md`, and update
all three in one pass after every note.

## Anchors, runs and prompts

| anchor | content |
|---|---|
| Character sheet | front, ¾, profile, back + a face close-up, grey background, no text |
| Vehicle / product sheet | several views **plus a person next to it** for scale (here a ship ≈ 5× a person) |
| Antagonist sheet | the creature, with its minions in a separate column so a minions-only crop is possible |
| Master plate per location | the establishing frame of each place, in the film's look |

- One art style line in every prompt (here: "1980s anime cel animation in the style of Macross and Bubblegum
  Crisis, hand-drawn line art, painted backgrounds, magenta, cyan and violet neon on deep navy, chrome, soft VHS
  bloom"). Every ref image at least 300 px on the short side: pad, do not upscale.
- **One location = one set of refs.** Send only refs of what is in frame: an exterior still in an interior shot
  pulls the exterior in. After a story rewrite, old stills are stale.
- Group shots by `scene` into runs of 4–11 s; short runs obey better and retake cheaply. Pad the last shot with a
  tail so the run is a whole number of seconds; the tail never goes in the edit. A retake of one broken shot is a
  4 s run of just that shot.
- **Consistency from your own best frames.** For a retake, add a frame of a good shot from the same film as a ref
  ("@image2 is a frame from this same film: copy its design and drawing style"). This fixed a scene the director
  called "AI slop".
- Times in prompts are absolute from the clip start ("2.4–4.0 s: she puts the helmet on").
- Anatomy and props are spelled out: "exactly two arms", "his hands are empty: no card, no tablet, no glowing
  object", "one person in the cockpit". A prop or pose in a reference video gets copied, so remove it from the
  reference.
- Reference mode with a previz or rough clip, greyscale refs and the pass-through check are in the `varg-previz`
  skill (`references/seedance-v2v.md`). With no previz at all, image-to-video from a master plate or a character
  still.

Prompt shape that worked for a run with a camera reference:

```
@video1 is a black-and-white previz of this shot. Copy ONLY the camera (framing, lens, position, movement), the
hard-cut timing and where everyone stands. Do not copy its look or its props; the result must not look like @video1.
@image1 is a frame from this same film: <what it shows>. Keep <face, suit, set, light> exactly like this.
@image2 is <the character sheet>: same face, hair, outfit.
<constraints: exactly two arms; hands empty; one person in the cockpit; we are inside, no stars>
Every frame is clean cel animation with crisp ink lines and flat colour: no noise, no grain, no static, no smeared blur.
Look: <style line>.

<N> shots, hard cuts exactly as in @video1:
1. 0.0–1.8 s. <shot size + angle>: <one action>.
2. 1.8–4.0 s. …

Full-bleed 9:16 frame, no borders, no letterbox. No text, letters, numbers, logos or UI anywhere in the frame.
No dialogue, no lip-sync.
```

Bookkeeping: `check_balance` and `get_current_team` (who pays) → `estimate_cost` on one request, quoted as the
ceiling → an explicit go → submit with `wait: false` → write the job id into `jobs.json` at once → poll `get_job`
→ download to `out/NN_<run>.mp4` → write the file id and billed credits next to the job. A failed job is not
billed: say so, fix, resubmit once.

## QA every output before it goes near the edit

`contact_sheet.sh out/NN_run.mp4 qa/NN.jpg 5`, then look at every frame:

1. Count people and arms; every hand belongs to a body in frame.
2. Props that should not exist (a glowing card read as a blade through the fist; a helmet with a third arm).
3. Pass-through (the output looks like the grey previz) and text drawn by the model.
4. Style drift against the anchors: grey "static" mush is slop; retake with a frame of a good shot as a ref.
5. Timing: where the real cut or action lands. Models sometimes ignore "cut at 3.6 s"; write the real in-points
   into `place.json`, not the requested ones.

Faults of up to about 6 frames are cut out in the edit (a jump cut plus a slight slow-mo of the part before);
anything longer, or anything the director sees twice, is a retake.

## The rough cut: `place.json`

Maps every storyboard shot to footage; times are seconds in the source clip:

```json
{ "v04": ["01_A1", 3.583],
  "x28": [["12_F2_r5", 3.6, 1.794], ["12_F2_r5", 0.0, 1.794]],
  "x33": [["12_F3", 5.377, 0.897, {"vf": "hue=h=t*600:s=1.7"}],
          ["../clips/o2_v1", 1.5, 0.224, {"freeze": true, "vf": "negate,hue=s=0"}]],
  "p15": [["06_D", 0.0, 1.0, {"vf": "setpts=1.3*PTS,fps=24"}], ["06_D", 1.0, 1.12]] }
```

- A clip + in-point fills the whole shot. A list is segments `[clip, in, dur, opts]`; the last one fills the rest
  of the shot exactly. `opts.vf` adds ffmpeg filters (tints, slow-mo); `opts.freeze` holds the first frame.
- Shots missing from `place.json` come from `--fallback` (the animatic) or black, so the cut is always full length.
- The "needs more source than the clip has" warning caught two real bugs: a frame of the next world flashing in,
  and a cut one frame short, which also trimmed the song through `-shortest`.
- Re-cuts are cheap: the same generations re-ordered into a new sequence (close-up → blast → close-up → blast),
  shots of an old version reused, a missing beat bought by slowing a segment 1.1–1.3×.
- Back up `place.json` before re-cutting.

Lip-sync note from this video: on the sung anime close-ups, the original take cut per phrase looked better than
the lip-sync pass, which damped the drawn mouth. Run the pass (section 7 of `SKILL.md`), compare it with the
original take, and decide per shot.

## Graphics layers (HyperFrames)

Main `index.html`: a `#bg` video (the cut, upscaled once to 1080×1920 at 30 fps), compositions `fx`, `logos` and
`lyrics`, and the song. They were generated from Python lists (HTML + GSAP calls) so every time comes from
`songmap.json`.

| layer | what worked |
|---|---|
| lyrics | word-timed, a dark rounded box in the top band, the active word highlighted, colours by act |
| brand / model tags | logo + the **current** model name from `list_models`, flipping on beats, over characters' heads in staggered rows, never in the lyric band |
| hits | impact flashes or inverted impact frames, camera punches on `#bg` (x/y jitter for 6 frames, scale 1.06 → 1) |
| anime inserts | radial focus lines, diagonal cut-in banners, katakana SFX stamps, manga panel splits, CRT cards that flatline |
| set pieces | 50 error pop-ups, provider lanes switching, a router ring of logos, end lyrics big over the face |

- Overlays never cover the lyric band and never sit on faces; text at least 40 px on a 1080-wide frame. To place
  tags over heads, measure the head positions on frames first.
- Animate transforms (`x`, `y`, `scale`), never `left`/`top`. Repeated tweens on one element use `fromTo` with
  `immediateRender: false`; overlays start at `opacity: 0` in CSS.
- `mix-blend-mode` elements under a `backdrop-filter` impact frame turn it into a flat colour: keep them apart.
- A state class with the same name as a component class hides things; prefix state classes.
- Under nvm the shell `npx` can be a broken function: call the full path to that Node's `npx` with its `bin` on
  `PATH`. Run `hyperframes check` before every render; a draft render to check, `--quality delivery` for the master.
- After rendering, look at frames at the changed times (a contact sheet), not only at the lint result.
- Related layers: `anime-jp-subtitles` (fansub and karaoke lines, telop, tategaki, katakana SFX) and
  `anime-triple-split` (three panels on three beats; it also hides a weak shot), both code2video templates.

## Director rounds

1. Append the note to `brief.md` verbatim with the date, in the director's own language.
2. Split it into free fixes (re-cut, graphics, text), paid fixes (retakes, new shots) and questions.
3. Paid fixes: say what, why, the length and the credit estimate in one question, and wait for the yes. A direct
   order ("redo this shot") is the yes for that shot only.
4. Do the free fixes while generations run; QA each output, place it, re-render as a **new** version
   (`final_v7` → `final_v8`, never overwrite a delivered file).
5. Look at the new render at every changed time before reporting.
6. Report: the file, what changed per note (with times), what was not done and why, credits spent this round.

| note | fix that worked |
|---|---|
| "texts at the start are strange" | removed the hook text and render bar; open on the face and the hit |
| "add the icons like in the first version" | logo pills on every brand line, logo + name tags over characters |
| "the scene at 1:02 is cringe" | re-cut existing takes into close-up / blast / close-up / blast, flashes, punches |
| "more like 2001" | tinted eye freeze frames, worlds solarising in, colour cycling, stargate slices |
| "12–18 s looks like AI slop" | retake without "static" in the prompt, a frame of a good monster shot as a ref |
| "weird object in his hand at 31 s" | retake with "hands empty" and a camera-only reference (the previz had the card) |
| "helmet bug at 29 s" | retake with "exactly two arms, both hands on the helmet" |
| "labels overlap the lyrics" | measured head positions on frames, tags in two rows above heads, below the lyric band |
| "show the hero a bit more before the models" | moved one beat from the next shot, shifted the tags with it |
| "old model names" | names from `list_models`, never from memory |
| "make it smaller for Telegram" | `tg_export.sh` |

## Files the project ended with

`brief.md` · `treatment.md` · `songmap.json` · `storyboard.json` · `refs/` (sheets, plates, frame grabs) ·
`requests*.json` + `jobs.json` (job ids, file ids, billed credits) · `out/` (generations) · `place.json` ·
`renders/cut.mp4` · `hf/` (HyperFrames project) · `renders/final_vN.mp4` + `_tg.mp4`.
