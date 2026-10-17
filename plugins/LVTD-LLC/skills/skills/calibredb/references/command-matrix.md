# CalibreDB Command Matrix

Source baseline: <https://manual.calibre-ebook.com/generated/en/calibredb.html>

## Global options

- `--with-library <path|url>`: local path or Content server URL (`http://host:port/#library_id`)
- `--username`, `--password`: server auth
- `--timeout`: server connection timeout

## Discovery & reporting

- `list`: list books, supports `--fields`, `--search`, sorting, JSON with `--for-machine`
- `search <expr>`: returns matching IDs (comma-separated)
- `show_metadata <id>`: inspect metadata, optional `--as-opf`
- `list_categories`: tag-browser style category report
- `custom_columns`: list custom columns

## Ingest & metadata changes

- `add <files|folders>`: add books/formats
  - key options: `--automerge`, `--duplicates`, `--recurse`, `--one-book-per-directory`
- `set_metadata <id> --field key:value`: update one/more fields
- `add_format <id> <ebook_file>`: attach/replace format
- `remove_format <id> <FMT>`: delete one format from record
- `set_custom <column> <id> <value>`: set custom column value

## Export & distribution

- `export <ids>` or `--all`: export books/files/metadata
  - key options: `--to-dir`, `--formats`, `--single-dir`, `--template`, `--progress`
- `catalog <output.ext>`: generate catalog (csv/epub/mobi/xml...)

## Library maintenance

- `check_library`: filesystem/library consistency checks
- `backup_metadata`: force OPF backup refresh
- `clone <new_path>`: clone structure/settings into empty library
- `restore_database --really-do-it`: rebuild DB from OPFs (high risk)

## Full-text search (FTS)

- `fts_index enable|disable|status|reindex`
- `fts_search <expr>` with optional snippets/json output

## Practical command snippets

```bash
export CALIBRE_LIBRARY="/path/to/Calibre Library"

# JSON list
calibredb list --with-library "$CALIBRE_LIBRARY" --fields id,title,authors,tags,formats --for-machine

# Filter by tag/title/author
calibredb list --with-library "$CALIBRE_LIBRARY" --search "title:python or tags:python"

# ID pipeline pattern
ids=$(calibredb search --with-library "$CALIBRE_LIBRARY" "title:python")
id_filter=$(python3 -c 'import sys; print(" or ".join(f"id:{book_id.strip()}" for book_id in sys.stdin.read().split(",") if book_id.strip()))' <<< "$ids")
if [ -n "$id_filter" ]; then
  calibredb list --with-library "$CALIBRE_LIBRARY" --search "$id_filter" --fields id,title,authors
fi
```
