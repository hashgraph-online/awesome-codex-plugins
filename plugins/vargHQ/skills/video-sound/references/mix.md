# Mix and master: voice first, measured, checked on a phone

## Loudness targets

| Where it plays | Integrated | True peak | Source |
|---|---|---|---|
| YouTube | no published number; "YouTube doesn't turn up quieter videos"; -14 LUFS is the common reading; Stable volume on by default in the mobile app | -1 dBTP | Ian Shepherd https://productionadvice.co.uk/stats-for-nerds/ ; YouTube Help |
| TikTok, Instagram Reels | no official spec; practitioners deliver -14 LUFS | -1 dBTP | OpenMontage sound-design.md |
| Spotify | -14 LUFS | -1 dBTP; -2 if the master is louder than -14 | Spotify for Artists |
| Apple Podcasts | -16 LKFS ±1 | -1 dBFS | Apple |
| Streaming speech (AES TD1008) | -18 LUFS speech, -16 music | | Ian Shepherd summary |
| EBU R128 broadcast | -23.0 LUFS | -1 dBTP | EBU |
| US TV | -24 LKFS | | Alex Knickerbocker: "-14 LKFS is NOT a film or TV spec" |
| Netflix | -27 LKFS ±2 dialog-gated (programme -24 if under 15% dialogue) | -2 dBTP, limiter at -2.3 | Netflix spec v1.5 |
| Audiobooks (ACX) | -23 to -18 dB RMS; noise floor under -60 dB RMS; 1-5 s room tone at head and tail | -3 dB peak | ACX |

- "Lossy encoding for streaming or mp3 can also generate extra peak information above zero, so I recommend you don't
  exceed -1 dB TP" and keep the "short-term peak to loudness (PSR) ... above 8" (Ian Shepherd). Platforms normalise,
  so don't squash a mix to win loudness.
- earshot measured 7 pro launch films: median -14.8 LUFS, loudest 3 s only 1.1-3.5 LU above integrated, and "6 of 7
  references clip after AAC decoding": don't copy their peaks.
- ffmpeg `loudnorm` defaults to `I=-24`, `TP=-2`, `LRA=7` and upsamples to 192 kHz: set your own target and
  `-ar 48000`; two passes with `measured_*` and `linear=true` (Kyle Swanson). `sound.py mix` uses one static gain to
  the target and a 4x-oversampled limiter 0.5 dB under the ceiling, then re-measures.

## Levels

- Voice over music: sources span 7-25 dB. WCAG 1.4.7 (AAA): "background sounds are at least 20 decibels lower than
  the foreground speech content". OpenMontage: "MUSIC BED: -30 to -20 dB (18-20 dB below dialogue)"; "Duck music
  6-12 dB when narration is active; for complex educational topics, duck up to 22 dB". HyperFrames engine:
  `BGM_BED_VOLUME` "0.12 ≈ -18 dB — a bed under the voice"; its docs narrator has music "about −31 LUFS". BBC once
  proposed music 4 dB lower on all shows; mixers answered "dropping by 4dB will become a serious creative issue".
  Default in `sound.py check`: 10 dB in 300 Hz-4 kHz during every line; raise `checks.voice_over_music_db` to 20 for
  accessibility-first pieces.
- Effects: OpenMontage "SFX: -18 to -12 dB (6 dB below dialogue minimum)"; earshot measured pro hits 13-17 dB over the
  quiet bed between beats.
- Room tone: KNOX lays it "-18db" under the voice and handling noise at -24 dB; ACX wants a noise floor under -60 dB.
  Different measures: set it relative to the dialogue and check it is audible in the gaps but never competes.
- "Even audio quality matters a lot ... I've seen multiple videos fail because the music was too loud, the music was
  too chaotic, or the sound came through distorted." (Mario Joos, retention director)

## Ducking and carving

- Fast down, slow up: "only about 4 frames long if not less" down; "20-30 frames" back up (Derek Lieu). HyperFrames
  duck script: multiplier 0.25, 0.15 s in, 0.4 s out, bridge gaps under 0.6 s. `sound.py`: `duck.down` 4 frames,
  `duck.up` 24 frames, voice windows merged across gaps under 0.6 s.
- Carve the voice band: "you can use your equalizer to pull out the high frequencies of the music so it doesn't clash
  with voice but stays present in the mix" (NPR's May); "Carve by default — required whenever music plays under a
  voice" (HyperFrames, carve strength 0.8); a 3-band sidechain "lows 30%, mids 85%, air 55%" until the voice "sits
  about 9 dB over the music between 300 Hz and 4 kHz" (twoclipping); "Cut 2-4 kHz on the music bed" (OpenMontage).
  `sound.py` splits the bed at 300 Hz and 4 kHz (crossover bands sum flat) and ducks them 35% / 100% / 65% of
  `duck.depth_db`.
- Stems: lower only the stem that fights the voice (Jim Harrison). For one line that must land, remove the music:
  "music was the sacrificial victim. The miraculous thing is that you do not hear it go away" (Murch). Music under
  dialogue can also be made diffuse (distance, room) rather than only quieter (Murch on worldizing).

## Voice treatment by symptom (HyperFrames mixing.md)

| Symptom | Move |
|---|---|
| hum, rumble, handling noise | high-pass at 80 Hz |
| boomy, too close | peaking 200 Hz, -4 dB |
| muffled | peaking 250 Hz, -3 dB |
| words hard to make out | peaking 3 kHz, +2.5 dB, or duck the music |
| harsh | peaking 3.2 kHz, -3 dB |
| peaks clipping | limiter last |

OpenMontage chain for AI TTS: "HPF 80Hz, cut 500Hz, boost 2-5kHz, cut 6-8kHz", compression 3:1. Don't over-clean
(Mac Smith); don't level normal 4-6 dB declination.

## Space and edges

- Dialogue centre; music and ambience wide: "the "warmer" the sound, the more it tends to be given a full stereo
  ... treatment, whereas the "cooler" the sound, the more it tends to be monophonically placed in the center" (Murch).
- Mono: "If you want to check mono then do it from a single speaker." Listen on "phone speakers, earbuds, in a noisy
  environment" (Andy Allen) and "on domestic speakers" (George Foulgham, BAFTA-winning dubbing mixer).
- Edges: "Pretty much, none of your audio clips should have a hard cut at the beginning or end." (Lieu) `sound.py`
  fades every clip edge (30 ms; 5 ms at the start of an effect to keep its transient).
- Silence: "I try to use silence in unexpected ways three or four times in every film"; abrupt silence "can seem to
  the audience that something has gone wrong with the sound system"; "a sudden transition to silence as an indication
  of danger" (Murch). "Loud sounds like explosions are more startling and effective if they're preceded by a little
  silence." (Richard King)
- Scene changes: hold the last shot ~30% longer than a normal cut; pre-lap the next scene's sound ("if you use
  pre-laps, it sensitises the audience to sound", Murch).

## The checks (`sound.py check`)

| Check | Pass |
|---|---|
| loudness | platform target ±1 LU |
| true peak | at or under the ceiling (+0.1) |
| length | the video length ±1 frame |
| voice above music | ≥ `checks.voice_over_music_db` (default 10) in 300 Hz-4 kHz during every line |
| effects on their moments | real onset (or peak for `align: peak`) within 1 frame of `at` |
| cuts on the beat | every cut within 1 frame of the beat or downbeat grid |
| no dead air | no unplanned span under -60 dBFS longer than 0.3 s |
| mono safe | mono fold-down at most 6.5 dB quieter (3 dB = same in both speakers, 6 dB = fully wide, more = phase cancelling) |

## Does sound add views? (what the evidence is)

| Finding | Who and how |
|---|---|
| 88% of TikTok users call sound essential; 73% stop for ads with audio | TikTok-commissioned Kantar survey, 2021 |
| 2.4x more attention to ads on sight-and-sound platforms | Nielsen lab for Google, 400 people, 2016 |
| about 80% of Reels watched with sound on | EssenceMediacom for Meta, sponsored, 2024 |
| 92% watch mobile video with sound off; captions lifted ad recall 8% | Verizon Media and Publicis survey, 2019 |
| "audio assets are on average more effective than some visual assets"; a brand's own sonic cues beat borrowed music | Ipsos meta-analysis of 2,000+ ads |
| Fury Road's preview score rose 8 points after a sound-only redesign | Mark Mangini |
| the first 3-6 seconds decide; "videos should always include sound" | TikTok SMB Creative Playbook |

No public study compares watch time for one video with and without sound design. Build sound-first for TikTok and
Reels, caption for the sound-off viewer, own a recognisable sound, and never let music bury words. Mark the end of
the intro with a sound or a change of tone (Mario Joos).
