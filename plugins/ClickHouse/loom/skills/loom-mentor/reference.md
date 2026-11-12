# loom-mentor — full reference

The complete situation → plane → op table, every hint code with its action,
and `mentor.brief`. `SKILL.md` carries the short form and the rule for
calling an op your tool list does not show (`loom_op`).

## Where the advice arrives

In Claude Code and Codex the plugin's `loom-mentor-hint` hook lifts a
result's `hint` into your context as `Loom mentor (<code>, after <tool>): …`,
once per code per session — you do not have to look for the key.


| Channel | Shape | When |
|---|---|---|
| `context.pack` section `mentor` | `Loom mentor — <code>: <sentence> · …` (≤ 3 hints) | session start, when a rule fires on your agent's ledger profile |
| a successful tool result | `hint` + `hint_code` keys on the result (HTTP: `X-Loom-Hint` / `X-Loom-Hint-Code` headers) | one per call at most, each code once per session, six per session |
| `mentor.brief {org, namespace}` | usage by op, the planes this namespace offers, every hint with its evidence, `adoption` | on demand — call it when a hint arrives and you want the counts, or to answer "am I using loom well here?" |

A hint is one sentence with a count behind it. Read it, act on it once, move
on — the same code will not be shown again this session. Do not narrate the
hint to the user unless it changes what you are about to do.

## Situation → plane → op

| You are about to… | Use | Not |
|---|---|---|
| find where a symbol is defined, who calls it, what a file contains, an exact literal | `code.symbol`, `code.callers`, `code.outline`, `code.grep`; a concept → `code.search`; "is it safe to change" → `code.impact`; a stack trace → `code.trace` | grep/glob the checkout (the `loom-code` skill) |
| find which commit or PR changed a behaviour between two versions | `code.bisect_candidates` (listed on the coding toolset): the PRs that first shipped in the failing release and touched the frames; then `code.blame_range`, `code.history` | reading `git log` end to end |
| answer "has this test failure / crash / report been seen before" | `tracker.similar` (a report, an item number or a stack trace), `tracker.duplicate_check` (a draft issue → `duplicate_of` / `related` / `none`), `tracker.flaky` (a test name), `tracker.test_signal` (a test's own history) — `duplicate_check` is listed, the rest run through `loom_op`; `tracker.source.list` says whether the org has a tracker source | a memory row about the failure, or filing the issue blind |
| keep a spec, runbook, report, review body, or anything over ~2 KB | `knowledge.upsert` (Markdown, `source_uri`) plus ONE one-paragraph `memory.set` row under the same key that says what it is and points at it; recall through `loom_search`, which fans out to documents | one `memory.set` holding the text |
| keep a table of facts with identity (PRs by number, alerts by id, services) | `memory_schema.register` once (via loom_op), then `memory.record.write` per row — a later write folds field by field; `memory.record.query` / `memory.aggregate` count and group them | one memory row per item under `<prefix>-<id>` keys |
| record a claim your agent established | `memory.set` — plain text, claim first, readable key `<scope>/<kind>/<id>`, facets in `tags`; a revision rewrites the SAME key (the `loom-memory` skill) | a JSON blob under a hash key |
| keep your plan, a lease, a checklist, "where was I" | `working_memory.set` / `append` / `get` — small blocks read by key, never ranked or embedded, loaded first by `context.pack` | `memory.set` + `memory.get` in a loop |
| park a 3,000-line log, a page, a diff | `context.offload` (summary + TTL; returns a one-line pointer; callable via `loom_op`) then `context.fetch` by slice or regex | pasting it into a memory row or the transcript |
| know before deciding what the store already holds | `context.pack` once at session start (working memory, profile, relevant memories, procedures); `memory.search` / `loom_search` before a decision; `memory.brief` to orient on one question | writing without reading |
| a `memory.get` says `found: false` | `memory.search` (by meaning), `memory.list prefix=` (the siblings); a moved key answers with `canonical_key` — pass `follow=true` | inventing the key again |
| a write came back with `duplicate_of` or `conflict` | read the named row (`memory.get`, `memory.related`), revise THAT key, or `memory.link supersedes` if yours replaces it; a `conflict` → tell the user both values (`loom-memory`) | writing a third copy |
| the namespace holds facts that disagree | `conflicts.list` (over HTTP/SDK; the dashboard's Review queue) → `conflicts.resolve`; search penalises conflicted rows until then | leaving them |
| follow what is connected to an entity | `facts.traverse` from a seed entity, `facts.path` between two names (via loom_op), `memory.related` for a row's neighbours | a chain of searches |
| do a piece of work whose outcome should grade the memories it used | `run.begin` before, its `run_id` on writes (`memory.set`, `observe.record`; reads carry the session's run), `run.complete(memories_used=[…], outcome=…)` after — callable via `loom_op` | nothing; the store cannot tell which memories helped |
| make a decision that a future session should be able to check | `decision.record` (scenario, options, choice), later `decision.outcome`; `decision.precedents` before a similar decision — callable via `loom_op` | a memory row that says "we decided X" |
| do again something that worked | `procedure.match` on the new situation; `procedure.add` when a way of doing it proved out; `procedure.record_run` after | rediscovering the steps |
| finish a task | `namespace.validate` for the namespace you wrote to (the Stop hook runs it for your keys); `code.test_gate` in an indexed repo (`loom-code`) | "done" |
| recall abstains on facts you know you wrote | `namespace.audit`, then the `loom-optimize` skill | writing them again |

## What each hint code means, and what to do

| code | it says | do |
|---|---|---|
| `recall_by_key_only` | your agent reads by exact key far more than it searches | recall with `memory.search` / `loom_search`; move the hot key to `working_memory` |
| `writes_never_read` | many writes, almost no reads across sessions | open sessions with `context.pack`; `memory.search` before deciding |
| `no_session_pack` | several sessions, none opened with `context.pack` | call `context.pack` first |
| `code_index_unused` | the org has indexed repos; your agent never called `code.*` | `code.repos` lists them; use the code plane for identifier questions |
| `tracker_unused` | writes tagged test/flaky/ci and no `tracker.*` calls, with a tracker source configured | `tracker.similar` / `tracker.duplicate_check` / `tracker.flaky` / `tracker.test_signal` |
| `bisect_available` | repeated blame/history calls, no bisect | `code.bisect_candidates` first, then blame |
| `documents_as_memories` | rows over ~2 KB or JSON past the embed clip stored as memories | `knowledge.upsert` + pointer row; `loom-optimize` moves the existing ones |
| `checkpoints_as_memory` | run dumps stored as memory rows | `context.offload`; one short episodic row per run |
| `duplicates_written` | a tenth or more of writes landed as duplicates | `memory.related` / `memory.get` before the write; revise the same key |
| `conflicts_pending` | conflicted facts nobody has looked at | `conflicts.list` → `conflicts.resolve` (or the owner's Review queue) |
| `records_for_identities` | many writes keyed by a number under one prefix | `memory_schema.register` + `memory.record.write` |
| `coordination_loop` | one key written or read dozens of times in a session | `working_memory.set` / `get` |
| `facts_graph_unused` | rows carry entities; the graph was never walked | `facts.traverse`, `memory.related`, `facts.path` |
| `runs_unused` | sessions without a run ledger | `run.begin` / `run.complete(memories_used)` |
| `search_abstains` | a large share of searches abstained | claim-first values; `loom_search` fan-out; `namespace.audit` |
| `reads_miss` | a fifth or more of the keys asked of `memory.get` this week were not there | a key from a search hit that misses is a chunk or a moved key: follow `canonical_key`, or recall by meaning with `memory.search` |
| `relied_on_chunk_ids` | `run.complete(memories_used)` credits chunk ids (`chunk:<session>:<n>`) | credit the fact: every chunk hit carries `parent_memory_key` |
| `relied_on_missing_keys` | keys credited in `run.complete(memories_used)` answer no live row | name the `memory_key` the search returned (or its `parent_memory_key`) and re-read it with `memory.get` first |
| `get_miss` (per call) | no row at that key | `memory.search`; `memory.list prefix=`; `follow=true` |
| `search_identifier_query` (per call) | you sent a symbol, scoped name, call or path to memory search and it came back thin | `code.symbol` / `code.callers` / `code.grep` / `code.search` — memory holds what was said about it, the index holds what it is |
| `set_stack_trace` (per call) | the value you wrote is a stack trace | `code.trace` resolves the frames; `tracker.similar` finds the reports that name it; keep the memory row as the one-line finding (or `context.offload` the dump) |
| `set_issue_reference` (per call) | the row names an issue or PR number | `tracker.item` for its tracker record; `memory_schema.register` + `memory.record.write` for a table of tickets; `code.pr_check` before opening a duplicate |
| `agent_unnamed` | your writes land under the anonymous agent name `-` or `*` | name the agent (SDK `agent=`, MCP `clientInfo.name`) so the mentor, cost and provenance can tell this caller apart |
| `search_abstain_code` / `search_abstain_knowledge` (per call) | memory abstained where the code index / documents would answer | `code.search` / `code.symbol`; `loom_search` |
| `set_duplicate` (per call) | this write duplicates a named row | revise that key; `memory.link supersedes` |
| `set_large_value` (per call) | the value is a document | `knowledge.upsert` + pointer row |
| `set_churn` (per call) | the same key set five times this session | `working_memory.set` |
| `run_over_budget` (per call) | `run.get` found the run past the `budget_usd` / `budget_seconds` its `run.begin` set | finish and `run.complete`, or ask the user before spending more |

## Asking for the evidence

```
mentor.brief {org, namespace}            # agent defaults to yours; window 7 d
```

Returns `usage` (calls per op), `planes` (each plane with `calls`,
`available` for this namespace, and a one-line `when`), `hints` (code,
severity, text, `ops`, `evidence` — the counts the rule fired on) and
`adoption` (per code: sessions where the hint reached this agent, and how
many then called a hinted op). `usage_evidence` counts your use of Loom rung
by rung, from a call made to a graded run, each marked `server` (Loom saw it)
or `client` (a caller reported it); the ledger rungs count only calls
recorded under your agent, not one that names no agent or reads across
agents (`*`), as MCP sends `memory.search` and `memory.list` unless you
name another agent. `healthy` is "no warning-level hint". Over
HTTP: `POST /v1/mentor.brief`; from the CLI: `loom mentor --org <org>
--namespace <ns> [--agent <a>]`.

## Rules

- A hint names a count; if you doubt it, `mentor.brief` shows the count. Do
  not argue with a hint in prose — either follow it or say in one line why
  not this time.
- An op your tool list does not show runs through `loom_op {op, arguments}`
  (`tracker.similar`, `context.offload`, `mentor.brief`); never call an
  unlisted `loom_*` name directly. An op hidden from MCP (`conflicts.*`)
  answers "not available" through `loom_op` too: use the dashboard's Review
  queue or HTTP/SDK for those.
- A code in no table here is newer than this skill. Follow the
  hint's own sentence and the ops it names; `mentor.brief` lists the codes
  that fire today with their evidence.
- The mentor never rewrites or refuses a call. What it names as a data
  problem (`documents_as_memories`, `checkpoints_as_memory`,
  `records_for_identities`) is reworked by `loom-optimize`, with the owner's
  approval and redirects; what it names as a habit is yours to change on the
  next call.
- `LOOM_MENTOR_TTL_SECONDS=0` on the server turns the mentor off; do not
  ask for that because the hints are inconvenient — ask because they are
  wrong, and say which count is wrong.
