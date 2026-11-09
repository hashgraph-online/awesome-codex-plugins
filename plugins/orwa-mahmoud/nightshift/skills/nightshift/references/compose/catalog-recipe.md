# Adding a shift to the catalog

A shift is markdown, not code. It touches no hooks and changes no enforcement, which is why the
catalog can grow without the product growing.

**Adding one is one new file in `shifts/`, copied from `templates/shift-entry.md`, and no edits to
existing ones.** [Add to a catalog](https://github.com/orwa-mahmoud/nightshift/blob/main/docs/add-to-a-catalog.md)
walks through the steps for every catalog. Nothing shared changes, so two contributors can add a
shift the same week and never meet in a diff, and Hunt offers a new file the moment it lands.

Every entry is checked against the template: its title must declare the ending, and it must carry
a **When to use** section and an **Item** section with a pasteable box and a Verify line. An
optional `tests/shifts/<your-shift>.bats` is for what is specific to yours — above all its
refusals, which are the lines a tired model reaches past at 4am.

Before writing, understand what you are writing: **a shift is a contract handed to an agent that
will work unattended, on a stranger's workspace, while they sleep.** It is not documentation and
not a suggestion. Every line is an instruction that will be followed literally.

To discuss an idea before writing files, open a
[catalog shift proposal](https://github.com/orwa-mahmoud/nightshift/issues/new?template=catalog_shift.yml)
or comment on [#21](https://github.com/orwa-mahmoud/nightshift/issues/21). The form does not replace
this recipe or the contract test — a merged entry is still the file described here.

## The six things an entry must declare

An entry that leaves any of these unanswered cannot be reviewed and will not be merged.

**1. Ending — finite or open-ended.** Finite work is a known list and stops when the list is clear;
hours are an optional cap. Open-ended work has no natural end but the clock and must not start
without a deadline. This single word decides whether Hunt asks for hours. An open-ended entry must
also carry `Ending: open-ended` as a sub-bullet inside its pasteable item, so
Start can enforce the deadline after Hunt moves the item away from its catalog heading.

**2. Discovery — how the work is found.** Name the mechanism: the project's own gate commands, a
scan of a directory, a rotating set of lenses. "Look for problems" is not a discovery method.
Do not require a `.py` helper. The model writes receipts from `receipts/cycle-specialist-evidence.md`.

**3. Definition of done.** What ends the shift, precisely. *"A full scan reports nothing new"* is
testable. *"The code is better"* is not.

**4. What it will never do.** The refusals are the most important lines in the entry, because they
are what a tired model reaches for at 4am. Be specific: never silence a linter instead of fixing
it, never weaken a test to make it pass, never delete without proving unreachable, never rewrite
history.

**5. Verification.** The item gate must be green at every commit in repository mode, or every
artifact receipt in artifact mode — state which commands prove this entry meets its definition of
done. Artifact-mode completion is `$NS/receipts/`, not a git log.

**6. Supported stacks.** Which projects this makes sense on, and how it detects them. An entry that
assumes vitest should say so rather than failing quietly on a Go repo. An entry that can run in
artifact mode should say so and must not require a git history that cannot exist.
An entry that cannot run in artifact mode must say `Never select this entry in artifact mode`.
Do not `git init` a notes folder to make a commit-only entry fit.

Two more that make an entry pleasant rather than merely correct: a **typical hours** hint so the
owner is not guessing, and **deduplication** against `snag-log.md` so a finding the owner already
rejected is never raised twice.

## Shape

`templates/shift-entry.md` shows it. The title line carries the name, the ending, and one line on
what the shift is for: `# <Name> — <finite|open-ended> — <one line>`. **When to use** says when an
owner would choose it, what they wake up to, which projects it supports, and the receipt it
writes. **Item** holds the box ready to paste under `## Items`, in a `text` fence: an imperative
title ending in a full stop, then one bullet each for how the work is discovered, the working loop,
what it will never do, the ending condition stated as a test, and the Verify line: the commands
that must pass before each commit or artifact receipt.

## Review

Every catalog PR is read by a human before merge. Schema conformance is necessary and not
sufficient: a plausible entry can still be a bad night on someone's repository, and no automated
check catches that. Expect questions about the refusals and the ending condition — those are where
unattended work goes wrong.

Entries are also welcome to be narrow. "Clear ruff findings in a Django project" is more useful
than "improve Python code", because a narrow entry can state a specific definition of done.

## Cited research

Shifts that read owner-approved URLs or local files and write a cited report inherit
[`cited-research.md`](../shift/cited-research.md). That contract is not itself a catalog entry: Hunt still
lists only `shifts/`. Put SEO, documentation-from-sources, and synthesis work in `shifts/` and
point their Verify line at `ns check-report`.
