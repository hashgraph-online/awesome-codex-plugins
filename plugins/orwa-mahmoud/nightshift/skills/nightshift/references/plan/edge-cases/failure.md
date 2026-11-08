# Failure — an item that can stop partway through a change

## When it applies

The item changes more than one thing, and one of those changes can fail.

## Cases

- **Partial failure** — some of a batch succeeds and some does not; what is kept and what is said.
- **Rollback** — undoing the change leaves the system as it was before, and how to run it.
- **The error the user sees** — the message names the cause and the next step, not a stack trace.

## Example lines

- WHEN half the batch fails THEN the item names the rows it kept and the rows it did not
