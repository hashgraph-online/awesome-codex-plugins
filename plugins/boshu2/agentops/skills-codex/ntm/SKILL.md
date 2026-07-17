---
name: ntm
description: Use NTM as an optional pane adapter for
---
# NTM — optional pane adapter

NTM hosts explicit agent roles in persistent panes. It is transport, not an
AgentOps lifecycle controller. The caller chooses the panes, roles, commands,
write scopes, and stopping point.

Robot surfaces work because they report what the pane is doing, not what was
sent to it; a dispatch layer that only proved delivery would let every dead
worker look busy.

Judge pane liveness by the truth-stack, strongest first: new artifacts on
disk, then transcript growth, then robot state and attention flags, then bare
process existence. A successful prompt send sits below all of these and proves
nothing about work.

Named failure mode — **kill-the-witness**: restarting a stuck pane before
capturing its state, destroying the only evidence of why it stalled.

Anti-pattern: restarting an unresponsive pane as the default remedy.
Corrective: rescue before restart — snapshot robot state and transcript,
attempt a nudge, and restart only when the truth-stack shows no liveness at
any level.

## Boundary

- Never start or probe NTM merely because it is installed.
- Discover the live command contract with `ntm --help`,
  `ntm --robot-capabilities`, and `ntm --robot-snapshot` before unfamiliar
  actions.
- Dispatch each caller-supplied command once. NTM does not select work, retry a
  failed command, validate a candidate, integrate changes, or decide what runs
  next.
- Pane roles are descriptive. They grant no ownership, admission, Git, release,
  or delivery authority.
- Concurrent writers require caller-supplied disjoint scopes and whatever
  isolation the repository requires. NTM does not infer safe concurrency.
- Safety, lock, mail, and pipeline features remain substrate facts. Their state
  cannot change an RPI phase result or semantic verdict.

## One-shot dispatch

1. Record the explicit session, pane, role, working directory, and command.
2. Inspect robot capabilities and current snapshot.
3. Create or select only the named pane.
4. Send the command once.
5. Observe robot state, attention, and transcript until the command exits or the
   caller's observation window ends.
6. Return the factual result and stop.

For a software-factory layout, the caller may name producer, tester, validator,
or integrator panes. The same identity rule still applies: a validator for a
candidate must have a distinct context identity from its author. Merely placing
two roles in different panes is a declared runtime fact, not proof of semantic
independence. Mixed-model judgment panes follow
the `agent-native` model-dispatch recipe (probe, disclose, never
`claude -p`).

## Output

Return:

- session and pane identifiers;
- role and exact command;
- start and observation timestamps;
- exit status when known;
- robot state and relevant transcript references;
- degraded or unavailable substrate surfaces;
- effects that were and were not observed.

A timeout, nonzero exit, or degraded source is reported as evidence. The caller
decides whether to invoke another experiment.

## Useful live surfaces

Prefer machine-readable robot surfaces for capability, snapshot, attention,
tail, and pipeline observations. Use interactive key injection only when the
caller explicitly requests an interactive action and no robot command provides
the needed behavior.

External NTM documentation and examples remain the authority for command syntax;
this skill owns only the AgentOps boundary above.
