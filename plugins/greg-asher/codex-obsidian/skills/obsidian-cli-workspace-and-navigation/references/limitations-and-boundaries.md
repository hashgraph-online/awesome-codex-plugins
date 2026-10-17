# Limitations and Boundaries

## This skill supports

- official desktop Obsidian CLI workspace/navigation command families
- vault metadata and vault list inspection
- workspace and tab inspection plus workspace state changes
- navigation and utility commands (`open`, `random*`, `unique`, `web`, `wordcount`)

## This skill does not cover

- note-content CRUD/tasks/properties/history workflows
- runtime administration for plugins/themes/snippets/command registry
- Sync/Publish workflows
- runtime diagnostics or eval/CDP flows
- community tooling outside official CLI

## Operational limits

- desktop Obsidian app must be available
- `vault:open` is not currently covered by this skill in this plugin release
- workspace load/delete can significantly change current app layout state
