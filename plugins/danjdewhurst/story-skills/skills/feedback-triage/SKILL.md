---
name: feedback-triage
description: This skill should be used when the user asks to "process beta reader feedback", "alpha reader feedback", "feedback round", "synthesize reader feedback", "reader notes", "beta feedback", "reader readiness check", "review copy", "send the draft to readers", "share with readers who don't use GitHub", "triage the reader panel", or wants to collect, reconcile, and act on external reader feedback for a story project. NOT for running the simulated reader panel itself (use reader-panel), rounds with a professional editor (use editorial-review), or for checking a manuscript is ready to query or publish (use submission or publishing).
---

# Feedback Triage

## Overview

Process alpha/beta reader feedback as a structured, reconcilable workflow:
collect per-reader feedback files, hold all revision until the round is
complete, synthesize convergent/divergent/single-reader findings into a
decision record with a readiness verdict, and hand a concrete revision plan
to the `revision-continuity` skill.

## Prerequisites

A story project with at least one drafted chapter (or a complete draft) that
readers have read. Verify `story.md` exists in the project root.

## When to Use

- Starting a feedback round (recruiting readers, sending chapters out)
- Giving readers a review copy, including the GitHub Pages review-copy
  workflow and the reader-note issue form (step 1 of the workflow; other
  skills point here)
- Recording feedback as it arrives
- Synthesizing a completed round into decisions
- NOT for revising the manuscript (use `revision-continuity` with the
  synthesis's revision plan)
- NOT for the agent's own critique of the draft (use `revision-continuity`
  audits; reader feedback is external input)
- NOT for producing simulated persona reads (use `reader-panel`; this
  skill synthesises the round it writes)

## Workflow

### 1. Set up the round

1. Decide the round scope: which chapters readers get (`chapters-read` range)
   and how many readers (2–4 per round is typical; one reader is a data
   point, not a round).
2. Create the round folder: `feedback/round-{N}/`.
3. Give readers a review copy they can open without a terminal. Build it
   from text you can get back, so the round can be rebuilt and old labels
   mapped later (step 2 of Collect). Save that text first:

   - **Git project:** work from the book's folder, the one that holds
     `story.md` (`cd` there first), because `-- .` below means the
     current folder. Check that `.gitignore` lists `dist/` (`story init`
     writes one that does; add the line if it is missing), so earlier
     review copies stay out of the commit. Then run
     `git status --untracked-files=all -- .` and show the user what it
     lists: the copy is built from the working tree, but a tag points at
     the last commit, so uncommitted changes would make the two differ.
     Look through it for private files (a `.env`, keys or credentials,
     scanned documents): unless the user says to commit one, add it to
     `.gitignore` first. Ask before committing and before tagging. With
     approval, commit the project folder only (skip the commit when the
     tree is already clean) and tag that commit:

     ```shell
     git add -A -- .
     git commit -m "Feedback round {N}" -- .
     git tag feedback-round-{N}
     ```

     If the user declines the commit, never tag the last commit over an
     uncommitted tree: take a snapshot as below, or stop.
   - **Project without git, or the user declined the commit:** take a
     snapshot with `story snapshot feedback-round-{N} --path .`.

   Then build the stamped HTML copy from that text:

   ```shell
   story build . --format html --stamp feedback-round-{N}
   ```

   Never push, and never move or delete a tag, without the user's
   approval: a push to `main` can publish the manuscript through the
   review-copy workflow below. The single-file HTML copy in `dist/` has a table of
   contents, the build stamp at the top, and a paragraph label beside every
   paragraph (`ch03-p12` is chapter 3, paragraph 12). A label is the
   chapter and the paragraph's position in that build, not a permanent id:
   any earlier edit in the chapter renumbers it, and `story move` changes
   its chapter part. Ask readers to cite the label, the build stamp, and the
   paragraph's first few words with each note.

   **GitHub review copy.** This is the setup the other skills point to.
   For a project on GitHub, offer the templates from the Story Skills
   repository (https://github.com/danjdewhurst/story-skills,
   `templates/github/`). The `review-copy.yml` workflow publishes the HTML
   copy to GitHub Pages on each push to `main`, stamped with the date and
   short commit, with a **Note** link beside every label (`--note-url`)
   that opens the issue form prefilled with the label, build, and first
   words. Like every build, it leaves out a matter page whose `permission`
   is `pending` or unclear (warning `permission-pending-left-out`), so an
   uncleared epigraph never reaches Pages; never add `--include-pending`
   to the workflow. The `ISSUE_TEMPLATE/manuscript-note.yml` issue form asks readers
   for the label, build, first few words, note type (typo or wording,
   confusing, continuity, pacing, character, sensitivity or authenticity,
   loved this, other), how much it affected their reading, and the note.
   Before asking to copy them, warn that a public Pages site makes the
   manuscript public unless the repository and Pages are private, and
   confirm the visibility the user wants. Then copy them into the story
   repository's `.github/workflows/` and `.github/ISSUE_TEMPLATE/` only
   with the user's approval, and create a `manuscript-note` label first;
   GitHub only applies existing labels.
4. For each expected reader, create a stub file from
   `references/feedback-template.md` at
   `feedback/round-{N}/{reader-kebab}.md` with frontmatter filled in and the
   body sections empty. The stub list is the round's checklist.

### 2. Collect feedback (the discipline)

1. As each reader's notes arrive, record them in their file using the
   template. Quote or closely paraphrase; do not editorialize yet. Keep
   each note's paragraph anchor (`ch03-p12`) in its **Where** line; convert chapter
   or page references from other formats to anchors when the location is
   unambiguous. For notes filed through the issue form, fetch them with
   `gh issue list --label manuscript-note --state open --json number,title,body,author`
   and map the form's "How much did it affect your reading?" answer to the
   template's severity: `Made me want to stop reading` is `major` (`blocking`
   when several readers stopped at the same place), `Pulled me out for a
   moment` is `minor`, `Barely noticed` is `nit`, and a blank answer is
   `minor`. A `Typo or wording` note with a blank answer is a `nit` unless
   the reader says more.
2. **Map old labels to the current text.** When a note's build is older
   than the manuscript, its label may point at a different paragraph now.
   Resolve every label from the round in one run against the text the
   round saved in step 1: the git tag (or the short commit in the note's
   build stamp), or the snapshot of the same name when the project has no
   git or the user declined the commit. A `reader-panel` round saved its
   text the same way as `panel-round-{N}` instead of `feedback-round-{N}`.
   `git tag --list 'feedback-round-{N}'` and `story snapshot --list --path .`
   show which one the round has. Readers type labels into the issue form,
   so before a label goes into the command, check that it is lower-case
   letters, digits, and hyphens ending in `-p` and a number (`ch03-p12`,
   `front-epigraph-p1`), and ask about any other. Quote each label:

   ```shell
   story compare . --ref feedback-round-{N} --anchor 'ch03-p12' --anchor 'ch07-p4'
   ```

   For a snapshot, use `--snapshot feedback-round-{N}` in place of
   `--ref`. Each line gives the current label: `(text unchanged)`, or `(edited, NN%
   similar)` when the paragraph was revised (check it is the one the
   reader meant). `not found in the current text ("…")` means the
   paragraph was cut or rewritten past recognition: search the chapter for
   the reader's quoted words, or the words shown, and mark the note
   ambiguous if nothing matches. `no such label` means the label never
   existed in that build: check the note's build and the reader's typing.
   Record the current label in the **Where** line, keeping the reader's
   original label in brackets. Sensitivity and authenticity reads use the same file shape;
   see the `editorial-review` skill for commissioning them.
3. Run the **canon check** on each problem note: verified against the bible,
   contradicts canon (usually a setup problem — note the canon file), or
   outside canon scope. Record the result in the file.
4. **Do NOT revise until all feedback for the round is in.** Revising on
   partial feedback optimizes for the first reader and invalidates the
   others' reads. If a reader is late, either wait or formally close the
   round without them (note it in the synthesis) — never silently proceed
   on a partial set.

### 3. Synthesize

Only when every expected reader file is collected. If the round's files
carry `source: simulated`, it is a panel round from the `reader-panel`
skill: follow "Simulated rounds" below as well.

1. Read all reader files for the round.
2. Sort every finding into exactly one category:
   - **Convergent** — ≥2 readers agree independently. Strongest signal;
     becomes a revision item by default.
   - **Divergent** — readers disagree. Adjudicate: check both sides against
     canon and premise, record which side wins and why.
   - **Single-reader** — one reader only. Weigh by specificity:
     specific + canon-verifiable → investigate or accept; vague +
     taste-based → usually decline.
   - **Declined-with-reason** — explicitly rejected, with a recorded reason
     referencing canon, premise, genre contract, or craft principle.
3. Write `feedback/round-{N}/synthesis.md` using
   `references/synthesis-template.md`, including the frontmatter readiness
   verdict: `ready` | `needs-revision` | `not-ready`.
4. Build the numbered revision plan with concrete file targets.

### 4. Hand off the revision plan

1. Present the synthesis summary and readiness verdict to the user.
2. If the verdict is `needs-revision` or `not-ready`, hand the revision
   plan to the `revision-continuity` skill for execution. The synthesis is
   the input; revision-continuity owns the edits.
3. If the verdict is `ready`, the round is closed — proceed to the next
   round, the next drafting stage, export, or the `submission` skill.

## Simulated rounds

The `reader-panel` skill writes persona reads in this skill's file shape,
with `source: simulated` and `persona` in the frontmatter. A file without
`source`, or with `source: human`, is a human reader's. Synthesise a
panel round as usual, with these differences:

- **Label it.** Set `source: simulated` in the synthesis frontmatter and
  start the readiness line with "Simulated round:". Refer to the files by
  persona ("the line-editor persona"), never as readers or beta readers.
- **Personas are not independent.** Several personas run by one model
  agreeing is one signal, not convergence. Sort every simulated finding as
  single-reader or declined-with-reason, weighed by how specific and checkable it is: a quoted POV
  slip or a contradiction with both sides cited is worth acting on; a
  taste note is usually declined.
- **Check before acting.** Personas leave the canon check to you (they
  cannot read past their range), so run it here, and confirm each
  simulated problem in the text before it enters the revision plan. A note the text does not bear out
  is declined with the reason "not borne out by the text".
- **What `ready` means.** A simulated round's `ready` means ready for
  human readers, nothing more. It never closes a book for submission or
  publication; hand off to a human round, not to `submission`.
- **Never mix rounds.** Simulated and human reads go in separate rounds.
  If a round holds both, move the simulated files to their own round
  before synthesising. When a later human round repeats a simulated
  finding, the human readers' notes carry it; the earlier panel adds no
  weight.
- The sensitivity persona only flags passages for a human reader. Its
  notes become items for an `editorial-review` brief, never a finding that
  a portrayal is fine.

## Conventions

- Feedback lives under `feedback/round-{N}/`; `{N}` is a plain integer
  (`round-1`, `round-2`).
- Reader files use kebab-case reader ids: `feedback/round-1/maria-chen.md`.
- Locations cite paragraph labels from `story build --format html`
  (`ch03-p12`) where available. Labels are paragraph positions in one
  build, so tag and stamp each round's build, rebuild and resend the review
  copy between rounds, and map an old label to the current text with
  `story compare . --ref <round-tag> --anchor '<label>'` (or
  `--snapshot <round-name>` when the round was saved as a snapshot; step
  2.2) rather than reusing it after a revision.
- Every feedback file and the synthesis carry YAML frontmatter
  (`reader`, `round`, `chapters-read`, `overall-verdict` / `readers`,
  `readiness`). Simulated reads and their synthesis also carry
  `source: simulated`; simulated reads carry `persona`.
- Findings are quoted or closely paraphrased from readers, never invented.
  If a note is ambiguous, mark it ambiguous in the file rather than
  resolving it silently.
- Declined findings always carry a recorded reason. A synthesis with
  unexplained rejections is incomplete.
- Bidirectional discipline: when synthesis creates or resolves
  `continuity/questions/` entries (reader confusion often reveals clarity
  gaps), update those files too.

## CLI Maintenance

Use the Story CLI when it is available. If `story` is not installed, use the bundled fallback `node ../story-maintenance/scripts/story.js` with the same arguments. Use `node <checkout>/bin/story.js` instead only when the user names a Story Skills repository checkout or you are working in one. Write the script as an absolute path (resolve the fallback relative to this skill folder) and run it from the folder you would run `story` from, so `.` and other relative paths keep their meaning. Use Node, not Bun or a package script: Bun would load that folder's `bunfig.toml` (which can run code) and `.env`, and a package script runs from the checkout's root. If no CLI is available, perform the registry, backlink, and word-count checks manually.

After creating or updating feedback files and synthesis:

```shell
story reindex .
story wordcount . --write
story check .
```

## Reference Files

- **`references/feedback-template.md`** - Per-reader feedback file template with frontmatter (`reader`, `round`, `chapters-read`, `overall-verdict`, and `source`/`persona` for simulated reads), paragraph anchor citations, the review-copy note for readers, and canon-check discipline
- **`references/synthesis-template.md`** - Round synthesis template: convergent/divergent/single-reader/declined-with-reason categories, readiness verdict, revision plan

## Shared Conventions

Every story skill follows the shared conventions in [`../story-maintenance/references/conventions.md`](../story-maintenance/references/conventions.md), resolved relative to this skill folder. Read it before creating, renaming, or linking story files. If that file is missing because this skill was installed without `story-maintenance`, the essentials are: kebab-case ids and filenames, YAML frontmatter on every story-project file, `_index.md` registry tables that `story reindex` rebuilds (never edit them by hand), bidirectional links between entities, `characters` for who is on the page and `mentions` for who is only referred to, `status: deceased` plus `died-in: chapter-{NN}` for deaths, and no project-local generator or build scripts (run only the installed or bundled Story CLI).
