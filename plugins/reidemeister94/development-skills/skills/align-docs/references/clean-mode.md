# `align-docs --clean`

Clean mode reconciles every existing first-party document, applies the shared format, and removes proven noise. Reuse normal inspection, but change nothing before the proposal is approved.

## Inspect and classify

Read every first-party documentation file and enough reliable evidence to verify it. For each document, identify its role, owner, validity, archive state, duplicate claims, broken links, and whether the implementation still matches it.

Use the authority rules in `align-docs`. Code is not the source for every promise or past decision.

Keep uncertain content active and report the uncertainty. List duplicate `NNNN` prefixes without renumbering them; `resolve-merge` owns that work.

## Put each fact in the right place

Apply the [documentation contract](../../../shared/documentation.md) retroactively to every existing in-scope file, including plans, chronicles, component docs, and archives — not only files this run changes. Write meaningful metadata from the document itself.

Lifecycle metadata lives in frontmatter with the fields and rules of the documentation contract.

Move legacy lifecycle blockquotes into frontmatter and remove only those metadata lines. Chronicle decision prose is immutable: never merge, delete, or rewrite it.

Apply the lifecycle placement rules in `align-docs` across the entire corpus, not only documents affected by the current task.

Delete only approved documents that contain no unique fact, decision, or useful history.

For a large migration, apply the approved structure to a small representative batch, verify it, then continue. A failed pilot stops the migration.

## Propose, then stop

Present one exact proposal containing:

- normal alignment fixes;
- frontmatter additions or lifecycle changes per file;
- every move, merge, archive, and deletion with its destination or surviving owner;
- supersession and obsolescence relationships;
- the resulting ATLAS sections and entries;
- unresolved conflicts or evidence gaps left unchanged.

Ask **Apply (Recommended) / Modify / Cancel**, then stop. Approval must follow this exact proposal; earlier general permission does not replace it.

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
