---
name: history-and-undo
description: See a Leeway file's earlier versions or the drive's trash, and bring things back. Use when asked to undo, revert, restore, recover a deleted file, see who changed something, or show a file's history on the Leeway drive.
---

# History and undo on the Leeway drive

Nothing written to a Leeway drive is lost straight away: every overwritten file keeps its earlier contents as versions, and deleted files and folders wait in the trash for 30 days.

## Earlier versions of a file

1. `list_versions` with `path`: newest first, each with `version_id`, `at`, `size`, `rev` and `by` (the person, the app and the device that made it).
2. Show the person which version you mean (when and by whom), and read it with `read_file` if they want to compare.
3. `restore` with `version_id` puts it back. What it replaces becomes a version itself, so a restore can be undone the same way.

## Deleted files

- `delete` with `path` moves a file to the trash; `recursive: true` is needed for a folder. It answers with a `deleted_id`. Check with the person before deleting anything they didn't name.
- `list_deleted` lists the trash, newest first; `prefix` narrows it to one folder.
- `restore` with `deleted_id` brings it back to where it was. If something now sits at that path, `on_exists` chooses what happens; by default nothing is overwritten. `to` puts it somewhere else.

## Who changed what

`list_events` lists recent activity, and each version's `by` names who made it.

## What can't be done here

There is no tool to empty the trash or erase history: the trash empties itself after 30 days. If someone asks for a permanent erase, say so rather than deleting more.

## Report

Say what you restored, from which version or deleted entry, and its path and `rev` now.
