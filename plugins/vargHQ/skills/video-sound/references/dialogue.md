# Dialogue and narration: write for the ear, then leave room

## Build the voice track first

- Ken Burns' editor Craig Mellish: "We screen with just the talking heads and the narration and any voices that
  there might be." (a "radio cut", before picture) https://www.provideocoalition.com/art-cut-ken-burns-doc-editor-craig-mellish-ace/
- Baby Driver: "came up with a 100 minute radio play ... then we could put the pictures on top of that." (Paul
  Machliss) https://www.motionpictures.org/2018/03/baby-drivers-oscar-nominated-editor-paul-machliss-marrying-music-mayhem-2/
- For an agent: lines first, word timestamps from them, every cut on a word boundary or a pause, never inside a word.
  Remotion: generate TTS per scene and size the composition with `calculateMetadata`.

## Write for the ear

- "Fancier isn't better in radio. "So it'd be like saying 'the vehicle' instead of 'the car.'"" One idea per
  sentence; contractions ("won't", "don't"). (NPR's Marielle Segarra, https://www.ctpublic.org/2023-02-17/need-to-write-a-toast-or-a-script-here-are-7-tips-to-let-your-voice-shine-through)
- "Have an idea of how much your host can actually say in one breath, and write to their breath." Alternate short
  and long sentences; "Words with long vowel sounds and l's, m's, n's and r's take longer to say and immediately slow
  things down." (CBC's Chris Wodskou, https://www.cbc.ca/radio/docproject/blog/the-craft-of-writing-for-radio-16-tips-from-a-veteran-script-writer-1.3562474)
- "Instead of saying '1,988 people', say 'nearly two thousand people'." Read it aloud for one-breath sentences.
  (https://mediahelpingmedia.org/how-to/how-to-write-a-radio-news-script)
- "Having written a commentary, the first thing to do is to carefully see what you can get rid of." (David
  Attenborough) Khris Brown: "Cut your line count and make them good." Randy Thom: wall-to-wall dialogue leaves no
  room for sound.
- Realism: Google's TTS docs: write the text "as a real spoken transcript—including natural conversational
  disfluencies and hesitations (for example, "Oh uh yeah I think... hm, so that's interesting")".
- Narration written by an LLM: tell it to avoid its tics, "Narrate like a university professor" rather than short
  punchy sentences and piles of numbers (prior X bank, deedydas, 4,381 saves).
- Narrator pace for explainers: 145-155 words per minute "with room to breathe" (HyperFrames docs narrator).

## Pauses, breaths, small actions

- **Room.** Fewer lines per generation. Randy Thom: "linger on a shot after the dialog is finished, or before it
  begins ... so that we can listen." Hold 1-3 s with only ambience after a key line.
- **The breath before a thought, not breath everywhere.** NPR's voice coach Jessica Hansen: "When you start a
  thought with a full, supported breath, your speech has more energy." Randy Thom on overdone tracks: "all the space
  not occupied by actual words is filled with grunts, groans, and breathing".
- **Behaviour, not emotion.** "Never prompt emotions. Prompt behavior. Type "she is afraid" and you get the cliche
  version of afraid." Good: "Jace stops mid-stride. His eyes move cage to cage. Jaw tightens. He lowers the pistol a
  few inches." (PJ Ace, https://x.com/PJaccetturo/status/2100218145088950429). In TTS a reaction tag does it: "[sigh]
  [sad] I just don't know anymore. The sigh grounds the emotion physically." (Fish Audio)
- **Show the action to the voice.** "Animation or even storyboards of what will show on screen can help an actor
  tailor their delivery." (Bonnie Bogovich) For efforts and grunts, write the exact action per line.
- **Cut-offs and trailing off.** "Truncating the first speaker's line with double dashes (or an ellipsis) is common"
  (John August). ElevenLabs: `Speaker 1: [starting to speak] So I was thinking we could—` / `Speaker 2: [jumping
  in] —test our new timing features?`; also `[overlapping]`, `[interrupting]`. Gemini backchannels inside a turn:
  `So the launch is Thursday |oh hmm| Are we actually ready?`
- **Together, not isolated.** "the actors are no longer working in a vacuum, but rather reacting to the performance
  and delivery of another human being" (Jesse Harlin). Generate an exchange in one dialogue call (ElevenLabs Text to
  Dialogue: up to 10 voices, keep it at or under 2,000 characters, generate several and pick; Gemini 3.8 two-speaker)
  or pass `previous_text` / `next_text` (or request ids) when stitching single takes.
- **A sound half a second before the reaction** (Johnnie Burn, Oscar for The Zone of Interest).

### lines.md

```markdown
| id  | who | text exactly as sent | direction | after | shot |
|-----|-----|----------------------|-----------|-------|------|
| L01 | MIA | [exhales] I didn't mean to break it... | ashamed, to her brother | 0.9 s | s02 |
| L02 | MIA | [sniffs] I was only trying to fix the light — before you got home. | quieter, avoids his eyes | 0.6 s | s02 |
| L03 | LEO | [jumping in] —You were trying to fix it? | dry, a small smile | 1.5 s hold | s03 |
```

## Dialogue inside video models

| Model | Line syntax | Sound rules |
|---|---|---|
| Seedance 2.x | `{Really, sis?}` then `DELIVERY: understated, mildly incredulous, younger-brother annoyance with warmth underneath. Estuary British accent. No shouting.` (PJ Ace) | Seedance 2.5 always generates audio (settings.audio is ignored). "NO MUSIC. Generate absolutely no musical soundtrack, melody, instruments, tonal bed, or ambient music. Use only diegetic sound effects, ambience, dialogue, and foley written inside <>." then `<moving train ambience, carriage vibration, ...>`. "Short dialogue beats long: I'll take two clipped lines across a cut over one long line that loses sync halfway through." (fal) "Low room tone underneath, the soft drone of an air vent, no score." |
| Kling 3.0 | `The black-suited agent slams his hand on the table.[Black-suited Agent, angrily shouting]: "Where is the truth?"`; `Immediately,` between speakers | unique labels, no pronouns; voice description per character; 2.6 guide: 10 s clips and at most two speakers |
| Veo 3.1 | `Man: (Hand on his hunting knife) "That's no ordinary bear." Woman: (Voice tight with fear, scanning the woods) "Then what is it?"` | `SFX:` and `Ambient noise:` cues; timestamped segments; a voice extends only if present in the last 1 s; Veo 3.1 Preview in the Gemini API shut down 2026-10-22 |
| Sora 2 | a `Dialogue:` block below the visual prose, consistent labels | a 4 s shot holds one or two short exchanges |
| Wan / replace speech | "Remove ALL on-screen text. NO subtitles, NO captions ... Replace the original speech with this EXACT script, word for word." (Simone Canc) | |
| Any, accent | state it: if left out "the model defaults to American" (Jay Nwabueze; engagement flagged); a real reference recording does more than text | |
| Lip-sync later | prompt "the character should be speaking naturally" (sync.) | one clean voice per input; long jobs split into 30-40 s chunks |

Per-shot example (Seedance 2.5 / Kling 4, 15 s): `1. (0–2.5s, moving arm's-length selfie) ... MILA: "Arm day. This
should be quick."` ... `She speaks with an American accent.` ... `Shot 4: No dialogue — breathing and distant gym
sounds.` (Alpha Mom, https://x.com/YourAlphaMom/status/2116635769729323171)

If a native voice drifts: clone a clean line and re-dub (Daubrez), or run the clip audio through a voice changer.
Always check generated lines against the script by transcript; models add gibberish words. Generate the voice
separately and paste its exact script into the video prompt for speaking clips (ZssBecker, 3,135 saves,
https://x.com/ZssBecker/status/2113320998527221875); lock the audio over the whole clip.
