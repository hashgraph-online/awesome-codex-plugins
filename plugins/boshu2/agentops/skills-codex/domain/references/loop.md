---
name: Loop
kind: concept
status: draft
see-also: [factory, evolve, rpi, autodev, context-compiler, behavior-shaping]
---
# Loop

The umbrella for the AgentOps operating loop. **One loop body, two drivers, one inner tick, one config.** The same five-beat shape (research, plan, implement, validate, ratchet) runs at every scale; the only things that change across scales are the driver and the stop policy.

Doctrine: [`docs/architecture/canonical-loop-model.md`](../../../docs/architecture/canonical-loop-model.md).

## The shape

| Part | What it is |
|---|---|
| **Loop body** | The five-beat tick: research → plan → implement → validate → ratchet |
| **Two drivers** | [Evolve](evolve.md) (in session, AgentOps-shipped) and [Factory](factory.md) (out of session, substrate-owned) |
| **Inner tick** | [RPI](rpi.md): one research-plan-implement-validate cycle over one bead |
| **Config** | [Autodev](autodev.md): the durable intent the loop reads each tick. NOT a loop. |

## Fractal

The loop is fractal: the same shape at every layer, run by a human or a stand-in agent. rpi is one tick; evolve is N ticks toward a goal; a factory is the same loop run unattended over a queue by an out-of-session substrate. Because the shape repeats, the ratchet rules (no self-grade, fresh agent on failure, knowledge becomes constraints) apply identically at every layer. That is what makes the loop compound up the layers instead of repeating flat.

## When to use

- Use **Loop** as the umbrella noun. Do not call evolve, rpi, autodev, or factory "the loop" as bare synonyms; name the specific driver, tick, or config.
- When an agent asks "which loop do I run?", the answer is driver + tick: run the rpi tick, driven by your session (Evolve) or by a substrate (Factory).
- The in-session loop is the AgentOps product and runs zero-dependency; the Factory driver opts into an orchestration substrate.

## Bounded context

Spans **BC3 Loop** (the loop body, drivers, and tick) and reads from **BC1 Corpus** (context in/out). Orchestration of the Factory driver belongs to the substrate, outside AgentOps' bounded contexts.

## See also

- `factory.md`, `evolve.md` — the two drivers
- `rpi.md` — the inner tick
- `autodev.md` — the config that drives the loop
- `context-compiler.md` — what handles context at each loop edge
