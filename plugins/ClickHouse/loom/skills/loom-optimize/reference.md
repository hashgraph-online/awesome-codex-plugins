# loom-optimize — remedy tables

The finding → remedy → ops mapping behind Step 2 of `SKILL.md`. The recipe
it follows is `docs/guides/investigation-agent-memory.md`.

## Audit findings

| finding | remedy | ops |
|---|---|---|
| `double_encoded_values`, `json_prefix_excerpts`, `hash_keys` | move to a readable key `<scope>/<kind>/<id>` with a claim-first `value`: decode once, the claim sentence first, then the source line, then the rest as short lines | `memory.get` → `memory.move {from_key, to_key, value, tags, entities, valid_at, if_match_sha256}` |
| `oversized_values`, `episodic_blobs` | the body becomes a Markdown document; a one-paragraph row under the readable key points at it; the old key moves onto that row with the paragraph as `value` | `knowledge.upsert {source_uri: loom://<org>/<namespace>/<key>}` then `memory.move {…, value: <paragraph>}` |
| `coordination_as_memory` | the block goes to working memory; the old key moves with `keep_redirect: true` so the writer's next `memory.get` still answers | `working_memory.set {block_key}` then `memory.move` |
| `hand_rolled_index_rows` | leave the rows readable, add `tags: [kind:index, deprecated]`, and tell the writer to stop writing them — the key is the index | `memory.update_by_id` (tags only) |
| `exact_key_store` | a writer change: exact-key reads of one key belong in working memory; recall goes through `memory.search`. No data change | none — list the keys |
| `version_churn` | a writer change: the same key rewritten again and again, with new or restated content (a copy that keeps the value and its count, such as a conflict marking, a tags edit by id or a lock, is not counted); no data change | none — list the keys |
| `unembedded_rows` | covered by `oversized_values` / `episodic_blobs` when the same rows appear there; otherwise list them for the owner | none |
| `telemetry_unavailable`, `index_backlog`, `intentional_exact_key_reads` | nothing for the writer: the deployment's state (kind `system_state`) or a workflow. While `telemetry_unavailable` warns, `exact_key_store` and `intentional_exact_key_reads` are in `skipped`, not clean, and `coordination_as_memory` checks key names only: rerun once the ledger covers the window; a stalled `index_backlog` goes to the deployment's owner | none — no section in the plan |

## Mentor hints that are data changes

The mentor (the `loom-mentor` skill) names three more cases
that are data changes; they are reworked here under the same invariants,
with `mentor.brief`'s `evidence` as the count in the plan section:

| mentor hint | remedy | ops |
|---|---|---|
| `documents_as_memories` | the same move as `oversized_values`: the body becomes a Markdown document, a one-paragraph pointer row under the readable key, the old key moves onto it | `knowledge.upsert` then `memory.move {…, value: <paragraph>}` |
| `checkpoints_as_memory` | a run dump becomes a `context.offload` blob (summary + TTL); the memory row is replaced by one short episodic row keyed by run id, moved from the old key | `context.offload` then `memory.move {…, value: <one-line ledger>, memory_type: episodic}` |
| `records_for_identities` | rows keyed `<prefix>-<id>` with scalar fields become one registered schema and one record per row; each old key moves onto a one-line pointer row naming the record | `memory_schema.register` once, `memory.record.write` per row, then `memory.move` |

Habit hints (`recall_by_key_only`, `writes_never_read`, `code_index_unused`,
`tracker_unused`, `duplicates_written`, `coordination_loop`, …) are
writer changes: no data moves; list them for the owner as the checklist.
