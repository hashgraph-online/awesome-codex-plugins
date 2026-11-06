# Every check

`Status` says how far to trust the threshold. **Published** means a source states it. **Convention** means common practice, no authority.
**Fixtures** means we set it on planted defects in `tests/`, so calibrate it on your own references. All thresholds live in `scripts/thresholds.json`.

## Broken frames

| Check | How it works | Threshold (status) | False flags, and limits |
|---|---|---|---|
| `spec` | ffprobe: codec, pixel format, size, odd dimensions, frame timing | yuv420p, H.264/HEVC/AV1/VP9, `--size` (convention) | A deliberate 10-bit master |
| `decode_errors` | Full decode, stderr collected | Any (convention) | Harmless warnings on odd containers |
| `black_frames` | Mean luma under 16, std under 6, brightest pixels under 40, with light on one side | Run at most 0.25 s (fixtures) | Longer black is reported as a choice, not a flag. Dim screens with text are not black |
| `frozen_frames` | Frame change under 0.06 for 0.4 s, with motion both sides | (fixtures) | A deliberate hold on a move. Compare with the brief |
| `repeated_frames` | A frame with almost no change while the frames around it move, over 2% of moving frames | Under 5% of the motion around it (fixtures). An encoder never makes a repeat quite identical | Screen recordings and 12 fps animation really do repeat |
| `glitch_frames` | Differs from both neighbours, which match each other; 8x8 cell test for local damage | Jump over 6 and 4x local level, neighbours under 0.35 of it (fixtures) | A real one-frame flash used as an effect |
| `seam_shots` | Shot shorter than 0.12 s. A run of cut frames that only climb or only fall in brightness is one flash or fade, not many shots | (fixtures) | A very fast montage |
| `flicker` | Luma reversals per second inside a shot; robust local shimmer on an 8x8 grid | 4 per s; local 2.5 (fixtures) | Strobing lights in the scene |
| `soft_shot` | Laplacian sharpness per shot against the film's median | Under 25% of the median (fixtures) | Tracks framing, so a smooth wide shot reads soft. One repo saw magenta garbage score 62.7 |
| `flash_safety` | Opposing changes of 10% relative luminance | Over 3 flashes in 1 s ([published](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html), WCAG 2.3.1) | Whole-frame average only, so a small area counts less. ITU BT.1702 adds a 25% area rule and red flashes |

Trap: ffmpeg's `blackdetect`, `freezedetect` and `silencedetect` default to 2 s, so a one-frame fault passes unless you lower them.

## 1. Everything is the same size

| Check | How it works | Threshold (status) | False flags, and limits |
|---|---|---|---|
| `text_scale` | OCR blocks in each frame, largest block height over smallest. Stacked lines of one size count as one block | Under 1.3 in half of multi-block frames (fixtures) | Text only. A clean two-column list |
| `object_scale` | Attention blobs, biggest area over second | Under 1.25 with 4+ blobs (fixtures) | Weak on textured scenes, and fires often on real footage. Open the sheet |

No validated hierarchy metric exists. Eyes settle it: name the largest and second largest element.

## 2. Nothing leads the eye

`leads_the_eye` builds a map from colour and contrast, a spectral residual and motion, then counts peaks and the top peak's share of attention. It flags 8+ peaks with under 0.3 in the top one (fixtures). Clean real footage reached 7 peaks. It also writes `attention_sheet.jpg`.

This is far weaker than learned models: on video ads, classic saliency scores CC 0.07 to 0.09 where [ViNet-S and ViASNet score 0.56 to 0.57](https://arxiv.org/abs/2605.29302). Use it as a report. If a decision rests on it, run UNISAL or DeepGaze IIE. Never ask a vision LLM where people look.

## 3. Too much on screen

| Check | How it works | Threshold (status) | False flags, and limits |
|---|---|---|---|
| `text_load` | Words on screen at once | 18 (fixtures) | A deliberate UI screen. Say so in the brief |
| `reading_time` | Characters per second a line stays up, with OCR at 2 fps taken at its most generous | 20 cps ([convention](https://backlothelp.netflix.com/hc/en-us/articles/115000239632), Netflix subtitle limit) | Scrolling text |
| `text_contrast` | Two-tone split of the text box, WCAG ratio | 3:1 ([published](https://www.w3.org/TR/WCAG22/#contrast-minimum), large text) | Busy background behind the box |
| `text_size_floor` | Line height against the short side | 2.6% (convention, HyperFrames) | Small print required by law |
| `safe_zone` | Text boxes against the platform's interface | Reels 14/35/6% ([official](https://www.facebook.com/business/ads-guide/update/video/instagram-reels)). TikTok 240/660/120 px and Shorts 288/672/48/192 px on 1080x1920 are third-party readings | Interfaces change |
| `frame_load` | Edge density and blob count | 0.16 edges, 60 blobs (fixtures) | Edge density only explains about 28% of search time, so treat it as a report |

## 4. Motion has no cause

| Check | How it works | Threshold (status) | False flags, and limits |
|---|---|---|---|
| `motion_cause` | Global affine fit separates camera from objects. A start is a rise above the shot's own level. It lists starts with no sound within 0.3 s and no text change within 0.6 s | Rise over 1.0 object or 1.5 px camera, and over the shot's level (fixtures) | Only finds candidates. A cause in the picture (a hand, a hit) is invisible to this. Eyes decide |
| `constant_drift` | Share of shots with a slow, steady camera move | 60% of shots (fixtures) | A deliberate slow push throughout |
| `camera_shake` | High-pass of the camera path | 2.5 px at 480 wide (fixtures) | Real handheld |

No paper validates this. Michotte's causality window (about 50 to 200 ms, gone by 0.5 s) comes from lab dots.

## 5. Graphics pinned to the screen

`pinned_graphics`: per-pixel inter-decile spread over the shot, so one bad frame cannot fake motion. It finds crisp regions that stay still while what surrounds them moves. A region only counts if the camera path says it should have travelled 6% of the width (the centre of a push-in stays put), and if it looks the same in every frame (a label passing over a smooth patch does not). Letterbox bars are masked. Wide lines and lines in the top or bottom third are "caption or title", and only the rest are flagged (fixtures). It still read keys on a keyboard as stuck during a slow push, so open the frame.

Only testable when the scene moves. On a locked-off shot it reports `info`, which means not tested. Whether a graphic should be pinned comes from the brief: subtitles and logo bugs should. No published method or threshold exists.

## 6. Labels slide off

`label_drift`: Lucas-Kanade tracks points on the label and on the world around it, and adds up how far they part. It flags over 1.5% of frame width (fixtures). With `--labels` you give the exact anchor from your render, which is the real test. Without it, the surroundings stand in for the target, so a label floating over a moving scene also shows drift, and it counts as minor.

`labels.json`: `[{"t0": 1.0, "t1": 3.0, "label_box": [x, y, w, h], "anchor_box": [x, y, w, h], "text": "Battery"}]`, in pixels at 480 wide.

## 7. Bands and blocks after upload

`upload_banding`: encodes a copy at the platform's rough bitrate, runs CAMBI on source and copy, and runs ffmpeg's `blockdetect`. It flags dark shots with upload CAMBI at 5 or more, and bright shots at 7.5 or more. It writes the source and copy side by side, plus both with shadows lifted.

- CAMBI: 0 none, about 5 starts to annoy, 24 the worst seen ([Netflix](https://github.com/Netflix/vmaf/blob/master/resource/doc/cambi.md)). SROCC -0.923 against viewers on Netflix's set, [0.71 on an independent one](https://arxiv.org/abs/2508.08700). VMAF scored 0.088 on the same test, so it cannot see banding. Do not use VMAF for this.
- X's table lists 1280x720 at 2048K, which is the default profile. The other profiles are guesses under their upload specs, because nobody publishes delivered ladders.
- Limit: it simulates the encoder. One private upload and a re-download is the real test.
- Fix: grain has to survive to the delivered encode. Dither before a lossy encode gets quantized away, so add stronger grain or lift the blacks.

## 8. Numbers jiggle

`counter_jiggle`: OCR finds a number whose value changes. Each digit is then tracked with template matching while it keeps matching itself. A digit that keeps its value must not move while its neighbours count. It reports that digit's shake as a percent of its height, and flags over 1% (fixtures), or OCR readings that go backwards.

Tabular figures read 0.00% and proportional figures read 3.17% on our fixtures. We found no research and no other tool. If you have the source, check `font-variant-numeric: tabular-nums` and that the font has the feature.

Limit: it needs a digit that holds for at least a quarter of the count. A counter whose every digit changes every frame reports `held_digits: 0`, which means not tested.

## 9. Face, outfit, light

| Check | How it works | Threshold (status) | False flags, and limits |
|---|---|---|---|
| `face_identity` | YuNet finds faces, SFace compares them within and across shots | Cosine 0.363 ([published](https://github.com/opencv/opencv/blob/4.x/samples/dnn/face_detect.py) for real faces) | AI faces drift within a clip (ArcFace distance: real 0.084, [AI 0.17 to 0.48](https://arxiv.org/abs/2505.11425)). A profile or a stylized face |
| `face_drift` | The same comparison between the start and end of one shot | Cosine 0.363 | A title drawn across a face reads the same as a morph. Open the pair |
| `outfit_change` | Median colour below the chin, CIEDE2000 between shots | 18 (fixtures) | A costume change in the story. Colour only, so a new garment of the same colour passes |
| `face_light_change` | Face lightness and left-minus-right cheek | 18 L*, 25 levels (fixtures) | A head turn moves it too |
| `light_between_shots` | Median colour per shot, CIEDE2000 | 15 with `--groups` (fixtures). Otherwise a report | Needs to know which shots share a scene |

InsightFace's models are not for commercial use, which is why this uses OpenCV's.

## 10. Sound after the cut

`sound_on_cut`: spectral-flux onsets and a signed offset per cut. It flags a habit, not one cut: the median strong offset is late past the threshold, or half the cuts miss and fewer than half land. It needs 3+ cuts with a sound near, so a piece with 2 cuts is not tested. A shift test compares cuts on sound against chance (`z`), which says whether the edit follows the sound at all.

Thresholds: [BT.1359](https://www.itu.int/dms_pubrec/itu-r/rec/bt/R-REC-BT.1359-1-199811-I!!MSW-E.doc) late 125 ms and early 45 ms (published, on lip sync and not on cuts). No lag threshold specific to cuts exists. A planted 160 ms read as about 150 ms, and a planted 0 read as about -10 ms, so offsets carry about 10 ms of bias.

## 11. Spelling

`spelling`: RapidOCR at 2 fps plus each shot's middle, tracked over time. It checks words against pyspellchecker with your `--allow` list. A word misread in one frame and read right in others is OCR noise, not a typo. `expected_text` compares with your `--expected` lines, which is the stronger test.

These are candidates: read every crop. Voting across frames can hide a brief corruption. No tool detects AI gibberish directly, so low-confidence regions are worth a look.

## 12. Template, not references

`template_vs_references`: aligns shots with dynamic time warping, measures palette (CIEDE2000), composition, texture, tone, structure and rhythm against each set, and reports `margin`. Hand-built, not validated for taste. CSD and DreamSim are the better models if you can run them ([CSD](https://arxiv.org/abs/2404.01292), [DreamSim](https://arxiv.org/abs/2306.09344)). Run `reference.py` from extreme-motion-design for another view.

## Voice and music

| Check | How it works | Threshold (status) | Limits |
|---|---|---|---|
| `loudness` | ebur128 integrated and true peak | -20 to -9 LUFS (convention, no platform publishes a target; -14 is common), -1 dBTP (published, EBU and Spotify) | |
| `clipping` | Runs of 3+ samples at full scale | 3 runs (fixtures) | |
| `audio_dropouts` | Gaps 45 dB under the body, 30 ms to 1 s, with a 25 dB edge inside about 23 ms on both sides | (fixtures) | A deliberate hard mute. A pause in speech fades, so it does not count |
| `audio_length` | Audio against video length | 0.25 s (fixtures) | |
| `level_jumps` | RMS per shot | 12 dB between shots (fixtures; Video Use calls an end card 15 dB under dialogue a bug) | |
| `voice_script` | Whisper against `--script`, word error rate | 8% (fixtures) | Whisper repairs what it hears: in a [learner-speech study](https://arxiv.org/abs/2406.03235) it kept a common grammar mistake only 58.7% of the time. It can also invent words. So it says little about pronunciation |
| `voice_pitch` | Pitch spread in semitones | Report only | Music in the mix raises it. Use it on a dry voice |
| `music_facts` | Tempo and beats only with a clear pulse, cuts on beats within 70 ms against chance, how tightly cuts lock to the tempo grid against chance, abrupt end, spectral cutoff | Abrupt end only (fixtures) | Editing is elastic, so this is a report. AI music detectors are not a quality signal, and their miss rates reach 93.6% after a pitch or time change |

Not built here: lip-sync offset. SyncNet's score matched human ranking at [0.34](https://arxiv.org/abs/2610.09223), so use `joonson/syncnet_python` or PVSync as a hint and never rank on it alone.

## Images

`judge.py image` runs sharpness, exposure, attention, load, scale, OCR, spelling, contrast and reference distance. Laplacian sharpness tracks framing and once scored magenta garbage 62.7, so read it as a hint. For hands and limbs, ask eyes to name every object, and do not trust a model's "looks fine": GPT-4o and LLaVA missed them in the [paper's example](https://arxiv.org/abs/2411.13842).
