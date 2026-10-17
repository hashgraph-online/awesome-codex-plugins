# Builds

What each `story build` format writes, and the flags and `story.md` fields it reads. `SKILL.md` says when to build; read the matching section here before running a format or explaining its output. `docs/manuscripts.md` explains the same builds for users, and `docs/cli-reference.md` lists every flag.

## build

`build` when the user asks to build the book artifact; supports markdown, EPUB, DOCX, Shunn, HTML, print, narration, metadata, Fountain, Twee, and ink outputs in `dist/`, and a codex site in `dist/codex/`, with front and back matter. For EPUB, set `cover: path/to/cover.jpg` (inside the project, and holding the kind of image its extension names) and `author` in `story.md` to embed a cover image and creator; never pass the cover or the `build-style` `css` file as `--out`, which is refused. For an anthology, set `editor` in `story.md` and `author` on each chapter: builds credit the editor on the title pages and print each story's writer under its heading, outside the word count (docs/manuscripts.md#story-authors-in-collections-and-anthologies).

A matter page with `permission: pending`, a misspelt `permission` key, or any value but `not-needed`, `granted`, or `public-domain` is left out of `export` and of every build that prints matter (markdown, EPUB, DOCX, HTML, print, narration), with a `permission-pending-left-out` warning for each. Report the warning rather than work around it. Add `--include-pending` only for a proof the author reads alone, never for a file anyone else sees; `cli-defaults` cannot set it, and other builds refuse it.

## html

`build --format html` when the user wants a review or reading copy for people who never open a terminal: a single HTML file with a table of contents and a paragraph label on every paragraph, shown faintly in the margin as a link labelled `ch03-p12` (chapter 3, paragraph 12), that reviewers cite in notes.

- A label is the paragraph's position in that build, so any earlier edit renumbers it; add `--stamp <round or date>` so notes can name the build, and ask reviewers to quote each paragraph's first few words.
- `--note-url <url>` adds a Note link beside each label, prefilled with `title`, `anchor`, `build`, and `quote` query parameters for the reader-note issue form.
- The `feedback-triage` skill sets up the GitHub Pages workflow that publishes it, and the issue form.

## print

`build --format print` for a print-ready interior: HTML with CSS paged media, trim size from `--trim` (`5x8`, `5.25x8`, `5.5x8.5`, `6x9`, `a5`; default `5.5x8.5`), mirrored margins with gutter, running heads (author on verso, chapter title on recto, blank on chapter openings), page numbers at the foot of chapter and back-matter pages, chapters on recto, a raised initial at each chapter opening, widow and orphan control, and a copyright page.

Add `--pdf` to render it to `dist/<story-id>.pdf` with a paged-media engine the user has installed (Prince, WeasyPrint, Paged.js CLI `pagedjs-cli`, or headless Chrome/Chromium, tried in that order; `--pdf-engine <name|path>` picks one); the CLI does not bundle one and exits 4 with install hints when none is found.

See the `publishing` skill.

## narration

`build --format narration` for an audiobook narration script: a pronunciation guide table from every `pronunciation` field, each chapter with an estimated finished runtime at the language's narration pace (155 words per minute in English), scene breaks as `[pause]`, and a total runtime. In a collection or anthology, each story with its own chapter `author` gets a spoken credit after its heading, and the opening credits name the `editor` and then the story authors the book's credits leave out. See the `adaptation` skill.

## metadata

`build --format metadata` for a retailer metadata sheet from `story.md`: title, series, authors, ISBN, publisher, date, language, description with its character count against common limits (KDP 4,000), keywords, BISAC subjects, word count, estimated page count, AI disclosure, and a readiness checklist of missing fields. See the `publishing` skill.

## twee

`build --format twee` for a Twine story (Twee 3) of a branching book: one passage per chapter, named by its id, with a `[[text->chapter-NN]]` link for each entry in the chapter's `choices` frontmatter (`text` and `to`).

- The first chapter is the start; once any chapter has choices, a chapter without them is an ending, and with none anywhere each chapter links to the next.
- The IFID comes from `ifid` in `story.md`; without it the build derives one from the story id and warns with the `ifid:` line to add.
- It refuses to build while a choice is malformed or leads to a missing chapter; `story validate` and `story links` report the same problems, and `links` warns about chapters no choice path reaches.

See the `interactive-fiction` skill, or `adaptation` to convert a linear book.

## ink

`build --format ink` for the same branching book as an ink story for Inky and inklecate: one knot per chapter (`chapter-03` becomes `chapter_03`), a sticky `+ [text] -> knot` choice for each entry in `choices`, `-> END` for a chapter without choices, the title, author, and IFID as global tags, and prose escaped so ink reads it as text. It shares the Twee build's rules, checks, and refusals. See the `interactive-fiction` skill.

## codex

`build --format codex` when the user wants a browsable story bible: a static site in `dist/codex/` with an index, a page per character, location, faction, artifact, system, and arc (fields, relationships, chapters it appears in, and backlinks), and timeline, threads, and progress pages, cross-linked and with no script or external asset.

- It is spoiler-safe by default (no entity notes, statuses, deaths, knowledge, clues, or resolutions); add `--spoilers` only for the author's own copy, never for one readers will see.
- `--out` names a folder, and a rebuild replaces an earlier codex there.
- Its headings, columns, and notes follow `story.md` `language`, like other build labels; to reword one, add a `codex-` entry under `labels` (see docs/manuscripts.md#build-labels).

## epub

`build --format epub` also writes EPUB 3 accessibility metadata, language, semantic chapter and matter markup, and a landmarks nav, and uses the optional `story.md` publishing fields (`cover-alt`, `isbn`, `publisher`, `publication-date`, `description`, `subjects`, `language`, and `copyright`, which generates a copyright page when no copyright matter page exists).

## shunn

`build --format shunn` when the user wants Shunn manuscript-format markdown: title page, contact block, word count, chapter breaks, and double-spaced prose; `story build . --format docx --shunn` applies the same Shunn formatting to a Word file, `dist/<story-id>.shunn.docx`, so it never replaces the plain `docx` build, and `story build . --format shunn --pdf` renders a Shunn PDF with an installed engine.

## build-style

A `build-style` block in `story.md` styles the EPUB, HTML review copy, and print interior: `preset` (`classic`, the default, `modern`, or `elegant`), overridden by `body-font`, `heading-font`, `heading-style`, `scene-break`, `drop-caps`, and `paragraphs`, plus `css` for an extra stylesheet inside the project. The Shunn and DOCX builds ignore it. `story validate` reports `invalid-build-style` for a bad block, and the EPUB, HTML, and print builds stop on the same problems. Change it only when the user asks for a different look; see the `publishing` skill, and Build styles in `docs/manuscripts.md` for every value.
