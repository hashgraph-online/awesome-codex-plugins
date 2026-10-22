# Composition plans

Homie plans music as sections with their own length, lyrics and styles. Discover the official
ElevenLabs MCP music capability and read its current schema before adapting this local plan
to a generation request; the local plan is not a promise about a provider API.

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
  seconds; the boundaries are rounded to the millisecond so the planned total is exact. Measure
  the generated audio before relying on these boundaries.
- **Local planning limits.** Each section 3 s to 120 s (at 120 BPM a bar is 2 s, so the shortest section is 2
  bars); the whole song 3 s to 10 min; a line up to 200 characters.
- **Styles.** The first chunk carries the global styles, the tempo and the key (they set the whole
  song); every later chunk repeats the tempo and adds its own. `avoid` becomes each chunk's
  negative styles; an instrumental section also avoids vocals and says `{instrumental, no vocals}`
  in its text (text in curly braces is a direction, not a lyric).
- **Lines.** A sung section's text is `[Name]` and its lines. About one line a bar at pop tempos,
  two at most; more comes back rushed or skipped.

## Generation and review

Read the discovered music tool's model guide, supported durations, lyric controls and output
formats. Adapt the plan to that schema; do not send unsupported fields or assume a fixed model.
Quote the requested duration through the official integration where available, and keep it
within the approved budget. Record unknown cost explicitly when no quote is exposed.

Short hooks and contractions can drift. Listen to every sung line; use an official transcription
capability if available and compare the words with the plan. The page should show what is
actually sung. Timestamps are optional provider output, not guaranteed by Homie.

Keep the original audio under `music/<slug>/work/`, along with the local composition plan and
any usable timing metadata. Place the final audio through `homie-studio media import` and keep
its normalized receipt in `media/provenance.json`. Local analysis, mastering and loop commands
operate on downloaded files; they do not generate music or inspect provider credentials.
