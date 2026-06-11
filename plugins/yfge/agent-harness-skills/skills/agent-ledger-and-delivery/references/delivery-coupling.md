# Delivery Coupling

Use this when ledger records must be tied to code review, tasks, commits, or handoff.

## Coupling Levels

- Advisory: records are expected but not mechanically checked.
- Commit-coupled: relevant changes must include a ledger record in the same commit.
- Review-coupled: review notes must link the ledger record.
- Task-linked: ledger records reference the task or work-state entry they summarize without owning its current status.
- Gate-coupled: a hook or CI check blocks missing records for configured paths.

## Skip Policy

- Skips must be explicit and searchable.
- A skip record should state reason, affected paths, validation that still ran, and follow-up owner if any.
- Emergency skips should create a repayment task or follow-up record.

## Validation

- Check whether changed paths trigger a required record.
- Confirm the ledger record names the prompt, goal, task reference, changes, validation, risks, and linked delivery artifacts.
- Confirm review notes and commit bodies do not claim validation that is absent from the record.
- Confirm task status is updated in the work-state surface, not only in the ledger.

## Do Not Include

- Silent bypasses.
- Raw private conversation transcripts.
- Two active ledger formats without a deprecation note.
