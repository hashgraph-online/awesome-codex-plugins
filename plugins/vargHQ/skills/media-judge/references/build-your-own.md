# How to build a judge for AI-made video

This is how to build a judge that finds the facts in a video, image or track an agent made. It covers launch films, cinematics, short drama, reels and ads. Every snippet here ran on test clips on 2026-11-03 and lives in `references/recipes/`. The finished version is `scripts/judge.py`.

## The idea in three lines

1. **Code finds the moment.** Read every frame and every sample. Output a time, a number and a picture.
2. **Fresh eyes read only that moment.** A model that did not make the video answers narrow questions about those frames.
3. **The verdict is a count.** Blockers, major flags, minor flags. Rank on the counts. Never blend them into one mark.

You measure and do not grade because model judges fail in exactly the way you would hope they wouldn't. On temporal glitches, 12 vision models topped out at 54.1% accuracy. Claude Opus caught 17.5%, and Gemini 3 Flash called about 87% of clean clips glitchy ([TempGlitch](https://arxiv.org/abs/2605.21443), gameplay clips). Going from 1 to 5 fps barely helped. And nobody on X is measuring: in 4,078 posts, 7 of the 12 failures below had no described test at all.

## What you are testing

| # | Failure | Code gives you | Eyes settle |
|---|---|---|---|
| | Broken frames | every black, frozen, repeated and glitch frame | nothing, unless it might be deliberate |
| 1 | Everything is the same size | block heights, biggest over second | which element should be biggest |
| 2 | Nothing leads the eye | attention peaks and their share | whether the peak is on the subject |
| 3 | Too much on screen | words at once, edge density, reading time, contrast, safe zone | can you read the product from the frame alone |
| 4 | Motion has no cause | moves that start with nothing near them | what causes each one |
| 5 | Graphics pinned to the screen | regions still while the scene moves | should it be pinned |
| 6 | Labels slide off | distance between label and surroundings | what it points at |
| 7 | Bands and blocks after upload | CAMBI before and after an encode | where the bands are |
| 8 | Numbers jiggle | shake of a digit that keeps its value | nothing |
| 9 | Face, outfit or light changed | identity score, torso colour, side light | whether the story asks for it |
| 10 | Sound after the cut | signed offset at each cut, against chance | whether a late sound is a choice |
| 11 | Spelling | candidate words with crops | typo or misread |
| 12 | Looks like the template | distance to each, and the margin | three things only this brief could produce |

## Step 1: Broken frames with OpenCV

Read every frame at a small size and keep only numbers. Three facts catch most faults:

- **Black:** dark and flat, with light on one side. A fade has no sudden edge.
- **Glitch:** the frame differs from both neighbours, and the neighbours match each other.
- **Frozen:** nothing moves for 0.4 s, with motion before and after.

```python
cap = cv2.VideoCapture(path)
frames = []
while True:
    ok, frame = cap.read()
    if not ok:
        break
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    frames.append(cv2.resize(gray, (320, 180), interpolation=cv2.INTER_AREA).astype(np.float32))
g = np.stack(frames)
step = np.abs(g[1:] - g[:-1]).mean(axis=(1, 2))   # change from one frame to the next
skip = np.abs(g[2:] - g[:-2]).mean(axis=(1, 2))   # change across one frame

for i in range(1, len(g) - 1):
    local = np.median(step[max(0, i - 12):i + 12])
    a, b = step[i - 1], step[i]
    if min(a, b) > max(6, 4 * local) and skip[i - 1] < 0.35 * min(a, b):
        print(f"{i / fps:6.2f}s glitch frame (jump {a:.1f} then {b:.1f}, neighbours differ by {skip[i - 1]:.1f})")
```

On a planted one-frame glitch at 3.00 s, that prints `3.00s glitch frame (jump 27.6 then 27.7, neighbours differ by 3.0)`. Full script: `recipes/broken_frames.py`.

If you want the cheap version, ffmpeg's filters work, but **they default to 2 s, so a one-frame fault passes**. Lower them:

```bash
ffmpeg -hide_banner -nostdin -i film.mp4 \
  -vf "blackdetect=d=0.04:pix_th=0.10:pic_th=0.98,freezedetect=n=-60dB:d=0.4,scdet=t=10,metadata=print:key=lavfi.scd.time:file=-" \
  -af "silencedetect=n=-45dB:d=0.1,ebur128=peak=true:framelog=quiet" \
  -f null - 2>&1 | grep -E "black_start|freeze_start|silence_start|lavfi.scd.time|I:  |Peak:"
```

## Step 2: Build the test bench before anything else

**A check that stops firing looks exactly like a clean video.** So plant faults. Take a real clip, make one copy per defect with the defect at a known time, keep untouched copies as controls, and run your judge on all of them.

`tests/make_fixtures.py` does this and `tests/run_bench.py` scores it. A catch only counts if the event lands on the planted moment. Use real footage, not synthetic gradients, because real footage is what gives you false flags. Our first full run caught 3 of 29, because one crash in the face code took most runs down, and only a bench shows you that. Add a fixture each time a person finds something the judge missed.

**Then keep some footage out.** Tuned on one set of clips we reached 25 of 25. On footage the thresholds never saw, 18 of 22, and 6 of 8 controls clean. The second number is the real one, so don't tune on it. Its misses are worth reading: a planted freeze on a still has nothing to show, and a piece with 2 cuts can't show a habit.

**Then run it on real work and check every flag by eye.** Planted defects never showed us these, and each one was a false flag at first:

- A dim terminal with faint text reads as a black frame. Check the brightest pixels too.
- A fade to white reads as five one-frame shots. Brightness that only climbs is one transition.
- Letterbox bars and the centre of a slow push-in look "pinned". Mask the bars and ask how far the camera says that spot should have moved.
- OCR drops spaces ("makea") and misreads small interface text. Skip addresses and code, and split long words into known ones.
- A pause in speech reads as a drop-out. A real drop-out has a hard edge on both sides.
- A steady pad beating against itself reads as a stream of hits. Scale the onset floor on the strongest events.
- Our beat tracker reported 120 BPM and placed beats 0.33 s apart, which made a film on a 0.5 s grid look off the beat. Ask whether cuts lock to the tempo grid, which a phase error can't hide.

## Step 3: Banding after upload

Nothing else on the list needs this test as much. Your source can be clean and the upload broken, and VMAF cannot see it (it scored 0.088 against viewers where CAMBI scored -0.923). So encode at the platform's bitrate, and measure CAMBI on both copies.

```bash
ffmpeg -y -v error -i in.mp4 -map 0:v:0 -vf "scale=1280:720,format=yuv420p" \
  -c:v libx264 -preset veryfast -b:v 2048k -maxrate 3072k -bufsize 4096k upload.mp4
for f in in.mp4 upload.mp4; do
  ffmpeg -v error -i "$f" -i in.mp4 -lavfi \
    "[0:v]scale=1280:720,format=yuv420p[a];[1:v]scale=1280:720,format=yuv420p[b];[a][b]libvmaf=feature=name=cambi:log_fmt=json:log_path=cambi.json:n_subsample=3" \
    -f null -
done
```

A dark gradient with dither in it read **mean 0.35 in the source and 17.80 after the encode**. Netflix's scale runs from 0 for none, through about 5 where it starts to annoy, to 24 at the worst seen. 2048K at 1280x720 comes from X's table. Nobody publishes delivered encoders, so this is a simulation, and one private upload and re-download beats it. To fix it, the grain has to survive the delivered encode, so add stronger grain or lift the blacks.

## Step 4: Everything that is text

Run OCR (RapidOCR is good on CPU) at 2 fps plus each shot's middle, and join the results into tracks over time. From tracks you get:

- **Spelling:** check each word against a dictionary and your allow list. A word misread in one frame and read right in others is OCR noise. These are candidates: read each crop before calling it a typo. If you have the script, diff against it, which is the stronger test.
- **Load:** words on screen at once.
- **Reading time:** characters per second, against Netflix's 20 cps subtitle limit.
- **Contrast:** split the text box into two tones and compute the WCAG ratio. 3:1 for large text.
- **Safe zones:** text boxes against each platform's interface. Reels is officially 14% top, 35% bottom, 6% sides.
- **Same size:** block heights, with stacked lines of one size joined into one block so a paragraph doesn't count as many items.

The default OCR model invents lone Chinese glyphs in dark textures. Drop one-character results and anything with low confidence, or your spelling check will fill with noise.

## Step 5: Numbers that jiggle

We found no tool and no research on this, and no post on X in our sample. The test is simple. **A digit that keeps its value must not move while its neighbours count.** Track each digit with template matching while it keeps matching itself, and measure its shake.

```python
for x, y, w, h in digits:
    moves, px, held = [], float(x), 0
    for a, b in zip(crops, crops[1:]):
        left = int(round(px))
        tpl = a[y:y + h, left:left + w]
        win = b[y:y + h, max(left - 20, 0):left + w + 20]
        if tpl.shape != (h, w) or win.shape[1] < w:
            break
        res = cv2.matchTemplate(win, tpl, cv2.TM_CCOEFF_NORMED)
        _, score, _, loc = cv2.minMaxLoc(res)
        if score >= 0.92:                       # same digit as last frame
            dx = loc[0] + max(left - 20, 0) - left
            moves.append(dx)
            px += dx
            held += 1
    if held >= 0.25 * (len(crops) - 1):
        print(f"digit at x={x}: held {held} frames, shake {np.std(moves) / h * 100:.2f}% of its height")
```

Tabular figures read `shake 0.00%`. Proportional figures read `shake 3.17%`. Our first version compared glyph centres across all frames, and it could not separate the two, because the digits that are changing add noise. Watching only the digit that isn't changing fixed it.

## Step 6: Attention, load and scale

No published threshold exists for any of these, so report them and let eyes decide. A contrast and colour map with a motion term is free and fast, but it is far weaker than learned models: on video ads, classic saliency scores CC 0.07 to 0.09 where ViNet-S and ViASNet score 0.56 to 0.57. If a decision rests on it, use UNISAL or DeepGaze IIE.

Count the peaks, the top peak's share and the biggest blob over the second. Overlay the map on the frame so eyes can answer one question: does the top peak sit on the subject? **Never ask a vision LLM where people look.** They scored CC 0.34 to 0.41 against real gaze. For clutter, edge density is as good as costlier measures, though it only explains about 28% of search time.

## Step 7: Motion, pinned graphics and labels

Separate the camera from everything else first. Fit one affine transform to tracked corners with RANSAC. Whatever it explains is the camera and the rest is object motion. Then:

**Motion with no cause.** List each move that starts, meaning a rise above what the shot was already doing, and check for a sound or text change within 0.3 s. Code can only find candidates. A hand or a hit in the picture is invisible to it, so eyes name the cause or write "no visible cause". Separately, count the shots with a slow, constant move, because a slow drift on every shot is how an unmotivated move looks in numbers.

**Pinned graphics.** Find what stays still on the glass while the scene moves behind it. Use the inter-decile spread rather than the standard deviation, so one bad frame can't fake a moving scene. We found no other tool for this.

```python
spread = (np.percentile(st, 90, axis=0) - np.percentile(st, 10, axis=0)) / 2.56
detail = cv2.GaussianBlur(np.abs(cv2.Laplacian(st.mean(axis=0), cv2.CV_32F)), (0, 0), 3)
mask = ((spread < 2.5) & (detail > 4)).astype(np.uint8)
```

If the scene doesn't move, you can't test this. Report "not tested", never "clear". Captions and logos are supposed to be pinned, so eyes check the role against the brief.

**Labels sliding off.** Track points on the label and points on the world around it, and add up how far they part. A label that slid read 260.8 px apart, and a locked one read 0.0. If you render with HyperFrames or Remotion, you know the anchor, so pass it. That is the real test. Without one, a floating label over a moving scene also shows drift.

## Step 8: Face, outfit, light

OpenCV ships YuNet to find faces and SFace to compare them, and they are free for commercial use, unlike InsightFace's models. Cosine 0.363 or more means the same person. A swapped face read -0.012 and the same person read 0.742.

```python
det = cv2.FaceDetectorYN.create(yunet_path, "", (320, 320), 0.7, 0.3, 50)
rec = cv2.FaceRecognizerSF.create(sface_path, "")

def embed(img):
    det.setInputSize((img.shape[1], img.shape[0]))
    _, faces = det.detect(img)
    face = max(faces, key=lambda r: r[2])
    return rec.feature(rec.alignCrop(img, face))

cos = rec.match(embed(a), embed(b), cv2.FaceRecognizerSF_FR_COSINE)
```

That threshold was set on real faces. AI faces drift inside a single clip (ArcFace distance: real video 0.084, AI video 0.17 to 0.48), so compare across shots against the same person's spread within a shot. For outfit, compare the median colour below the chin in CIEDE2000. For light, compare face lightness and left cheek minus right cheek. No validated method exists for light direction, so these only tell eyes where to look.

## Step 9: Sound on the cut

Find onsets with spectral flux and take a signed offset per cut. Then run the part most people skip: **shift the cuts at random and count how often they land on sound by chance.** Without that, any busy track looks in sync.

```python
hit = lambda cs: np.mean([np.min(np.abs(onsets - c)) <= 0.05 for c in cs])
sims = [hit((cuts + rng.uniform(0, dur)) % dur) for _ in range(400)]
print(f"on the cut: {hit(cuts):.0%}, by chance {np.mean(sims):.0%}, z {(hit(cuts) - np.mean(sims)) / np.std(sims):+.1f}")
```

Hits on the cut read `on the cut: 100%, by chance 4%, z +5.6`. Hits planted 160 ms late read `+148 ms LATE` at every cut. Flag a habit and not a single cut, because one cut with an unrelated noise nearby proves nothing. BT.1359's numbers (late 125 ms, early 45 ms) are for lip sync, and nothing published covers cuts. The tool measured about 10 ms early on perfectly placed hits, so don't read single-digit precision into it.

## Step 10: Voice and music

**Voice.** Use ebur128 for loudness and true peak, count runs of clipped samples, find drop-outs, then diff a Whisper transcript against the script. No platform publishes a loudness target: -14 LUFS is convention, and YouTube's number comes from a third party's measurement. Whisper repairs mistakes (in one learner-speech study it kept a common grammar error only 58.7% of the time) and sometimes invents words, so it hears what it expects. On a test line, the right script read 0.0 word error, and a wrong one read 0.188 and named each changed word (`script 'movie' heard 'film'`). Decode the audio yourself and pass samples to `faster-whisper`, because a PyAV version clash can break its own decoder. Mispronounced names need a person or an audio model.

**Music.** Only run a beat test when the pulse is clear, because a tracker invents a metronome on calm music. Measure cuts on beats within 70 ms against the same shift test. Report it and don't gate on it, since editing is elastic. Also check for an abrupt ending and a hard spectral cutoff. Skip AI music detectors: their miss rates reach 93.6% after a pitch or time change, and they say nothing about quality.

## Step 11: Images

Use the same code on one frame: text, spelling, contrast, attention, load, reference distance. Laplacian variance is a weak measure of sharpness, and one repo saw it score magenta garbage 62.7. Hands and limbs need eyes, but ask the model to name every object rather than to check the hands.

## Step 12: Compare with the reference

Align shots first, then compare within each pair. A flat frame-by-frame diff is useless on a recreation.

1. **Align:** dynamic time warping over shots, using a blended picture distance.
2. **Measure per pair:** structure, palette (CIEDE2000), composition, texture, tone, cut offset.
3. **Measure the whole:** shots, average shot length, shot-length variation, motion level.
4. **Show it:** a sheet with ours next to theirs, worst pairs first. Numbers say where it differs. Eyes say whether that matters.

**Looks like the template?** Measure the distance to the references and to the template, and take `margin = distance to template - distance to references`. Above 0 means closer to the references. The idea is simple, and no paper has tested it. For stronger style models, use [CSD](https://arxiv.org/abs/2404.01292) and [DreamSim](https://arxiv.org/abs/2306.09344), and skip Gram matrices.

Also keep a list of named defaults you ban, the way HyperFrames does, and add to it whenever you catch a new one.

## Step 13: The vision pass

- **Fresh context.** The judge hasn't seen the prompts. GPT-4 preferred its own output 0.705 and 0.912 of the time on tasks where people saw equal quality.
- **Only the window.** Code flags the moment, and the model sees those frames. Whole-video review is where the near-chance numbers come from.
- **Describe, then what is unusual, never what is wrong.** On GlitchBench that wording moved results from 29.5% to 57.2%, and "describe" reached 64.9%. Asking it to "double check" adds 2.70 points.
- **Yes or no with a timestamp per rule.** No score out of 10. People on X report that scales drift and can be negotiated.
- **Prove you looked.** Quote something visible in the frame, or the answer is dropped.
- **A place and a fix for every finding,** and cap it at two or three passes.
- **Put the order in code.** Agents skip review that lives only in instructions.

`references/eyes.md` has the question for each failure. `references/llm-judge.md` has the bias numbers and how to write criteria. The short version: ask for what it sees and let code decide. Our judge, asked "which is better?", picked the take shown second 75% of the time, and repeated itself 90% of the time while doing it.

## Step 14: Rank

Use facts as gates and rank on counts: blockers, then major, then minor, then the reference margin. If takes tie on facts, judge each take alone with observations and let code decide, with a win needing a margin of 2. Still tied? Pairs: hide the names, run both orders and treat a flip as a tie. For many takes, gate first, compare by Swiss pairs and fit Bradley-Terry. `references/ranking.md` has the details and the ways this gets gamed.

## Step 15: Reverse engineer a finished piece

Run the same tools on someone else's video, and split the fields honestly:

| Measured by code | Estimated by a model | Cannot be recovered |
|---|---|---|
| Cuts, shot lengths, cuts per 10 s | Hook type | Prompt, model, seed |
| Camera move and speed, motion, holds | Lens, light type and direction | Reference images and revisions |
| Palette, brightness curve | Persona, angle, offer, message order | Spend and conversion |
| Loudness, tempo, onsets, words with timestamps | What a shape reads as | Whether the structure caused the result |
| Text boxes and on-screen time, faces | Prop and wardrobe continuity | |

ShotBench puts the best model under 60% on cinematography terms: lens 48.9%, light 49.4%, camera move 48.9%. So measure the camera move and mark the lens as an estimate. Then challenge your clone by running the comparison in Step 12 against the original.

## What it still can't do

- Tell you a video is good. Code proves broken or correct. As one creator put it, a ten-dimension score was great while the video looked like a slide deck.
- Hear. Mispronunciation, flat delivery and masking need a person or an audio model.
- Know intent. A pinned graphic, a costume change or a hard cut might all be choices, so the brief decides.
- Reproduce the real encoder.

Only a few thresholds here are published. Most were set by planting defects in our own footage, so calibrate them on yours and keep labelled pass and fail examples beside each one. Keep some checks out of any automatic loop, and look at a sample yourself every round.
