# Pre-delivery checks

Run these in order after the last render. The first section blocks delivery; the second is a judgement call the author makes and records.

## 1. Blocking checks

Every one of these must pass before the report is called done. Each has an observable test, not a feeling.

| Check | Test | Failure means |
|---|---|---|
| Source exists and parses | The render report is valid JSON with `status` set | The source or the pipeline broke before layout |
| Pages rendered | `layout.pages >= 1` | Nothing reached the page; usually an empty body or a broken template |
| No overflow | `layout.overflow` is empty | Content was clipped off the bottom of a page |
| No over-wide block | `layout.wide` is empty | A table or image is wider than the text column |
| Images loaded | every entry in `layout.images` has `ok: true` | An image path is wrong or the file is missing |
| PDF page count matches | `pdfPages == pages` | The print engine reflowed the paginated DOM |
| Requested formats exist | every non-null entry in `outputs` is a file on disk | A render step failed silently |
| Citations resolve | every `[Sn]` marker has a source-list row, and vice versa | A claim has no traceable source |
| Conclusion present | the first page contains the recommendation | The report opens with background |

The render report carries all of the layout checks as `errors[]` entries, so reading it is the check.

## 2. Judgement checks

These have no mechanical test. The author answers each one in the delivery note.

- **Does the first page answer the brief's decision?** Read only page 1; if the answer is not there, the structure is wrong.
- **Does every section open with its claim?** Scan the first sentence of each section; a section starting with setup is a section to rewrite.
- **Is every table comparing something?** A table whose rows share no column of meaning is prose in a box.
- **Does every figure have a caption that interprets?** A caption naming the axis is a label, not a caption.
- **Is the page count what the brief allowed?** Over budget means cut content, not shrink type.
- **Does the summary compress rather than truncate?** A summary that is the conclusion copied verbatim adds nothing.

## 3. The read-back

Open the delivered artifact and read it as the audience would. For a PDF, open the PDF. For images, look at each page. For HTML, open it in a browser at the printed width.

Reading the source instead of the artifact does not count: the artifact is what the reader gets, and layout breaks are invisible in the source.

Confirm during read-back:

- The footer page count reads `n / total` and the last page says `total / total`.
- The table of contents page numbers match where the sections actually are.
- No heading sits alone at the bottom of a page with its body on the next.
- Korean text has no broken glyphs, and Latin identifiers inside Korean sentences are not hyphenated.
- Table column alignment survived: numbers right, text left.

## 4. The delivery note

Report these, briefly:

- Absolute paths of every file produced.
- Page count and the format list.
- Which checks passed, and any advisory finding kept.
- Anything the brief assumed that the user should confirm.
- Any format that could not be produced, and why.

A delivery note that says "done" without paths is not a delivery.

## Sources

> Checked 2026-11-13.

| Claim | Source |
|---|---|
| Reading the rendered surface rather than the source as completion evidence | `instructions/validation/index.md` |
| Risk-matched verification depth and the inspected-result requirement | `instructions/validation/index.md` |
| The layout checks themselves (`overflow`, `wide`, `images`, page-count agreement) | This package's `assets/runtime/report.js`, verified on 2026-11-13 |