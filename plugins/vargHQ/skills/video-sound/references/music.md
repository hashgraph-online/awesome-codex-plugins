# Music: decide it, map it to the beats, finish it in the edit

## How much, and where

- Murch: "approach music in films the way you would approach administering drugs" (https://www.webofstories.com/play/56752).
  No Country: "There is actually music in the film, but it's always snuck in behind wind or car sounds" (Carter
  Burwell). Creator editor Hayden Hillier-Smith (MrBeast, Mark Rober): "I couldn't make anything without nailing the
  perfect soundtrack first." Genre decides; say which in `plan.md`.
- Take it away once: "They let us settle into the language of the film, so they can take it away from us ... There
  was no music, slow cuts" (Hillier-Smith on Civil War). "When you fade music out in a piece, the silence has the
  subtle effect of spotlighting whatever comes directly after." (NPR's Michael May) "Sudden silence ... can be the
  strongest kind of hit. Use it with caution." (composer Jon Brantingham)
- Under a voice: "Look for music that feels "incomplete," that has left sonic room for another element"; no vocals;
  "instruments that inhabit the same frequency as the voice are problematic (trumpets, etc.)"; "Think "pensive" or
  "hopeful" — avoid "sad" or "happy."" (NPR Training, https://www.npr.org/sections/npr-training/2025/05/31/g-s1-67187/score-best-practices-for-using-music-in-audio-storytelling)
- Spotting: "We can reduce the score's role into three elements: emotion, intensity, and perspective." and "With
  every temp track, we ask "why this, why now?"" (composers Coole and Nettleship). James Horner on too many
  "catches": "very difficult to write really wonderfully lyrical music when you're always having to accentuate what
  picture does."
- Lyrics: "If the spot is trying to sell a fun experience, lyrics about complicated love will be wrong ... people do
  listen to the words." Keep instrumental versions (Paul Greco, JWT).
- Order: "You should do audio first" (Derek Lieu). When dialogue sets the timing, "I built the edit around the
  performances, then generated music to fit" (Burak Tuyan).

## Tempo, length, the beat map

- "how the tempo feels is more important than the technical beats per minute (BPM)" (Julia Trainor, music supervisor).
- "Fast tempos give forward momentum ... Slow tempos can have an effect of freezing time." (Brantingham)
- Genre bands (Stable Audio guide): 60-80 ballads, 80-100 R&B and house, 100-120 pop, 120-140 upbeat pop and techno,
  140-160 dubstep and metal. Measured launch films: 108-136 BPM, median 123; music under 89-100% of the film (earshot).
- Bars: one 4/4 bar = 240 / BPM seconds (2.0 s at 120). "120 BPM, 7 bars, something happens on every beat." (launch
  brief, 21,165 saves, https://x.com/twoclipping/status/2103273003555402193). Story pieces: "you never want to cut
  your film too closely to the beat of the track. Doing so will always result in a final product that feels like a
  music video." (Noam Kroll)
- Fit the hits: test a tempo range (Brantingham: 117-123 BPM in 0.25 steps) and keep the one whose beats land
  fewest frames off the hit points. Name the exact seconds in the brief: "The track's hit goes on 9.97s, whooshes on
  8.66 and 9.80." (twoclipping)

Beat map format (plan.md):

```markdown
| time    | bars | music                         | voice / picture                 | effects                  |
|---------|------|-------------------------------|---------------------------------|--------------------------|
| 0-8 s   | 1-4  | just a muted pulse + hi-hat   | L01 at 0.5 s                    | click on the 4.0 s cut   |
| 8-12 s  | 5-6  | sub bass enters               | L02 at 8.25 s                   |                          |
| 12-13 s | 1/2  | stopped on the bar line       | hold; room tone only            | whoosh swells, peak 13.0 |
| 13 s    | 7    | re-enters on the downbeat     | logo lands                      | impact 13.0              |
| 14-20 s | 7-10 | groove, then ring out         | L03 at 14.0 s                   |                          |
```

## Prompting music models

| Model (varg id) | What works | Known failures |
|---|---|---|
| ElevenLabs Music v2.5 (`eleven_music_v2_5`; `provider_options.elevenlabs.music_length_ms`, `force_instrumental`) | "A prompt answers five questions ... genre, mood, instrumentation, tempo, and production era. Any question you leave open, the model answers with the most statistically likely choice". Studio words move levers ("sidechained, close-mic'd, bone-dry, tape saturation, plate reverb"). "start with just a shuffled drum loop, add a warm sub bassline after four bars, then bring in chopped vocal stabs" - "Without the just, the model fills the silence". Loops: "state the bars, the BPM, the key — and state what's banned". The ElevenLabs API also takes composition plans: up to 30 sections with `duration_ms`, the first section's styles set the genre. | naming an artist or song returns an error (ElevenLabs bans artist, song, album, label names). Our test: BPM held 3/3; planned half-bar silence + hit 0/3; 20 s asked, 29 s back once |
| Lyria 3.5 (`lyria_3_5`) | `[Genre & style] + [Mood] + [Instrumentation] + [Tempo & rhythm] + [Vocal style & language] + [Lyrics]`; "instrumental" to drop vocals; timed sections: "[0:12 - 0:24] Verse 1: The laid-back drum beat enters ... Intensity: 3/10 (Low)"; "Build to a beat drop at 12 seconds"; "point out that it can use timestamps to align audio with video events" (fofr, Google DeepMind) | no negative prompt on 3.5 (varg spec); in our October run it ignored `duration` (20 s asked, about 90 s back): ask for length in the prompt and fit |
| Suno v6 | lyrics field as a timeline: `[MASSIVE DROP: XXX Cloud Trap] / [The trap beat cuts out instantly] / [Just the sad acoustic guitar and the vinyl crackle] / [Fade to silence]` (INK); Exclude field; "Designed as background music. Easy to sample and loop." for beds; video upload: "make a soundtrack to this video" | "All models prior to v6 have been retired": older tag tricks need re-testing; tempo can speed up across a song (composer Tomoya Kinoshita); an unwanted sound often comes from one style word ("subtle brushed drum"): delete it |
| Mureka 9.5 (`mureka_9_5`) | instrumental from up to 1,024 characters | the model picks the length |
| Stable Audio 2.5 | genre, key instruments, mood, details, then the use: "perfect for opening credits" | |
| ACE-Step 1.5 (open) | `bpm`, `keyscale`, `duration` as parameters: "Don't write tempo, BPM, key, and other metadata information in Caption"; 6-10 syllables per lyric line | "Final result might be 118 or 122, not exactly 120" |

Always measure what came back (`sound.py beats`). In our test librosa's tempo estimate read 117.45 for a 120 BPM
take (tempo bins; the average beat gap gives 120.0) and the downbeat guess was half a bar off on a uniform pulse;
the bass entry at bar 5 showed the real bar line. Convert MP3 to WAV before analysis ("MP3 files can have slight
offset differences", All-In-One). For true downbeats and labelled sections use Beat This! or All-In-One (`allin1`).

## Edit music to length

- Whole bars: "find the first beat of a bar ... then cut out (or copy and paste) as many bars as you need" (May).
  Cut whole sections; at the splice "there was a double beat there ... So we're going to take one out" (Brent Pierce).
- Button, don't fade: "The goal is to take the music ending and move it up where the video ends." (Danny Greer)
  Button endings are "1 – 4 seconds to your final note, leave the tail on". `sound.py fit` keeps the opening and the
  real ending and removes downbeat-to-downbeat bars from the middle.
- Stops and drops in the edit: two music cues in `cues.json` (cut on a bar line, back on a later downbeat), room tone
  through the gap, an impact on the downbeat.
- Picture choreographed to a song: "we tried to set ourselves a rule of not editing the music"; "If you cut 2 seconds,
  the whole rest of the scene will suddenly drift." Action runs long? "loop it cleanly over a little riff and once it
  was mixed in with all the other sound effects the audience would never be aware of it." (Machliss)
- Trailers: "a compelling intro, a building main section and a massive ending"; "Gaps between sections are thus
  essential"; "Trailer endings typically reach a huge climax but don't resolve" (Dan Graham, Gothic Storm). Music
  progresses "after you've finished giving a piece of information. They're chapter breaks." (Adam Gonzales, AV Squad)
- Under narration: `demucs --two-stems=vocals song.mp3` -> `no_vocals.wav`. Lower only the clashing stem when you
  have stems (music editor Jim Harrison).
- Automatic remix tools (Premiere Remix) work within about ±5 s and slice lyrics: instrumentals only (Larry Jordan).
- One theme in many versions: "10, 15, 20 versions of it with different instrumentations and different tempos and
  moods" (Ken Burns' team). Generate a dozen variations and edit stems together (Daubrez).

## Licences

| Service | Commercial use |
|---|---|
| ElevenLabs Music | "All online and offline commercial use permitted, except film, TV, radio, and Studio Games" on self-serve plans; free plan downloads not permitted; no artist, songwriter, song, album, publisher or label names in prompts (https://elevenlabs.io/music-terms) |
| Suno | "Songs downloaded while subscribed are granted commercial use rights"; free-plan songs: "we retain ownership"; Pro 20 / Premier 60 downloads a month; "Music made 100% with AI would not qualify for copyright protection" |
| Udio | "downloading of audio, video, and stems has been disabled" |
| Lyria | "Google won't claim ownership over that content" but "may generate the same or similar content for others"; SynthID watermark |
| Mureka API | "All content generated through paid API calls comes with full usage rights and commercial authorization." |
| Stable Audio 3.0 | community licence under $1M revenue; you own outputs |
| TikTok ads | Commercial Music Library; "filter for songs approved for business use" |
| Library tracks | Mixkit and Pixabay are free for commercial use; note the source and licence per track |
