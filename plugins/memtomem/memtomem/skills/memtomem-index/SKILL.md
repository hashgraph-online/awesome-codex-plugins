---
name: memtomem-index
description: Index or re-index an explicitly selected file or directory with memtomem. Use for initial ingestion or intentional refresh after file changes.
---

# Index memory files

Derive the file or directory path from the current user request.
If the request does not clearly specify the file or directory path, ask before calling a tool — and
in a non-interactive context (a subagent or scripted run with nobody to ask), do not
stall and do not guess: stop and report `insufficient_input` naming the missing file or directory path.
A request that does specify the file or directory path proceeds normally in either context.
Require an explicit file or directory path before calling `mem_index`; never rely on its `.` default. Resolve ambiguity with the user before indexing a broad directory.

Use `force=false` and `auto_tag=false` unless the user explicitly requests otherwise. Report scanned, indexed, skipped, deleted, and blocked counts. Explain redaction or embedding-mismatch failures without bypassing them automatically.
