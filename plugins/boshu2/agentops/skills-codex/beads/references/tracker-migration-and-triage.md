# Tracker Migration And Triage

Use this reference when a project mixes bd with another issue tracker or when an imported plan needs to become dependency-aware bd work.

## Migration Rules

1. Treat live `bd` state as the active AgentOps tracker unless the repo explicitly declares otherwise.
2. Preserve source tracker IDs in issue descriptions, not as replacement IDs.
3. Convert every blocker relation into a br dependency edge.
4. Convert "later" notes into explicit low-priority issues or drop them with rationale.
5. After migration, run `br ready --json` and verify the ready queue contains only actionable work.

## Triage Views

| Question | bd query | Use |
|---|---|---|
| What can start now? | `br ready --json` | Pick unblocked work. |
| What is stale? | `br list --status open --json` | Find old broad parents. |
| What blocks this? | `bd show <id> --json` | Read dependencies before planning. |
| What changed? | `bd vc status` | Closeout and git sync evidence. |

## Acceptance Check

Before closing a migration or triage task, prove:

- Every retained task has owner, priority, type, and acceptance criteria.
- Broad parents have execution-ready child issues.
- The ready queue has no item that requires extra discovery before work can begin.

---

**Source:** Adapted from an external skill corpus / `bd-to-br-migration`, `beads-br`, and `beads-bv`. Pattern-only, no verbatim text.
