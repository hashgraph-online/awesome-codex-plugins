# relaymail code map (fixture — what is actually on disk)

> **This file stands in for reading the code.** In a real run you produce this
> map yourself by reading the implementation; here it is pre-baked so the
> worked example is reproducible.

| Surface | File | What the code actually does |
|---|---|---|
| `send` command | `src/send.rs` | Real. Registers inbox, writes message, fsyncs outbox, retries on conflict. 14 passing tests including a crash-recovery test. |
| `sync` command | `src/sync.rs` | `todo!("cross-host replication")` behind a CLI flag that parses but exits 0 without doing anything. Zero tests. |
| `dlq` subcommands | — | No file exists. `dlq` is not registered in the CLI dispatch table. |
| Outbox store | `src/store.rs` | Real, used only by `send`. |

Closed beads cluster on `send` internals (13 of 13 touch `src/send.rs` or
`src/store.rs`). No open bead mentions `sync` replication or any `dlq` surface.
