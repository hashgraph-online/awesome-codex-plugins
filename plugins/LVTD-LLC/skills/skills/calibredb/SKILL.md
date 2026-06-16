---
name: calibredb
description: Manage and query Calibre libraries with the calibredb CLI (local paths or Calibre Content server URLs). Use when listing books, searching/filtering library records, reading/updating metadata, adding/removing formats, exporting books, maintaining custom columns, running library checks, managing FTS indexing/search, or creating catalogs/backups from a Calibre library.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: CalibreDB
  category: Knowledge Management
  tags: calibre,ebooks,library-management,metadata,cli
---

# CalibreDB

Use this skill for all command-line operations on Calibre libraries.

## Library path

- Calibre library locations are user-specific. Identify the target library path
  or Content server URL before running commands.
- Prefer explicit path in every command: `--with-library "$CALIBRE_LIBRARY"`.
- If the user has not provided a library path, ask for it or inspect the local
  environment for an existing Calibre library before proceeding.
- For machine-readable outputs, use `--for-machine` or JSON-capable subcommands.

## Safety model

Start with read-only operations, then escalate only when needed.

### Read-only (safe by default)

- `list`
- `search`
- `show_metadata`
- `custom_columns`
- `list_categories`
- `check_library`
- `fts_search`
- `fts_index status`

### Mutating (confirm intent for destructive/irreversible)

- Usually safe with clear intent: `add`, `set_metadata`, `set_custom`, `add_format`, `embed_metadata`, `backup_metadata`
- Confirm before destructive actions: `remove`, `remove_format`, `remove_custom_column`, `restore_database`, `fts_index reindex` on full library

## Core workflow

1. Identify target library and set `--with-library`.
2. Discover relevant book IDs with `search` (or `list --search`).
3. Inspect records with `show_metadata` or `list --for-machine`.
4. Apply minimal required mutations.
5. Validate with follow-up `list/search/show_metadata`.

## Quick command patterns

### 1) List books

```bash
export CALIBRE_LIBRARY="/path/to/Calibre Library"
calibredb list --with-library "$CALIBRE_LIBRARY" --fields id,title,authors,formats --limit 20
```

Machine output:

```bash
calibredb list --with-library "$CALIBRE_LIBRARY" --fields id,title,authors,tags,formats --for-machine
```

### 2) Search and get IDs

```bash
calibredb search --with-library "$CALIBRE_LIBRARY" "title:python"
```

Use IDs in follow-up commands.

### 3) Show metadata

```bash
calibredb show_metadata --with-library "$CALIBRE_LIBRARY" 123
```

As OPF:

```bash
calibredb show_metadata --with-library "$CALIBRE_LIBRARY" --as-opf 123
```

### 4) Update metadata fields

```bash
calibredb set_metadata --with-library "$CALIBRE_LIBRARY" 123 \
  --field title:"Example Book" \
  --field tags:"python,reference"
```

### 5) Add/export books

```bash
calibredb add --with-library "$CALIBRE_LIBRARY" "/path/to/book.epub"
calibredb export --with-library "$CALIBRE_LIBRARY" 123 --to-dir "/tmp/export"
```

### 6) Library health check

```bash
calibredb check_library --with-library "$CALIBRE_LIBRARY"
```

## Content server usage

To target a running Calibre Content server:

```bash
calibredb list --with-library "http://hostname:8080/#library_id" --username <user> --password <pass>
```

From docs: use special `#-` library id to list server libraries.

Security note: `--password` is passed as a process argument and may be visible
to other users on shared machines via process-listing tools. Prefer local or
trusted hosts for authenticated Content server commands, and redact credentials
from shell history, logs, and task transcripts.

## Reference files

- Command matrix + options: `references/command-matrix.md`
- Safe operational playbooks: `references/safe-workflows.md`
