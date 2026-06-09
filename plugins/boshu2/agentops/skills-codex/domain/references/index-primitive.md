---
name: Index
kind: primitive
status: tracer
see-also: [entry, citation]
---
# Index

The discovery surface for the corpus. The catalog an agent reads first to find
the right Entry to load.

## Definition

An Index is a markdown file at a known location that lists every Entry under
its root by slug, concept name, status, and kind. Agents are expected to load
the Index before loading any individual Entry, and to use it as the only
authoritative listing.

## Shape

- Lives at `<corpus-root>/INDEX.md`
- Groups Entries by structural role (primitives, vocabulary, test, ...)
- Each row: `slug | concept | status | kind`
- Includes a status legend and growth rules

## When to use

- An agent landing in this repo for the first time should load the corpus
  Index before answering any question that touches vocabulary.
- Skills, hooks, and CLI commands citing a corpus Entry should resolve the
  citation through the Index, not by guessing the file path.

## Anti-pattern

- A second discovery surface that duplicates Index rows (e.g., a sidebar in
  a doc, a hard-coded list in a skill). The Index is the sole source of truth;
  anything else is a stale fork waiting to drift.
- Implicit indexing (scanning the directory). If the file is not in the Index,
  it does not exist for citation purposes.

## Example in this codebase

`skills/domain/references/INDEX.md` is the corpus Index. The file you are
reading right now (`index-primitive.md`) is an Entry **about** the Index
concept — distinct file, distinct slug, deliberately separated to survive
case-insensitive filesystems.

## See also

- `entry.md` — what gets listed in an Index
- `citation.md` — how an Index resolves citations
