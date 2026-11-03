---
name: memtomem-setup
description: Set up and verify a first memtomem memory source. Use for onboarding, choosing an index path, or confirming that search works.
---

# Set up memtomem

Derive the memory source path from the current user request.
If the request does not clearly specify the memory source path, ask before calling a tool — and
in a non-interactive context (a subagent or scripted run with nobody to ask), do not
stall and do not guess: stop and report `insufficient_input` naming the missing memory source path.
A request that does specify the memory source path proceeds normally in either context.
1. Call `mem_status` and treat the default `provider=none` BM25-only configuration as healthy.
2. If status says memtomem is not configured, stop before indexing and give the exact terminal bootstrap command from the plugin README. Preserve project context by prefixing it with `cd <project-root> &&` when the setup is project-specific. Retry only after the user completes that explicit trust step.
3. Obtain an explicit notes or memory directory from the request; ask for one when absent.
4. Call `mem_index` on that path with `force=false` and `auto_tag=false`. This is a one-shot index and must not silently register a watcher root.
5. Choose a representative phrase from the indexed material and call `mem_search` to verify retrieval.
6. Report the effective DB path, indexed path, and first-success result. Mention embeddings only as an optional relevance enhancement.

Do not install Ollama, enable automation hooks, or edit host instruction files unless the user separately requests those actions.
