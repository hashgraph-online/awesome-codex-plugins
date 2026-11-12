---
name: save-to-drive
description: Save or change files on the person's Leeway drive without overwriting anyone else's edit. Use when asked to save, write, put, upload or update something "in Leeway", "on my drive" or at a drive path such as /Notes/plan.md.
---

# Save to the Leeway drive

The drive is shared: people, their computers and other agents change it while you work. Every write keeps the earlier contents as a version, so nothing is lost, but a blind overwrite still throws away someone's current work until they notice. Write so that can't happen.

## A new file

`write_file` with `path`, `content` (text; `content_base64` for bytes), and `if_none_match: "*"`. If something is already there it answers `ALREADY_EXISTS` instead of replacing it: pick another name or treat it as a change (below). `mkdirs: true` makes missing parent folders; `make_folder` makes an empty one.

## Changing a file

1. `stat_file` or `read_file` the path and keep its `rev`.
2. Make the change from what you just read.
3. `write_file` with the new contents and `if_match` set to that `rev`.
4. `CONFLICT` means it changed since you read it. Read it again, merge your change into the new contents, and retry with the new rev (`error.details.current_rev`). Never drop the `if_match` to get past a conflict.

## Big files

`write_file` carries up to about 4 MB. For larger files: `start_upload` with `path` and `size` gives `parts`, each with a `url`. Send each part's bytes with an HTTP `PUT` to its url (for example `curl -T` with the part's byte range), then `commit_upload` with the upload `id`. Those PUTs leave this machine, so they need network access from the shell. Codex's default `workspace-write` sandbox has none: curl fails to resolve the storage host (exit 6), which is the sandbox, not Leeway.
- **Ask first:** ask the person to allow network access for those commands.
- **For a file under about 4 MB:** use `write_file` instead.
- **If anything fails:** `abort_upload` leaves the file as it was.

## Saved for good

A write answers once the drive has it, and everyone reading the drive sees it at once. It is durable (safe in Leeway's storage) a moment later. Before you report work as finished, call `sync` with the paths you wrote, or pass `durable: true` on the last write.

## Retries and long calls

- Give a write an `idempotency_key`. Retrying with the same key returns the first answer instead of writing twice.
- A call waits at most 30 seconds. Longer work comes back as an operation: `get_operation` with its `id` waits for it.
- `BUSY`, `DEADLINE_EXCEEDED` and `UNAVAILABLE` are retryable after `retry_after_ms`. `FORBIDDEN` names the missing scope in `details.scope`: tell the person, don't work around it.

## Report

Say what you saved by path and its new `rev`. The drive's history records the change under your connection's name.
