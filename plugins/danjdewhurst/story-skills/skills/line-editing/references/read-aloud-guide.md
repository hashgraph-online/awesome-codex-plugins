# Read-Aloud Guide

The ear catches what the eye skips: stumbles, accidental rhymes, a
sentence too long to say in one breath, three paragraphs with the same
rhythm, dialogue no one would speak. A read-aloud pass is the cheapest
line edit there is.

## Build the narration script

```shell
story build . --format narration
```

The script is markdown with a pronunciation guide (from every
`pronunciation` field on characters, locations, factions, artifacts, and
glossary terms), each chapter with an estimated runtime at 155 words per
minute, scene breaks marked `[pause]`, and a total runtime. Missing
pronunciations for invented names are a finding: add a `pronunciation`
scalar (for example `SEER-sha`) to the entity file.

## Listening options

1. **The author reads aloud.** Best, because the author hears their own
   intended rhythm. Suggest it for key chapters (opening, midpoint,
   climax, ending).
2. **System text-to-speech.** Flat but honest: a synthetic voice does not
   smooth over awkward syntax. Check what is installed before offering:

   ```shell
   command -v say espeak-ng spd-say
   ```

   - macOS: `say -f chapter.txt` or `say -o chapter.aiff -f chapter.txt`
   - Linux: `espeak-ng -f chapter.txt` or `spd-say "$(cat chapter.txt)"`
     (short passages)

   Extract only the chapter prose into a scratch text file outside the
   story project, and delete it afterwards. **Ask before installing any
   package.** If nothing is installed, the author's own reading or their
   device's built-in screen reader works.
3. **The agent reads for sound.** Without audio, read each sentence for
   breath length, stress pattern, and repeated sounds. Weaker than
   listening; say so.

## What to listen for

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Stumble or re-read | Garden-path syntax, ambiguous modifier | Reorder so the subject and verb come early |
| Run out of breath | Sentence too long for its content | Split at the turn, or make the length earn itself |
| Sing-song | Same length and stress, sentence after sentence | Vary by intent: a fragment, a long cumulative line |
| Unintended rhyme or jingle | Sound echoes (*the light was bright tonight*) | Swap one word |
| Tongue-twister | Clustered sibilants or plosives | Rephrase, unless the tongue-twist is the effect |
| Dialogue sounds written | Complete, grammatical, speech with no interruption | Contractions, fragments, interruption, subtext |
| Same voice for everyone | Undifferentiated dialogue | See the differentiation levers in `line-edit-checklist.md`; run `story voices .` |
| Name mispronounced | Invented name with unclear stress | Add `pronunciation`; consider a simpler spelling |
| Drag | Scene summary or exposition between beats | Mark for `scene-craft` or `revision-continuity` |

## Recording findings

Record each finding as an edit note (see `edit-note-format.md`) with the
chapter and paragraph, the problem heard, and a proposed fix. Group by
chapter. The narration runtimes are also useful for pacing: a chapter far
longer to hear than its neighbours is worth checking with `story pacing .`.

## Picture books and chapter books

For `picture-book` and `chapter-book` forms, read-aloud is not optional:
the text will be read aloud by an adult to a child. Listen for page-turn
rhythm, refrains, and words a young listener cannot parse.
