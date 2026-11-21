---
name: loom-mentor
description: >
  Use when a loom hint (a tool result's `hint`, an `X-Loom-Hint` header or
  a "Loom mentor" line) names a plane or op you do not know how to use, or
  when the user asks "what can loom do", "how should I be using loom", "am I
  using loom well", "loom mentor". A hint that already names the op to call
  needs no skill: call it or carry on with the task. Maps a situation to the
  loom plane and op that fits — code index, tracker record, documents,
  records, working memory, offload, the entity graph, runs, decisions,
  procedures, duplicates, conflicts, bisect — and says what to do about each
  hint code. NOT for deciding the shape of one write (loom-memory), NOT for
  grep-vs-code.* in an indexed repo (loom-code), NOT for reworking a
  namespace that already holds the wrong shape (loom-optimize).
disable-model-invocation: true
---

# loom-mentor — the store's advice, and where each plane lives

Loom has a few hundred operations; your tool list shows the ones a coding
session uses most. The mentor reads what your agent called this week and
names the plane it is not using: a `hint` on a tool result, a `Loom mentor`
line in the session primer. Read a hint once, act on it once; the same code
is not shown again this session.

This skill routes. The destination skill owns the detail: the shape of a
write is `loom-memory`, code questions are `loom-code`, reworking stored
rows is `loom-optimize`.

## Calling an op your tool list does not show

A listed op is the tool `loom_<op with dots as underscores>`
(`tracker.similar` → `loom_tracker_similar`). An op that is not in your
tool list runs through `loom_op {op: "tracker.similar", arguments: {…}}`;
`loom_op {op: "help", query: "<words>"}` lists matching ops and their
arguments. Your host can only call tools it was shown, so never call an
unlisted `loom_*` name directly. The tracker tools are listed when the MCP
entry mounts `/mcp?toolset=coding+tracker` (the plugin's `toolset` option),
or a second entry mounts `/mcp?toolset=tracker`.

## The planes a hint points at

| Situation | Op |
|---|---|
| "has this crash / test failure / report been seen before" | `loom_tracker_duplicate_check` (listed: draft title + body → `duplicate_of` / `related` / `none`); `loom_tracker_similar`, `tracker.flaky`, `tracker.test_signal` (listed on `coding+tracker`, else through `loom_op`) |
| which PR broke a behaviour between two versions | `loom_code_bisect_candidates` (symbols or paths, `good_version`, `bad_version`) |
| about to open a PR | `loom_code_pr_check` (title, body, paths, symbols, issues) |
| is it safe to change X | `loom_code_impact` |
| a document, runbook or report over ~2 KB | `knowledge.upsert` + one pointer row (`loom-memory`) |
| a table of facts with identity (PRs, alerts, services) | `memory_schema.register` once, then `memory.record.write` |
| your plan, a lease, "where was I" | `loom_working_memory_set` |
| a 3,000-line log or diff to park | `context.offload`, then `context.fetch` |

Tracker ops take the tracker namespace, or the repository's code namespace
when it is bound to one (`tracker.binding` says which).

## The hints you will see most

| code | do |
|---|---|
| `tracker_unused` | run the tracker check above before filing or grepping |
| `code_index_unused` | `loom_code_symbol` / `loom_code_search` for identifier questions |
| `bisect_available` | `loom_code_bisect_candidates` first, blame second |
| `get_miss` | `loom_search` by meaning; `memory.list prefix=`; `follow: true` |
| `set_duplicate` / `duplicates_written` | revise the named row, never a third copy |
| `documents_as_memories` / `set_large_value` | a knowledge document plus a pointer row |

Every other code, the full situation table and `mentor.brief` (the counts
behind a hint) are in `reference.md` beside this file. A code that is in
neither table is newer than this skill: follow the hint's own sentence and
the ops it names, or ask `mentor.brief` for its evidence.
