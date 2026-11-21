---
name: taskhold-todos-to-tasks
description: Turn TODO, FIXME and HACK comments in a codebase into Taskhold tasks that keep the file path and line number, so the backlog lives in one list the person and every agent share. Use when the user says "turn these TODO comments into tasks", "collect the TODOs", "file the FIXMEs", "move TODO.md into Taskhold", or "what TODOs are left in this repo". Needs the Taskhold MCP tools (taskhold_*); if they are missing, use the taskhold skill to set up.
---

# TODO comments to Taskhold tasks

## Find them

Search the repo for `TODO`, `FIXME` and `HACK` comments, skipping vendored and generated code (node_modules, dist, build, .next, vendor, lockfiles). For each, note the file, the line and the comment text plus a line or two of surrounding code.

## Skip duplicates

Before filing, `taskhold_search` with a few words of the comment (and `taskhold_list` with `project`) to skip TODOs that already have a task.

## File each one

`taskhold_create_from_todo` with:
- `title`: the TODO rewritten as a short action ("Retry failed webhook deliveries"), not the raw comment.
- `file_path` and `line_number`: where the comment is.
- `description`: the comment text and the surrounding context the next agent needs.
- `priority`: low by default; medium or high only for real bugs (FIXME that breaks behavior, security notes).
- `project`: the repo folder name.

The task gets the `todo-from-code` label and keeps the code location.

## Report back

Tell the person how many TODOs you found, how many you filed, how many were duplicates, and the three that look most important. Don't delete the comments unless they ask; a later agent can remove each one when it completes the task.

## TODO.md files

For a TODO.md or similar list the person points at, file each open item with `taskhold_create` (no code location), keeping their order as priority where it is clear.
