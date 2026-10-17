# Validation

1. Run `obsidian version` using the sanitized wrapper.
2. Validate discovery commands: `bases`, `base:views`, `bookmarks`.
3. Validate one structured query: `base:query ... format=json`.
4. Validate one mutating `base:create` test in a disposable vault.
5. Validate one explicit `bookmark` command per target type.
6. Confirm response includes risk level, output format, and side-effect summary.
7. Confirm non-bases/bookmarks requests route out of this skill.
