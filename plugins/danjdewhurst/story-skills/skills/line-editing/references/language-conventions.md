# Dialogue And Punctuation By Language

Dialogue and punctuation conventions differ by language, and often by
country and publisher within one language. Read `language` in `story.md`
(a BCP 47 tag; a missing field means `en`), then use this file to choose
the conventions with the author and record them in the style sheet's
**Dialogue And Punctuation** section. The style sheet wins over this file:
it records what this book does.

These are common conventions, not rules every publisher follows. When the
draft already does something consistently, keep it and record it. When
the author's publisher has a house style, follow that.

## Applying it

1. Read `language` and two or three chapters. Note what the draft does:
   which quote marks, whether dialogue opens with a dash, where the
   punctuation sits around a tag, and any spaces before punctuation.
2. Compare with the row for the language below. Where the draft is
   inconsistent, ask the author which form wins, as for spelling.
3. Record the choice in `style-sheet.md`, with one example line of
   dialogue with a tag, so later chapters and other agents follow it.
4. Copyedit against the recorded choice. The English dialogue table in
   `copyedit-checklist.md` applies only to English.
5. Type the real characters (`«`, `—`, `「`), not ASCII stand-ins such as
   `<<` or `--`, unless the style sheet says otherwise.

`story voices` attributes quoted lines by finding the quote marks and
dialogue dash of the book's `language`: guillemets, low-high quotes, and
corner brackets everywhere, `»…«` for German and Danish, `”…”` and an en
dash for Swedish and Finnish. If it reports no attributed lines, or far
fewer than the book has, for a book whose dialogue uses dashes or quote
marks it does not recognise, do the voice pass by reading instead.

## Conventions by language

| Language | Quotes (outer, inner) | Dialogue | Spacing and other marks |
|----------|----------------------|----------|-------------------------|
| English (US) | “…”, ‘…’ | Quote marks; comma or full stop inside the closing quote | No space before punctuation |
| English (UK) | Often ‘…’, “…” (many publishers use US order) | Quote marks; punctuation inside or outside by sense, per house style | No space before punctuation |
| French | « … », “…” | Guillemets, often with an em dash (—) marking a change of speaker inside them; some books use dashes only | A no-break space inside guillemets and before `: ; ! ?` (often a narrow no-break space, U+202F, before `; ! ?`). Quebec usage often drops the space before `; ! ?` |
| Spanish | «…», “…”, then ‘…’ | An em dash (raya) opens each line and sets off the tag: `—Ya voy —dijo ella—. Espera.` | No spaces inside guillemets; `¿` and `¡` open questions and exclamations; the full stop goes after a closing dash or quote |
| Portuguese | Brazil “…”; Portugal «…» | An em dash (travessão) opens each line and sets off the tag | No space before punctuation |
| Italian | «…» or “…” | Guillemets (caporali) or an em dash, by publisher | No spaces inside guillemets or before punctuation |
| German | „…“ and ‚…‘, or »…« and ›…‹ in many books | Quote marks; a comma follows the closing quote before the tag: `„Komm“, sagte sie.` | No space before punctuation |
| Swiss German | «…», ‹…› | Quote marks | No spaces inside the guillemets |
| Polish | „…”, «…» | Usually a dash opening each line in fiction | No space before punctuation |
| Russian | «…», „…“ | An em dash opens each line and sets off the tag | No space before punctuation |
| Czech | „…“, ‚…‘ | Quote marks | No space before punctuation |
| Swedish | ”…”, ’…’ (both marks the same shape) | Quote marks or a dialogue dash, by publisher | No space before punctuation |
| Greek | «…», “…” | Guillemets or a dash | `;` is the question mark; the raised dot `·` is the semicolon |
| Japanese | 「…」, 『…』 | Each spoken line in 「」, usually its own paragraph | Full-width `、` and `。`; no spaces between words; modern fiction usually drops `。` before a closing `」`; `……` and `――` are doubled |
| Chinese (Simplified) | “…”, ‘…’ (full width) | Quote marks | Full-width `，。！？：；`; `……` (six dots) and `——` are doubled; `《》` marks titles |
| Chinese (Traditional) | 「…」, 『…』 | Corner brackets | Full-width punctuation as above |
| Korean | “…”, ‘…’ | Quote marks | Spaces between words |
| Arabic | « » or “ ”, by publisher | Quote marks or a dash, by publisher | Right to left; `،` comma, `؛` semicolon, `؟` question mark |
| Hebrew | Varies by publisher | Varies by publisher | Right to left |
| Hindi | “…”, ‘…’ | Quote marks | `।` (danda) ends a sentence |
| Thai | “…” | Quote marks | No spaces between words; a space separates phrases and sentences |

A language not in the table: ask the author for two or three published
books whose conventions they want to follow, read how those books set
dialogue, and record the result.

## Beyond punctuation

- **Capitalisation** differs: German capitalises every noun; French and
  Spanish do not capitalise month and day names; titles of works follow
  each language's own rules. Record the book's choices.
- **Numbers**: the decimal and thousands separators differ (`1,000.5` in
  English, `1.000,5` in German, `1 000,5` in French; Spanish varies by
  country). Record one style.
- **Forms of address** carry voice in many languages (French *tu*/*vous*,
  German *du*/*Sie*, Spanish *tú*/*usted*, Japanese honorifics and
  politeness levels). Record who addresses whom how in the character
  files, and treat a change as a relationship beat, not a typo.
- **Craft advice** about dialogue tags (*said* is invisible), filter
  words, and -ly adverbs comes from English-language editing. Its aim
  (keep the reader close, let the dialogue carry the tone) applies in
  any language; its word lists do not. Do not translate an English word
  list into another language and count it.
