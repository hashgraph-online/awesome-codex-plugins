# Voices: cast, direct, make them sound real

Every rule below has a source; quotes are verbatim. Checked 2026-11-03.

## Why AI voices sound fake, and the fix

| Tell | Who names it | Fix |
|---|---|---|
| Rushed: too many words for the clip | Henry Daubrez (Google Flow filmmaker in residence): "When you're pushing 20 lines of text through a 30s generation, the model will speed through the delivery to fit all the lines" https://x.com/henrydaubrez/status/2117576741640151210 | Fewer lines per clip. "a 4-second shot will usually accommodate one or two short exchanges" (OpenAI Sora 2 guide) |
| Too clean: no room, no breath | Randy Thom (Skywalker Sound): ADR performances "almost always lack the "life" of the original" http://filmsound.org/articles/designing_for_sound.htm | Room tone under every line; ElevenLabs `audio_effects` (environment, distance, background noise) places the voice in a room at no extra cost https://elevenlabs.io/docs/overview/capabilities/text-to-speech |
| Over-cleaned | Mac Smith (Emmy, Skywalker Sound): "softening consonants and rounding off the dialogue ... can hurt the intelligibility" https://x.com/GiganticCranium/status/1942005349458039243 | Don't denoise generated voice; reduce only loud breaths (iZotope RX Breath Control "Target" mode) |
| Levelled flat | HyperFrames diagnosis: "A 4–6 dB spread across windows is normal speech ... Levelling a track that only has declination flattens the prosody and is heard as robotic." | Leave natural declination alone; fix only 12 dB+ unevenness |
| No soul in a synthetic character | Ben Burtt: "I went to synthesizers at first but the results sounded too much like a machine" (R2-D2 ended "50 percent electronic and 50 percent human") https://www.npr.org/transcripts/131968222 | Start robots and creatures from a human performance, then process it |
| Flat clone | digitalsamba toolkit: "A clone copies its reference clip's **pace and intonation**. If the lines come out fast and flat, the clip is fast and flat" | Fix the reference clip (more pitch movement, slower), don't time-stretch below 0.9x |

## Cast from candidates; a person picks

Voice director Khris Brown (launched the LucasArts voice department): "Target people who, in their reads, make you
feel something personal and emotionally resonant." and "Better no voice at all than poor voice."
https://www.gamedeveloper.com/audio/q-a-veteran-director-khris-brown-on-the-secrets-of-great-voice-acting

1. **Casting note** = role + listener + 2-3 precise adjectives: "Make everything into a role ... who is speaking?
   Neutral bystander? Impassioned preacher? Wry humorist? Helpful teacher? Caring nurse? Smiling enthusiast?"
   Replace "conversational" with a situation: "Toss off that last phrase like it's something you've discussed a
   million times" (voice actors on Game Developer, https://gamedeveloper.com/audio/directing-the-voice-over-actor-tips-for-better-communication).
2. **Shortlist 3-5 voices.**
   - Premade: filter by gender, age, accent, use case; listen to the preview. varg MCP `search_voices`; on
     `eleven_v4` pass the raw ElevenLabs voice id (it is in the preview URL path), e.g. Brian
     `nPczCjzI2devNBz1zQrb`, Jessica `cgSgspJ2msm6clMCkdW9`, Liam `TX3LPaxmHKxFdv7VOQHJ`, River
     `SAz9YHcvj6GT2YYXdXww` (HyperFrames' docs narrator: "Relaxed, Neutral, Informative", 145-155 wpm).
   - ElevenLabs Voice Design: "we'll generate three voice options for you" for the price of one preview. Prompt
     format: `Native <Language>. <Gender>, <Age range>. <Quality level>. Persona: <2–5 words>. Emotion: <2–3
     adjectives>. <1–2 sentences about timbre, pacing, delivery>`. Guidance scale: "High numbers can cause voice to
     sound artificial or robotic" (their examples: trailer voice 20%, relatable entrepreneur 40%). The preview text
     (100-1000 chars) "should complement the voice description, not contradict it". "thick" works better than
     "strong" for an accent; don't put FX words (reverb, echo, phone, tape) in a design prompt. Same seed + same
     inputs = same voice. https://elevenlabs.io/docs/eleven-creative/voices/voice-design
   - Gemini voice design: a 1-2 sentence description, e.g. "A warm, thoughtful astronomer in his late 60s with a
     gentle British accent, speaking with quiet wonder." https://ai.google.dev/gemini-api/docs/voice-design
     Gemini prebuilt traits as a shortlist: Charon informative, Kore firm, Puck upbeat, Algenib gravelly, Achernar
     soft, Enceladus breathy, Gacrux mature, Sulafat warm, Achird friendly, Sadaltager knowledgeable.
3. **Audition the hardest line**, 2 takes per voice, on one page (`scripts/audition.py`). Contrast two speakers:
   in Hume's blind test "mixed-gender pairs average 4.65 on speaker separation"; same-gender pairs 2.87-3.44
   https://www.hume.ai/blog/evaluating-multi-speaker-tts
4. **Screen with numbers, never pick by them.** Reject takes with wrong words (transcript), bleed or a second voice
   (DNSMOS `-p`), low naturalness (UTMOS). digitalsamba scores narration takes by pitch spread minus a penalty per
   10 wpm outside 140-170. "Human votes remain the preference ground truth; these are objective backstops."
   (tts-bench, https://github.com/5uck1ess/tts-bench)
5. **STOP: the person listens** on headphones and a phone speaker, and picks. Lock voice id, model, settings.

Casting by video type has no expert chart. Documented starting points: ElevenLabs' "Movie Trailer Voice" design
example ("Dramatic voice, used to build anticipation in movie trailers") at 20% guidance; phone-mic audio for UGC;
Seedance builds a voice from the character's look, so the character sheet casts the voice; ElevenLabs has no child
voices by policy; finance and trust-heavy niches cast an older voice (prior X bank, MethodByVid, 6,276 saves).

## Direct it: exact syntax per model

| Model (varg id) | Pause | Breath, reaction | Delivery | Watch out |
|---|---|---|---|---|
| ElevenLabs v4 / v3 (`eleven_v4`, `eleven_v4_turbo`, `eleven_v3`) | `...`, a line break, `[pause]`, `[short pause]`, `[long pause]` | `[sighs]` `[exhales]` `[laughs]` `[laughs harder]` `[clears throat]` `[inhales deeply]` `[exhales sharply]` `[chuckles]` `[swallows]` | `[whispers]` `[sarcastic]` `[curious]` `[excited]` `[crying]` `[mischievously]`; a stage note before a paragraph: `[Low, steady voice, restrained urgency]`; CAPS for emphasis | v4/v3 ignore SSML `<break>`; only tags you can hear ("DO NOT use tags such as [standing], [grinning], [pacing], [music]"); narrative cues ("she asked, her voice trembling") are read aloud; write `[low, gravelly voice]`, not a tag that reads as a sound cue |
| ElevenLabs older (`eleven_multilingual_v2`, flash, turbo) | `<break time="1.5s" />` up to 3 s | | | "Using too many break tags in a single generation can cause instability" |
| Gemini 3.8 TTS (`gemini_3_8_flash_tts`) | `<short pause>` `<long pause>` | `<breath>` `<heavy breath>` `<exhales>` `<sigh>` `<cough>` `<chuckle>` `<laugh>` `<gasp>` `<sob>` `<yawn>` `<throat-clearing>` ... | `style` (varg: `provider_options.fal.style_instructions`): short, "whispered urgently" | "Long-form "Audio Profile" paragraphs and multi-bullet "Director's Notes" ... are the most common cause of voice drift"; split the turn when emotion changes; listener reactions as `|oh hmm|` inside a turn |
| Google Cloud Gemini-TTS | `[short pause]` ~250 ms, `[medium pause]` ~500 ms, `[long pause]` 1000+ ms | `[laughing]` | style prompt | emotion tags like `[scared]` are spoken aloud |
| Fish Audio S2 / Drama 3 | `[pause]` `[long pause]` | `[inhale]` `[exhale]` `[sigh]` `[shaky breath]` `[small laugh]` | `[barely holding it together, forcing a smile]`; `<emphasis>...</emphasis>` | "Tags affect what comes after them. Place the tag right before the point where you want the shift to happen." "Takes vary, so render a few" |
| OpenAI `gpt-4o-mini-tts` | in `instructions` | in `instructions` | labelled fields: Voice Affect, Tone, Pacing, Emotion, Pronunciation, Pauses (openai.fm presets) | shuts down 2027-01-06; usage policy requires telling listeners the voice is AI |
| Hume Octave | `[pause]`, `trailing_silence` | | under 100 characters: "frightened, rushed" | rate goes in `speed` (0.5-2.0), not words |
| Dia (open) | | `(laughs)` `(sighs)` `(gasps)` `(sniffs)` `(inhales)` `(exhales)` ... | `[S1]`/`[S2]` speakers | under 5 s of audio sounds unnatural; over 20 s speeds up |

Settings: ElevenLabs stability "Lower values (0.30-0.50) create more emotional, dynamic delivery but may
occasionally sound unstable. Higher values (0.60-0.85) produce more consistent but potentially monotonous output."
Eleven v4 has only Stability and Similarity (no Style or Speed). Spell out numbers, symbols and URLs before TTS
("$42.50" -> "forty-two dollars and fifty cents"). Fix names on v4 with IPA in slashes: `"/ˌbaɪoʊˈkemɪstri/"`.
ElevenLabs' own "Enhance" prompt is a safe agent instruction: "DO NOT alter, add, or remove any words from the
original dialogue text itself. Your role is to *prepend* **audio tags**, not to *edit* the speech."
Sources: https://elevenlabs.io/docs/overview/capabilities/text-to-speech/best-practices ,
https://ai.google.dev/gemini-api/docs/speech-generation , https://cloud.google.com/text-to-speech/docs/gemini-tts ,
https://fish.audio/blog/how-to-use-inline-tags-in-fish-audio-s2/ , https://github.com/openai/openai-fm ,
https://github.com/nari-labs/dia

## Our test: what direction does (eleven_v4, 2026-11-03)

One line, four versions, Jessica and Liam, 2 takes each, $0.24. Whisper transcript + ffmpeg + librosa.

| Version | Length | Words/min | Pause after "break it" | Loudness |
|---|---|---|---|---|
| Bare: `I didn't mean to break it. I was only trying to fix the light before you got home. I'm sorry.` | 5.7 s | 231 | 0.36 s | -26.5 LUFS |
| + `...` and `—` | 6.5 s | 207 | 0.51 s | -26.8 |
| + `[exhales]` `[sniffs]` `[swallows]` | 8.7 s | 194 | 0.92 s | -29.8 |
| + `[quietly, ashamed]` `[voice breaking]` | 8.0 s | 200 | 0.89 s | -31.6 |

0/16 tags spoken, 16/16 transcripts match the script. "quietly" lowered the read 5 dB: re-level after directing.
Varg returns the cached file for an identical request: change the text slightly for a second take.

## One voice across shots

- **Voice block per character**, repeated in every prompt, then a DELIVERY line per moment: "27-year-old male, light
  casual working-class British accent, street-level London-adjacent ESTUARY, NOT cockney. Warm mid-range, youthful,
  relaxed, slightly rough with a light rasp." (PJ Ace, https://x.com/PJaccetturo/status/2100218146703696189)
- **Clone and re-dub:** "I pulled a clean line from VEO 3.1 ... duplicated it to build up around 10s of voice sample
  ... muted VEO's baked audio, regenerated voices in Eleven Labs and re-synced manually." (Daubrez,
  https://x.com/henrydaubrez/status/1991623042943037953)
- **Kling:** "If you choose a subject with a pre-bound voice tone, it's not recommended to set the tone again in the
  prompt." https://kling.ai/quickstart/klingai-video-3-model-user-guide
- **Seedance voice reference:** black-screen video with the voice (Kavan Cardoza's method via PJ Ace, May 2026,
  https://x.com/PJaccetturo/status/2054926137659417076) vs an ElevenLabs v4 mp3 (PJ Ace, Nov 2026). Test both.
  Dry references: "Seance will automatically apply the correct environmental reverb" from the location prompt.
- **Voice changer** to pull drifting native voices to one target (MetaPuppet, https://x.com/MetaPuppet/status/1943380104719274327).
- **Perform it yourself:** "Transfer the performance, movement and audio from Video 1 onto the the character Image 1.
  Do not add any music" (Uncanny Harry, https://x.com/Uncanny_Harry/status/2087589869354672222).
- **Series:** one narrator, model and pace for every film; stop rather than fall back to another voice (HyperFrames
  had to re-voice three docs films).

## Consent and disclosure

- ElevenLabs: "You can only create a Professional Voice Clone of your own voice. Even with their consent, you cannot
  clone someone else's voice." Instant clones require confirming "the right and consent to clone the voice".
- Gemini voice replication needs a 10-30 s clip plus a consent recording by the same adult speaker.
- Open weights forbid it too: Sesame CSM "Do not use this model to generate speech that mimics real individuals
  without their explicit consent"; Fish Drama 3's licence bans cloning a real person without consent.
- YouTube needs an AI label for realistic content that makes a person seem to say what they did not; cloning your
  own voice for voice-over or dubs needs none (https://support.google.com/youtube/answer/14328491).
