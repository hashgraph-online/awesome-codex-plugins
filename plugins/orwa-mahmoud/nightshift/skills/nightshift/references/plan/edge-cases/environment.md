# Environment — an item that depends on the machine it runs on

## When it applies

The item uses a path, the network, a tool, or a folder whose permission it does not control.

## Cases

- **Windows paths** — backslashes, drive letters, case-insensitive names, reserved names, CRLF.
- **No network** — offline, a timeout, a proxy, a DNS failure.
- **Missing tool** — a command, runtime or library the item calls is not installed.
- **Read-only folder** — no write permission where the item writes.

## Example lines

- WHEN the output folder is read-only THEN the item names the folder and writes nothing else
