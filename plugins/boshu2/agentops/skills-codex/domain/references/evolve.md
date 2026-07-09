---
name: Evolve
kind: concept
status: draft
see-also: [loop, factory, rpi, autodev, context-compiler]
---
# Evolve

The **in-session driver** of the [Loop](loop.md): an interactive agent running the loop self-paced, allowed to end with the session. Evolve runs N [RPI](rpi.md) ticks toward a goal: select the next-best work, run a tick, run a post-mortem, repeat. It is the outer loop relative to rpi, and the same loop body as [Factory](factory.md) under a different driver.

## When to use

- Use **Evolve** for the in-session, self-paced driver. It is the AgentOps product and zero-dependency: it runs in a plain session with no daemon and no substrate.
- Evolve's *logic* (which bead next, N cycles toward a goal, when to post-mortem) stays in AgentOps. Evolve's *cadence*, when run unattended, becomes a substrate cron Order; that cadence is orchestration, not loop logic.

## Stop policy

A session may end with its budget (the session-scope discipline: 2-4 PRs per session, post-mortem at the threshold). This is the one place the loop's stop policy differs from Factory, which stops only on an operator marker.

## Bounded context

**BC3 Loop.** The work-selection ladder and the N-cycle accounting are AgentOps domain logic.

## See also

- `loop.md` — the umbrella; Evolve is one of its two drivers
- `factory.md` — the same loop body, driven by a substrate instead of a session
- `rpi.md` — the tick Evolve repeats
- `autodev.md` — the config Evolve reads each cycle
