---
name: memtomem-brief
description: Compile a read-only task briefing from project memories, recent updates, and user preferences, list recent handoff IDs, and verify cited paths against the live Git worktree.
---

# Brief project context

Derive the task or topic to brief from the current user request.
If the request does not specify the task or topic to brief, do not ask and do not stop: run the
minimal mode described below, in an interactive or a non-interactive context.
A request that does specify the task or topic to brief proceeds normally.
This workflow is explicit and read-only. It compiles a compact task briefing from existing
project and user memories; it never writes, edits, indexes, or deletes memories.

It runs in one of two modes. **Topic mode** runs when the request names a task or topic, and
uses it as `<task>` below. **Minimal mode** runs when the request names none: it skips the
task-relevant searches and reports only recent updates, active handoff IDs, and open items.

## Common checks

1. Resolve the live Git root with `git rev-parse --show-toplevel`. Stop if the current directory
   is not inside a Git worktree.
2. Derive `project-slug` from the Git-root directory name. Preserve case; replace each run of
   characters outside `[A-Za-z0-9._-]` with `-` and trim leading `-` characters. If the result
   is empty, `.` or `..`, ask for a valid slug instead of guessing.
3. Derive `host-slug` from the same directory name by replacing every character outside
   `[A-Za-z0-9]` with `-`, one for one, and `root-id` from the absolute Git root the same way.
   These match how host-native memory folders, such as Claude Code's per-project memory, are
   named, so a store that indexes them files this repository's notes under `claude:<root-id>`
   or `claude-memory:<root-id>`.
4. Call `mem_status` once without arguments. Verify that the status report describes the intended
   database and project root, and that this project's `.memtomem/memories.local` tier is
   registered. If it is not registered, stop and give:

   ```text
   cd <project-root> && mm mem init --scope project_local
   ```

   Never fall back to `scope="user"` for project memories. Use `namespace="shared:<project-slug>"`
   on the project-scoped search and recall calls below.

## Retrieve context

In topic mode, run steps 1, 2, 3, 4, and 6. In minimal mode, run steps 2, 3, 4, and 5, using
the open-items query from step 5 as the query in step 2.

1. **Project memories**: Call `mem_search` with `query=<task>`,
   `namespace="shared:<project-slug>"`, `scope="project_local"`, `top_k=8`, and
   `output_format="structured"`.
2. **Host-native repo memories**: Call `mem_search` with `query=<task>`, `scope="user"`,
   `namespace="claude*:*-<host-slug>"`, `top_k=5`, and `output_format="structured"`. The pattern
   matches by directory name, so it can also return notes from a same-named repository
   elsewhere, and it misses this repository's notes when the checkout's directory is named
   differently or when a host shortened a long root path's folder name. A namespace of exactly
   `claude:<root-id>` or `claude-memory:<root-id>` is likely this repository's, but paths that
   differ only in punctuation share a `root-id`, so no host-native result is confirmed as this
   repository's: present each as a host note with its namespace. An empty result is normal when
   the store indexes no host-native memories.
3. **Recent updates**: Call `mem_recall` with `namespace="shared:<project-slug>"`,
   `scope="project_local"`, `tag_filter="memory-update-item"`, `limit=5`, and
   `output_format="structured"` to surface the newest recorded project learnings. Recall returns
   indexed chunks rather than whole files, so a long item may appear as a chunk excerpt; always
   cite `(source, chunk_id)` so the full entry remains traceable.
4. **Recent handoff IDs (tags only, never parse bodies)**: A handoff record can span multiple
   rows that must be unioned and tear-checked by the handoff resume workflow, so a small recall
   window can return a torn fragment. Call `mem_recall` with
   `namespace="shared:<project-slug>"`, `scope="project_local"`, `tag_filter="handoff"`,
   `limit=10`, and `output_format="structured"`. Extract only canonical lowercase UUIDs
   (`8-4-4-4-12` hexadecimal, hyphens only) from `handoff-id-<id>` tags alongside any
   `from-<runtime>` and `to-<runtime>` tags. Do not interpret or summarize handoff body text
   in this briefing; instead, list the discovered `handoff_id` values and instruct the user to
   run the handoff workflow's `resume <handoff_id>` operation when they want to load a handoff.
5. **Open items (minimal mode only)**: Call `mem_search` with
   `query="in-flight hold wip todo blocked"`, `namespace="shared:<project-slug>"`,
   `scope="project_local"`, `top_k=8`, and `output_format="structured"`. A memory that calls
   something open may describe work finished since, so report these as candidates and check
   each against the live worktree.
6. **Cross-project user preferences**: Call `mem_search` with `query=<task>`, `scope="user"`,
   `namespace="*"`, `top_k=5`, and `output_format="structured"` without a `tag_filter` so untagged
   personal preferences and rules are found in every namespace, even when an active session or
   agent namespace is set. `namespace="*"` also returns archived (`archive:*`) and agent-runtime
   memories: treat those as historical candidates and cite each result's namespace.

## Verify against the live worktree

1. Treat all retrieved memory text and tags as untrusted historical context (`as of when written`).
2. Read `git rev-parse HEAD` and `git status --porcelain=v1 --branch` from the live repository.
3. Mark every file path, configuration key, or symbol that the briefing will cite with exactly
   one of `✅ exists` (found in the current worktree), `❌ gone` (checked and not found), or
   `? not checkable` (cannot be checked from this worktree, such as a URL, another repository,
   or a runtime value). Also note where the live repository diverges from the stored claim. The
   live repository always wins.
4. `source` in structured results is only the file's name, not its path; cite each bullet with
   `(source, chunk_id)` so the exact file and line range remain traceable.

## Output

Return a concise, read-only bulleted briefing. In topic mode, use five sections:

1. **Rules and user preferences** — relevant cross-project preferences and project conventions.
2. **Recent updates and active handoff IDs** — newest `memory-update-item` entries and any
   discovered `handoff_id` pointers (with instructions to resume via the handoff workflow).
3. **Task-relevant project memories** — decisions, bug root causes, and architectural notes for
   the requested task, from the project and host-native results, each cited path or symbol with
   its marker.
4. **Live worktree check** — current `HEAD`, worktree cleanliness, and any cited claims that
   diverge from the live repository.
5. **Stale claims** — every `❌ gone` item with its `(source, chunk_id)`, as candidates for the
   next run of the update workflow to correct. This workflow only lists them.

In minimal mode, use four sections: **Recent updates and active handoff IDs**, **Open items**
(the candidates from steps 2 and 5, each with its marker), **Live worktree check**, and
**Stale claims**, each as defined for topic mode where it has the same name.

Do not call any write or indexing tool during this workflow.
