# Branch awareness

Inspect the current Git branch and revision before promoting implementation-derived knowledge when Git is available.

Use these implementation states: `observed`, `proposed`, `implemented`, `merged`, `released`, and `reverted`.

## Promotion rules

- Record unmerged branch findings as Promotion Inbox candidates with `applies_to_branch` and `applies_to_revision`.
- Do not update canonical Current State to imply that branch-only work is merged or released.
- Permit durable branch-scoped knowledge only when the user explicitly wants it retained and the branch scope is clear.
- After merge, verify the target branch contains the change before proposing `merged`.
- Use `released` only with release evidence; merge alone is insufficient.
- If work is reverted, preserve the historical decision when useful and mark implementation state `reverted`; do not erase the history.

If Git information is unavailable, label implementation state `unverified` and ask only when the distinction materially affects the note.
