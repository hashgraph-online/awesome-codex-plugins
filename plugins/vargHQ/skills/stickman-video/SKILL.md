---
name: stickman-video
description: >-
  Make a viral stickman video in code, with no video model: a jointed SVG stick figure (round
  head, two-bone arms and legs with fixed bone lengths, poses written as joint angles) acts out
  a survival-choice story, a POV story, a "fake friend vs real friend" contrast, a history
  explainer or a stick fight, with a DAY counter, rules that appear one at a time, word-timed
  captions, procedural sound and a two-choice "FOLLOW FOR DAY 2" ending, rendered to a
  1080x1920 MP4 with HyperFrames. Ships the working rig (planted-foot walk, breathing idle, head
  turns, blinks, shock, crouch), script templates with word counts, the fixes for stiff
  head-only stickman animation, and a 24 s example whose voice cost $0.04 (4 credits). Use when someone
  asks for a stickman video, stick figure animation, a faceless stickman channel, a survival
  choice story, POV stickman, or wants to "make videos like the viral stickman reels". For
  Google Flow or Veo clip prompts use kaomei/stickman-video-director instead.
license: MIT
compatibility: >-
  HyperFrames 0.9 (bunx hyperframes or npx hyperframes; brings Chrome, needs Node 22 and
  ffmpeg). The voice is optional: the varg MCP (https://mcp.varg.ai/mcp) or a VARG_API_KEY, or
  any recorded file. Word timings come from local whisper.cpp through hyperframes transcribe.
  No key is needed for the picture, the sound effects or the render.
metadata:
  author: vargHQ
  version: "1.0.0"
  varg.cost.typical: "$0.04 (4 credits) for a 60-word ElevenLabs v3 voiceover; picture, sound and render free"
  varg.runtime.typical: "17 s to render 24 s of 1080x1920 at 30 fps on an Apple M1 Pro"
  varg.models: "eleven_v3 (voice, optional)"
  varg.outputs: "mp4 1080x1920 30 fps, contact sheet"
  openclaw:
    requires:
      anyBins:
        - ffmpeg
    homepage: https://varg.ai/how-to
allowed-tools: Bash(bunx:*) Bash(npx:*) Bash(bun:*) Bash(ffmpeg:*) Bash(ffprobe:*) Bash(curl:*) Read Write Edit
---

# Stickman video: a jointed figure, a few rules, a choice

Stickman reels are a format wave on X, TikTok and Shorts in autumn 2026, and the pitch that travels is "100% code, $0 video generation" ([@finnardley](https://x.com/finnardley/status/2115786060231770351), 65,440 views). The complaints are just as consistent: limbs too long, a character that only moves its head, monotone animation ([a user replying to the stickman-video-director author](https://x.com/GazunH26262/status/2121123319143633304)). This skill fixes those with a real rig: bones of fixed length, poses as angles, legs solved by inverse kinematics, and several motion layers running at once.

The example in `assets/example/` is a 24.3 s "Day 1: lighthouse rules" reel built with this skill: an original premise, a 60-word voice for $0.04 (4 credits), procedural sound, word-timed captions, three rules, a two-choice ending, rendered in 17 s.

## 1. Ask, then go

Ask once, in one message, with a default for each. Then write the script and show it before building.

| Ask | Options | Default |
|---|---|---|
| Format | survival choice (DAY N + rules + 1/2 ending), POV, contrast (fake vs real), history explainer, stick fight | survival choice |
| Length | 15–25 s (one episode, Shorts/Reels), 45–60 s, longer = a series of episodes | 20–25 s |
| Ratio | 9:16, 16:9 (YouTube long form), 1:1 | 9:16, 1080x1920, 30 fps |
| Voice | AI narrator on varg at about $0.04 (4 credits) per 60 words, their own recording, no voice (captions + sound only) | AI narrator, calm and tense |
| Style | night set with a white figure; paper white with a black figure; retro TV glow; one set drawn in code | night set |

If they bring a premise, use it. If not, offer three one-line premises that are not copies of a known channel's episodes (see section 9).

## 2. Five formats and why each travels

View counts are the X posts' own counters on the collection date (2026-11-13). Follower and income figures inside those posts are the posters' claims, not verified.

| Format | What it is | Why it travels | Evidence |
|---|---|---|---|
| **Survival choice** | Second person ("you"), a DAY counter, 3–4 rules that appear one at a time, a rule gets tested, the ending card "1: … / 2: …" and "FOLLOW FOR DAY 2" | The choice asks for a comment, the DAY counter promises a series, the rules give the viewer something to check against the picture | [@finnardley](https://x.com/finnardley/status/2115786060231770351) code-only prompt with exactly this structure, 65,440 views; [@brainextends](https://x.com/brainextends/status/2111569272732553535) zombie-on-a-farm interactive episodes ("22M views, 154K followers in 5 days"), 50,885 views; [@laurgrowth](https://x.com/laurgrowth/status/2117973871513194869) empty subway, "1: GET ON / 2: STAY", 6,615 views; [@CrazyKaomei](https://x.com/CrazyKaomei/status/2119617667623776480) doomsday-survival style with an A-or-B ending, 21,050 views |
| **POV** | "POV: you're the last one in …"; the viewer is the figure, the first frame is the situation | No setup needed; the hook is the situation itself; easy to make 4–5 hook variants of one story | [@FeyiLux](https://x.com/FeyiLux/status/2103734366182441001) "how to start the POV stickman niche" (and: the niche is crowded, write 4–5 hooks), 26,076 views; [@nolantoken](https://x.com/nolantoken/status/2113601722253758649) creepy stickman stories with choice endings, an app account claiming 56.3k followers in 15 posts, 12,034 views |
| **Contrast** | Two figures, the same situation twice: fake friend vs real friend, you vs you, white figure vs yellow figure; one line of text | Readable with the sound off in under a second; relatable; ends in "tag your real friend" | [@ghosstty_](https://x.com/ghosstty_/status/2117010986812998119) on 4 "fake friend vs real friend" reels over 50M views each (top 97.3M), 7,620 views; [@maubaron](https://x.com/maubaron/status/2119163598660665748) on 11-second stick-figure clips, black background, one line of text, "225M views in a few days", 13,229 views |
| **History explainer** | A deadpan narrator; a grand event told through one small stickman's absurd problem; each claim one picture | The contrast between the serious voice and the silly picture; evergreen topics; long watch time | [@CrazyKaomei](https://x.com/CrazyKaomei/status/2112791668332319070) "history picture book" style, "deadpan absurd contrast", 57,439 views; [@sarpstar](https://x.com/sarpstar/status/2119082994925211686) an 8-minute documentary made in code overnight, 540,864 views; a reply asking how to get this style with a consistent character was pointed to the stickman-video-director repo |
| **Stick fight** | Two figures stand in for two teams, apps or models and fight in three exchanges | Rivalry, a clear winner, short; the "made 100% in code" claim is part of the post | [@rayanabdulcader](https://x.com/rayanabdulcader/status/2119995155625181371) two chat-app dock icons fighting as stick figures, 100% code, 137,490 views; [@Framer_X](https://x.com/Framer_X/status/2117995586528104755) a stickman fight used as the motion reference for other characters, 72,629 views |

Also cited for the size of the wave: [@Aygramm_](https://x.com/Aygramm_/status/2112481704724004911) "stickman animations are the new gold rush", 40,656 views; [@theoardley](https://x.com/theoardley/status/2116684286837330374) listing "stickman survival stories" among free Claude video skills, 499,979 views.

## 3. Script templates

**Pace, measured.** ElevenLabs v3 "Adam" read the 60-word example in 25.1 s raw (2.4 words/s, sentence pauses of about 0.4 s). Shortening every pause to 0.2 s gave 22.2 s (2.7 words/s) without stretching speech. Plan at 2.5 words per second of voice, then tighten pauses. Leave 2 s after the last word for the ending card.

### Survival choice, 20–25 s, 55–65 words

| Beat | Seconds | Words | Line pattern | Picture |
|---|---|---|---|---|
| Hook | 0–1.2 | 2 | "Day one." | DAY N title already on frame 0 over the figure mid-stride |
| Situation | 1.2–5 | 10–12 | "You're the new [role]. The last [role] left three rules." | walk in, stop, look back over the shoulder, look up, look at the camera on "three rules" |
| Rule 1 | 5–7.6 | 6–8 | "Rule one: [simple instruction]." | rule card 1 lands on the word "Rule"; the figure shows it (points at the thing) |
| Rule 2 | 7.6–12.3 | 12–14 | "Rule two: [instruction]. If [condition], [don't do X]." | the condition comes true on screen; the figure almost does X and stops |
| Rule 3 | 12.3–15.2 | 7–8 | "Rule three: never [the thing about to happen]." | the figure walks to the danger and looks at it |
| Break | 15.2–20.2 | 12–14 | "It's [time]. [The rule is tested]. And [a twist that makes it personal]." | the HUD clock flips; shock jump; crouch and tremble; the camera creeps toward the danger |
| Choice | 20.2–22.3 | 8 | "[Option 1], or [option 2]?" | "1:" lands on option 1's first word, "2:" on option 2's; the figure looks between the two |
| Hold | 22.3–24.3 | 0 | none | "FOLLOW FOR DAY 2" for at least 2 s |

The example's script: "Day one. You're the new lighthouse keeper. The last keeper left three rules. Rule one: the light never stops turning. Rule two: count the ships. If there's one more than yesterday, don't wave. Rule three: never open the door after midnight. It's twelve-oh-one. Someone knocks. And the voice outside sounds like yours. Open the door, or keep the light on?" Write numbers as words for the voice ("twelve-oh-one") and fix them back in the captions.

### POV, 15–20 s, 35–50 words

0–1 s: the text "POV: [situation]" on frame 0 (on screen; the voice may read it). Then three escalating beats of 3–4 s, 8–12 words each, each one a new action or a new thing in the set. End on a question or a choice (6–8 words). Write 4–5 hook variants and test them as separate posts.

### Contrast, 10–15 s, 0–25 words

0–1.5 s: one line of setup text ("When you trip in public:"). Then the same staging twice, 4–6 s each, label on top ("FAKE FRIEND" / "REAL FRIEND"): the same trigger, opposite reactions, a 0.4 s hold on each reaction. 1–2 s ending: "Tag your real friend". Often no voice: music bed and two or three effects.

### History explainer, 45–60 s, 110–150 words

"In [year], [grand event]." in a deadpan voice, then one claim per sentence, one picture per claim, a change every 2–3 s. Every third beat cuts from the grand scale (a map, a crowd of identical figures) to one small figure's problem. End on an ironic payoff and a question. Every fact needs a source you can name; never invent dates, numbers or quotes.

### Stick fight, 10–20 s, 0–10 words

Name tags over two figures (generic stand-ins, not real logos). Three exchanges: anticipation 0.15–0.2 s (wind up the opposite way), hit in 2–3 frames, reaction held 0.3–0.5 s, a hit sound on the contact frame. A reversal in the third exchange, then a winner pose and one line of text.

## 4. The rig, and the fixes for stiff stickmen

The figure is `assets/stickman-rig.html` (a 9-second pose tour that renders as is) and the same code as `assets/example/rig.js`. API, channel table and pose values: `references/rig.md`.

| Complaint | Fix in the rig |
|---|---|
| Limbs too long, proportions drift | Fixed bones in local units: head radius 36, neck 12, torso 124, upper arm 70, forearm 66, thigh 86, shin 84. Nothing ever stretches; an unreachable foot target stops where the leg ends. |
| Limbs detach, poses pop | One SVG path per limb, recomputed every frame from joint angles. Never swap whole images between poses. |
| Feet slide | The walk phase comes from the distance the hips have travelled, not from time: the stance foot is planted at any speed. Legs are two-bone IK with the knee bending forward. |
| Only the head moves; monotone | Every shot has a body action. Motion is layered: keyed pose, walk cycle, breathing (3.1 s) and weight shift (5.7 s), tremble, blinks, and a line boil (seeded jitter of 0.8 px redrawn 12 times a second). |
| Everything moves at once, on one curve | Overlapping action: the head leads by 0.05 s, the near arm follows by 0.05–0.07 s, the far arm by 0.09–0.11 s. Eases by job: `snap` for reactions, `back` for gestures, `inOut` for looks, `walk` (short ramps, constant speed) for travel. |
| The face says nothing | A head turn is the eyes sliding across the head (spacing narrows toward profile). Brows appear only with an emotion; an O-mouth for shock; eyes up to 1.6x. |
| Arms vanish when they cross the body | The near arm and leg get a dark outline pass that starts partway down the bone, so the shoulder and hip joins stay clean. |

Acting rules:

- One action per beat: anticipate (0.1–0.2 s), act fast (`snap`, 0.1–0.15 s), hold the reaction 0.4–0.8 s.
- Shock is a sequence, not a pose: jump back 40 px with arms up and eyes 1.5x, land with the knees absorbing (`hipDrop` 34), then crouch (`hipDrop` 80, lean 26, tremble). Keep the eyes visible after the crouch: drop the near arm to the knees when the figure peeks.
- Look-around: over the shoulder (`lookX` -1), then up, then at the camera on the line that matters.
- Never both arms in unison, never a perfectly mirrored pose.
- No principal picture holds still for more than 2.5 s. Breathing alone does not count, and neither does a camera move or a text entrance on its own: give the figure an action.
- Turning around is a 0.16 s flip through edge-on; author a blink on it.

## 5. Sound and captions

**Voice.** On varg: `check_balance`, then `search_voices` with an intent such as "calm, tense, low male English narrator for a dark survival short", then `estimate_cost`, then one `generate_speech`. The example used "Adam" (Deep English Story Voice, varg voice id `preset_610bdb815cd5`) on `eleven_v3`: 354 characters, 60 words, **$0.04 (4 credits)**, one take. Download the file, then shorten the pauses: `bun tighten-pauses.mjs voice.mp3 assets/audio/voice.wav` (pauses over 0.25 s become 0.2 s; speech is never time-stretched).

**Word timings, free.** `bunx hyperframes transcribe assets/audio/voice.wav --model small.en --language en` runs whisper.cpp locally (2 s for 22 s of voice) and writes `assets/audio/transcript.json`. Read it: the example's ASR wrote "twelve-oh-one" as "1201". Do not pay for transcription.

**Captions.** `bun captions.mjs assets/audio/transcript.json <voice start> <words already on a title> <ending card start>` writes the groups into `index.html`: at most 3 words, one line of at most 18 characters (font shrinks from 74 px for long lines), a break at punctuation or a pause of 0.15 s or more, the active word in yellow. Place them under the rules and above the figure's head, inside the 168–1330 px band of a 1080x1920 frame. Hide them while the ending card shows the same words.

**Ambience and effects.** One bed plus 2–4 effects, each on a visible cause. `bun sfx.mjs assets/audio 25` synthesizes everything with ffmpeg, so nothing needs a licence: a sea, wind and lamp-motor bed normalised to -30 LUFS; a low thud for the title stamp; a door knock in three takes at different pitch; an electrical buzz gated by the same on/off table as the lamp flicker in the picture; a whoosh that peaks 0.8 s after it starts. If you use a library sound instead, keep its URL and licence (CC0 or the library's own terms) next to the file. Levels in the example: voice 1.0, bed 1.0, knocks 0.65–0.8, thud 0.45–0.55, buzz 0.3, whoosh 0.4; the mix measured -13.5 LUFS integrated, -1.0 dBTP true peak, no clipping (measured with `hyperframes audio`, not listened to).

## 6. Build it in HyperFrames

1. `bunx hyperframes init my-reel --resolution portrait --non-interactive --skip-transcribe` (or `npx`).
2. Copy `assets/example/` into it (`index.html`, `rig.js`, `captions.mjs`, `sfx.mjs`, `tighten-pauses.mjs`), or start from `assets/stickman-rig.html` as `index.html` for a bare stage. The example has no media: make `assets/audio/` with steps 3 and 4.
3. Voice, pauses, transcript, captions (section 5).
4. `bun sfx.mjs assets/audio <film seconds + 1>`; place each effect so its peak lands one frame after its picture.
5. Write the film in `index.html`:
   - One clock. A proxy object with a setter, tweened from 0 to the duration on the paused GSAP timeline, redraws the set and the rig for that exact time. Nothing reads a clock, `Math.random` or the previous frame.
   - The set is SVG inside a camera group (`translate · scale · translate` from three keyed channels `cx`, `cy`, `cs`). Draw it in code: walls, a window, a door, a lamp. A world wider than the frame lets the camera pan between places.
   - The figure: `Stickman.create(group, { scale, ground, blinks })`, a `Stickman.track(...)` of pose keys written as `P.move(start, duration, { channel: value }, ease)` on the voice's word times, and `Stickman.draw(fig, P, t)` inside the clock.
   - HUD, rules, captions and the ending card are HTML clips animated on the same timeline. Rules land on the word "Rule"; the clock flips on its word.
6. `bunx hyperframes lint`, then `bunx hyperframes check --json --no-cache`. Use `bunx hyperframes`, not `bunx --bun hyperframes`: under the Bun runtime `check` printed nothing on repeat runs.
7. Look: `bunx hyperframes snapshot --at <12 beat times> --no-end`, then `--range <walk start>,<walk end> --frames 8` for the walk, and zoomed crops of the figure at the reaction poses.
8. `bunx hyperframes render --quality delivery --output out.mp4`, then `ffprobe` (duration equals the root `data-duration`), `bunx hyperframes audio out.mp4 --json`, and a contact sheet decoded from the MP4.

Two traps the example hit:

- **Caption hard-kill.** Under a clip host, GSAP records the inherited `visibility: hidden` as the start value, so `tl.set(group, { visibility: "hidden" }, end)` leaves every group hidden after a backward seek. Kill caption groups with `opacity: 0` only.
- **Two-line captions** collide with things drawn in the set (the example's ship numbers). Keep one line per group.

The example is one `index.html` on purpose (one clock drives the rig and the set), so `lint` warns that the scenes are not sub-compositions; that warning is expected.

## 7. Checks before delivery

- [ ] Frame 0 is the hook: the DAY title or the POV line plus the figure mid-action, never black.
- [ ] Limbs attached in every sampled frame, bones the same length, feet on the ground except in a jump, no foot sliding during the walk (8-frame strip).
- [ ] Walk, breathing idle, a head turn, one reaction (shock or crouch) and blinks all appear; nothing principal holds for more than 2.5 s.
- [ ] Rules appear one at a time on their words; the clock or DAY counter changes on its word.
- [ ] Captions one line, word-timed, inside 168–1330 px, nothing readable under the right-hand action rail.
- [ ] The ending: "1:" and "2:" on screen with the spoken options, "FOLLOW FOR DAY 2" for at least 2 s.
- [ ] Sound present, effects on their pictures, about -14 LUFS, true peak at or under -1 dBTP; say it was measured, not heard.
- [ ] `check` has no errors; duration and size match (1080x1920, 30 fps).

## 8. Costs

| Item | Measured |
|---|---|
| Voice, 60 words, ElevenLabs v3 on varg | $0.04 (4 credits), one take |
| Word timings (local whisper.cpp) | free, 2 s |
| Sound effects and ambience (ffmpeg) | free |
| Render, 24.3 s at 1080x1920, 729 frames | free, 17.3 s on an Apple M1 Pro (hardware GPU, screenshot capture) |
| Total for the example | $0.04 (4 credits) |

## 9. Other routes

- **kaomei/stickman-video-director** ([GitHub](https://github.com/kaomei/stickman-video-director), MIT, by [@CrazyKaomei](https://x.com/CrazyKaomei), about 5,900 stars in November 2026). Director mode writes a treatment, then one prompt per roughly 10-second clip for Google Flow (Gemini Omni Flash), Veo, Kling, Runway or Luma; you generate and edit the clips yourself. Autopilot renders a narrated, captioned MP4 locally (Node 20+, FFmpeg) after a 20-second sample is approved; the author recommends Codex. Eleven visual styles. Install by pasting the repo URL into your agent with "Install this Skill for me"; the installed skill is called `directing-stickman-videos`. Use it when the person wants generated clips or one of its styles.
- **Generated 2.5D look on varg.** A character sheet and set stills with `gpt_image_2_6` (estimate on 2026-11-13: up to $0.06 (6 credits) per 9:16 image), approved first, then animate with `kling_v4` (estimate on the same day: up to $0.79 (79 credits) for a 5 s 9:16 clip, priced as text-to-video; price the image-to-video call itself before the batch; `kling_v4_flash` for drafts). Run `estimate_cost` before each batch. The honest caveat: video models drift on stick figures. Limbs multiply or thicken, heads detach, hair and clothes appear, and two shots rarely match. Keep shots to 5 s, reuse the same reference, judge every take, and keep anything that must stay jointed (a walk, a fight, a pose that carries the joke) in code. A hybrid works: generated background stills under the code figure.

## 10. What not to do

- Do not copy a named channel's characters, names, catchphrases, signature outfit or episode premises. Make your own figure and your own premise; "inspired by a format" is fine, a look-alike is not.
- Do not use real people's names, faces or cloned voices; use generic stand-ins in fights and contrasts, not real logos.
- Label AI content where the platform asks for it (TikTok's AI-generated label, YouTube's altered or synthetic content disclosure for realistic material), and write "AI voice" in the caption when the narrator is synthetic.
- Do not present invented stories as true, and do not invent facts in explainers. Keep survival stories PG: tension, not gore.
- Do not promise views or income: the numbers in the posts above are the posters' claims.
- Do not use `Math.random`, `Date.now`, timers or the previous frame as state; do not swap images for poses; do not stretch bones; do not put text below 1330 px on 9:16.

## Sources

- X research, collected 2026-11-13: the posts linked in section 2, the stickman-video-director launch and updates by [@CrazyKaomei](https://x.com/CrazyKaomei/status/2084217266703393186), and user questions under them ([limbs and monotone motion](https://x.com/GazunH26262/status/2121123319143633304), [two-bone IK arms and lip sync by loudness](https://x.com/tebet007/status/2116324211002401064)).
- kaomei/stickman-video-director: `SKILL.md` (Director pacing of about 20–25 voice words per 10 s clip, a visual change every 2–3 s) and `references/autopilot.md` (no principal-picture inactivity over 2.5 s; camera moves or text entrances alone do not count as animation).
- HyperFrames CLI 0.9.41 documentation (`hyperframes`, `hyperframes-core`, `hyperframes-cli` skills).
- Measured on the example: voice job on varg on `eleven_v3` for $0.04 (4 credits), whisper.cpp `small.en`, ffmpeg loudness, HyperFrames render log.
