---
name: Autodev
kind: concept
status: draft
see-also: [loop, evolve, factory, rpi, anti-pattern]
---
# Autodev

The **config/intent layer** the [Loop](loop.md) reads every tick, NOT a loop. Autodev is the durable intent crafted into context: PROGRAM.md / AUTODEV.md plus GOALS.md plus ADRs. The loop consumes it; it does not run it.

## When to use

- Use **Autodev** for the config that drives the loop. Lead with "the PROGRAM.md / AUTODEV.md contract that drives the loop", never with "bounded autonomous dev loops" (that phrasing implies a loop and is the source of the original sprawl).
- Autodev is consumed by both drivers ([Evolve](evolve.md) and [Factory](factory.md)) every tick. It is the highest-leverage antecedent: arrange it well and the loop's behavior follows.

## Anti-pattern

- **Treating Autodev as a fourth loop.** It is config, alongside GOALS and ADRs. Calling it a loop re-creates the confusion the canonical model resolves. See [Anti-Pattern](anti-pattern.md).

## Bounded context

**BC1 Corpus / intent.** Autodev is one of the durable intent sources the loop reads; it sits with GOALS.md and ADRs as the antecedent layer, not in BC3 Loop.

## See also

- `loop.md` — Autodev is the config of the one loop
- `evolve.md`, `factory.md` — the drivers that read Autodev each tick
- `rpi.md` — each tick reads Autodev as part of its Research beat
- `anti-pattern.md` — what treating config as a loop costs
