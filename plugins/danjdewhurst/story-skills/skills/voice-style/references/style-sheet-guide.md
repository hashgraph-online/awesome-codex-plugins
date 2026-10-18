# Style Sheet Guide

`style-sheet.md` sits in the project root next to `story.md`. It is
optional; `story validate` checks it when present and `story prose` reads
it.

## Frontmatter

```yaml
---
type: style-sheet
dialect: british
preferred:
  - use: toward
    avoid: towards
  - use: OK
    avoid: okay
watch-words:
  - almost
  - a beat of silence
allow-words:
  - quietly
---
```

- `type` must be `style-sheet`.
- `dialect` is `british`, `american`, or `unspecified`. British or American
  turns on a built-in list of common spelling pairs (colour/color,
  grey/gray, defence/defense, travelled/traveled, and their inflections).
  -ise/-ize is not in the list because British publishers use both; add
  `preferred` entries for the words the book uses. The pairs are English:
  for a book in another language use `unspecified`, and record that
  language's variant choices (Brazilian or European Portuguese spellings,
  German reformed or traditional spelling) as `preferred` entries.
- `preferred` entries need a non-empty `use` and `avoid` that differ. The
  frontmatter parser does not read inline lists, so write one entry per
  avoided form. A style-sheet entry naming either word of a built-in dialect
  pair replaces that pair.
- `watch-words` may be phrases. Matching is case-insensitive on letter
  boundaries, so compounds (*grey-haired*) and possessives count.
- `allow-words` silences built-in filter words, -ly adverbs, echo words,
  said-bookisms, and dialect pairs.
- `add-words` and `replace-words` change the language pack's word lists
  for this book, one `- list-name: word, word` entry per line, such as
  `- said-bookisms: rugió, bufó` or `- filter-words: []` (an empty list).
  `replace-words` drops the pack's list first; `add-words` adds to it, or
  supplies a list for a language with no pack, which turns its check on.
  The list names are in `docs/project-format.md`, Word lists. Add words
  only when the author asks for them, then run `story validate`, which
  warns about a list name it does not know.

## Sections

**Voice.** Narrative distance (how close to the POV character's head),
sentence rhythm, register (formal, plain, lyrical), and what the prose never
does. Quote two or three sentences from the draft that sound exactly right;
a quoted sample calibrates better than adjectives.

**Spelling And Usage.** Explain the dialect choice and every exception.
Usage rules such as *all right* not *alright*, *OK* not *okay*, *toward*
not *towards*.

**Capitalisation.** Titles and ranks (*the king* vs *King Aldric*),
institutions, invented terms, deities, and directions (*the North* as a
region). Invented terms also get glossary entries with `story add term`
(see the `worldbuilding` skill). After you add terms, run `story reindex .`, `story wordcount . --write`, and `story check .`.

**Hyphenation And Compounds.** Every compound the book has settled:
*ember-stone*, *half-light*, *well-known* before a noun.

**Numbers, Dates, And Time.** Spelled-out threshold, how in-world dates and
calendars are written, and how time of day is told.

**Dialogue And Punctuation.** Double or single quotes, closed or spaced
dashes, ellipsis style, what italics are for, and the default tags
(in English, *said*/*asked* plus action beats is the usual baseline).
Other languages use guillemets, dialogue dashes, corner brackets, or
spaces before punctuation: choose and record them with
`../../line-editing/references/language-conventions.md`, including one
example line of dialogue with a tag.

**Character Voices.** One line per POV character or major speaker, linked
to the character file:
`- **[Sera Voss](characters/sera-voss.md)** — direct; clipped when stressed.`
The character file's Voice & Speech Patterns section stays canon.

**Watch List.** Why each watch word is on the list and the rule for it
(*one per scene*, *replace with the concrete noun*).

## Extracting a voice from sample prose

Read at least 1,000 words and note, with examples:

1. Distance: are feelings named (*she was afraid*) or shown through the body?
2. Rhythm: typical sentence length and when it changes. `story prose .`
   reports average, longest, and spread per chapter.
3. Register: vocabulary level, contractions, profanity, era markers, and
   in languages that have them, forms of address (*tu*/*vous*,
   *du*/*Sie*) and politeness levels.
4. Figurative language: how often, and drawn from which domain (the POV
   character's world, not the author's).
5. Paragraphing: long blocks or frequent breaks; one-line paragraphs for
   impact or not.
6. What never appears: the absences are part of the voice.

Write the Voice section from these notes, then show it to the user before
drafting further.
