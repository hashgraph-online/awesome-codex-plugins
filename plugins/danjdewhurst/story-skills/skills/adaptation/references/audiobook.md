# Audiobook

## Narration Script

```shell
story build . --format narration --out adaptations/audiobook/narration-script.md
```

The script has a pronunciation guide table built from every
`pronunciation` field, then each chapter with its estimated finished
runtime at 155 words per minute (about 9,300 words per finished hour),
scene breaks as `[pause]`, and the total runtime. Actual pace varies by
narrator and genre; thrillers read faster than literary fiction. Use the
total to budget, not to promise.

155 words per minute is the English narration rate. Speech rate in words
differs by language, because words differ in length, so the build uses
the rate in the language pack for `language` in `story.md` (120 words a
minute for German) and English's rate for a language with none. A book
counted in characters (Chinese and Japanese, or `count-unit: characters`)
is timed at 300 characters a minute; Mandarin narration runs a little
slower, and the count includes punctuation. The script's first line names the rate it
used. These are starting estimates: time the narrator reading a sample
chapter and rescale the totals.

The opening and closing credits are in the book's language, from the
pack's build labels; the headings and `[narrator]` marker stay in
English. In a collection or anthology, each story with its own chapter
`author` has a spoken credit after its heading (`Written by Ines
Calder.`), and the opening credits name the `editor` and then the story
authors the book's credits leave out. Check the credits with the user
before recording.

Rebuild after every manuscript or pronunciation change. The file is
generated; keep narrator notes in `production.md`, not in the script.
`--out` never replaces an existing file under `adaptations/`, so delete
the old script before rebuilding it.

## Pronunciation

Add `pronunciation` to any character, location, faction, artifact, or
glossary term whose name a stranger could misread:

```yaml
name: Seersha Vale
pronunciation: SEER-sha VAYL
```

- Respell in plain syllables with the stressed syllable in capitals.
  Avoid ambiguous spellings (`th` in *thin* or *this*? write
  `TH as in thin`).
- Respell for the narrator's language. `SEER-sha` assumes English
  spelling; a German or Spanish narrator would read it differently. For
  a book in another language, respell in that language's spelling
  conventions, mark stress the way its narrators expect, and add IPA
  when the author or narrator wants it. In languages with tone or
  pitch accent, ask how the narrator wants it marked. In Japanese, the
  kana reading usually does this job.
- Include invented words, made-up units, non-English names, real places
  with local pronunciations, and any name with a silent letter.
- For real places and names, record the source (a local speaker, a
  pronunciation dictionary) in a research note; do not guess.
- Aliases that sound different need their own guide entry in the
  character body.

## Read-Aloud Review

Mark each for a narrator note or an author decision:

- Dialogue runs of four or more lines without a tag: the listener loses
  track of the speaker. A narrator can voice characters, but an added tag
  may still be needed.
- Visual devices: text messages, letters, lists, tables, maps, chapter
  epigraphs, unusual typography, footnotes. Decide how each is read (a
  voice change, "a text from Mara:", or cut).
- Homographs whose meaning depends on context (*lead*, *read*, *wind*).
- Scene breaks that rely on white space: the `[pause]` marks them.
- Front and back matter: most audiobooks replace the copyright page and
  also-by list with spoken opening and closing credits.

## Production Routes

Check each platform's current terms, royalty shares, and exclusivity rules
before choosing.

- **ACX** (Audible, Amazon, Apple): the author posts the book, holds
  auditions, and pays the narrator per finished hour, shares royalties with
  them, or a mix. Exclusive distribution pays a higher royalty than
  non-exclusive and binds the audiobook for a set term.
- **Findaway Voices by Spotify** and other wide distributors: distribute
  an audiobook the author has produced to many retailers and library
  platforms, with author-set pricing.
- **Hire a producer or narrator directly:** the author owns the files and
  can distribute anywhere.
- **Audio rights sold to an audio publisher:** the publisher produces it.
  See the `publishing` skill's rights inventory.

## Narrator Auditions

1. Write a casting brief: genre, tone, POV and tense, the narrator's
   voice (gender, age range, accent), the main characters with accents and
   ages, and the pronunciation guide.
2. Choose an audition script of 2-5 minutes that covers narration, the
   hardest dialogue scene, at least two main characters, and a name from
   the pronunciation guide.
3. Judge on: pace, character distinction, pronunciation, emotional range,
   and clean audio. Listen at normal speed on ordinary headphones.
4. Agree in writing: rate or royalty share, schedule, rounds of
   corrections, and who owns the files. Not legal advice; see the
   `publishing` skill's contract checklist.

## Files And Audio Checklist

Platforms set strict technical specs. These are typical of ACX and similar
platforms; check the platform's current spec:

- [ ] One file per chapter, plus separate opening credits, closing
      credits, and a retail sample
- [ ] Opening credits: title, author, narrator; closing credits: "The
      end", title, author, narrator, copyright line
- [ ] Retail sample: a few minutes, usually from early in the book, with
      no explicit content and no credits
- [ ] Consistent loudness and a low noise floor within the platform's
      range; peaks below its ceiling
- [ ] Room tone at the head and tail of every file, within the
      platform's range
- [ ] Mono or stereo consistently, at the platform's required format and
      bitrate
- [ ] No mouth clicks, breaths cut mid-word, or edits audible
- [ ] File names in order (`00-opening-credits`, `01-chapter-01`, ...)
- [ ] Square cover art at the platform's size, reformatted from the book
      cover
- [ ] Pronunciations spot-checked against the guide

Map chapters to files from the narration script's chapter list: runtimes
there estimate each file's length.

## AI Narration

- Some platforms accept AI or synthetic narration, some restrict it, and
  some offer their own synthetic voices. Check the platform's current
  policy.
- Disclose it: platforms and listeners expect synthetic narration to be
  labelled. Add it to `ai-disclosure` in `story.md` and to the retail
  description.
- Voice cloning of a real person needs that person's written consent.
- Synthetic narration still needs the pronunciation guide and a
  human listen-through for errors.

## Production File

```markdown
---
type: audiobook-production
story: {story-id}
updated: YYYY-MM-DD
---

# Audiobook: {Title}

- Route: {ACX | Findaway Voices | direct | audio publisher}
- Narrator: {name, as supplied by the author}
- Estimated runtime: {from the narration script}
- AI narration: {none | details}

## Narrator Notes

| Chapter | Note |
|---------|------|

## Files

| File | Chapter | Status |
|------|---------|--------|
```
