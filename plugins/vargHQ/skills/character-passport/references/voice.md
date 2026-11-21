# How they speak: the voice line

Every speaking character gets a ```voice block next to the passport. It is pasted into the TTS model's style or
voice-design field and kept identical across every line the character says.

```voice
Pace: <words per minute> overall; <where the pauses go>.
Pitch: <low / low-mid / mid / high>, <texture: husky, breathy, nasal, clear, gravelly>, <energy>.
Accent: <language background> + <region> + <class or setting>; <2-3 audible features>.
Verbal habit: <one phrase, tag or tic>, with an example line.
Default emotion: <the feeling they speak from>, <what they hold back>, <what they never do>.
```

Example (tested):

```voice
Pace: steady conversational, about 130 words per minute; short pauses only at full stops. Pitch: low-mid, slightly husky, tired. Accent: light Dalmatian Croatian accent in English: tapped r, pure open vowels, "th" close to "t". Verbal habit: ends statements with a flat tag "no?" ("It's late, no?"). Default emotion: dry and calm, holding back exhaustion, never theatrical.
```

## Pace in numbers

Write pace as words per minute **overall** (pauses included, what a viewer feels). Measure every test take:

```bash
python3 scripts/voice_check.py take.wav --text "<the exact line>" --target-wpm 130
```

Tested 2026-11-03 on Gemini 3.8 Flash TTS (voice Gacrux), same 22-word line:

| Take | Instruction | Measured |
| --- | --- | --- |
| No voice line | none | 144 wpm, 3.2 s of pauses |
| v1 | "slow, about 130 wpm, a half-second pause before each sentence, a longer pause after 'The last bus'" | 92 wpm, 6.5 s of pauses: FAIL |
| v2 | "steady conversational pace, about 130 wpm; short pauses only at full stops" | 129 wpm: PASS |

Models follow the direction of a pace word ("slow"), not its number. Fix the words, re-measure, keep the take
that passes. Pause words ("half-second pause", "…") multiply: use them only where the script needs a beat.

## Accent

Name three things: first language or region, social setting, and 2-3 audible features (r, vowels, th, stress,
intonation). "Light" or "strong". No script checks an accent: a person listens once before approval. For a real
reference of an accent, use the Speech Accent Archive or IDEA (reference-sites.md) and describe what you hear;
do not clone a real speaker's voice without consent.

## Verbal habit

One recurring phrase, tag or tic that belongs to this person: a tag question ("no?"), a filler ("look,"), a
catchphrase, a habit of answering a question with a question, counting on fingers out loud. Write it into the
**script**, not only the voice line: TTS will not invent it reliably. One habit per character, used 1-2 times per
scene, never every line.

## Models (varg, 2026-11-03)

| Need | Model | Notes |
| --- | --- | --- |
| Test lines with written direction | `gemini_3_8_flash_tts` (30 voices, `provider_options.fal.style_instructions`) | $0.01 a take; accent and pace as words; two-speaker dialogue via `speakers` + `turns` |
| Final, most expressive | `eleven_v4` / `eleven_v4_turbo` | Audio tags in the text ([sighs], [whispers], [laughs]); use raw ElevenLabs voice ids (names can 404 on v4) |
| Same voice across a series | one fixed voice id + the same voice line + the same model | Changing model or voice id changes the person |

## Voice before picture

Approve the voice before any talking shot. Lip-sync to the approved take, or pass it as an audio reference.
Seedance 2.5 re-voices an `@audio1` line with its own timing; mute and retime if the exact take matters.

## From people with finished work (verbatim in x-evidence.md)

- Name the accent every time; left out, models default to American. For an accent the model lacks, use 5-15 s of a
  consenting real speaker reading conversationally, at the scene's energy ([@jaynwabueze](https://x.com/jaynwabueze/status/2095171650241110448)).
- Screen-test a video model's native voice at 480p, keep the take you like, and reuse its audio as the reference in
  every clip, or "one character can sound like three different people" ([@godswayfoundinc](https://x.com/godswayfoundinc/status/2112506617732153757)).
- A reusable voice line names register, texture and accent mechanics: "low gravel baritone, authentic Greek-British
  hybrid accent, Mediterranean vowels under clipped British consonants" ([@heavypulp](https://x.com/heavypulp/status/2080007449549967661)).
- TTS prompt structure: audio profile, scene, director's notes (style, breathing, pacing, articulation, accent),
  sample context; tags can be plain-English directions ([@_philschmid](https://x.com/_philschmid/status/2044669629012815965)).
- Put a tag exactly where the change happens; never two tags side by side ([@GoogleAI](https://x.com/GoogleAI/status/2047377023656436013)).
- With uploaded audio in Seedance, also type the spoken words into the prompt so it does not riff
  ([@CuriousRefuge](https://x.com/CuriousRefuge/status/2051473951768125646)).
- Direct breathing as part of the line; pick an exact emotion per line from an emotion wheel; always give the line's
  context ([@AdamCurleyVA](https://x.com/AdamCurleyVA/status/1999104127738229223)).

## Numbers (sources in craft-evidence.md)

| Speech | Words per minute |
| --- | --- |
| Everyday conversation | about 150 |
| Audiobooks, podcast hosts | 150-160 ([VirtualSpeech](https://virtualspeech.com/blog/average-speaking-rate-words-per-minute)) |
| BBC radio news | 168 ([Speech tempo](https://en.wikipedia.org/wiki/Speech_tempo)) |
| Phone calls, pauses included | 196, range 111-291 ([Yuan, Liberman, Cieri 2006](https://www.ldc.upenn.edu/sites/default/files/interspeech2006-towards-integrated-understanding.pdf)) |
| Auctioneers | about 250 |

- Budget words by clip length: 150 wpm = 2.5 words a second, so an 8 s clip holds about 20 calm words.
- Pauses: brief < 200 ms (comma), medium 200-1000 ms (full stop, ellipsis), long > 1 s only when thinking.
- Pitch: adult men 90-155 Hz, women 165-255 Hz. Creak and breath on purpose, not by default.
- Accent: first language + region + class/education + strength; ElevenLabs advises "thick" rather than "strong" and
  avoiding "foreign" or "exotic" ([Voice Design](https://elevenlabs.io/docs/product-guides/voices/voice-design)).
- ElevenLabs v4 has no style or speed sliders: control pace with text (punctuation, line length, tags).
- Cover-the-names test: remove speaker names from the script; you must still know who says each line.
