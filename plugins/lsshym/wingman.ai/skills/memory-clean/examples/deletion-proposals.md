# Deletion Proposal Examples

Use these examples only when `SKILL.md` says a `DELETE_CANDIDATE` proposal is needed.

## Low Risk

```text
Deletion proposal:
1. .wingman/memory/context.md :: 2026-05-18 typo-only log
   Reason: typo-only correction with no unique decision, file pointer, or reusable lesson.
   Preserved elsewhere: None needed.
   Risk: low
```

## Medium Risk

```text
Deletion proposal:
1. .wingman/memory/context.md :: 2026-05-18 duplicate upload status investigation
   Reason: duplicated by the later 2026-05-19 log, which keeps the canonical field, affected files, and follow-up.
   Preserved elsewhere: .wingman/memory/context.md :: 2026-05-19 upload status fix
   Risk: medium
```

## Redaction Candidate

```text
Deletion proposal:
1. .wingman/memory/context.md :: 2026-05-20 local debugging note
   Reason: contains a credential-like token that should not remain in memory.
   Preserved elsewhere: sanitized debugging conclusion can remain in context.md without the token.
   Risk: medium
```

## Invalid Deletion Candidate

Do not propose deletion for:

```text
.wingman/memory/domains/upload.md :: scan_status canonical field rule
```

Reason: it is current domain truth. If replaced, mark it `superseded` and point to the replacement instead of deleting it.

## Confirmation Boundary

Valid confirmation names exact proposal IDs, such as `确认删除 1` or `delete 1 and 2`.

Invalid confirmation leaves the decision to the agent, such as `你决定`, `随便`, `看着办`, silence, or approval of compaction without deletion approval.
