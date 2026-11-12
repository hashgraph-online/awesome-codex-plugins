---
name: workspace-publish
description: Make bigger changes to a Leeway folder in a workspace (a private fork), show the diff, and publish it back only when the person agrees. Use for multi-file edits, renames or reorganising a Leeway folder, or when asked to fork, draft, stage, review or publish changes on the drive.
---

# Work in a workspace, then publish

A workspace is a fork of one folder that costs no extra room. You change the fork; the live folder, and everyone using it, is untouched until you publish. Use one whenever a change spans several files, or the person should see it before it lands.

## 1. Fork

`create_workspace` with `source` set to the folder, such as `/Site`, and optionally a `name`. Keep the answer's `id` and `path`: the fork is at `/.workspaces/<id>/`, and that folder holds the same files as the source.

## 2. Change the fork

Use the ordinary tools on paths under the workspace's `path`: `read_file`, `write_file`, `make_folder`, `move`, `delete`. For example `/Site/index.html` is `/.workspaces/<id>/index.html` in the fork. Save as the save-to-drive skill says.

## 3. Show the diff

`diff_workspace` with `id` lists each change: `path`, `op` (add, modify or delete) and `conflict`. `conflict: true` means the live folder also changed there since you forked. Show the person the list, and for a conflict say what changed on both sides.

## 4. Publish, when they agree

1. `publish_workspace` with `id` and `dry_run: true` shows what would be applied.
2. `publish_workspace` with `id` puts the changes into the live folder in one step.
   - It never overwrites a live change: with the default `on_conflict: "keep_both"`, a conflicting file is kept beside the live one, listed in `conflicts` with its `kept_as` path.
   - `on_conflict: "fail"` publishes nothing when anything conflicts.
   - Publishing again is safe.
3. A long publish may come back as an operation: `get_operation` waits for it.

## Or throw it away

`drop_workspace` with `id` discards the fork; its files go to the trash. `list_workspaces` and `get_workspace` show open workspaces. Unused ones expire on their own (14 days by default).

## Report

Say what was published, by path, and name any `kept_as` files the person should look at.
