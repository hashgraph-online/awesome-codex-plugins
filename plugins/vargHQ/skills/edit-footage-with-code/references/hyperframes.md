# Editing footage in HyperFrames

Read the official `hyperframes` and `hyperframes-core` skills for the composition contract; this page only covers what changes when real footage is the spine. If they are missing: `npx hyperframes skills`.

HyperFrames' strength in public reports is the motion and caption layer, not judging footage (@sara_nambiar, @two3pro, @darrrragh). So cut first, then composite. Script-based editing and auto speech cleanup in the HyperFrames desktop app shipped on 2026-10-23, with almost no independent reports yet, so treat it as a fast way for a person to edit by words and verify its cuts the same way.

## Put the cut in a project

```bash
npx hyperframes init film --non-interactive --skip-skills && cd film && mkdir -p assets
# Keyframes more than about 1 s apart freeze on seek, so the cut carries one keyframe per second
ffmpeg -i ../edit/acut.mp4 -c:v libx264 -crf 16 -g 30 -pix_fmt yuv420p -c:a copy assets/acut.mp4
```

There are two ways to carry the cut. Pick one:

| | One file | Many clips |
|---|---|---|
| What | `assets/acut.mp4` from `cut.sh` as a single `<video>` | `edit/clips.html`, one `<video>` per segment on the original take |
| Good for | Overlays on a locked cut. Fast and simple. **The default** | A person who will keep trimming in the desktop app |
| Timing | The cut's own transcript is the clock | Same, after every change |

In a new project, keep the root's `data-duration` equal to the cut's length. A transcript's last word can run past the media and end the render in black, so clamp to the ffprobe length.

```html
<video id="spine" class="clip" src="assets/acut.mp4" data-start="0" data-duration="63.933"
       data-track-index="0" playsinline data-has-audio="true"
       style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover"></video>
```

## The clock

```bash
npx hyperframes transcribe assets/acut.mp4 -d . --model small.en --json   # or --model small --language <code>
```

`small.en` translates non-English speech into English, so name the language for anything else. Read the transcript before using it. Whisper invents "Thank you." over silence, so drop words that begin inside a final silence.

Reach for `hyperframes transcribe --engine parakeet` (after `hyperframes models install parakeet`) when local accuracy matters, or `--engine heygen` for speaker labels, which bills their plan.

Look up every cue's time in this file. Never estimate from sentence order, which is where most reports of drifting graphics come from (@bozhou_ai). Match by word position, not by text, or a repeated word takes the wrong time.

## Layers, in order

1. **Spine:** the cut, track 0, sound on the video.
2. **Punch-ins:** a transform on a wrapper around the spine, set instantly on a word. See `hyperframes-keyframes`.
3. **Cards and lower thirds:** each one a sub-composition with a **transparent root**, or it hides the speaker. See `overlays.md` in the `hyperframes` skill for placement rectangles and picture-in-picture sizes.
4. **Captions:** one host with `data-track-kind="captions"`. Find styles with `npx hyperframes catalog --tag caption-style --json`. Before placing them, scan a 1 fps contact sheet: footage may already have burned-in subtitles mid-clip.
5. **Sound:** music and effects as separate `<audio>` with ids. An `<audio>` with no id is left out of the mix. Mix with `hyperframes-audio`; source with `media-use`.

Before hand-building any named visual, check the registry of about 450 blocks: `npx hyperframes catalog --json`, then `npx hyperframes add <name>`. A tester reported that `add` overwrites the system clipboard with a code snippet, so warn the person if they are working at that machine.

Grades, grain and blur on footage go through `npx hyperframes media-treatment`, never CSS filters.

## Check it

```bash
npx hyperframes check --json                     # the contract: fix errors, weigh warnings
npx hyperframes snapshot --at 1.2,8.4,20.0       # stills at the times you changed
npx hyperframes audio --json                     # where sounds land: onsets, loudness, silence
npx hyperframes render --output out.mp4
python3 <skill>/scripts/qa_cut.py out.mp4 --heard heard.json --intended edit/intended.json
```

Do not pass `--edl` to `qa_cut.py` once the render's length differs from the cut's.

`check` passing is not approval. One user's version passed with 0 errors while a frame scan found 56 stretches with nothing in the picture (@heygalatea). Look at the frames.

One tester measured a render's AAC sitting 21.4 ms early against the master, one AAC frame. For a mix you already mastered, mux it over the render with `ffmpeg -i out.mp4 -i master.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k final.mp4`.

Fix small things by hand or in the desktop app: a chat round trip for a one-word caption change costs tokens and time (HeyGen, users). Before changing a project someone else touched: `npx hyperframes history --since mine --who <you>`.

## Known limits

- Sound is the agreed weak spot (@nateherk; one builder self-rates music at 35%). A person chooses the music.
- A heavy motion-graphics look is its own failure, the "agentic look" (@EnriTarta). Cut overlays before adding them.
- `hyperframes-audio`'s free music fallback can land on a model with a non-commercial license. See the `video-asset-sources` skill.
