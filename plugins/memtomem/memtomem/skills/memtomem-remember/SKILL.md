---
name: memtomem-remember
description: Save an explicit user-requested memory with memtomem. Use only when the user clearly asks to remember, record, or persist information for later.
---

# Remember information

Derive the content to remember from the current user request.
If the request does not clearly specify the content to remember, ask before calling a tool — and
in a non-interactive context (a subagent or scripted run with nobody to ask), do not
stall and do not guess: stop and report `insufficient_input` naming the missing content to remember.
A request that does specify the content to remember proceeds normally in either context.
Confirm that the user explicitly requested persistence. Add a natural title and a small set of useful tags only when they are clear from the content.

This workflow writes user-scope memory only. Call `mem_add` with `scope="user"` and without a `file` argument (an explicit file path can carry its own scope); never pass `project_local` or `project_shared`.

- If the user explicitly asked for a project-only destination (for example "only in this project" or `project_local`), do not write. Explain that this workflow stores memories in the user-scope store shared with their other agents, and save there only if they then agree; in a non-interactive context, stop without writing and report `unsupported_scope`.
- Otherwise, for a project-specific fact, name the project in the content or a tag so it stays findable.

Always leave `force_unsafe=false`. Report the effective scope, written file, and indexed chunk count. If the tool reports a similar memory, surface the warning rather than silently creating another variant.
