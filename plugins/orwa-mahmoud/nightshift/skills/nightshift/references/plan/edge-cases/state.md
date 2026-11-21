# State — an item that writes something the next run will find

## When it applies

The item creates or changes a file, a config, a cache, or a row that a later run reads.

## Cases

- **First run** — nothing created yet: no config, no cache, no database row, no prior output.
- **Upgrade from the previous version** — data or files written by the release before this one.
- **Interrupted halfway** — killed between two writes; what the next run finds and does.
- **Run twice** — the same command again on its own output; the result is the same or refused.

## Example lines

- WHEN the import is run twice THEN the second run adds no rows and says so
