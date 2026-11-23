# Sound: beds, hits, voice and loudness

Read this when a film has music, sound effects or a voice. `scripts/sound_bed.sh` makes a quiet pad; `scripts/finish.sh --audio` sets loudness. This file is the craft around them.

## Order of work

Picture first, sound second. Changing a shot's length after the sound is placed means re-pinning every sound.

1. Lock the structure and timing of the picture.
2. Lay the music bed, fitted to the beat grid.
3. Pin every sound effect in one central table (time, file, volume), not scattered through the build script.
4. Add the voice and duck the bed under it.
5. Measure loudness on the encoded file, never on the mix before encoding.

## Fit the beat grid, do not trust a tempo estimate

- Detect beats, then fit a straight line through them, `t = t0 + i * period`, by least squares. Accept the fit when the residual is under about 15 ms. `scripts/beat_grid.py analyze music.wav --out grid.json` does this (it needs librosa) and also scores half, same and double speed against the onsets, because trackers often lock to half or double tempo.
- A song whose tempo changes needs one grid per section. Cut the file at the change and fit each part.
- Keep times as floats in seconds until the last step; round to frames only at the end (`beat_grid.py snap grid.json --times ... --fps 30`). Write the timeline in beats where you can.
- `beat_grid.py snap ... --emit js` prints a small `snap(t)` function and the grid for use in a HyperFrames timeline.
- Verify by analysing the audio extracted from the rendered MP4, not the source. If every cut is off by the same amount in the same direction, that is encoder priming (AAC adds 1024-2112 samples of delay at the start), not a wrong grid: shift the audio, not each cut.
- Whole-frame hits (flash, shake, scale pump) go on the strongest beats only; everything else lands on the hero element. Stepping content may advance one step per beat; amplitude pulses may not.

## Pin each effect by its peak

A sound effect has a quiet start and a loud peak. Place it so the peak, not the start, lands on the visual event:

`start = event_time - peak_lag - output_offset`

Measure `peak_lag` once per file (the time from the file start to its loudest sample). Whooshes start 1-3 frames early because the ear expects the sound just before the object arrives.

## Layering

- A big moment is a phrase: a riser that begins one to two bars before the hit, an impact that lands on the object (the loudest effect in the piece), a sparkle about 0.4 s after.
- Two or three simple sounds per big moment, staggered 10-40 ms. More turns to mush.
- For a burst of six items, alternate two samples and step the volume down along the burst.
- Real recorded objects beat synthetic UI bleeps.
- Do not synthesise noise effects, and do not let anything hiss under a voice. White-noise whooshes made with a generator read as static. Check the pauses against the voice: measure the level and the 4-12 kHz band in a silent gap.

```bash
# level of a pause between 12.0 s and 12.4 s, and of its 4-12 kHz band (8 kHz centre, 8 kHz wide)
ffmpeg -hide_banner -ss 12.0 -t 0.4 -i mix.wav -af "volumedetect" -f null - 2>&1 | grep -E "mean_volume|max_volume"
ffmpeg -hide_banner -ss 12.0 -t 0.4 -i mix.wav -af "bandpass=f=8000:width_type=h:w=8000,volumedetect" -f null - 2>&1 | grep -E "mean_volume|max_volume"
```

- Dedupe a sound library by checksum, or the same file appears under three names and gets used three times.

## Ducking and carving

| What | Value |
|---|---|
| Bed under the voice | 12-18 dB below |
| Bed rise in gaps | 6-10 dB, over 0.3-0.6 s |
| Sidechain attack / release | 20-50 ms / 300-600 ms; at least 1.5 s release on voice-only social cuts |
| Carve | cut the bed 1-4 kHz (where speech lives) instead of only turning it down |
| Breath before the first word | 0.2-0.4 s |
| Breath after the last word | 0.3-0.6 s |

In ffmpeg 8 and later, `sidechaincompress` takes the sidechain by input order, not by an option name. Mix the bed pre-attenuated, with `amix=normalize=0` so the mix does not change levels by itself.

## Loudness

- Target -14 LUFS integrated, true peak at or below -1 dBTP, 48 kHz, measured on the encoded file. `scripts/finish.sh` does a two-pass loudnorm and a limiter; `scripts/check_delivery.sh` measures the result.
- AAC re-encoding can push the true peak up. For derived copies (a different size, a trimmed cut), copy the master's audio stream (`-c:a copy`) instead of encoding again.
- Build a loudnorm filter string in a script, not typed into an interactive zsh: zsh reads `$var:l` as a modifier and removes the `:l`.
- When voice lines differ in tone, matching loudness alone is not enough; match their tone (EQ each toward one target) and then de-ess and compress.
- Ship a no-music version when the film has music, and log every track's source and licence (the next section helps).

## Free music and effects with credit

`scripts/fetch_music.py` searches Openverse for CC0, public domain and CC BY audio, downloads a track, and writes `ATTRIBUTION.md` (title, creator, licence and link, source). CC BY needs that credit in the video description. It never offers NonCommercial, NoDerivatives or ShareAlike tracks. Listen to a track before using it; check the licence on its source page.

## Optional generators (you install them; brief2mp4 only calls them)

These make audio from a prompt or take it apart. None is installed by brief2mp4, and each has its own licence. The code licences below are permissive; the model weights differ, so read the notes.

| Tool | Does | Install | Licence and limits |
|---|---|---|---|
| [Audiocraft / MusicGen](https://github.com/facebookresearch/audiocraft) (Meta) | Music beds and sound effects from a text prompt | `python3 -m pip install audiocraft` (needs PyTorch; a GPU helps) | Code MIT. **Model weights are CC BY-NC 4.0: non-commercial use only.** Do not use its output in a commercial video without checking the weights licence |
| [F5-TTS](https://github.com/SWivid/F5-TTS) (SWivid) | Voice-over and voice cloning from a short reference | `python3 -m pip install f5-tts` | Code MIT. **Pre-trained models are CC BY-NC** (trained on the Emilia dataset). Clone only a voice you have the right to |
| [Demucs](https://github.com/adefossez/demucs) (Alexandre Defossez; originally Meta) | Splits a song into drums, bass, vocals and other, so cuts can follow the drum stem | `python3 -m pip install demucs` | MIT. The original Meta repository is archived; the maintained fork is the one linked. Check the licence of the song you split |

Fit a beat grid to the drum stem rather than the full mix when the music is dense: `demucs --two-stems=drums song.wav`, then `beat_grid.py analyze` on the drums file.

Film mode (`scripts/film.py`, see `formats.md`) calls these two as optional routes: `film.py voice --voice f5-tts --ref-audio ref.wav --ref-text "..."` and `film.py assets --musicgen "calm piano"`. When the tool is not installed it prints the install command and the licence note and stops; nothing is bundled. `scripts/sfx_synth.py` makes the effects in code (no white noise, seeded, peak under -1 dBTP), and `scripts/mix.py` applies the numbers in this file: the bed 7 dB under the voice's loudness in gaps and a further 8 dB down under speech, ramping down 0.12 s before the first word and up over 0.5 s after the last, effects pinned by their peak, -14 LUFS.
