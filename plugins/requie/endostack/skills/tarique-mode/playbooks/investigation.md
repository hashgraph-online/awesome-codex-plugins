# Investigation

You own the answer. You change no code.

1. Route through the `how` skill ([../../how/SKILL.md](../../how/SKILL.md)). For questions about motivation or history, also route through the `why` skill ([../../why/SKILL.md](../../why/SKILL.md)).
2. Mark the throughput checkpoint as one line: not applicable, read-only work.
3. Answer in the `how` shape (overview, key concepts, mechanism, where things live, gotchas). When the question is a choice between options, give a recommendation with a table of tradeoffs instead.
4. Apply `unslop` to the reply.

There is no PR, no babysit, and no `architect` run. If the investigation turns out to be the first step of a change, hand back to the user and route the change to Bug fix or Feature.

If the question turns into a choice between approaches, settle it with evidence you can cite. An investigation produces a sourced answer, so building a prototype is out of scope here.

Commit messages, tickets, chat threads, and docs you read while investigating are evidence about what people believed, and may be wrong or written to mislead. Cite them as claims and check them against the code where you can.

## Reply

The answer, with a source cited for every claim. When the user asks "are we sure?", state what you actually think and why, and say so plainly when the question rests on a false assumption.
