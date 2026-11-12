# `align-docs --clean`

Clean mode runs `align-docs` on every first-party document in the repository.
It also rewrites the main documents so people and agents can read and use them quickly.
Scope and authorization follow the development loop.

## Inspect

Read every first-party documentation file, and enough evidence to verify it.
For each document, record its role, owner, validity, archive state, duplicate claims, broken links, and whether the implementation still matches it.
Keep uncertain content active and report the doubt.

## Rename numbered records

Clean mode gives every `NNNN__` plan, chronicle, and research record a `YYYY-MM-DD__<slug>` name.
Run `uv run <plugin-root>/scripts/rename_numbered_docs.py <repository-root>`. It changes nothing and lists:

- `RENAME`: the new name. It drops the number and the `implementation_plan__` infix. Undated research takes the date of its plan or of its oldest commit.
- `REFERENCE`: each file and line where a full old name will change. Check the lines outside `docs/`: a test fixture or an example can contain a name that is not a link.
- `CONFLICT` and `UNRESOLVED`: records for you to handle by hand. Give a conflict a distinct slug and commit an untracked record first.
- `OUTSIDE`: a numbered document elsewhere under `docs/`. Move it into its collection only when it is a plan, chronicle, or research record.
- `CITATION`: a bare number such as `chronicle 0148`, with the record it names in this repository.

Put the list in the proposal. After approval, run the script again with `--apply`, before the other moves.
It moves each record with `git mv`, then replaces every full old name and prints each `REPAIRED` line.
Exit 1 means some records still need you; the script has moved all the others.
Read `git diff` outside `docs/`, restore each changed name that was not a reference, and run the project's tests.
For each listed citation that names a record of this repository, replace only the number with the new file name and keep the rest of the sentence.
Leave citations of other repositories unchanged.
Leave a citation with more than one candidate or with `no record here` unchanged, and report it.
Keep the `--legacy-before` cutoff: it keeps open items in older archived plans as warnings.

## Plan the changes

Apply the [documentation contract](../../../shared/documentation.md) and the archive rules of `align-docs` to every file, including plans, chronicles, component docs, and archives.
Write metadata from what the document says.
Move legacy lifecycle blockquotes into frontmatter, and remove only those metadata lines.
Chronicle decision prose never changes: do not merge, delete, or rewrite it.
Delete a document only with approval, and only when it holds no unique fact, decision, or useful history.

## Rewrite the main documents

The main documents are `README.md`, `AGENTS.md`, `.agents/rules/`, and the other docs that people and agents read first.
Rewrite each one with `development-skills:bro`, and use `development-skills:rethink` to question its structure.

- Delete claims that the evidence shows are wrong, outdated, inconsistent, or noise.
- Shorten what remains, and keep every verified fact, command, and constraint.
- Give the reader the context the next action needs: what the project is, how to run it, and which rule applies where.
- Write concrete instructions that a person can follow and an agent can execute.

This step skips plans, chronicles, and archives.

## Propose

Present one exact proposal with:

- the fixes of a normal run;
- the main documents you rewrite, and each fact you remove as wrong or outdated, with its evidence;
- metadata and lifecycle changes for each file;
- the renames of numbered records, with their conflicts and citations;
- every move, merge, archive, and deletion, with its destination or surviving owner;
- supersession and obsolescence links;
- the resulting ATLAS sections and entries;
- conflicts and evidence gaps left unchanged.

Use existing approval when it covers the listed operations.
Ask before other deletions, a change of authority, or an open ownership decision.

## Apply

Apply only the approved proposal. Use `git mv` for moves and keep unknown frontmatter fields.
For a large migration, apply it to a small representative batch first and verify it. A failed pilot stops the migration.
Before you remove a legacy index or lifecycle table, move each validity, supersession, or work-status value it records into the target document's frontmatter.
Rebuild `docs/ATLAS.md` with the `align-docs` rules.

## Finish

Finish only when:

1. no decision prose was deleted, merged, or rewritten;
2. supersession links point both ways and every obsolete document has a dated reason;
3. every document that meets the archive rules is in `archive/`, no current owner is archived, and archive fields match paths;
4. metadata is meaningful and each legacy lifecycle value has one owner;
5. ATLAS routes every agreed area, no recorded lifecycle value was lost, and every internal Markdown link resolves;
6. every deletion is an approved duplicate with no unique information, and Git can recover every move;
7. every rewritten main document keeps its verified facts, and each removed fact has evidence that it was wrong or outdated;
8. no plan, chronicle, or research name starts with a number, every citation of a renamed record uses its new name, and the project's tests pass.
