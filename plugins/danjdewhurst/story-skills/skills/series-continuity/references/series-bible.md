# Series Bible And Multi-Book Pitch

A series bible is the record of canon that every book in a series must
respect. In a Story Skills series there is no series-level folder or shared
database: each book is its own project, and the bible is spread across the
books' own files, which `story series` reads and checks. This reference
covers where each part of the bible lives, how to keep it current, and how
to plan and pitch a series of several books.

## Where the bible lives

| Bible content | Where it goes | Checked by |
|---------------|---------------|------------|
| Series id, retail name, book order | `series`, `series-title`, `book-number` in each `story.md` | `story series` (errors on mismatched ids and duplicate numbers, warns on differing `series-title`) |
| Chronology | `follows` and `precedes` in each `story.md`, with backlinks | `story series` (order, cycles), `story links` (paths, backlinks, matching `series`) |
| Where this book sits and what it must not contradict | `## Series Notes` in each book's `story.md` body | Read by hand |
| Characters, places, systems, factions, artifacts, terms | The entity files, copied with the same filename id and `name` into each book that uses them | `story series` (deaths, revivals, name and pronunciation drift, destroyed artifacts) |
| Fixed endpoints a prequel must reach | `## Series Canon` in the entity file | Read by hand |
| Who knows what, and since which book | `knowledge-state` in `continuity/state.md`, with a shared `fact` id | `story series` (a fact learned twice), `story continuity` (fact id format, one entry per character for a given fact) |
| Events from another book | `## Backstory Events` in `plot/timeline.md` (sequel) or `## Series Canon` notes (prequel), linking the other book's chapter file | `story links` (the linked file exists in a book this one follows or precedes) |
| Threads paid off in a later book | Open promise, question, or clue files, with an entry in `continuity/exemptions.md` whose `reason` names the later book | `story continuity` (the finding shows as `dismissed`) |

Do not keep a second copy of canon in a separate bible file and treat it as
the source. A fact written only in prose is a fact no command can check,
and two copies drift. Put each fact in the file that owns it, and give the
reveals, secrets, and discoveries other books depend on a `fact` id.

## Reading the bible

`story series .` is the bible's table of contents. Run it from any linked
book (an unlinked companion does not appear):
it lists every linked book in chronological order with its `book-number`
and `status`, then the shared canon by kind (characters, locations,
systems, factions, artifacts, glossary terms, facts). For each shared id,
read that entity's file in each book where it appears, and the `Series
Notes` of each book.

What the checker cannot see, read for by hand across books: ages and
dates, travel time, knowledge without a `fact` id, physical description,
and tone. When a book's `Series Notes` gives an age or a time gap, check it
against the other books' `plot/timeline.md`.

## Writing the Series Notes

Every book's `story.md` gets a `## Series Notes` section. Keep it to short
bullets:

- Publication position and chronological position, when they differ
  (`Book 2 in publication order, but set first in the chronology`)
- The time gap to each linked book
- Canon fixed by the other books that this book must not contradict:
  deaths, ages, who holds what, what has been revealed
- The state the main characters must be in at this book's end (prequel) or
  start (sequel)
- Threads this book leaves open for a later book, and which book pays them
  off

State each fact as a fact a draft could contradict ("Maren seals the ember
well and burns out his own affinity"), not as a theme or a mood. Name no
characters or events that do not exist in some book's files.

## Keeping the bible current

- **After drafting or revising any book**, run `story series .` and
  `story links .` in it. Fix errors in the book that is wrong, which for a
  prequel is the prequel: the later book is canon.
- **When canon changes** in an earlier book, update the later books'
  `Series Notes`, carried entity files, and `Backstory Events` rows, then
  run `story series .` in each.
- **When a fact first appears on the page**, give it a `fact` id with
  `learned-in` in that book, and carry it without `learned-in` into every
  later book.
- **When a name changes**, rename it with `story rename` and `--prose` in
  every book that defines the id, so each book's chapter text follows, or
  keep the old id. In each book, run it with `--dry-run` first, show the
  user that book's replacements, and run it for real only once they
  approve. In each book, after the rename, run `story reindex .`, `story wordcount . --write`, and
  `story check .`. Put a new title or epithet in `aliases`, not `name`.
- **Before naming a new character** in a later book, run
  `story names '<name>' --path '<other-book>'` against each earlier book, so
  a minor character does not echo a major one.

## Planning a multi-book series

Plan the series in the first book before drafting later ones:

1. Set `series` (kebab-case, the same in every book) and `series-title` in
   the first book's `story.md`, and give it `book-number: 1`.
2. Decide the series shape with the user:
   - **One story across several books:** an overarching question that only
     the last book answers. Record it as a promise or question in book
     one's `continuity/` folders, with an exemption naming the book that
     resolves it.
   - **Linked standalones:** each book closes its own main question; only
     characters, world, and some threads carry over.
   - **Prequel or companion:** set before the existing books, or alongside
     them with no chronology link (no `follows` or `precedes`, the same
     `series`). `story series` finds books only by following links, so it
     never sees an unlinked companion and cannot check its canon or its
     `book-number`. Compare a companion's shared entity files and fact ids
     with the other books by hand, and record the companion in each book's
     `Series Notes`.
3. Give each book a complete arc of its own. Even in a single story told
   across several books, each book needs its own question answered by its
   own ending; leave the series question open, not the book's.
4. List the planned books, their working titles, and one-line premises in
   book one's `story.md` `## Series Notes`. Create a book's project with
   `story init '{Title}' --follows '<book-dir>'` (or `--precedes`) only when
   work on it starts. A planned book with no project needs no links yet.
5. Decide which canon is fixed now (deaths, the world's rules, the order of
   major reveals) and which stays open. Fix only what book one's ending
   depends on.

## Pitching a series

Agents and editors buy one book at a time. Pitch the first book as a
standalone with series potential, not the series as a whole:

- **Query letter:** pitch book one only. One sentence near the word count
  is enough: `THE LAST EMBER is an epic fantasy, complete at 95,000 words.
  It stands alone, with series potential as the first of a planned
  trilogy.`
  Never pitch a debut that only works as part one. See
  `../../submission/references/query-letter.md`, resolved relative to this
  reference file.
- **Synopsis:** cover book one's ending in full. Mention the series
  question only if book one sets it up on the page.
- **Series overview**, for when an agent or editor asks for one: save it to
  `submission/series-pitch.md` in book one. Keep it to a page:

```markdown
---
type: series-pitch
series: {series-id}
updated: YYYY-MM-DD
---

# Series Pitch: {Series Title}

## Series Logline

{One sentence: the world, the overarching conflict, and what is at stake
across the whole series.}

## Shape

{Number of planned books, whether it is one story or linked standalones,
and how each book closes its own main question.}

## Books

| # | Title | Status | Logline | What it resolves |
|---|-------|--------|---------|------------------|
| 1 | {Title} | {complete / drafting / planned} | {one sentence} | {the book's own question} |
| 2 | {Title} | {planned} | {one sentence} | {the book's own question} |

## Series Arc

{Two or three sentences on how the main characters and the central conflict
change from the first book to the last.}
```

Fill the `Books` table from `story series .` for the linked books that
exist (each book's `book-number` and `status`), and from book one's
`Series Notes` for planned books and unlinked companions. Use publication order (`book-number`), not chronology, in the
`#` column. For a self-published series, the `publishing` skill covers
series metadata and retailer series pages.
