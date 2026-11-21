# Input — an item that reads text, a file, a list, or a path

## When it applies

The item takes input it did not produce: a file, a string, a list, or a path.

## Cases

- **Empty** — no bytes, no rows, an empty string, an empty list.
- **Huge** — far past the size the item was written for: a long line, a large file, many rows.
- **Malformed** — truncated, wrong type, wrong encoding, a missing required field, trailing junk.
- **Unicode** — non-ASCII text, combining characters, right-to-left text, emoji, a byte-order mark.
- **Paths with spaces** — and other characters a shell or a URL treats specially: quotes, `#`, `%`.

## Example lines

- WHEN the config file is empty THEN the loader names the file and the key it expected
