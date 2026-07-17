---
name: agent-mail
description: Use Agent Mail as an optional messaging and
---
# Agent Mail — optional coordination adapter

Agent Mail carries messages, acknowledgements, identities, and temporary file
reservations. It is not a task tracker, queue, proof ledger, or lifecycle
controller.

Reservations prevent collisions only because every cooperating writer checks
them against the same absolute project path; one writer registered against a
different path resolution makes the whole ledger advisory fiction.

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
  evidence that a change is correct or complete.
- Agent Mail never selects work, changes tracker state, commits code, validates,
  integrates, closes, releases, or delivers work.

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

Return the project, identity, thread/message ids, reservation ids and paths,
conflicts, timestamps, and any degraded or unavailable surface. The caller owns
all subsequent decisions.

## References

- [CLI and MCP surface notes](references/TOOLS.md)
- [Coordination patterns](references/WORKFLOWS.md)
- [Troubleshooting](references/RECOVERY.md)
