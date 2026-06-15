# Plan To Beads Workflow

Use this reference when a prose plan, design note, or research artifact needs to become executable br work.

## Conversion Loop

1. Identify the smallest independently verifiable outcomes.
2. Create one br issue per outcome, not per file and not per vague phase.
3. Add dependency edges for true sequencing only.
4. Put validation commands and expected artifacts in each issue body.
5. Add parent-child links for epics and broad follow-up work.
6. Re-read `br ready --json` after creation and fix any issue that is not actionable.

## Issue Quality Bar

Each created issue must answer:

- What files or surfaces are probably in scope?
- What behavior changes when this closes?
- How will the implementer prove it?
- What can be skipped without invalidating the outcome?
- What existing parent, research, or plan discovered it?

## Polish Pass

Run a final pass over the issue graph before handing to `/crank`:

| Check | Failure |
|---|---|
| Ready issues have acceptance criteria | Worker will rediscover scope. |
| Dependencies are minimal | Parallelism collapses. |
| Broad parents have children | Parent wording becomes implementation scope. |
| Validation blocks name commands | Closeout becomes subjective. |

---

**Source:** Adapted from an external skill corpus / `beads-workflow`. Pattern-only, no verbatim text.
