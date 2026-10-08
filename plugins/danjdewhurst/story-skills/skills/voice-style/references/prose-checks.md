# Prose Checks

`story prose .` counts; it never judges. Each check below says what is
counted, when it becomes a warning, and when to keep the text anyway.
Headings, HTML comments, and scene-break rules are ignored. Only the
chapter prose is read: the text after `## Chapter Text`, or after the
outline divider.

| Check | Counted | Warning when |
|-------|---------|--------------|
| Avoided spelling | Each `preferred` avoid form and each dialect-pair avoid form, anywhere in the prose | Any occurrence |
| Filter words | *felt, saw, heard, noticed, realized/realised, wondered, seemed, watched, knew, decided, thought, sensed* in narration | Over 10 per 1,000 narration words, once a chapter has 300 narration words |
| -ly adverbs | Narration words ending in *-ly*, minus common non-adverbs (*only, family, early*) and character-name tokens | Over 12 per 1,000 narration words, once a chapter has 300 narration words |
| Said-bookisms | Tags such as *hissed, snapped, retorted, exclaimed, smirked* in the first three words after a closing quote | Over 2 in a chapter |
| Plain tags | *said, asked* after a closing quote | Never; context only |
| Echoes | A word of 5+ letters repeated within 30 words, ignoring common function words and character names | Never; listed for rereading |
| Sentence rhythm | Words per sentence: average, longest, and spread (standard deviation) | Spread under 5 words across 20 or more sentences |
| Watch words | Each `watch-words` entry | Never; counts are listed |
| Repeated phrases | 4-word sequences inside one sentence, across the whole manuscript, that are not all function words | Never; the top 10 with 3+ uses are listed |
| Similar names | Character first names that match, share their first three letters, or are one or two edits apart | Any pair |

## Other languages

Read `language` in `story.md` (missing means `en`). The word lists come
from a language pack: English (`en`), Spanish (`es`), French (`fr`), and
German (`de`) have them, and a regional tag (`es-MX`, `fr-CA`, `de-CH`)
uses its language's. Spanish counts *-mente* adverbs and French *-ment*
adverbs; German has no adverb ending, so its adverb check is skipped.
French inverted tags count as their verb (*dit-il* is *dit*). The dialect
pairs are English only. Any other language has no lists. For a book not in
English:

- If the report says a check was skipped for the book's language, do that
  pass by reading, looking for the same effect in that language (verbs of
  perceiving that announce instead of show, adverbs propping up weak
  verbs, tags that tell the reader how to hear a line).
- If the author wants a skipped check run, or a pack's list changed (a
  verb the book uses as a plain tag, a regional said-bookism), ask which
  words, then add them to `style-sheet.md` under `add-words` or
  `replace-words` as `- list-name: word, word` entries (see
  `docs/project-format.md`, Word lists, for the list names), and run
  `story validate`. Never fill a list from a translation of the English
  one: ask for the language's own words.
- If a check ran with English word lists on a non-English book (the book
  has no `language` set), set `language` and rerun rather than reading the
  counts: they measure English words the book rarely contains.
- Never use `watch-words` to stand in for a missing check. Use
  `watch-words` for this book's own tics.
- Avoided spellings, watch words, sentence rhythm, and similar names do
  not depend on the word lists.

## Limits

The filter-word, adverb, and said-bookism limits are defaults. `story prose
--max-filter-words <n>`, `--max-adverbs <n>`, and `--max-bookisms <n>`
change them for one run; to change them for the book, record them under
`cli-defaults` in `story.md` (see `docs/project-format.md`, CLI defaults and
severity) and run `story validate`. A `severity` entry there can also make a
prose warning such as `prose-avoided-spelling` fail the run.

## Against the author's samples

With `samples` in the style sheet (at least 2,000 words of narration),
the filter-word and adverb limits come from the author's own prose, and
five more drifts are checked in either direction. A chapter needs 300
narration words before any is compared.

| Drift | Warning when the chapter is further from the samples than |
|-------|-------------------------------------------------------------|
| `prose-baseline-sentences` | 30% of their average sentence length (10+ sentences) |
| `prose-baseline-paragraphs` | 50% of their average paragraph length |
| `prose-baseline-dialogue` | 20 percentage points of their dialogue share |
| `prose-baseline-filter-words` | half their filter-word rate, at least 3 per 1,000 |
| `prose-baseline-adverbs` | half their adverb rate, at least 3 per 1,000 |

The report also lists the samples' 20 signature words (their most used
content words) and how many of them each chapter uses. A chapter that
uses few of them may have drifted in vocabulary, or may be about
something new. Read it before deciding.

## Responding

- **Filter words** distance the reader from the POV character: *She saw
  the door open* becomes *The door opened*. Keep one when the act of
  perceiving is the point (*She heard nothing — and that was wrong*).
- **-ly adverbs** often prop up a weak verb: *walked slowly* becomes
  *trudged*. Keep adverbs that change meaning rather than intensify it.
- **Said-bookisms** tell the reader how to hear a line the dialogue should
  carry. Use *said* or an action beat. Some books use a wider tag palette
  on purpose (older middle grade, some romance); record that in the style
  sheet and add the tags to `allow-words`.
- **Echoes** are fine when the repetition is deliberate (anaphora, a
  motif). Otherwise vary or cut.
- **Uniform rhythm** is a common marker of machine-drafted or fatigued
  prose. Break a run of similar sentences with a fragment or a long
  cumulative sentence where the moment calls for it.
- **Repeated phrases** show a writer's tics across the book (*let out a
  breath*, *the edge of the*). Add real tics to `watch-words` so every
  later check counts them.
- **Similar names** cost readers attention. Rename the less established
  character, with the user's approval, via
  `story rename character <id> '<New Name>' --prose`, so the chapter text
  follows as well as the references: run it with `--dry-run` first, show
  the user the replacements, and run it for real only once they approve.
