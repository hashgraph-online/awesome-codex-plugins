# `align-docs --clean`

Clean mode reconciles every existing first-party document, applies the shared format, and removes proven noise. Reuse normal inspection, but apply the development loop's scope and authorization rules.

## Inspect and classify

Read every first-party documentation file and enough reliable evidence to verify it. For each document, identify its role, owner, validity, archive state, duplicate claims, broken links, and whether the implementation still matches it.

Use the authority rules in `align-docs`. Code is not the source for every promise or past decision.

Keep uncertain content active and report the uncertainty. Date-and-slug files need no counter.

## Rename numbered records

Run `uv run <plugin-root>/scripts/rename_numbered_docs.py <repository-root>` to preview legacy plan, chronicle, and research renames.
Review each proposed name, reference, conflict, and bare-number citation before applying the proposal.
Resolve conflicts and untracked records by hand. Do not move numbered documents outside these collections without checking their role.
After approval, add `--apply` to move tracked records with `git mv` and update full-name references.
Review every changed reference, including those outside `docs/`, and repair relevant bare-number citations by hand.
An apply run exits 1 when a renamed record still has a bare-number citation or another unresolved problem.
Keep the documented `--legacy-before` cutoff so old archived plans retain their warning status.

## Put each fact in the right place

Apply the [documentation contract](../../../shared/documentation.md) retroactively to every existing in-scope file, including plans, chronicles, component docs, and archives — not only files this run changes. Write meaningful metadata from the document itself.

Lifecycle metadata lives in frontmatter with the fields and rules of the documentation contract.

Move legacy lifecycle blockquotes into frontmatter and remove only those metadata lines. Chronicle decision prose is immutable: never merge, delete, or rewrite it.

Apply the lifecycle placement rules in `align-docs` across the entire corpus, not only documents affected by the current task.

Delete only approved documents that contain no unique fact, decision, or useful history.

For a large migration, apply the approved structure to a small representative batch, verify it, then continue. A failed pilot stops the migration.

## Present the change

Present one exact proposal containing:

- normal alignment fixes;
- frontmatter additions or lifecycle changes per file;
- every move, merge, archive, and deletion with its destination or surviving owner;
- supersession and obsolescence relationships;
- the resulting ATLAS sections and entries;
- unresolved conflicts or evidence gaps left unchanged.

Use existing approval when it covers the listed operations.
Ask before additional deletions, changed authority, or unresolved ownership decisions.

## Apply and verify

Apply only the approved proposal. Use `git mv` for moves and preserve unknown frontmatter fields.

Rebuild `docs/ATLAS.md` as the routing map defined in the skill. Before removing any legacy index or lifecycle table, move each recorded validity, supersession, or work-status value into the target document's frontmatter.

Finish only when:

1. no decision prose was deleted, merged, or rewritten;
2. supersession links are bidirectional and every obsolete document has a dated reason;
3. every document that meets the archive rules is under `archive/`, no current owner is archived, and archive fields match paths;
4. frontmatter is meaningful and legacy lifecycle metadata has one owner;
5. ATLAS routes every agreed area, no recorded lifecycle value was lost, and all internal Markdown links resolve;
6. every deletion is an approved zero-information duplicate and every move is recoverable from Git.
