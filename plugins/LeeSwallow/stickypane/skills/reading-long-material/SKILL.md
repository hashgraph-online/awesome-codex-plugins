---
name: reading-long-material
description: Use when what the user should read runs to many pages (an onboarding guide, a report, a set of docs already in the project), and one long note would be scrolled past. Puts it on the stickypane board as a book, a folder of pages read in order.
metadata:
  cases: book-B1 book-B2
---

# Reading long material

```sh
# docs the project already has: show the folder, copy nothing
stickypane note link docs

# a book you write: a folder in a tab, a page per file
echo "What this service does, in five lines." | stickypane note write onboarding/guide/01-overview --open
stickypane page add onboarding/guide "02 How to run it"
stickypane page add onboarding/guide "03 Where things are"
stickypane page list onboarding/guide
```

Shapes: book (a folder inside a tab: here the tab `onboarding`, the book
`guide`); a page is any note, so html and mermaid pages work too.

`page add` makes an empty page named after its words, as `N` on the
board does; write it with `stickypane note write onboarding/guide/<page>`.
Pages read in the order of their file names: start a name with
`01-`, `02-` to fix the order. On the board, `,` and `.` turn the pages.

## How

- The first page is the summary: what the book says, in a screen. A
  reader who stops there should have the point.
- One subject per page; a page that runs past two screens is two pages.
- Existing docs: `note link` shows them where they are, so they never go
  out of date on the board. Do not copy them.
- Link pages to each other and to notes with `[[name]]` (`connecting-notes`).
- `${CLAUDE_PLUGIN_ROOT}/rules/writing-notes.md` has how to word a note;
  `${CLAUDE_PLUGIN_ROOT}/rules/touching-the-board.md` applies.

## Recipes

- `references/a-research-report.md`: findings that run long, with the answer on the first page.
- `references/a-postmortem.md`: what went wrong, a page for each part.
- `references/mixed-pages.md`: a book whose pages take different shapes.
