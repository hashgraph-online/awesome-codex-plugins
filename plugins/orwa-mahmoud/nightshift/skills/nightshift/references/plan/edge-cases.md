# Edge-case catalog

Read this only after the owner says yes to an edge-case pass. For each drafted item, pick the cases
below that the item can actually meet, never every case for every item, and turn each into one
WHEN/THEN line a test could fail on. The owner keeps, edits or drops each line; only the kept ones
reach the drafting table.

A case becomes a line by naming the concrete situation and the observable result:

```text
    - WHEN the config file is empty THEN the loader names the file and the key it expected
    - WHEN the import is run twice THEN the second run adds no rows and says so
```

"Handles errors" or "works on Windows" is not a line. Name the input, the state or the platform,
and what someone would see.

## Input

- **Empty** — no bytes, no rows, an empty string, an empty list.
- **Huge** — far past the size the item was written for: a long line, a large file, many rows.
- **Malformed** — truncated, wrong type, wrong encoding, a missing required field, trailing junk.
- **Unicode** — non-ASCII text, combining characters, right-to-left text, emoji, a byte-order mark.
- **Paths with spaces** — and other characters a shell or a URL treats specially: quotes, `#`, `%`.

## State

- **First run** — nothing created yet: no config, no cache, no database row, no prior output.
- **Upgrade from the previous version** — data or files written by the release before this one.
- **Interrupted halfway** — killed between two writes; what the next run finds and does.
- **Run twice** — the same command again on its own output; the result is the same or refused.

## Concurrency

- **Two sessions** — two processes or two users acting on the same thing at once.
- **A file changed underneath** — edited, moved or deleted between being read and being written.

## Environment

- **Windows paths** — backslashes, drive letters, case-insensitive names, reserved names, CRLF.
- **No network** — offline, a timeout, a proxy, a DNS failure.
- **Missing tool** — a command, runtime or library the item calls is not installed.
- **Read-only folder** — no write permission where the item writes.

## Failure

- **Partial failure** — some of a batch succeeds and some does not; what is kept and what is said.
- **Rollback** — undoing the change leaves the system as it was before, and how to run it.
- **The error the user sees** — the message names the cause and the next step, not a stack trace.

## Security

- **Untrusted input** — input from a user, a file or the network that could reach a shell, a query,
  a path or a template.
- **Secrets in logs** — tokens, passwords or personal data that could reach output, logs or errors.
