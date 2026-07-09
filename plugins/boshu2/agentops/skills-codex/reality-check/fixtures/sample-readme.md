# relaymail (fixture — fake project)

> Tiny message relay for agent fleets. **This README is the measuring stick**
> in the reality-check worked example: it claims three features.

## Features

1. **Send** — `relaymail send <to> <body>` delivers a message to any registered
   agent inbox, with at-least-once delivery and a durable outbox.
2. **Inbox sync** — `relaymail sync` replicates inboxes across hosts over the
   tailnet, so a message sent on one machine is readable on every machine.
3. **Dead-letter triage** — undeliverable messages land in a dead-letter queue
   with `relaymail dlq list|retry|drop` for operator triage.

## Status

Tracker says 13 of 18 beads closed (72%). Ship it?
