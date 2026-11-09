# Concurrency — an item that shares a file or a record with another session

## When it applies

Two processes, or two users, can touch the same thing while the item runs.

## Cases

- **Two sessions** — two processes or two users acting on the same thing at once.
- **A file changed underneath** — edited, moved or deleted between being read and being written.

## Example lines

- WHEN a second session writes the same file THEN the first session names the clash and keeps its own work
