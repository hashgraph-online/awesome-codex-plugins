# Sound effects: few, exact, on the right frame

"Few and exact: every effect has a cause on screen, and too many read as a template." (HyperFrames sound.md)
Measured: about 85% of hard cuts in top launch films have no sound of their own, about 2 whooshes per film
(Cinetic, https://github.com/Leonxlnx/cinetic/blob/main/skills/cinetic/references/sound.md); a strong accent lands
within a frame of only 4-25% of cuts; "Sound on visual events is no better than chance in most references" (earshot,
https://github.com/Leonxlnx/earshot/blob/main/docs/launch-video-sound.md). "Sound design is not about about making
every movement audible. It's about deciding what deserves the viewer's attention." (bruno, launch-film sound designer)

## What gets a sound, and when

| On screen | Sound | Timing | Source |
|---|---|---|---|
| a real cursor click | short click | 10-30 ms before the visible press | Cinetic, earshot (measured) |
| text typing in | "each key a noise burst at 3-12 kHz (ridge 8.6-11 kHz), essentially nothing under 2 kHz"; "keys at 62-148 ms spacing (median about 87 ms ...), level and timing jittered" | with each character | earshot motion-sfx-study (measured) |
| a badge, chip or number landing | low thump 80-150 Hz with a faint tick | "lands 25-40 ms after its cut"; runs about 200 ms apart | earshot (measured) |
| a real scene change | one soft whoosh; big whooshes for big moments only | "peak within about +-150 ms of the cut" | earshot; Nate Curtiss: "Never use the same effect twice in a row" |
| impacts, taps, sub drops | | "Attacks ... start 30-200 ms before the cut, with the body or peak landing within about 80 ms of it"; risers and glitches end on the cut | earshot |
| the payoff | riser into impact, once per film; or dip the mix 6-12 dB for 0.3-0.5 s before the hit | | earshot SFX.md, HyperFrames |
| the logo | "the music stops on a bar line or is filtered down; then 0.2–0.7 s of near-silence; then one soft element on the wordmark (+8 ms)"; "A tail of 0.5–2.5 s (about 1.5) to below −60 dBFS" | | Cinetic |
| successive notifications | "Successive dings step up a semitone" | | earshot |
| a UI interaction | must fit "the 0.5 second timeframe of a button interaction" | | bruno (@tvnxty) |

Lead disagreement: HyperFrames puts the peak one frame after the picture ("a sound early feels wrong sooner than
one late"); OpenMontage starts a whoosh "10-20ms before the visual transition"; earshot and Cinetic measured onsets
100-450 ms ahead with the apex on the visual peak. All put the loudest point on the event. Derek Lieu: "there are
definitely trailers I've made where something is two frames off sync and I think it looks better." Measure, then let
a person nudge by up to 2 frames.

Levels: OpenMontage table "Pop / Pluck ... <200ms ... -15 to -12 dB", "Click / Tap ... <100ms ... -20 to -15 dB",
"Impact / Hit ... <300ms ... -12 to -6 dB". earshot measured pro hits about 13-17 dB over the quiet bed between
beats; agent prompts that keep every effect under the music lose them. Repeated UI sounds: "Create 8-12 variations by
varying pitch, volume, timing, or mix" (Andy Allen, !Boring Software), but earshot lists "random pitch on typing" as
a cheap tell: vary from real variations, not random pitch shifts.

## Layering a scene (film sound)

- "five layers is the maximum that can be tolerated by an audience if you also want them to maintain a clear sense of
  the individual elements"; two-and-a-half of one kind blur (Walter Murch, http://web.archive.org/web/20260905170354/https://transom.org/2005/walter-murch/)
- Room tone under everything: "10 seconds of room tone is IMPORTANT AF!" (Braden Whiteside, jacknjellify sound
  designer). "ai voices sound fake because the audio is too clean" (KNOX, 5,761 saves).
- Establish a sound once in a close shot, then use it off screen (Randy Thom). Three or more walkers: one crowd
  footstep bed, not per-step sync (Murch).
- Distance: "you lose the bass and the top end"; "an echoey bounce if there was a wall there" (Johnnie Burn).
- Real sources: Lucas to Burtt, "go out into the real world with your tape recorder and record motors and animals";
  "Any sound is made up of four sounds, generally" (Lon Bender, Netflix ta-dum); Mangini sweetened Fury Road's
  tanker hits "with hump back whales moaning and growling"; Mac Smith slows recordings down for new textures.
- Readable chaos: "We paid attention to the relative frequencies of effects, and their rhythmic, sequential
  placement" (Gary Rydstrom). UI and transition sounds "mostly leave 300 Hz-1 kHz (where the voice and the music's
  chords are) to the music"; "Mono for objects, wide for textures" (earshot).
- Match fidelity to the era: a 1930s section "mixed in mono and then degraded using an old, worn out tape effect"
  (Factory Studios).

## Prompting effect models

ElevenLabs SFX v3 (`eleven_sound_effects_v3` on varg, tool `music`; `duration` 0.5-30 s, `provider_options.fal.loop`,
`prompt_influence` 0-1, default 0.3) https://elevenlabs.io/docs/capabilities/sound-effects :
- "describe the action, setting, atmosphere and performance you want rather than a broad sound category": "Rain
  against a window in a quiet apartment", "Footsteps on gravel approaching slowly", "Football crowd cheering, hearing
  a ball drop, crowd booing".
- Sequences with "then"; "Prompts that ask for an exact number of repetitions, such as "triangle hit 4 times", are
  not always followed" -> make one hit and repeat it. Terms it knows: impact, whoosh, ambience, one-shot, loop, stem,
  braam, glitch, drone. For exact timing "break prompts into smaller, sequential elements and combine results
  manually".
- Higher `prompt_influence` (0.8 in ElevenLabs' own skill) for literal UI sounds; `loop: true` for beds.

Our run (2026-11-03, $0.07): "Single crisp click on a laptop trackpad, close-mic'd, dry, quiet room, one-shot" at 1 s
came back as near silence (peak -54 dBFS); "Loud, crisp computer mouse click, close-up, one-shot" with no duration
came back usable (0.48 s, -9.3 dBTP); the whoosh had 0.40 s of silent lead-in and its peak at 1.21 s; the room-tone
loop came back at -53.5 LUFS. Measure every effect (`sound.py measure`) before placing it.

Stable Audio 3.0: source, action and decay, mic/room/processing, optional `TrackType: SFX`; not for voices.

Video models:
- Veo: "SFX: thunder cracks in the distance", "Ambient noise: the quiet hum of a starship bridge"; per timed segment.
- Kling 2.6: "[Object: Wooden Door] suddenly [Action: Slams ] + [Sound Effect: Bang ]"; ambience = scene + sound
  elements + spatial reverb.
- Seedance: a `SOUND DESIGN:` line listing every audible event in order ("...and the final lid slam ... No background
  music overpowering the action." AIwithkhan, 389k views); "Also no "whoosh" or "zoom" sound effects." (PJ Ace).
- Native audio you don't want: keep a good take's dialogue and regenerate only effects and ambience around it
  (Mirelo SFX, prior X bank); the Seedance and Veo "sound signature" makes some directors replace effects with a
  library (Daubrez uses Epidemic Sound).

Foley from video: MMAudio "default output (and training) duration is 8 seconds"; the sync model uses "the central
square of each frame"; it "sometimes generates unintelligible human speech-like sounds"; weights CC-BY-NC.
HunyuanVideo-Foley takes text + video at 48 kHz. A video-only model with no text "stays almost silent" (Heather
Cooper): describe the sounds.

## Library, generated or code?

- HyperFrames: "Only **CC0** and **CC BY** sounds are used: never NonCommercial, ShareAlike or NoDerivatives" and "No
  synthesised tones, chimes or dings".
- earshot and Cinetic render sounds in code, but list "Code-synthesized beeps, sine pings and noise sweeps" as a cheap
  tell and say "Judge a made sound by the model-free measurements, spectrograms next to the references, robust
  re-renders, and a human blind test." Daniel White (Attio): synthesized UI feedback, "2kb. zero files."
- Use: code-made for UI ticks and pops in a code video; recordings or generated sounds for anything physical.
- Licences: Freesound CC0 free, CC BY credit, CC BY-NC no money-making use; Pixabay free commercial, no standalone
  redistribution; Sonniss GDC "expressly prohibited from using any sound effects ... for the purpose of training
  artificial intelligence technologies"; `@remotion/sfx` attribution-free, peaks at -3 dB.

## The cheap tells (audit before delivery)

"Code-synthesized beeps, sine pings and noise sweeps; one sample machine-gunned; a whoosh on every cut; a boom on
every logo; sparkle / shimmer sweeps standing in for "magic"; reverb on tiny sounds; random pitch on typing; partial
coverage (some presses heard, others silent); clicks at cuts; music chopped mid-note at a splice; an audible ambience
loop; a different room on every sound; the logo louder than the drop; an ending that stops mid-note instead of a tail
into silence." (earshot real-sound skill)
