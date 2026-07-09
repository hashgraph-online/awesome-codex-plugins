---
name: RPI
kind: concept
status: draft
see-also: [loop, evolve, factory, slice, context-compiler]
---
# RPI

The **inner tick** of the [Loop](loop.md): one Research → Plan → Implement → Validate cycle over one bead, one behavior, one acceptance proof. RPI is the unit both drivers run. [Evolve](evolve.md) runs N rpi ticks in a session; [Factory](factory.md) runs them unattended over a queue.

## The five beats

| Beat | What it does |
|---|---|
| **Research** | Compile the context this arc needs. `ao lookup` produces a decay-ranked, token-budgeted slice of the corpus. |
| **Plan** | Decompose the arc into a verifiable plan; no gold-plating. |
| **Implement** | Execute the plan in an isolated worktree, one vertical slice at a time. |
| **Validate** | Produce a PASS/WARN/FAIL verdict; the validator is never the implementer. |
| **Ratchet** | Capture evidence and durable learning under the promotion ratchet. |

## RPI is one invocable unit

A substrate dispatches the `/rpi` loop (an agent running the skill) as one unit; it does not drive the five beats as separate substrate steps. Decomposing rpi across the substrate seam would duplicate the loop shape and pit substrate retry against the ratchet rules. Whoever owns the loop owns its invariants, and AgentOps owns rpi.

## When to use

- Use **RPI** (or "the rpi tick") for one cycle over one bead. It is the [Slice](slice.md) of the loop: one coherent arc with a single rollback semantic.
- Do not call rpi "the loop"; rpi is the inner tick of the loop.

## Bounded context

**BC3 Loop**, reading from **BC1 Corpus** at the Research beat and writing to it at the Ratchet beat.

## See also

- `loop.md` — the umbrella tick lives here
- `evolve.md`, `factory.md` — the two drivers that run rpi
- `slice.md` — a single rpi arc is one slice
- `context-compiler.md` — what feeds rpi's Research beat and absorbs its Ratchet beat
