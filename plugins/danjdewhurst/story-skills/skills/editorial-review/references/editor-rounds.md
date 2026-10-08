# Editor Rounds and Review Copies

A human editor works in their own tools, usually Word with Track Changes.
The markdown project stays the source of truth: every round goes out as a
built file and comes back as edits the author accepts, transferred into
the chapter files.

## Types of edit

| Round | Editor delivers | Where it goes |
|-------|-----------------|---------------|
| Developmental / structural | Editorial letter, margin notes | `feedback-triage` (as a feedback round), then `revision-continuity` |
| Line edit | Tracked changes and comments | Accept in Word, transfer accepted text; see `line-editing` for the agent's own pass |
| Copyedit | Tracked changes, queries, a style sheet | Transfer text; merge their style sheet into `style-sheet.md` |
| Proofread | Marked-up PDF or HTML notes | Fix in markdown, rebuild, check again |

## Sending a round

1. Settle the chapters first: `story reindex .`,
   `story wordcount . --write`, and `story check .`.
2. Commit and tag the version sent, so the return can be compared
   against it. Work from the book's folder, the one that holds
   `story.md` (`cd` there first), because `-- .` below means the current
   folder. Check that `.gitignore` lists `dist/` (`story init` writes
   one that does; add the line if it is missing), so earlier builds stay
   out of the commit. Then run `git status --untracked-files=all -- .`
   and show the user what it lists. Look through it for private files
   (a `.env`, keys or credentials, scanned documents): unless the user
   says to commit one, add it to `.gitignore` first. With the user's
   approval, commit the book's folder only and tag that commit:

   ```shell
   git add -A -- . && git commit -m "Manuscript sent to editor, round 1" -- . && git tag sent-to-editor-1
   ```

   The `-- .` keeps files outside the book's folder out of the add and
   the commit, staged or not; when the book's folder is the repository
   root, that is the whole repository. If the status lists nothing,
   skip the add and the commit and run only the tag. If the user
   declines the commit, or it fails, never tag the last commit over an
   uncommitted tree: copy the project as below instead, or stop.

   Never push, move, or delete tags without approval. Without git,
   copy the project folder beside it (`../{project}-sent-to-editor-1`).
3. Build what the editor asked for:

   ```shell
   story build . --format docx          # Word, for tracked changes
   story build . --format docx --shunn  # Word in manuscript format
   story build . --format html          # single-file reading copy with paragraph anchors
   ```

4. Tell the user where the file was written (`dist/`) and what to send
   with it: the style sheet, the synopsis, and specific questions.

## Taking edits back

1. The author reviews tracked changes in Word and accepts or rejects
   each. The agent does not decide which edits to accept.
2. If the author shares the returned DOCX, read it with a DOCX-capable
   tool. Transfer accepted text into each chapter's markdown by hand,
   chapter by chapter; never convert the whole DOCX back over the
   project, which would drop frontmatter, scene structure, and metadata.
3. Open comments and queries become a list: wording queries to
   `line-editing`, story and continuity queries to `revision-continuity`,
   big-picture notes to `feedback-triage`.
4. Merge the editor's style decisions into `style-sheet.md`.
5. Report how much changed:

   ```shell
   story compare . --ref sent-to-editor-1
   ```

   The report lists each chapter's word change, added and removed
   chapters, and the share of paragraphs unchanged.
6. Run CLI Maintenance, then, with approval, tag the result
   (`editor-round-1-done`) before the next round.

## Review copies with paragraph anchors

`story build . --format html` writes one self-contained file with a
table of contents and a paragraph anchor on every paragraph: `ch03-p12` is
chapter 3, paragraph 12. Reviewers cite the anchor in an email, comment,
or issue, and the note points at an exact paragraph whatever format the
reader happens to be reading.

Anchors are paragraph positions counted in the built copy, not permanent
ids. After a revision, paragraph numbers can shift. Tag the commit you
share, build with `story build . --format html --stamp <tag>` so the copy
names its build, and ask reviewers to quote the build and each paragraph's
first few words. To place an old note, run
`story compare . --ref <round-tag> --anchor '<label>'` (repeat `--anchor` for
every label in the round): it prints each paragraph's current label, whether
its text was edited, or its first few words when it is gone, so you can
search for the reader's quote instead. Add `--note-url <issue-form link>` to
the build to give every label a **Note** link that prefills the issue form.

For a GitHub-hosted project, the `feedback-triage` skill sets up the
review-copy workflow, which republishes the HTML copy to GitHub Pages on
every push to `main`, and the issue form readers file notes with (step 1
of its workflow). Pages sites can be public: confirm visibility with the
user before enabling it, and ask before creating any file in `.github/`.
Collect those issues into a `feedback/round-{N}/` file per reader and
triage them with `feedback-triage`.
