# Copyedit and Proof Checklist

A copyedit makes the text correct and consistent with `style-sheet.md`.
It does not change voice or meaning. Tell the user plainly: this pass
catches much, but it is not a substitute for a professional copyeditor on
a book going to print.

Before starting, run `story prose .` and fix every avoided spelling it
lists. Keep the style sheet open: when the manuscript settles a new
question, record it there in the same change.

The grammar, usage, and dialogue tables below are for English. For a book
in another language (`language` in `story.md`), copyedit against that
language's grammar and the conventions the style sheet records, and use
`language-conventions.md` for dialogue and punctuation. The consistency
and proof sections apply in any language.

## Grammar and usage

- Subject-verb agreement, especially with collective nouns and long
  intervening phrases
- Pronoun case (*between you and me*), and *who*/*whom* only where the
  narration's register uses it
- Tense consistency with `story.md`; past perfect to enter a flashback,
  then back to simple past
- Commonly confused words: *its/it's*, *lay/lie*, *affect/effect*,
  *further/farther*, *peak/peek/pique*, *reign/rein*, *discrete/discreet*
- Usage rules recorded in the style sheet (*all right*, *toward*, *OK*)
- Dialogue is exempt from grammar fixes that would change the voice;
  only fix errors the character would not make

## Punctuation

- Commas: after introductory clauses, around non-restrictive clauses,
  before coordinating conjunctions joining independent clauses; the
  serial comma per the style sheet; no comma splices in narration unless
  the voice uses them deliberately
- Dashes: em dash style (closed or spaced) and en dash for ranges, per
  the style sheet; hyphens only in compounds
- Ellipses: one style throughout (three periods, spaced, or the single
  character) per the style sheet
- Apostrophes and quotes: curly or straight consistently; apostrophes
  facing the right way on leading elisions (*'til*, *'em*)
- Semicolons and colons used correctly or not at all

## Dialogue punctuation

| Case | Pattern (English, double quotes, US style) |
|------|-----------------------------------|
| Tag after line | `"We leave at dawn," she said.` |
| Tag before line | `She said, "We leave at dawn."` |
| Question or exclamation with tag | `"At dawn?" she asked.` (lowercase tag) |
| Action beat, not tag | `"We leave at dawn." She shouldered the bag.` |
| Interrupted line | `"We leave at—" / "No."` |
| Trailing off | `"We leave at…"` |
| Tag mid-sentence | `"We leave," she said, "at dawn."` |
| Tag between sentences | `"We leave at dawn," she said. "Pack light."` |
| Multi-paragraph speech | No closing quote at the end of a paragraph; opening quote on the next |
| Quote within a quote | Single inside double (reverse for British single-quote style) |

British house styles often use single quotes and may place punctuation
outside the quote when it is not part of the speech; follow the style
sheet's Dialogue And Punctuation section. A new speaker gets a new
paragraph. Action beats belong in the speaker's paragraph. Other
languages set dialogue differently (dashes, guillemets, corner brackets):
see `language-conventions.md`.

## Consistency

- Character, place, and term names match their entity files and
  `glossary/terms/`, including aliases and capitalisation
- Spelling of invented terms, hyphenation of compounds, and
  capitalisation of titles and ranks per the style sheet
- Numbers: spelled out or numerals per the style sheet threshold; times
  and dates in one style
- Italics: one rule for thoughts, foreign words, ship names, emphasis
- Physical details: eye colour, scars, ages, and heights match the
  character files (continuity errors go to `revision-continuity`)
- Chapter titles and numbers match `chapters/_index.md`

## Proof pass (on a built copy)

Proofread the book as a reader will see it, not the markdown. Build with
`story build . --format html` and, for print, `story build . --format
print --trim <size>`. Cite problems by paragraph anchor (`ch03-p12`).

- Typos introduced by editing: doubled words (*the the*), missing words,
  half-deleted sentences, a sentence edited in two tenses
- Scene breaks render as breaks; no stray markdown (`**`, `#`, `>`)
- Chapter headings, numbering, and order
- Front and back matter present, in order, with correct text
- Print copy: widows and orphans, a chapter title stranded at a page
  foot, running heads, page numbers, the raised chapter initial, hyphenation at
  line ends
- Final check that the copyright page and any credits match what the
  author supplied; never invent them
