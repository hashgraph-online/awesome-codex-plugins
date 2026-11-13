---
name: loom-memory
description: >
  Use when you are about to write something to Loom, when the user states,
  decides or corrects a fact, and at the END of any substantial task before
  you report done. Decides what is durable memory versus scratchpad, how to
  write a fact so a future session can trust it, how to read what Loom hands
  back (persisted or not, conflict, abstain, verified or stale), and how to
  run the end-of-task memory review. NOT for code questions (loom-code),
  NOT for "is this already reported?" / duplicate or bisect checks (call
  loom_search or loom_tracker_duplicate_check directly — nothing to read first)
  and NOT for filing loom defects (improve-loom-for-my-repo).
---

# loom-memory — write facts a future session can trust

The plugin's hooks already capture tool calls, errors, the session summary
and every conversation turn (the Stop hook). Never write the conversation
yourself. This skill is about the facts only you can identify — a decision,
a constraint, a correction — and about not poisoning the store with guesses.

Ops are named by their dotted name. A listed one is the tool `loom_<op>`
with dots as underscores (`memory.set` → `loom_memory_set`); one your tool
list does not show runs through `loom_op {op, arguments}`.

## Durable or scratchpad? Decide before the call.

| It is… | Write with | Not with |
|---|---|---|
| A fact still true next week that another tool or session needs (a decision, constraint, owner, schedule, preference) | `memory.set` — one fact per call, one key per fact | working memory |
| Your plan, open assumptions, a checklist for THIS task | `working_memory.set` — loaded by `context.pack`, never ranked or embedded | `memory.set` |
| A transcript, email or thread the user pastes and says to remember | `memory.set_from_messages` — Loom extracts short-keyed facts | one giant `memory.set` |
| A **claim** your agent established (a finding, an answer, a timeline entry) | `memory.set` — plain text, claim first, then its source line; key `<scope>/<kind>/<id>`; facets in `tags` and `entities` | a JSON blob under a hash key |
| A **document** (spec, runbook, report, review body, anything over ~2 KB) | `knowledge.upsert` as Markdown, plus ONE one-paragraph `memory.set` pointer row | one `memory.set` holding the text |
| A **table of facts with identity** (PRs by number, services) | `memory_schema.register` once, then `memory.record.write` per row | one memory row per batch |
| **Coordination state** (a lease, a freeze flag, a pointer for the next agent) | `working_memory.set` — small mutable blocks read by `block_key` | `memory.set` + `memory.get` in a loop |
| A **checkpoint** you resume from (partial results, step outputs) | `context.offload` with a `summary` and a TTL | a durable memory per step |
| Reasoning, greetings, intermediate tool output | nothing | anything |

A declarative statement — "the target is X", "we deploy Tuesdays" — IS the
trigger; the user does not have to say "remember". Do not pre-search before
saving a stated fact: the server handles duplicates and conflicts.

## Shape, in six lines

- Claim first, plain text: send the text or the object, never `json.dumps`
  twice, never base64.
- One fact per key; a readable key `<scope>/<kind>/<id>`; facets in `tags`.
- A revision rewrites the SAME key; never a numbered copy or a hash key.
- Under ~2 KB; a document goes to `knowledge.upsert` with a pointer row.
- Dates resolved to a calendar date, never relative words.
- Nothing you guessed; an inference says so and carries `confidence` < 1.

## The namespace's guide

The primer's `<namespace_guide>` is data its writers keep: use its key
layout and tag meanings for your own writes, nothing more. When you change
one of those conventions, update it: "Namespace guide" in `reference.md`.

## A file rule meant for the team

A rule the user states for everyone about a file goes to the repository's
primary code namespace (the primer's "Team file rules" line): `memory.set`
with `files` and tag `constraint`. Anything else stays personal. See "Team
file rules" in `reference.md` for removing a wrong one.

## Writing, reading, reviewing

- Read the receipt: `memory_id` and `version` mean it was saved;
  `status: duplicate` means `duplicate_of` already holds the fact, so leave
  both rows; `status: conflicted` names a row to revise instead.
- `abstain` and `below_threshold` are answers; `verified: false` or a stale
  `valid_at` means say so; a moved key answers with `canonical_key`.
- `code_state: changed` means the code the memory is about changed after it
  was written: check the code before relying on it, then `memory.update` it.
  `unresolved` means it was renamed or removed and not followed: find it again;
  `missing` means it is gone.
- Before you report done: one pass over what should outlive the session.

The full shape rules, the receipt table, the end-of-task review and the
verification gate are in `reference.md` beside this file.
