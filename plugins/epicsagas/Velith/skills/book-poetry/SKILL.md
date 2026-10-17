---
name: book-poetry
description: "Poetry craft reference: forms, the line, image, sound, compression, collection architecture, and poetry-specific AI tells. Read by all agents on poetry collections, chapbooks, and poetry-essay hybrids."
---

# Poetry

A poem is the one form where the reader will forgive nothing. Every word is load-bearing. Machine poetry fails by being competent: correct images, reasonable line breaks, a closing turn, and nothing at stake.

## Form

Choose per poem, not per collection, unless the collection is a formal sequence.

- **Sonnet**: 14 lines, volta; Petrarchan (8+6) or Shakespearean (4+4+4+2). Meter loosened in contemporary practice but the turn is not optional.
- **Villanelle**: 19 lines, two refrains. The refrains must change meaning through repetition or the form is empty.
- **Ghazal**: couplets, radif, the poet's name in the last couplet. Each couplet autonomous.
- **Haiku / 하이쿠 / 俳句**: cut, season, concrete image. 5-7-5 is a guideline in English; in Japanese it is the form.
- **시조**: 3장 6구 45자 내외, 종장 첫 구 3음절 고정. Modern 시조 flexes everything but the 종장.
- **Free verse**: no fixed meter; the line break is the form. Every break must do something: emphasis, delay, double meaning, breath.
- **Prose poem**: no line breaks; density and sentence rhythm carry it.

## The line

- A line is a unit of attention. What ends the line is emphasized. What starts it is emphasized. The middle is where you hide things.
- **Enjambment** creates speed and double readings; **end-stop** creates weight. A poem that only enjambs has no floor.
- Short lines intensify; long lines expand. Uniform line length is the first tell.
- Read every line aloud (in your head, slowly). Where the breath fights the line, decide whether that is the point.

## Image and sound

- One central image per poem, pushed further than the reader expects.
- Concrete over abstract, always. "Grief" is not an image. The chair nobody moved is.
- Sound: consonant clusters, vowel length, stress patterns even in free verse. Assonance and consonance are more useful than end-rhyme in contemporary work.
- Metaphor that explains itself is deleted. The reader makes the link or does not.
- Korean: 음보 (3·4조, 4·4조, 7·5조) as a resource, not a rule; 시어 chosen for 소리 as well as 뜻; 한자어 vs 고유어 texture decided per poem.

## Compression

After drafting: cut a third. Then cut the first stanza and see if the poem survives (it often does). Then cut the last two lines and see if it improves (it often does). What remains is the poem.

## Collection architecture

- 40-80 poems for a full collection; 15-30 for a chapbook. 시집: 50-70편 typical.
- Arc: opening poem sets the contract; the center holds the collection's core statement; the closing poem echoes or resolves. Sections as movements.
- Ordering principles: thematic, chronological, formal, tonal alternation. Never put two poems with the same shape side by side.
- Titles are thresholds. Title + first line is the entry contract.
- Sequences (linked poems) are the middle ground between poem and book; use them to build.

## Poetry-specific tells

- Closing turn that states the meaning.
- Three images per stanza, each abandoned.
- Uniform stanza length across a poem.
- Adjective-noun pairs ("silent ache," "quiet grief") in every line.
- Abstractions personified ("Hope waited at the door").
- Enjambment on every line.
- The word "silence" or its synonyms in every poem.
- A "you" addressed who never becomes specific.
- Nature imagery as default (moon, rain, river) without a reason for this poem.

## Format

Each poem is its own file: `drafts/p{NNN}-{slug}.md`, frontmatter with `form`, `lines`, `section`. Two trailing spaces at line ends so pandoc keeps breaks (`book-publish` handles it). Stanza breaks as blank lines. Word targets in `PRD.md` are poem counts × average lines, not word counts.

## Validation (architect scoring for poetry)

Collection has an arc and section logic; no adjacent poems share form and length; each poem has one central image; opening and closing poems chosen deliberately; form choices justified per poem in the outline.

## Visuals

Restraint. A collection can carry no images and be complete. When illustrated: one medium across the book, spot art at section openings only, images that sit beside a poem without illustrating it literally. Cover and section pages through `/book-visuals`; the art bible's palette is usually the narrowest of any genre.
