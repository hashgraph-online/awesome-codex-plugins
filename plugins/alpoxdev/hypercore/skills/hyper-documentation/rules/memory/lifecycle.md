# Memory Lifecycle

**Purpose**: Define how entries are read, updated, merged, compressed, expired, and deleted. **Read when**: the budget soft trigger fires, an entry is corrected or found stale, or an audit or `consolidate` run starts.

## 1. Read side

- Session start: read the index, then open only the topic files whose line matches the task, up to the lookup bound in `rules/memory/structure.md` §2 [A33, D:M9].
- Before acting on an entry that names a path, command, version, or state, verify it against the repository. If it differs, the entry is stale: the repository wins, and the entry is corrected in place [A29, A54, B68, F25].
- Memory is guidance, never proof of current behavior. Do not claim a fact is verified because memory says so [D:M9, B68].

## 2. Update

- Make delta edits: add, correct, or remove one entry. Do not regenerate the whole file; whole-file LLM rewrites caused measured context collapse and brevity bias [E40, E41].
- Prefer correcting a stale line to deleting it when the lesson still holds; update `verified` [E60].
- A fact that replaces an older one sets `supersedes` and moves the old entry to the archive instead of leaving both active [D:N1, F21].
- Keep one home per fact. If a new entry overlaps an old one, merge into the old one [A60].

## 3. Consolidate

Run `consolidate` when the soft trigger fires, at a scheduled review, or before the file is handed to another agent. It is one named step with four actions [B74]; the near-limit reminder to merge or drop is B38, and the consolidation pass is B67:

1. **Merge** duplicates and near-duplicates into one entry.
2. **Resolve** contradictions: keep the entry with the newer `verified` date and the higher trust, supersede the other, and record the reason. Contradicting instructions are resolved arbitrarily by the model, so none may remain [A20].
3. **Delete or expire** entries that fail the admission test or reach their expiry.
4. **Re-fit** the index under the soft trigger.

Take a snapshot before bulk edits so poisoning or a bad merge has a known-good state to return to [F15]. If nothing reusable is left to merge, write nothing: a no-op beats a filler entry [D:C9].

## 4. Expiry and forgetting

Forgetting is a required operation with a stated bound, not an aspiration. The values below are defaults to adapt; the first two are anchored in shipped systems, the rest are this package's choices.

| Entry | Default | Basis |
|---|---|---|
| Volatile fact (path, version, price, org state) | Re-verify after 30 days (this package's default); delete if it cannot be re-verified | D:C5 (30-day unused clock), A53 |
| Unverified or quarantined entry | Expires fastest; drop at the next consolidation | F2, F20 |
| Stable preference or rule | Keep; re-check when contradicted | A53 |
| Any entry unused across 90 days | Move to the archive | A53 (reinforcement-based expiry); the idle clock itself is this package's choice |
| Archive | Delete after a stated retention | D:C12 |

Reinforcement resets the clock; mere retrieval does not [A53]. Do not claim a decay rule improves quality without an ablation; the published forgetting rules have none [E34, E35].

## 5. Deletion

- Offer three granularities: one entry, one topic file, the whole store. The whole-store reset states that it is irreversible [F35].
- Deletion removes every copy: the index line, the topic file, any summary, and every derived entry made from the same source [F36, F43].
- State the propagation window of any copy that outlives the delete (backups, logs, review queues) in the handoff; never promise instant erasure [F37, F40].
- "Do not mention this again" suppresses surface use only. Keep it distinct from deletion in the file and in the handoff [F36].
- Keep an append-only change log of writes and deletes: timestamp, actor, source, class, decision, and a hash of the content [F47]. Log which entries were read for an answer when the runtime allows it [F37].

## 6. After compaction

Re-read the index and the instruction file after a compaction; do not trust the summary to have kept every rule. Compaction loses rules that exist only in context, and summaries below a few hundred tokens lose more [E43, E44, E45].

## Sources

> Checked 2026-11-09. Ids resolve in `references/memory/evidence-ledger.md`. The 90-day idle move and the archive retention are this package's choices, marked above.

| Claim | Source |
|---|---|
| Verify before acting; the repository wins | A29, A54, B68, F25 |
| Delta edits over whole-file rewrites | E40, E41 |
| Consolidation as merge, resolve, delete, re-fit | B38, B67, B74, D:C9 |
| Contradictions are resolved arbitrarily | A20 |
| Expiry and reinforcement | A53, D:C5, D:C12, F20 |
| No ablation behind published forgetting rules | E34, E35 |
| Three-granularity deletion and propagation | F35, F36, F37, F40, F43 |
| Append-only change log and snapshots | F15, F47 |
| Compaction loses in-context rules | E43, E44, E45 |
