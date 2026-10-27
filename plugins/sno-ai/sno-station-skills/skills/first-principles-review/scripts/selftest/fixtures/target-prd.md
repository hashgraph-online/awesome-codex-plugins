# Notification batching proposal

## Proposed solution

Add a new queue, worker fleet, and dashboard so every customer notification can be delivered
within ten seconds.

## Claimed constraints

- Every notification must arrive within ten seconds.
- The existing notification provider cannot batch messages.
- A dedicated worker fleet is required.
