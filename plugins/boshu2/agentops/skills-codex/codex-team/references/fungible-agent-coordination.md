# Fungible Agent Coordination

Use this reference when a lead session needs many interchangeable agents to make progress without tight hand-holding.

## Coordination Contract

Every worker prompt should carry:

- The objective and explicit non-goals.
- Owned files or directories.
- Current branch/worktree expectations.
- How to report completion and validation evidence.
- Where to leave questions when blocked.

Workers are fungible only when the packet is complete enough that any capable agent can execute it.

## File Reservations

Before dispatch:

1. Build an ownership table of write paths.
2. Serialize tasks that share writes.
3. Allow read overlap but tell readers which writers may change files.
4. Record abandoned reservations at closeout so the next lead does not inherit stale locks.

## Repeated Passes

For repeated skill application, define the pass count and stop condition upfront:

- Pass 1: broad scan.
- Pass 2: apply confirmed fixes.
- Pass 3: fresh rescan.
- Pass 4: validation and summary.

Stop early when a pass produces no actionable findings and validation is green.

## Session Mail

Use an inbox or coordination file only for state that outlives a single tool call: blockers, handoffs, file ownership, and validation summaries. Do not use it for chatty status updates.

---

**Source:** Adapted from an external skill corpus / `agent-fungibility-philosophy`, `agent-mail`, `ntm`, `vibing-with-ntm`, and `repeatedly-apply-skill`. Pattern-only, no verbatim text.
