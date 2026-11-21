# Review Workflow

Tracked changes, comments, accept, and reject — what each one does to the package bytes and what it must not do.

## 1. Revision marks in the XML

A tracked change is not metadata beside the text; it is the text wrapped in a container element that carries the author and the date:

| Element | Location | Meaning |
|---|---|---|
| `w:ins` | wraps `w:r` runs inside a paragraph | inserted content, accepted keeps it |
| `w:del` | wraps `w:r` runs inside a paragraph | deleted content, accepted drops it |
| `w:delText` | inside a `w:r` inside `w:del` | the deleted characters (not `w:t`) |
| `w:ins` / `w:del` inside `w:pPr/w:rPr` | paragraph mark itself | the paragraph mark was inserted or deleted |
| `w:moveFrom` / `w:moveTo` | paragraph level | a moved block, accept keeps `moveTo` |
| `w:commentRangeStart` / `w:commentRangeEnd` | paragraph level | the text span a comment refers to |
| `w:commentReference` | a run inside the range | links the span to `w:comment` in `comments.xml` |

Two rules follow and are easy to break:

- Deleted text lives in `w:delText`, never in `w:t`. A `w:del` whose runs still carry `w:t` shows the deleted text as normal text in some readers.
- Every `w:ins` and `w:del` carries `w:id`, `w:author`, and `w:date`. Missing any of them makes the change unattributable, and Word may drop it.

## 2. Word-level versus whole-paragraph edits

A review that rewrites a paragraph as one deletion plus one insertion loses what the reviewer actually changed: the reader cannot see which words moved. Split the run at the change boundary instead:

1. Keep the run's prefix as its own run.
2. Wrap exactly the changed text in `w:del` with `w:delText`.
3. Follow it with `w:ins` carrying the replacement.
4. Keep the suffix as its own run.

`replace` does this for one exact string. When a paragraph needs several changes, call it once per string, then `verify` once at the end.

## 3. Comments

A comment is two parts in one: the text in `word/comments.xml` and the range in the body. Both must exist or the comment is invisible:

- `w:commentRangeStart w:id="N"` before the anchored content
- `w:commentRangeEnd w:id="N"` after it
- a run containing `w:commentReference w:id="N"` right after the end

The comments part needs its own relationship from the document part and a content-type override. `verify` reports `comment-anchors` as `fail` when a comment has no range or a range has no comment — the two failures readers report as "the comment disappeared" or "Word wants to repair".

Anchor to a sentence the document contains, not to an offset. Anchoring is text-based so that a rebuild of the document does not silently attach the comment to the wrong sentence.

## 4. Accept and reject

Accepting keeps insertions and drops deletions. Rejecting restores deletions and drops insertions. Both also flatten the paragraph-mark container (`w:rPr/w:ins`, `w:rPr/w:del`) so the paragraph merge behaves like the change was never there.

Run order that stays honest:

1. `revisions <file>` — record the counts by kind and author before touching anything.
2. Copy the file, accept into the copy.
3. Copy the original, reject into the second copy.
4. `text` all three and compare: accepted and rejected must each contain what their names promise, and neither may still carry revision containers.
5. `verify` both outputs.

A file with no revisions gets `{"insertions_kept": 0, "deletions_dropped": 0}` from accept. That is a valid result, not a failure; say so instead of reporting a broken run.

## 5. Diffing two files

`compare a.docx b.docx` reports paragraph-level hunks with package facts (paragraph counts, digests). Use it to prove a review changed only what was named:

| Situation | Expected result |
|---|---|
| A comment was added, no text touched | `no textual differences` |
| One word was replaced | one `replace` hunk containing that paragraph |
| A section was rewritten | several hunks; read them before delivery |

`compare` reads text, so a pure formatting change reports no difference. When the request was "make this bold", the diff is not the proof — the render is.

## 6. What to report

Name the revision counts, the authors, the comment ids and their anchors, and which of accept/reject produced which file. A review report that says "표시했습니다" without the counts cannot be checked by the person receiving the file.

## Sources

> Checked 2026-11-13

- ECMA-376, revision marks and comment elements in WordprocessingML — https://ecma-international.org/publications-and-standards/standards/ecma-376/
- Microsoft Learn, accept all revisions in a word-processing document — https://learn.microsoft.com/en-us/office/open-xml/word/how-to-accept-all-revisions-in-a-word-processing-document
- Microsoft Learn, insert a comment into a word-processing document — https://learn.microsoft.com/en-us/office/open-xml/word/how-to-insert-a-comment-into-a-word-processing-document
