---
name: memtomem-recall
description: Recall memtomem memories created in a date range. Use for recent memories or requests scoped by day, week, month, source, or namespace.
---

# Recall memories

Derive the date range or recent-memory request from the current user request.
If the request does not clearly specify the date range or recent-memory request, ask before calling a tool — and
in a non-interactive context (a subagent or scripted run with nobody to ask), do not
stall and do not guess: stop and report `insufficient_input` naming the missing date range or recent-memory request.
A request that does specify the date range or recent-memory request proceeds normally in either context.
Translate relative dates such as “last week” into `since` and `until` values when possible, then call `mem_recall`. Preserve any source, namespace, scope, or result-limit constraint from the request.

Present memories newest first with their creation date and source. Ask for a date range only when the request provides no usable temporal constraint. Use topic search, not recall, when the user is asking what a memory says rather than when it was created.
