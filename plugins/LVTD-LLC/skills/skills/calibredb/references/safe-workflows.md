# Safe Workflows

## 1) Read-only audit flow

1. Verify library path exists.
2. Run `list --for-machine` with narrow fields.
3. Use `search` to identify candidate IDs.
4. Use `show_metadata` for targeted IDs.
5. Summarize findings before any mutation.

Example:

```bash
export CALIBRE_LIBRARY="/path/to/Calibre Library"
calibredb list --with-library "$CALIBRE_LIBRARY" --fields id,title,authors,formats --limit 50 --for-machine
calibredb search --with-library "$CALIBRE_LIBRARY" "title:python"
calibredb show_metadata --with-library "$CALIBRE_LIBRARY" 123
```

## 2) Metadata cleanup flow

1. Export current metadata for backup (`show_metadata --as-opf`).
2. Update minimal fields via `set_metadata --field ...`.
3. Re-run `show_metadata` to verify.
4. Optionally run `backup_metadata` for OPF sync.

## 3) Safe ingest flow

1. Add with explicit options (`--automerge` policy).
2. Verify resulting records with `search/list`.
3. Fix metadata only where needed.

## 4) Destructive action guardrail

Before running:
- `remove`
- `remove_format`
- `remove_custom_column`
- `restore_database`

Do all of:
1. Confirm exact IDs/labels targeted.
2. Produce pre-change snapshot (`list`/`show_metadata`).
3. Execute action.
4. Validate post-change state.

## 5) Database recovery warning

`restore_database` rebuilds DB from OPFs and can lose app-level settings.
Use only for real corruption recovery and always with explicit user approval.
