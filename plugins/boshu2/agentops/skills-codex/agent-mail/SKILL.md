---
name: agent-mail
description: Use Agent Mail as an optional messaging and
---
# Agent Mail — optional coordination adapter

Agent Mail carries messages, acknowledgements, identities, and temporary file
reservations. It is not a task tracker, queue, proof ledger, or lifecycle
controller.

Reservations are **advisory**: they prevent collisions only because every
cooperating writer checks them against the same absolute project path, and one
writer registered against a different path resolution makes the whole ledger
advisory fiction. Agent Mail enforces nothing on a writer that does not check.

Named failure mode — **silence-as-status**: reading an unanswered thread as
"work stalled" or "work done"; mail silence proves only that no mail arrived.

Anti-pattern: widening or renewing a reservation unprompted when a conflict
appears. Corrective: report the conflict to the caller as-is; scope and TTL
changes are the caller's call.

## Boundary

- Skip Agent Mail for a single writer.
- The caller supplies the absolute project path, agent identities, thread id,
  participants, paths, exclusivity, reason, and TTL.
- Reservations prevent accidental overlap among cooperating writers. They do not
  create work ownership or affect Plan, Candidate, or verdict semantics.
- Mail silence proves nothing about work status.
- A message or acknowledgement is evidence that communication occurred, not
  evidence that a change is correct or complete. The adapter cannot select AgentOps semantics, issue a binding verdict, or turn factory completion into delivery or validation proof.
- Release a reservation, including any `force_release`, only on the caller's
  explicit request for that exact reservation. Force-release has no autonomous
  trigger; a conflict is reported, not force-cleared.
- Agent Mail never selects work, changes tracker state, commits code, validates,
  integrates, closes, releases, or delivers work.

## Modes and authority

Two disjoint surfaces; do not reach the second from the first:

- **Coordination mode (default).** Register identity, reserve/release the
  caller's paths, send/read/acknowledge the caller's threads. This is the whole
  of routine use, and all of it writes durable Agent Mail records.
- **Admin / disaster-recovery mode (explicitly caller-authorized only).**
  Installing the git pre-commit guard, `doctor repair`, backup/restore, and the
  irreversible `clear-and-reset-everything` are a separate mode. Each requires
  the caller's explicit authorization for that specific operation; none is ever
  performed as a side effect of coordination. `clear-and-reset-everything`
  deletes the database and all storage and cannot be undone — never run it, even
  with `--force`, without an explicit destructive-reset authorization from the
  caller.

## Surfaces

Use the MCP tools when they are present. Otherwise use the self-describing `am`
CLI. Discover current syntax with `am mail --help`,
`am file_reservations --help`, and related group help; do not infer commands
from remembered aliases.

## One-shot use

1. Confirm that multiple explicitly coordinated writers share the repository.
2. Register the caller-supplied identity against the same absolute project path.
3. Reserve only the supplied paths, with a bounded TTL.
4. Report conflicts without waiting, narrowing scope, or changing the plan.
5. Send the supplied message once and record its id.
6. Read or acknowledge only the requested thread.
7. Release only reservations the caller explicitly asks to release.

## Output

Return the project, identity, thread/message ids, reservation ids and paths
(with their TTLs), conflicts, and timestamps. The caller owns all subsequent
decisions.

Terminal outcomes are explicit, never silent:

- **Adapter unavailable** — neither the MCP tools nor the `am` CLI is present:
  report that Agent Mail is unavailable and stop. Do not fall back to
  hand-written coordination or treat the absence as "no conflicts".
- **Reservation conflict** — report the conflicting reservation as-is; do not
  narrow, widen, renew, or force-release it.
- **Timeout / degraded surface** — report the operation as timed out or degraded
  with what was and was not observed; a timeout is evidence, not "done".
- **Cleanup** — reservations released this session are listed by id; any left
  in place (still holding a TTL) are named so the caller can see what remains.

## References

- [CLI and MCP surface notes](references/TOOLS.md)
- [Coordination patterns](references/WORKFLOWS.md)
- [Troubleshooting](references/RECOVERY.md)
