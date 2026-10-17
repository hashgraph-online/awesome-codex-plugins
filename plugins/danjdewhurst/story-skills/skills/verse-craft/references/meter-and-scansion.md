# Meter and Scansion

Meter is the pattern of stressed and unstressed syllables in a line.
Scansion is marking that pattern so anyone can check it. Show the marks;
never ask the author to take "it scans" on trust.

## Feet

| Foot | Pattern | Example |
|------|---------|---------|
| Iamb | da-DUM | a-WAY |
| Trochee | DUM-da | KEEP-er |
| Anapest | da-da-DUM | in the NIGHT |
| Dactyl | DUM-da-da | PAR-af-fin |
| Spondee | DUM-DUM | GREY ROCK |

## Meters

Name a meter by its foot and the number of feet per line: dimeter (2),
trimeter (3), tetrameter (4), pentameter (5), hexameter (6). Iambic
pentameter is five iambs: da-DUM da-DUM da-DUM da-DUM da-DUM.

Accentual verse (ballads, nursery rhymes, much song) counts only the
beats and lets the unstressed syllables vary. Say which kind the poem
uses before judging it.

## Finding a word's stress

1. Say the word in a normal sentence. Dictionary stress wins for words of
   two or more syllables (*KEEP-er*, *a-BOUT*, *PAR-af-fin*).
2. One-syllable words take stress from their role: nouns, main verbs,
   adjectives, and adverbs usually stress; articles, prepositions,
   conjunctions, and pronouns usually do not.
3. Stress is relative. Meter can promote a weak syllable a little
   (*and* on the third beat of "the KEEP-er AND his WIFE"), and a
   one-syllable verb between two stronger stresses can take a weak
   position ("when his CLOCK lost a HAND"); mark that as deliberate.
   Meter cannot shift a word's own stress: if it needs *KEEP-er* read as
   *keep-ER*, the line fails.
4. Accent changes stress and syllable count. Ask which accent the verse
   is for when a word such as *address*, *garage*, *fire*, *flower*, or
   *poem* sits on a key beat.

## Scansion table

Mark stressed syllables in capitals and separate feet with `/` (a `|`
would break the markdown table). Give the syllable count, the beat
count, the rhyme letter, and a verdict.

```markdown
| Line | Scansion | Syll | Beats | Rhyme | Verdict |
|------|----------|------|-------|-------|---------|
| 1 | a KEEP / er who LIVED / on a ROCK | 8 | 3 | A | ok |
| 2 | whose LAMP / was as TRUE / as a CLOCK | 8 | 3 | A | ok |
| 3 | when his CLOCK / lost a HAND | 6 | 2 | B | deliberate: *lost* demoted between two stronger stresses |
| 4 | he re-LIED / on the SAND | 6 | 2 | B | ok |
| 5 | and he KEEPS / his ac-COUNTS / in a SOCK | 9 | 3 | A | ok |
```

Verdicts:

- **ok** - the line fits the meter.
- **deliberate** - a variation the form allows (below); name it.
- **fault** - a stress on a weak syllable, a strong syllable forced weak,
  a missing or extra beat, or a stumble aloud. Say which, and propose a
  fix.

## Allowed variations

These are normal and do not need fixing:

- **Initial inversion:** a trochee in place of the first iamb
  ("KEEP-ing the LIGHT a-LIVE").
- **Feminine ending:** an extra unstressed syllable at the line end
  ("the LAMP was BURN-ing").
- **Headless line:** a missing first unstressed syllable in iambic verse
  ("LIT the LAMP and CLIMBED the STAIR"), or one or both missing in
  anapestic verse ("KEEP / er who LIVED / on a ROCK").
- **Anapestic substitution:** an anapest in iambic verse, or an iamb in
  anapestic verse, used sparingly.
- **Spondee:** two stresses together for weight ("GREY ROCK").

Two or more variations in one line, or the same variation in most lines,
means the poem is in a different meter than claimed. Say so.

## Common faults

- **Wrenched stress:** the meter forces a stress no speaker would use
  ("he LIT the LAMP with par-af-FIN", where speech says *PAR-af-fin*).
- **Padding:** filler added for a beat: *did* + verb, *so*, *oh*, *all*,
  doubled adjectives.
- **Elision to fit:** *o'er*, *e'en*, *'twas*, *th'* in modern verse. Only
  keep them in deliberate pastiche.
- **Syllable counting without stress:** ten syllables is not iambic
  pentameter unless the stresses fall on the even syllables.

## Verse in other languages

Everything above describes English accentual-syllabic verse. Languages
measure a line differently, so read `language` in `story.md` (a missing
field means `en`), or ask for a standalone poem, and scan by the
language's own tradition. Never scan non-English verse in English feet,
and never carry an English meter into a translation or a poem in another
language unless the author wants that effect.

| Tradition | What counts | Examples | How to scan |
|-----------|-------------|----------|-------------|
| Accentual-syllabic | Stresses and syllables | English, German, Dutch, Russian | As above, with the language's own word stress |
| Syllabic | Syllables, with fixed stress or a caesura | French alexandrine (12) and octosyllable (8); Spanish *octosílabo* and *endecasílabo*; Italian *endecasillabo* and *settenario* | Count syllables by the language's rules and mark the caesura or the fixed final stress |
| Quantitative | Long and short syllables | Classical Greek and Latin hexameter; Arabic and Persian *ʿarūḍ* meters | Mark each syllable long (–) or short (u) by the language's rules of vowel length and position |
| Mora-based | Morae (*on*), not syllables | Japanese haiku (5-7-5) and tanka (5-7-5-7-7) | Count *on*: a long vowel, `ん`, and a small `っ` each count one, so *Tōkyō* (とうきょう) is four |
| Tonal | Syllable count and tone pattern | Classical Chinese regulated verse (*lüshi*, *jueju*), five or seven characters a line | Mark each character level (平) or oblique (仄) and check the pattern |

Counting rules that trip agents:

- **French:** a mute *e* counts as a syllable before a consonant inside
  the line, not at the line end and not before a vowel, where it elides.
  Classical alexandrines break after the sixth syllable.
- **Spanish:** vowels across a word boundary usually join into one
  syllable (*sinalefa*). A line ending on a stressed final syllable
  counts one more; a line ending on a word stressed three from the end
  counts one fewer.
- **Italian:** vowels across a word boundary usually join, as in Spanish.
  The *endecasillabo* has its last stress on the tenth syllable.
- **Japanese:** count from the kana reading, not the kanji.

Adapt the scansion table to the tradition: keep the Line, Rhyme, and
Verdict columns and replace Scansion, Syll, and Beats with what the
tradition counts (syllables with elisions marked, long and short marks,
*on*, or tones). If you cannot scan a tradition reliably, say so and ask
the author or a native-speaker poet to check the lines.
