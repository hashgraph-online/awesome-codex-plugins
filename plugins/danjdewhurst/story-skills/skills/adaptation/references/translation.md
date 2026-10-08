# Translation

A translated edition is a separate story project: a copy of the source
project with the prose translated, the same entity ids, and its own
`language` and publishing metadata. Keeping the ids in English kebab-case
means `story links`, `story continuity`, `story timeline`, `story diagram`,
and `story compare` line up across editions, and a continuity fix in one
edition can be found in the other by id.

Translation contracts, translator royalties and credit, and the right to
license a translation are rights questions: see the `publishing` skill's
rights inventory and contract checklist. Not legal advice.

## Glossary As Term Base

The glossary is the translator's term base. Before translation starts, add
a `## Translations` section to every term that needs a fixed rendering:

```markdown
---
term: "Second Light"
category: concept
aliases:
  - afterimage glow
pronunciation: SEK-und LYTE
---

# Second Light

The faint duplicate reflection visible in a person's eyes after unsafe
archive playback.

## Translations

- es: la Segunda Luz (capitalized; never "segunda luz" in dialogue)
- de: das Zweitlicht (neuter; coined compound)
- fr: la Seconde Lueur (not "lumière": the word must suggest faintness)
```

- Record the reason when a choice is not obvious; the next translator
  needs it.
- Cover invented words, titles and ranks, forms of address, place names,
  faction names, units, and recurring phrases (oaths, sayings,
  catchphrases).
- Add terms the glossary lacks: `story add term 'Name' --category
  <category>` (the `worldbuilding` skill owns glossary terms).

## Names

For each character, location, and faction name, decide with the author
and translator:

- **Keep** the original (the default for most personal names).
- **Adapt** spelling or diacritics for the target language's readers.
- **Translate** speaking names whose meaning matters to the story
  (Blackwater, Mistress Thornquill).
- **Transliterate** into a different script by a consistent standard.

Record the decision in the entity's body in the source project. In the
translated project, set `name` (and `aliases`) to the translated form;
the id does not change. Check new names for clashes in the translated
project:

```shell
story names 'Zweitlicht' 'Schwarzwasser' --path ../book-de
```

Update `pronunciation` in the translated project for its narrator.

## Per-Language Style Sheet

Each edition gets its own `style-sheet.md`. Set `dialect: unspecified`
unless the target is British or American English, and use `preferred`,
`watch-words`, and the body for:

- Quotation style: « » with spaces in French, „ " or » « in German,
  em-dash dialogue in Spanish and many other languages (see
  `../../line-editing/references/language-conventions.md` for more)
- Formal and informal address (tu/vous, du/Sie, tú/usted) per character
  pair, and when it changes in the story
- Numbers, dates, units, and currency: convert or keep
- Profanity and register levels per character
- Treatment of foreign words already in the source (italics or not)

Record the tu/vous-style decisions per relationship: a switch from formal
to informal can be a plot beat, and it must happen in the same chapter in
every edition.

## Setting Up The Edition

1. Copy the source project folder to a new folder (`../book-de`), leaving
   out `dist/` and any `submission/`, `publishing/`, or `adaptations/`
   files that do not apply.
2. In the new `story.md`, set `language` (BCP 47: `de`, `es-MX`,
   `pt-BR`), and clear `isbn`, `publisher`, `publication-date`,
   `description`, `keywords`, and `subjects` for the new edition's own
   values. Every edition needs its own ISBN. `language` sets every
   generated label in builds: chapter headings, the table of contents,
   the copyright page, the review-copy note, the Shunn title block, and the
   narration credits. For a Japanese, Chinese, or Korean edition set in
   columns, also set `writing-mode: vertical`. Ask whether chapter
   numbers should use the language's own numerals (`第十二章`, `١٢`) and,
   if so, set `chapter-numerals: native`. Builds pick fonts for the
   language's script on their own. A language with no pack of its own gets English
   labels; ask the user for the wording and set each one under `labels`
   (`- chapter: Kapitel {n}`; see docs/manuscripts.md, Build labels). The
   metadata sheet and the narration script's working notes stay in
   English.
3. Remove `series`, `book-number`, `follows`, and `precedes` from the
   copied `story.md`. Those fields are for different books in a series,
   and copied values point at the source series, which breaks
   `story links` and `story series` for the new edition. Do not use them
   to link the editions. A translated series links its own translated
   books the same way the source series does.
4. Translate titles and prose in place, chapter by chapter, keeping every
   file name and id.
5. If AI or machine translation is used at any stage, record it in
   `ai-disclosure`; some retailers require disclosure of machine
   translation. Check their current policy.

## Continuity Across Editions

After each batch of translated chapters:

```shell
story reindex ../book-de
story wordcount ../book-de --write
story check ../book-de
story compare ../book-de --against .
```

`story compare` reports chapters added or removed between the editions;
the word and paragraph changes are expected and can be ignored. Also check:

- [ ] Every chapter and scene file exists in both editions
- [ ] Glossary terms rendered as the term base says (search the
      translated chapters for each term)
- [ ] `language` set (and `labels` for any wording to change), and a
      built EPUB or print interior checked for leftover English labels
- [ ] Chapter titles, epigraphs, and matter pages translated, with
      permissions cleared for the new language (quoted material may need
      a separate permission or an existing published translation)
- [ ] Word count differences are plausible: many languages run longer
      than English, so page counts and the cover spine change
- [ ] Revisions to the source after translation began are listed and
      carried across by chapter id

When the source changes, list the changed chapter ids (`story compare .
--ref <tag>` in the source project) and hand them to the translator.
