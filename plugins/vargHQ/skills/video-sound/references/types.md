# Variations by video type

The routine is the same for every video; what changes is what leads.

| Type | Leads | Music | Effects | Signature move | Master |
|---|---|---|---|---|---|
| Launch / product film | music | under nearly all of it, 108-136 BPM | 3-6 accents: reveal, key UI action, logo | music stops on a bar line before the logo | -14 LUFS |
| Cinematic AI film | room and silence | little, often hidden | off-screen, at real distances | a little silence before the big hit | -14 web, -24 TV |
| Music video | the song | the song, unedited | few, under the song | picture cut to the song | -14 |
| Trailer / ad | alternates | three acts with gaps | from the film's own sounds | a line, then a hit | -14 web, -24 TV |
| UGC / talking character | voice | none, or the room's | the room and the hands | phone-mic sound matching the camera | -14 |
| Narrated explainer / code demo | voice | a carved bed | one big hit every 7-10 s | every cut on a word or a pause | -14 social, -18 streaming speech |

## Launch and product films (code-made)

- Pick the track first and cut to it: "Music runs under (nearly) the whole film: AudioSet hears it in 89-100 % of 5 s
  windows in 6 of 7 films [measured]. Pick the track first and cut the picture to it" (earshot launch-video-sound.md).
  Tempo 108-136 BPM, median 123. Lock BPM and bar count before animating.
- Accents only where they matter: "deliberate accents go on the moments that matter (reveal, logo, key UI action)"
  (earshot). "this product video has a lot of information, so I knew music and sound design must never fight it for
  attention." (bruno, launch-film sound designer). UI sounds within 0.5 s.
- No silent cold open: first sound by 0.13 s (median), "6 of 7 films open at body level" (earshot). Cinetic instead
  lets the intro run 5-12 LU under the body for 2-3 s: pick one and say which.
- The logo ending (Cinetic): music stops or filters down on a bar line, 0.2-0.7 s of near-silence, one soft element
  on the wordmark, a 0.5-2.5 s tail to below -60 dBFS, then 0.4-1.1 s of silence on the end card.
- Sonic logo: "it had to be really short" (Netflix, about 3 s), built from layers, tested blind by the words people
  use for it; a first burst "closes off whatever sound was there before. It prepares you for the melody" (Intel's
  Walter Werzowa); the motif's rhythm can come from the syllables of the name.
- One narrator per series at 145-155 wpm, music about -31 LUFS under it (HyperFrames docs voice).
- Music and effects of agent-made launch films "sounds kinda the same" (bruno): a tempo, key and instrument choice
  that isn't the default, and one signature sound of your own, are the cheapest fixes.

## Cinematic AI films

- Generate with natural sound only and add music and atmosphere in post: prompt suffix "NO MUSIC NATURAL SOUND ONLY";
  "By removing AI music from the generation, he gets the sounds of fire crackling, footsteps, and sword slashes ...
  He then layers his own music and atmospheric sound in post." (Kavan Cardoza's method via PJ Ace)
- Point of view: "Most of the great sound sequences in films are "pov" sequences." (Randy Thom). Tag each scene in
  `plan.md` with whose ears we are in.
- Ambience as score: "To me the winds were the score throughout this part of the film." Build each place from 2-3
  layers that come and go (Craig Berkey, No Country for Old Men).
- Tension by subtraction: "we underplayed everything: BG's, footsteps, etc., to help create tension"; a string of
  small off-screen sounds before the reveal (Berkey); "a little silence" before explosions (Richard King); "a sudden
  transition to silence as an indication of danger" (Murch). Silence 3-4 times per film, eased into.
- Dream or flashback transitions: "all the sounds slow and change and become a different sound in the next sequence"
  (Richard King, Inception). Pre-lap the next scene's sound 0.5-2 s before its picture.
- Off-screen sounds at a real distance (lose bass and top, add reflections; Johnnie Burn), and a sound 0.5 s before a
  character reacts to it.
- Music: dose it (Murch); hide drones behind wind for realism (Burwell); for a cruel beat try indifferent, cheerful
  source music ("anempathetic", Michel Chion); one theme in many versions (Ken Burns' team); write the theme from the
  script before shots (Coppola and David Shire, per Murch).
- Voices: the AI feature in US cinemas used "eleven voice actors, four composers ... (including a foley artist)"
  (Gossip Goblin). Without actors, clone a clean line and re-dub, and use a fixed voice block per character.
- Native model audio has a signature ("a very iconic subtle 'echo' to all seedance audio", PJ Ace); replace effects
  from a library where it matters (Daubrez: Epidemic Sound for most SFX).

## Music videos

- The song is the master clock: "Synchronize cuts, breath, gaze, gestures and type to the actual audio. Do not invent
  a different song or singer." (Israa Ali, https://x.com/Israa_Ali2077/status/2117286613739032729)
- "we tried to set ourselves a rule of not editing the music. I think maybe 95% of the time, the song is complete and
  unedited." and "cars don't actually stop spinning after crashing on the beat, so maybe you put four bars of music
  but it takes six" (Machliss)
- Lip-sync: prompt "sings the vocals of [audio_ref] from the very first second to the end, perfectly lip-synced word
  by word in every shot where his mouth is visible"; feed the lip-sync model an isolated vocal (Demucs); when the
  performer should not sing: "no miming the lyrics, no lip-sync" (sandmrk).
- Long songs: "chop your song up into 15-second chunks, and make sure each chunk starts one second before the
  previous one ends" (techhalla). Cut reference audio to whole seconds with no tails (Kiber_Alla).
- Get word timestamps for every lyric word and animate each on its time; transcribe a generated song to check the
  sung words.

## Trailers and ads

- Three acts, gaps between them as edit points, an ending that doesn't resolve (Dan Graham, Gothic Storm labels).
  "a line of dialogue is followed immediately by a sound effect or big beat in the music cue that punctuates the
  story beats" (Derek Lieu). Braams: "It punches through to everything — and it's just one note." (Bobby Gumm,
  Trailer Park); "power-downs" under slow motion.
- Rhythm from the film's own sounds: "that sound of this man's skull throbbing against a chalkboard really became
  kind of the baseline for the trailer" (Mark Woollen). AV Squad: "I never want drums. You can always use sound
  effects to create those drum tracks"; "introduce a sound effect without the picture attached to it. And then in the
  next measure of music I will have the sound effect again but now with the picture."; music "progressions should
  happen after you've finished giving a piece of information. They're chapter breaks."
- Signature hits from your own sound: "signature braaams, such as the one made out of a dinosaur roar" (THR).
- Ads: "pick your moments to shine and pick your moments to get out of the way" (Kip Smedley); finish the longest cut
  first, then the 30/60 s from its best parts and a 7 s "just the punch line" (Tom Disher); a brand's own sonic cues
  beat borrowed music (Ipsos, 2,000+ ads).

## UGC and talking characters

- Match the camera: "AUDIO: Natural Japanese dialogue with accurate lip-sync, phone-mic quality, footsteps, traffic,
  birds, bakery sounds, bus engine, bicycle bell, wind and city ambience. No music, narrator, or cinematic SFX."
  (Sharon Riley, 151k views). Selfie UGC = phone-mic audio; camcorder = on-camera mic.
- "If its speaking, you need to generate the voice in eleven (or record it) separately. Then layer on the actual
  text/script of the voice in the prompt" (ZssBecker, 3,135 saves); lock the audio over the whole clip; check the
  output against the source audio for speed changes.
- One 3-6 word line per 2-3 s shot; "No dialogue — breathing and distant gym sounds" where nobody talks.
- A light bed under the voice: "coffee shop, room tone, street ambience" (KNOX).
- "A creator's accent doesn't hurt retention, but speech clarity does." (Mario Joos). Label realistic AI people.

## Narrated explainers and code demos

- Narration first, word timestamps from it, "the voice drives every cut" (varg how-to prompt card).
- Carved bed; duck deeper for dense topics (up to 22 dB, OpenMontage); streaming speech -18 LUFS (AES).
- "SFX: only about 1 big hit every 7-10 s, each one downloaded and trimmed so its peak lands on its word" and "The
  narrator never says a sound word; the SFX carry every sound." (finnardley, 1,942 saves)
- Mark the end of the intro: "A clear visual shift, a sound effect, a change in tone ... can all help signal that
  transition." (Mario Joos)
- Typing and UI: high-passed noise ticks, real clicks only on real clicks; over strong music "a typing-heavy film can
  drop the clicks and keys" (HyperFrames).
