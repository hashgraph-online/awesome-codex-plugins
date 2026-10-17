# Limitations and Boundaries

## This skill supports

- official desktop Obsidian CLI Bases and Bookmarks command families
- read-only discovery/query workflows for bases and bookmarks
- explicit base item creation and bookmark creation

## This skill does not cover

- general note-content CRUD workflows
- runtime administration for plugins/themes/snippets
- Sync/Publish workflows
- runtime diagnostics or eval/CDP flows
- community tooling outside official CLI

## Operational limits

- desktop Obsidian app must be available
- base identifiers and view names can be ambiguous and must be resolved explicitly
- `base:create` mutates vault content and should be treated as high impact
