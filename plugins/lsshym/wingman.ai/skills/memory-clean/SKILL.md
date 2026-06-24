---
name: memory-clean
description: "Use when the user explicitly asks to clean, compact, prune, trim, deduplicate, optimize, or reduce Wingman memory, or asks to resolve stale or conflicting memory rules."
---

# Wingman Memory Clean

## Core Rule

Clean Wingman memory only when the user explicitly asks. Optimize for future token cost, current-rule accuracy, and safe promotion of long-lived knowledge out of hot context:

- Keep default-read memory focused: `brief.md`, `context.md`.
- Keep current rules non-conflicting: `brief.md`, relevant `domains/`.
- Promote durable knowledge from `context.md` into `domains/`, `brief.md`, or `history/` before compacting old logs.
- Leave cold history event bodies alone unless the user explicitly asks about history cleanup.
- Delete logs only after a separate manual confirmation.

Do not clean memory just because it exists, is old, or history is large. This is not routine sync, full-memory rewriting, or automatic deletion.

## Repository Gate

1. Check whether `.wingman/memory/` exists.
2. Check whether `.wingman/memory/brief.md` and `.wingman/memory/context.md` both exist.
3. If missing, stop and report the repository memory state.
4. When helpful, inspect file size or line count only as diagnostics before reading large files. Size alone is not a cleanup trigger.
5. Read `brief.md` and `context.md` first.
6. Read domain or history files only when the requested cleanup scope points to them.

Never scan all memory files by default.

## Optional Resources

- Run `scripts/memory-stats.sh` when heading layout, file size, or candidate discovery is unclear. The script is read-only and does not replace semantic judgment.
- Read `examples/lossless-compaction.md` only when compacting current rules, ADRs, domain truths, or evidence-bearing logs.
- Read `examples/deletion-proposals.md` only when preparing a deletion proposal.

Do not read examples or run scripts by default. If the script cannot run in the current environment, fall back to file-size or line-count checks and read headings manually.

## Scope Selection

Use the smallest scope that matches the user's request:

| Scope | Read | Use When |
| --- | --- | --- |
| `context` | `context.md` | Recent logs are duplicated, stale, noisy, pointer candidates, or no longer hot. |
| `promotion` | `context.md`, `brief.md`, relevant domains/history projections | Context contains long-lived knowledge that should become current truth or history. |
| `brief` | `brief.md` | ADRs, registry, memory settings, or global rules are bloated, stale, or conflicting. |
| `domain` | One relevant domain file | A current rule changed, conflicts, or was duplicated. |
| `domain-split` | `brief.md`, one broad domain file | A domain file mixes unrelated subdomains and should become a folder domain. |
| `history-index` | Relevant history projection only | History indexes are bloated or copy event bodies. |
| `history-topic-index` | Relevant history projections and event metadata | History exists but feature lookup needs topic projections. |
| `delete-proposal` | Target files only | The user asks to delete logs or remove noise. |

If unclear, choose `context` unless the user mentioned rules, domains, ADRs, or history.

## Cleanup Candidate Check

Clean only when at least one concrete candidate exists:

- **Promotion candidate**: `context.md` contains durable rules, API contracts, field meanings, state flow, permissions, money rules, routing rules, product or business invariants, or recurring debugging conclusions that should become current truth or history.
- **Pointer candidate**: content in `context.md` is already represented by `brief.md`, `domains/`, or `history/events/` and can be compacted to a precise pointer.
- **Duplicate or correction candidate**: logs repeat the same task, or an older log was corrected by a later log.
- **Default-read noise candidate**: completed, low-reuse process logs obscure current work, pending work, or high-signal context.
- **Current-rule conflict**: two rules are marked current, or a replaced rule is not marked `superseded` or `deprecated`.
- **History-topic candidate**: history events exist but feature-time lookup needs `history/topics/<topic>.md`.
- The user explicitly identifies content to clean.

Do not clean solely because `context.md`, `brief.md`, or any other memory file exceeds a fixed line count. File size and line count are diagnostics only. If a file is long but has no safe promotion, compaction, pointer, deletion, conflict, or topic-index candidate, write nothing and explain that no worthwhile cleanup candidate was found.

## Retention Review

Before classifying a candidate, judge what would be lost if it were compacted or removed:

| Signal | Ask | Cleanup Implication |
| --- | --- | --- |
| Authority | Is it current truth, an accepted ADR, hot context, or history? | Current truth and accepted ADRs require exact preservation or explicit supersession. |
| Currentness | Is it still valid, partially replaced, or fully replaced? | Replaced current rules become `SUPERSEDE`, not deletion. |
| Evidence value | Is it the only source explaining a rule, decision, bug, or invariant? | If yes, keep the evidence or preserve a precise pointer before compacting. |
| Future relevance | Is a future task likely to need this fact, constraint, failure mode, or file pointer? | High relevance favors `KEEP` or lossless `COMPACT`. |
| Token cost | Does the text spend many default-read tokens on repeated wording or process detail? | High cost supports compaction only after core meaning is protected. |
| Sensitivity risk | Does it contain secrets, credentials, private data, or unsafe content? | Treat as `DELETE_CANDIDATE` or redaction candidate, still gated by confirmation when deleting. |

If the review is ambiguous, prefer `NO_ACTION` or a deletion proposal over irreversible cleanup.

## Classification

Classify before changing anything:

| Label | Meaning | Action |
| --- | --- | --- |
| `KEEP_HOT` | Still needed as active task, pending work, unresolved issue, or recent high-signal context. | Preserve in context. |
| `PROMOTE_DOMAIN` | Long-lived current truth belongs in a domain file or project ADR. | Write current truth with evidence, then compact context to a pointer when safe. |
| `PROMOTE_HISTORY` | Event has trace value but is not current truth. | Write history event and projections, then compact context to a pointer when safe. |
| `PROMOTE_BOTH` | Current truth and historical source event are both needed. | Write current truth first, write history event/projections, then compact context to a pointer. |
| `COMPACT_TO_POINTER` | Useful details are already preserved in current truth or history. | Replace verbose context with a precise pointer. |
| `SUPERSEDE` | Old current rule replaced by a newer rule. | Mark `superseded` or `deprecated`; do not delete. |
| `DELETE_CANDIDATE` | Duplicate, corrected, noisy, sensitive, or safely represented elsewhere. | Propose deletion; wait for confirmation. |
| `NO_ACTION` | Cleanup cost or ambiguity exceeds benefit. | Leave unchanged. |

For A -> B requirement changes: make B the only `current` rule, mark A as `superseded` or `deprecated`, do not delete old history just because the decision changed, and do not summarize A and B into a vague combined rule.

## Deletion Hard Gate

Never delete without explicit user confirmation after showing a proposal. Never delete:

- pending tasks;
- current work;
- unresolved bugs;
- accepted ADRs;
- current domain truths;
- user-protected notes;
- the only evidence explaining a current rule;
- history event bodies, unless the user explicitly asked to delete those specific history records.

Logs may be deletion candidates only when they are:

- duplicate logs with no unique useful content;
- typo-only, formatting-only, rename-only, or trivial local-change logs;
- failed attempts with no reusable lesson;
- same-task logs corrected by a later entry;
- obsolete context already preserved in `brief.md`, `domains/`, or `history/`;
- sensitive or unsafe content that should not remain in memory.

## Manual Deletion Confirmation

Before deletion, present exact proposal IDs with path, reason, preserved location, and risk. Read `examples/deletion-proposals.md` when preparing the proposal.

Valid confirmation must name exact current proposal IDs. Vague delegation, silence, or approval of compaction is not deletion approval. If the proposal changes, ask again.

## Compaction Rules

- `context.md`: preserve pending tasks, current work, recent high-signal logs, and useful facts. Prefer short pointers to domain truth or history events. Do not turn uncertain logs into durable rules.
- `brief.md`: preserve Memory Settings, current ADR meaning, and Domain Registry routing. Remove repeated explanations only when behavior remains clear.
- Domain files: keep current truths explicit, mark replaced rules `superseded` or `deprecated`, and do not merge semantically different rules.
- History indexes: keep projections as links. Remove copied event bodies only if the body remains linked. Do not rewrite event bodies unless explicitly requested.
- Promotion cleanup: when evidence is clear, write durable rules to `domains/` or ADRs to `brief.md`; write historical events under `history/events/YYYY/MM/` and update `history/domains/`, `history/topics/`, `history/months/`, and `history/index.md`; then compact context to a pointer.
- Topic indexes: when history exists but feature lookup is weak, create or update `history/topics/<topic>.md` using stable, generic topic names.

Compaction must be lossless for decision-critical meaning. A compacted entry must still preserve, when present:

- the exact current rule, canonical field, contract, invariant, or status transition;
- why the rule exists or the evidence pointer that explains it;
- where it applies and any important exceptions;
- current status: `current | superseded | deprecated`;
- replacement or supersession links;
- pending action, owner, blocker, or next step;
- source file, domain, history event, or date pointer needed to recover detail.

Do not replace a specific rule with a vague summary. Read `examples/lossless-compaction.md` when the safe compacted shape is unclear.

## Workflow

1. Apply Repository Gate.
2. Select the smallest cleanup scope and read only files needed for it.
3. Run Cleanup Candidate Check.
4. Run Retention Review for each candidate.
5. Classify candidates.
6. Apply safe, evidence-backed `PROMOTE_DOMAIN`, `PROMOTE_HISTORY`, `PROMOTE_BOTH`, `COMPACT_TO_POINTER`, and `SUPERSEDE` changes when meaning is preserved.
7. For `DELETE_CANDIDATE`, present a deletion proposal and wait.
8. Delete only explicitly confirmed IDs.
9. Report files read, files changed, promotions, pointer compactions, superseded rules, topic indexes, proposed deletions, and confirmed deletions.
10. If nothing changed, report the blocking reason or that no worthwhile cleanup candidate was found.

## Completion Rule

Do not say memory was cleaned if no file changed.

If only a deletion proposal was produced, say cleanup is pending confirmation.
