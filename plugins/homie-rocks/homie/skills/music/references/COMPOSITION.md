# Composition plans

ElevenLabs Music (`music_v2`) takes either a short prompt or a **composition plan**: a list of
chunks, each with its own length, text, and styles. Anything with words goes through a plan.

## The spec `plan` reads

```json
{
  "title": "Paper Lanterns",
  "bpm": 118,
  "key": "D minor",
  "beatsPerBar": 4,
  "styles": ["bright indie synth-pop", "punchy live drums", "warm female lead vocal, clear diction, close to the mic", "big hook"],
  "avoid": ["rap", "heavy autotune", "spoken word"],
  "sections": [
    { "name": "Intro", "bars": 4, "instrumental": true, "styles": ["filtered arpeggio, no drums yet"] },
    { "name": "Hook", "bars": 8, "lines": ["We light the paper lanterns", "and let the whole night see"], "styles": ["full drums", "stacked harmonies"] },
    { "name": "Verse", "bars": 8, "lines": ["Ten more minutes on the rooftop", "the city humming under me", "every window is a story", "and none of them are asleep"] },
    { "name": "Outro", "bars": 4, "instrumental": true, "styles": ["drums fall away", "ends on a held chord"] }
  ]
}
```

What `plan` does with it:

- **Whole bars.** A section of `bars` bars at `bpm` lasts `bars × beatsPerBar × 60 / bpm`
  seconds; the boundaries are rounded to the millisecond so the total is exact. For `music_v2`
  ElevenLabs holds every section to its length, so section starts are bar lines in the render.
- **Limits.** Each section 3 s to 120 s (at 120 BPM a bar is 2 s, so the shortest section is 2
  bars); the whole song 3 s to 10 min; a line up to 200 characters.
- **Styles.** The first chunk carries the global styles, the tempo and the key (they set the whole
  song); every later chunk repeats the tempo and adds its own. `avoid` becomes each chunk's
  negative styles; an instrumental section also avoids vocals and says `{instrumental, no vocals}`
  in its text (text in curly braces is a direction, not a lyric).
- **Lines.** A sung section's text is `[Name]` and its lines. About one line a bar at pop tempos,
  two at most; more comes back rushed or skipped.

## Traps, measured

- **A prompt with `lyrics_text` has come back with nothing sung.** Words go in the plan's
  sections. `render --prompt` refuses words for this reason.
- **`output_format` is a query option, not a body field.** Put in the JSON body it is rejected
  before anything is sent. The script passes `--output-format mp3_48000_192`.
- **Short hooks drift.** In one render a three-word hook came back as a different three words;
  making the key word unambiguous (and on a strong beat) fixed it in the next render. The lyric
  check (Scribe) is what catches this, not listening once.
- **Contractions drift.** "I'll wake up" came back "I wake up": the check passes lines at 75 % of
  their words, and the page should show what is actually sung.
- **The cost is about 27.5 credits per second** of `music_v2` on a paid plan (1,015 credits for
  37 s and 5,204 for 189 s, measured). The quote uses this; the render records the real number off
  the account.

## What a render leaves

`music/<slug>/work/render-<n>.mp3` (the audio as rendered), `render-<n>.json` (the plan
ElevenLabs used, song metadata, and word timestamps: the model's own times for every sung
word, which the `video` skill uses for lyric type), `music/<slug>/render.json` (the latest),
`budget.json` (the cap and every call), and a line in `music/receipts.jsonl`.
