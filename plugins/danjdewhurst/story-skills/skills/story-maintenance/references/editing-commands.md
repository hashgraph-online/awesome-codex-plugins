# Editing Commands

How the commands that create, rename, move, split, merge, and remove entity files, the `impact` that tests such a change first, and the `import` that builds a project from a manuscript, behave, and what to check after them. `SKILL.md` says when to run each command; read the matching section here before running one or explaining its result. Run any of them with `--dry-run` first when the change touches many files. `docs/cli-reference.md` lists every flag.

After a command changes files, run `story reindex .`, `story wordcount . --write`, and `story check .` in that project. After `import`, run them in the new project folder that the output names, not in the folder you ran it from: `story reindex <folder>`, `story wordcount <folder> --write`, and `story check <folder>`.

## add, rename, and remove

`add`, `rename`, `move`, and `remove` for deterministic entity file operations when they fit the requested change.

- `add` takes ids, not names, for reference options (`--planted chapter-01`, `--pov mara-quill`), and `add scene` needs its chapter to exist, so add the chapter first.
- Ids stay ASCII kebab-case. Cyrillic and Greek names are transliterated (`story add character 'Пётр'` writes `characters/petr.md` and keeps `name: Пётр`), but a name in a script with no transliteration table (`李明`) needs the id by hand: `story add character '李明' --id li-ming` writes `characters/li-ming.md`, and `story rename <kind> <id> '<New Name>' --id <new-id>` does the same on a rename. `--id` is refused for chapters and scenes, whose ids come from their numbers.
- `rename` rewrites the id in frontmatter and links but leaves chapter prose alone. Add `--prose` when the chapter text should use the new name too: preview with `story rename <kind> <id> '<New Name>' --prose --dry-run`, show the user the replacements, and run it without `--dry-run` only once they approve. `--prose` works for characters, locations, factions, artifacts, systems, and terms. It rewrites only drafted chapters: an `outline` chapter keeps the old name, so list them with `story list chapters --where status=outline` and update their text by hand. It leaves aliases as written, and lists the matches it left alone (a name that may be an ordinary word, a reference-link label) for you to check by hand; the `character-management` skill has the full steps. `rename` never changes a chapter or scene id: use `move`.
- `remove chapter` refuses while scene files point at the chapter, so remove those scenes first; it walks back ledger statuses that relied on the chapter (planted to planned, paid-off to planted or planned, answered or resolved questions to open), so review the ledgers afterwards.

## move

`move` whenever a chapter's number or a scene's chapter or position changes, never a hand rename: chapter and scene ids encode their numbers.

- `story move chapter <id> --number <n>` renames the chapter and its scene files, sets `number` and the `# Chapter N:` heading, and rewrites every reference to the old id (scene `chapter`, clue and promise `planted`/`payoff`, question `introduced`/`resolved`, research `used-in`, `died-in`, `continuity/state.md` `since`/`learned-in` and `current-chapter`, markdown links, and bare ids in `plot/timeline.md` and arc bodies).
- A taken number is refused (`chapter-05 already exists: move it first. To make room, renumber from the highest chapter down`), so to insert a chapter move the later chapters up one, highest first, then `add chapter --number <n>`.
- `story move scene <id> --chapter <chapter-id>` moves a scene to the next free number in that chapter (`--scene <n>` picks the number, and `--scene` alone reorders within the chapter) and adds its location and characters to the new chapter; give at least one of the two.
- `move` works only on chapters and scenes (use `rename` for other ids), never edits prose or outline beats that mention a chapter number, and reindexes.
- References are written before the files move, so rerun an interrupted move: it first puts back what the stopped move changed.

## split and merge

`split` and `merge` to split a chapter in two or join two neighbouring chapters, instead of moving prose and renumbering by hand.

- `story split <chapter-id> --at '<marker>'` keeps the text before the marker and makes the rest the next chapter (`--title` names it; default `<title> (continued)`), moving the later chapters up one. The marker is a scene break number (`--at 2`), a heading, or a unique line of the chapter text. Scene records after the split move with their text, by order.
- `story merge <chapter-id> <next-chapter-id>` appends the second chapter's prose after a scene break, adds its outline beats, notes, scenes, and list fields to the first, points every reference to it at the first, and moves the later chapters down one.
- In a branching book (one with `choices`), both work only on chapters with no choices, and `merge` only when no choice leads to the second chapter; anything else is refused, naming the choices in the way. The renumbering points every choice at the new ids, and a split gives the first half a `Continue` choice that leads to the rest, so ask the user whether to reword it. Both list each choice they add or point elsewhere, under `--dry-run` too.
- `split` also refuses when it would give a chapter (the last one it renumbers, or the new one when none follows) a `chapter-NN` that a file already names, such as a payoff scheduled for a chapter not written yet. Only abandoned threads naming the new chapter's id are let through, with an `adopted-references` warning. Ask the user which chapter those references mean, point them where the message says (the chapter they belong to, or the next id), then run it again.
- Run `--dry-run` first and show the user the list. A split or merge stopped part way (`interrupted-change` from `story validate`) is put back by running it again, which then splits or merges, or by `story doctor --fix`; until then every other write command is refused.
- Then work through the warnings: `split-references` lists files that still name the split chapter (a clue, death, or progression there may now belong to the new chapter, which the CLI cannot tell), `split-scenes` says scene records were assigned by order, and `merge-conflicts` lists fields the two chapters set differently, including `numbered: false` on only one of them (the merged chapter keeps the first chapter's numbering).
- Neither edits prose, so reread for chapter numbers in the text.

See the `revision-continuity` skill.

## impact

`impact` to test a structural or plot change before making it, and to answer "what breaks if ...".

- `story impact <command> <args...>` takes `rename`, `remove`, `move`, `split`, or `merge` with exactly the arguments and flags that command takes (`story impact move scene chapter-03-scene-02 --chapter chapter-09`), or `die <character-id> <chapter-id>`, which sets the character's `died-in` to that chapter and `status` to `deceased` (kept as it is for an `outline` chapter, a planned death, with a `planned-death` warning). For a character revived before that chapter it records a second death as a `status` progression.
- It copies the project to a scratch folder, runs `story check` there, makes the change, runs `story check` again, and prints the files the change would touch, the change's own warnings, and only the findings it adds and clears, each with its check. Findings the project already has are left out, so a project with open errors can still be tested; one the change only gives new ids (a renamed entity, a renumbered chapter) is counted as carried over, not added.
- It never writes to the project, takes no lock, and leaves the undo log alone. It refuses what the command would refuse, with the same message and exit code, and refuses while an interrupted change is in the project.
- It exits 1 when the change adds an error, and with `--strict` when it adds or gives a warning; `--json` gives `data.changes`, `data.added`, `data.cleared`, `data.carried`, `data.before`, and `data.after`, with the added findings as diagnostics.
- Show the user what the change adds before you make it. When it adds errors, say which files the user (or you, once they approve) must fix after the change, such as moving a dead character from later casts to `mentions`. To compare options, run it once per option, for example a death in chapter 5 and in chapter 9.
- Then make the change with the command itself (with `--dry-run` first when it touches many files) and run the maintenance block above.

## add matter

`add matter` when the user wants a dedication, epigraph, copyright page, acknowledgments, author's note, about-the-author, or also-by page.

- Pages live in `matter/` (indexed in `matter/_index.md` by reindex) with `title`, `placement` (`front` or `back`), `order`, and `heading` (pass `--heading=false` for a dedication or epigraph, or edit the scaffolded `heading:` key; never add a second one).
- Write the page text directly in the file; unwritten pages are left out of builds and `validate` warns about them.
- Never invent acknowledgments, biographical facts, or copyright details: ask the user for them.
- Matter pages that quote others' work (an epigraph, song lyrics) may record `permission` (`not-needed`, `pending`, `granted`, `public-domain`), `rights-holder`, and `credit`; `validate` warns when `permission: pending` remains on a complete story and when `granted` has no `rights-holder`, and export and the builds leave a `pending` page out (warning `permission-pending-left-out`) unless `--include-pending` is given.

See the `editorial-review` skill.

## add research

`add research` when the story relies on a real-world fact: notes live in `research/` with `status` (`open`, `verified`, `disputed`), whole-citation `sources`, and `used-in` chapter ids, plus optional `--accuracy` (`must-be-accurate`, `blended`, `invented`), `--confidence` (`high`, `medium`, `low`), `--method` (`fact`, `interview`, `site-visit`, `expert-review`, `reading`), and repeatable `--risk` (`legal`, `medical`, `weapons`, `safety`, `cultural`, `defamation`, `technical`).

`validate` warns when a final chapter relies on open or disputed research (invented notes never trigger this), and when a note with a `risk` is used in a final or complete chapter with no `reviewed-by`.

See the `research` skill.

## import

`import` when the user has an existing manuscript or chapter drafts and wants a Story Skills project built from them.

- Follow up by creating character and location files from the printed entity candidates, and by setting `form` and `target-words` in `story.md` (import refuses `--form`; without them `story validate` never checks length and `story progress` has no target).
- Directory sources import in natural file-name order (`chapter-2` before `chapter-10`).
- A `.docx` source, or a `.docx` file in a source folder, is read as a Word document. A `docx-content-left-out` warning means the document had comments, footnotes, images, text boxes, tables, list numbering, ruby readings, or tracked changes that the import did not carry over (tracked changes are read as accepted). Tell the user which, since a comment or footnote may hold text they meant to keep. Chapters split only on chapter headings and lines, such as `Chapter 1: The Arrival` or `Prologue`, in a heading style or in a paragraph of their own. If the import gives one long chapter, the chapter titles are probably bare titles or numbered by Word's list numbering: ask the user to type `Chapter N` into each chapter title and import again.
- An `.odt` (OpenDocument text) or `.epub` source, or such a file in a source folder, is read the same way, with no Pandoc needed: an EPUB in its reading order, one XHTML document after another. An `import-content-left-out` warning names what the file had that the import did not carry over, such as footnotes, images, tables, or EPUB documents outside the reading order: tell the user which. An EPUB's front matter (title page, copyright page, epigraph) imports as a chapter titled `Opening`; ask the user whether to delete it or move it into `matter/`. An EPUB locked with DRM is refused; ask the user for the manuscript the ebook was made from.
- `import --force` into an existing directory deletes every `chapter-NN.md` in `chapters/` before writing the imported chapters, so confirm with the user before forcing an import over a project with drafted chapters. It first saves the project as snapshot `before-import-<n>` and prints `story snapshot --restore before-import-<n>`; tell the user that name, since that restore puts the old chapters back.
- A Story Skills chapter file keeps its `author`; for a collection or anthology of other files, add `--bylines` to set each chapter's `author` from the by-line opening its prose (`By Ben Other`, taken out of the prose) or its file's frontmatter `author`. A line that is not clearly a by-line stays in the prose, so check the chapters left without `author` and set it by hand.

## collect

`collect` in a collection or anthology project when its `story.md` `stories` lists the story projects it gathers, in reading order, such as `stories: [../low-tide, ../salt]`. Each entry is a story project folder beside the collection.

- It writes each story as one chapter, as `import` makes one from the story's chapter file: the story's `story.md` title, its chapters' prose joined by `* * *`, and its writer in the chapter's `author` when that is not the collection's own `author`. It writes the word counts and rebuilds the registries.
- Each line of its report says whether a story was `added`, `changed` since the last run, or `unchanged`. Tell the user which stories changed.
- It changes only chapters with `collected-from`. A chapter the user wrote in the collection keeps its file and number, and the stories fill the other numbers. A `collect-hand-written-copy` warning names a hand-written chapter with a story's title, most likely an old copy: ask the user before you delete it.
- A story taken out of `stories` has its chapter removed. Reorder `stories` to reorder the book.
- It refuses, and writes nothing, when a `stories` entry is not a story project (the `collection-story-*` codes, which `story links` also reports), and when a collected chapter was edited in the collection. Make that edit in the story project instead. `--force` discards the edit after it saves snapshot `before-collect-<n>`, so ask the user first and tell them the snapshot name.
- It refuses to move or remove a chapter that a scene, or a frontmatter field such as a character's `died-in`, names. Keep those records in each story's own project.
- Run `story collect . --dry-run` first when the user wants to see the changes. Then run `story reindex .`, `story wordcount . --write`, and `story check .`.
