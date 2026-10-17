# Form Choice

The idea's scope decides its natural length. A premise stretched past its
scope sags in the middle; one squeezed below it reads as a summary.

## Count the moving parts

| Moving part | Short forms | Middle forms | Novel |
|-------------|-------------|--------------|-------|
| POV characters | 1 | 1-2 | 1 or more |
| Plot threads (MICE threads, see `../../plot-structure/references/mice-quotient.md`) | 1, maybe 2 nested | 2-3 | 3 or more |
| Significant locations | 1-2 | 2-4 | Any |
| Story time span | Hours to days | Days to months | Any |
| Named cast | 1-3 | 3-6 | Any |
| Changes the story dramatises | One | One major, one minor | Several, interlocking |

If most parts land in one column, recommend that form. If they straddle,
say so and give the trade-off: cut a thread to shorten, or add a
complicating thread to lengthen.

## The forms

The `form` field in `story.md` takes one of these values; `story init
--form <form>` sets it and a default `target-words` when none is given.

| `form` | Rough length | What it does well | Watch out for |
|--------|--------------|-------------------|---------------|
| `flash` | Up to about 1,500 words | One moment, one image, one turn | Needing backstory to land |
| `short-story` | About 1,000-7,500 | One change, a single effect (see `../../plot-structure/references/short-story-form.md`) | Subplots, large casts |
| `novelette` | About 7,500-17,500 | One change with room for a second character's pressure | Being a long short story with padding |
| `novella` | About 17,500-40,000 | A contained situation, one strong arc, intensity | A novel's worth of threads |
| `novel` | About 40,000-200,000; genre norms vary | Multiple arcs, subplots, world, time | A single-situation premise that cannot generate 60+ scenes |
| `serial` | Episodes, each with its own question | Ongoing situations, cliffhangers, reader habit | A story that only pays off at the end; see the `genre-craft` serial reference |
| `picture-book` | Up to about 1,000 words, text shared with art | One emotional truth, read-aloud rhythm, page turns | Describing what the art will show |
| `chapter-book` | Roughly 4,000-15,000 for early readers | Short chapters, simple plots, a series-able lead | Vocabulary and sentence length above the reader |

The bands are rough conventions; SFWA award categories set the
novelette and novella lines that many short-fiction markets use. Genre
norms for novels are in `../../submission/references/word-count-norms.md`.
`story validate` warns when `target-words` sits outside the form's usual
range; take the warning to the user rather than silently changing either.

These bands are English word counts. The same story runs to a different
count in another language, and Chinese and Japanese publishing count
characters, not words. For a book not in English, agree the target with
the user from the norms of the market it is written for, and treat the
form's English range as a rough guide only.

`serial` sets no book-level `target-words`: set `target-words` on each
episode chapter instead.

## Questions that decide it

1. **Where does the story end?** If the ending is one scene after the
   inciting situation resolves, it is short. If each answer opens a new
   question, it is long or serial.
2. **How much world must the reader learn?** A world that needs teaching
   needs pages. Short forms need a world readers already know, or one
   revealed in a single strange rule.
3. **What does the user want to finish?** A first project, a market
   (magazine, anthology, agent, retailer), or an experiment? A short story
   finished beats a novel abandoned. Ask; do not assume.
4. **Who is the reader?** Picture books and chapter books have audience
   conventions that override scope; see `../../genre-craft/references/mg-ya.md`
   for middle grade and YA.

## Changing form later

Form is a planning decision, not a contract. If drafting shows the idea
is bigger or smaller, edit `form` and `target-words` in `story.md`, then
run `story validate .` and `story report .`.
