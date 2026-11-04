# Audio visualizer (silk ribbons, wireframe terrain, ASCII stream)

Turns an audio or video file's soundtrack into motion: flowing silk-like ribbons, a scrolling wireframe landscape
built from the spectrum, or a field of terminal characters that brightens with the sound. Use it for music releases,
podcast clips, audiograms, lyric-video backgrounds and loops behind a voiceover. Formats 16:9, 9:16 and 1:1; length
follows the audio (preset default 20 s).

## How the pros do it
- **Analyse offline, then animate from the data.** A render must be deterministic: extract per-frame band values
  once (HyperFrames: `extract-audio-data.py`, Remotion: `useAudioData` + `visualizeAudio`) and sample them per frame
  from the timeline; no live Web Audio in the render. [62][71]
- **Use an FFT window much longer than one frame.** At 30 fps one frame is 1470 samples at 44.1 kHz, too short for
  bass; HyperFrames uses a 4096-sample window (≈ 10.8 Hz per bin) centred on each frame. The Web Audio default is
  fftSize 2048 (powers of two from 32 to 32768), giving fftSize/2 bins, with a Blackman window. [60][61][71]
- **Group bins on a log scale, never linearly.** Linear bins give the bass a handful of bars and the hiss hundreds.
  Use log-spaced bands from 30 Hz to 16 kHz (HyperFrames) or musical bands: bass 20–140, lowMid 140–400,
  mid 400–2600, highMid 2600–5200, treble 5200–14000 Hz (p5.sound). FFmpeg's `showcqt` is a constant-Q (musical) scale
  from E0 to D#10. [64][66][71]
- **Convert to decibels and normalise per band.** Raw magnitudes are dominated by bass; Remotion's recipe is
  `20·log10(v)` mapped from −100 dB to −30 dB (the Web Audio defaults). HyperFrames normalises each band to its own peak
  over the track so treble stays visible. [60][62][71]
- **Smooth with fast attack and slow release.** Web Audio smooths each bin as `τ·prev + (1−τ)·now` with τ = 0.8
  by default (p5.sound uses 0.8 too); Remotion averages the previous, current and next frame. Broadcast meters encode the
  same idea: a PPM integrates in 5–10 ms and falls 20 dB in 1.7 s; a VU meter rises in 300 ms. So: rise within a frame,
  fall over 150–400 ms. [60][62][64][69][70]
- **Map a normalised "1 = normal" level to motion.** MilkDrop's model: bass/mid/treb ≈ 1 is normal, < 0.7 quiet,
  > 1.3 loud; the `_att` versions are damped for smooth motion; typical mapping is
  `zoom += 0.1·(level − 1)`. Use raw levels for hits, damped levels for big shapes. [65]
- **Scale the reaction to what moves.** Text should move 3–6% at most; shapes and backgrounds can swing 10–30%. [71]
- **Drive accents from beats, not from raw volume.** Beat-track offline (librosa defaults: sr 22050, hop 512 ≈ 23 ms
  resolution, start tempo 120 BPM) and fire short decaying impulses on beats. [68]
- **Pick the form from the music, not the other way round.** HyperFrames' audio-reactive guide warns against generic
  equalizer bars, rainbow cycling and white strobes when the visualizer is decoration; here the visualizer is the
  content, so commit to one strong form and one palette. [71]
- **ASCII needs a density ramp and the right cell shape.** Paul Bourke's 10-level ramp is `" .:-=+*#%@"` (70-level for
  finer tone); characters are taller than wide, so sample half as often vertically. [67]

## Presets
| Preset | Look | Key values |
|---|---|---|
| `audio-visualizer.silk-ribbons` | 5 translucent ribbons flowing across a dark gradient; bass swells the lower ribbons, highs ripple the top | bg #0B0B12→#1B1030, ribbons #FF5EA8 #8A5CFF #4CC9F0 #F9C74F #FFFFFF, width 2–4 px + glow 16 px, additive blend, release 0.45 s |
| `audio-visualizer.wire-terrain` | Perspective wireframe landscape; each new row is the current spectrum, rows scroll toward the horizon | grid 96 bands × 48 rows (1.6 s history), line 1.5 px #39FF88 on #030805, height = level^0.7 × 18% frame height, camera pitch 60°, far fog 70% |
| `audio-visualizer.ascii-stream` | Monospace character grid; brightness and glyph density follow a spectrum/waveform field | JetBrains Mono 500, cell 12×24 px at 1080p (160×45 grid), ramp " .:-=+*#%@", fg #C8FFD4 on #050807, glow 6 px, release 0.25 s |

## Timing and numbers
- Analysis: sample rate 44.1 kHz; FFT 4096 (≈ 10.8 Hz/bin) for bands, Hann/Blackman window centred on each frame;
  30 fps → 1470-sample hop [60][71]. Bands: 32 (ribbons), 96 (terrain), 64 (ASCII), log-spaced 30 Hz–16 kHz [71].
- Level mapping: dB = 20·log10(mag); clamp −100…−30 dB → 0…1 [60][62]; then per-band normalise to the track's 98th
  percentile (not the single max, so one transient does not flatten the rest; house tweak of [71]).
- Envelope per band (house default from meter ballistics [69][70]): attack = 1 frame (33 ms); release τ = 0.25 s for
  bars/ASCII, 0.45 s for ribbons, 0.6 s for terrain height. Per frame: `y += (x − y) · (x > y ? 1 : 1 − exp(−1/(fps·τ)))`.
- Beat impulse: on each beat, add 1.0 to a pulse value that decays with τ = 0.12 s; map pulse to 6–12% scale on shapes,
  ≤ 4% on any text [71].
- Motion budgets: ribbon amplitude 4–14% of frame height; terrain peak 18% of frame height; ASCII brightness 0–100%
  mapped through the ramp; background colour shift ≤ 10% lightness.
- Idle floor: keep 8–12% motion in silence (slow phase drift 0.1–0.2 cycles/s) so the frame never freezes.
- 9:16: ribbons run vertically or sit in the middle 50% of height; terrain camera lower (pitch 50°) to fill the tall frame;
  ASCII grid 90×80 cells at 12×24 px.

## Build it
1. **Extract:** `python extract-audio-data.py input.mp4 --fps 30 --bands 64 -o audio-data.json` (HyperFrames
   `hyperframes-creative` skill); or in Remotion `visualizeAudio({fps, frame, audioData, numberOfSamples: 64})`
   (power of two) per frame. [62][71]
2. **Drive per frame:** in HyperFrames, loop over frames and `tl.call(draw, [frames[f]], f / fps)` on the paused
   timeline (a single tween will not react); apply the attack/release envelope in that loop so it is seek-safe
   (recompute from frame 0, or precompute the smoothed array). [71]
3. **Silk:** for ribbon i, `y(x) = A_i(t)·sin(2π(k_i·x + φ_i(t))) + 0.4·A_i(t)·sin(2π(2.3k_i·x − φ_i(t)))` with
   `φ_i(t) = 0.15–0.4 cycles/s · t`; A_i from band group i (bass → bottom ribbon); draw as canvas strokes with
   `globalCompositeOperation = "lighter"`.
4. **Wireframe terrain:** three.js `PlaneGeometry(96, 48)`; each frame shift the height rows back one and write the current
   bands into row 0; `LineSegments` with `EdgesGeometry` or a wireframe material; fog to background. (The three.js
   example feeds a 64-bin `DataTexture` from fftSize 128 to a shader; same idea, offline data.) [63]
5. **ASCII:** start from the HyperFrames `ascii-render-pass` component (luminance grid → density-ramp glyphs) and feed it
   a field built from the bands (e.g. a radial or horizontal spectrum image) instead of a video. [67]
6. **Fast no-code path (ffmpeg):** `ffmpeg -i song.mp3 -filter_complex "[0:a]showcqt=s=1920x1080:fps=30:sono_g=3[v]" -map "[v]" -map 0:a -c:a copy out.mp4`;
   or `showfreqs=s=1920x1080:mode=line:fscale=log:win_size=4096` for a log spectrum line; `showwaves=s=1920x400:mode=cline:rate=30`
   for a centred waveform. [66]
7. Other starting blocks: HyperFrames `waveform` (gradient equalizer shader), `sine-wave`, `oscilloscope-trace`
   (CRT beam with phosphor decay); the `music-to-video` skill for beat-grid cutting.

## Mistakes that look amateur
- Linear frequency bars (one fat bass bar, 200 identical hiss bars) → log or constant-Q bands. [64][66][71]
- Bars that flicker every frame → fast attack, 150–400 ms release, or damped `_att`-style values. [60][65][69]
- Visuals glued to loudness, so the quiet intro is dead and the chorus clips → per-band normalisation + idle floor. [71]
- Live Web Audio analysis inside the render (nondeterministic, frame drops) → offline extraction, per-frame sampling. [62][71]
- Audio and picture out of sync by one window → centre the FFT window on the frame time, not at its start. [71]
- Text pumping 20% on every kick → ≤ 4–6% on text, bigger swings only on shapes. [71]
- ASCII stretched vertically → sample half as often vertically / use a 1:2 cell. [67]

## Sources
[60] W3C — Web Audio API (AnalyserNode) — https://webaudio.github.io/web-audio-api/ — fftSize, smoothing 0.8, −100/−30 dB, Blackman
[61] MDN — AnalyserNode — https://developer.mozilla.org/en-US/docs/Web/API/AnalyserNode — bins = fftSize/2
[62] Remotion — visualizeAudio — https://www.remotion.dev/docs/visualize-audio — samples, smoothing, dB mapping
[63] three.js — webaudio_visualizer example — https://github.com/mrdoob/three.js/blob/dev/examples/webaudio_visualizer.html — 64-bin DataTexture
[64] p5.sound — fft.js — https://github.com/processing/p5.js-sound/blob/main/src/fft.js — band ranges, smoothing 0.8
[65] Ryan Geiss — MilkDrop preset authoring — https://www.geisswerks.com/milkdrop/milkdrop_preset_authoring.html — 1 = normal, _att damping
[66] FFmpeg — filters (showcqt, showfreqs, showwaves) — https://ffmpeg.org/ffmpeg-filters.html
[67] Paul Bourke — ASCII grey-scale ramps — https://paulbourke.net/dataformats/asciiart/
[68] librosa — beat.py — https://github.com/librosa/librosa/blob/main/librosa/beat.py — beat_track defaults
[69] Wikipedia — Peak programme meter — https://en.wikipedia.org/wiki/Peak_programme_meter — 5–10 ms attack, 20 dB/1.7 s fall
[70] Wikipedia — VU meter — https://en.wikipedia.org/wiki/VU_meter — 300 ms rise
[71] HyperFrames — hyperframes-creative audio-reactive guide + extract-audio-data.py — https://github.com/heygen-com/hyperframes — FFT 4096, log bands, per-frame sampling, scale budgets
