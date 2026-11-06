# Example: a 20 s launch soundtrack, designed vs plain

A made-up product ("Tide", a calendar app). Three voice lines on `eleven_v4` (voice Brian
`nPczCjzI2devNBz1zQrb`), a 120 BPM bed on `eleven_music_v2_5`, four effects and a room-tone loop on
`eleven_sound_effects_v3`. Total model spend about $0.25.

```bash
./fetch.sh                                               # the generated files, from s3.varg.ai
python3 ../../scripts/sound.py mix cues.json -o mix.wav
python3 ../../scripts/sound.py check mix.wav --cues cues.json
python3 ../../scripts/sound.py preview mix.wav --cues cues.json -o preview.mp4
```

Watch: designed https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_024cbf6d16ee.mp4 ·
plain https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_7391d35ac5ee.mp4

## The plan

| time | bars | music | voice / picture | effects |
|---|---|---|---|---|
| 0-8 s | 1-4 | just a muted pulse + hi-hat | L01 at 0.5 s: "[calm, warm] Your week... is already full." | click on the 4.0 s cut |
| 8-12 s | 5-6 | sub bass enters | L02 at 8.25 s: "[calm, warm] Tide reads it — and finds the hours you lost." | |
| 12-13 s | 1/2 | stopped on the 12.0 s bar line; room tone stays | the build holds | whoosh swells, peak on 13.0 |
| 13 s | 7 | re-enters on the downbeat | logo lands | impact on 13.0 |
| 14-20 s | 7-10 | groove, then rings out | L03 at 14.0 s: "[warm, a small smile] This is Tide. [short pause] Your week, handed back." | |

Music prompt: "Minimal electronic launch score, 120 BPM, in D minor, clean modern 2020s production, confident and
hopeful. Start with just a soft muted synth pulse and a ticking closed hi-hat for four bars. Then bring in a warm sub
bass and a rising filtered pad for two bars, building. Then half a bar of complete silence. Then one big low impact
with a bright, wide synth chord on the downbeat and a steady four-on-the-floor kick for two bars. End on a single held
chord that rings out and fades. Instrumental only." The model held 120 BPM and brought the bass in after four bars,
but made no silence and no hit, so `cues.json` makes the stop in the edit: `bed_a` ends on the 12.0 s bar line,
`bed_b` starts at 13.0 from the same point in the track, and the impact and the whoosh's peak land on 13.0.

Effects: the whoosh's loudest point is 1.21 s into its file, so it uses `"at": 13.0, "align": "peak"`. The first
click generation ("Single crisp click on a laptop trackpad ... one-shot", 1 s) came back near-silent at -54 dBFS;
`click2` is the retry with no fixed length.

## Results (`check.json`, `check_naive.json`)

| check | designed (`cues.json`) | plain (`cues_naive.json`) |
|---|---|---|
| loudness / true peak | -14.2 LUFS / -1.5 dBTP | -14.0 / -1.5 |
| voice above music, 300 Hz-4 kHz, worst line | +15.9 dB | -6.6 dB |
| effects on their moments | 3/3 within 1 frame | none |
| cuts on the beat | 4/4 | 1/4 |
| dead air | none | 1.2 s at the end |

Plain = the vague bed ("upbeat electronic track for a product launch") at full level, no ducking, no effects, no room
tone, cuts wherever they fell.
