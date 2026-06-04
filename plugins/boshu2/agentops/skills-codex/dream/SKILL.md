---
name: dream
description: 'Retired pointer — out-of-session compounding moved to the substrate (NTM + MCP + managed-agents).'
---
# Dream Skill - Retired (out-of-session compounding moved to the substrate)

**Status: RETIRED (soc-2rtm0).** The in-tree out-of-session compounding engine
and its whole CLI surface (the former always-on lane) were removed, along with
the always-on background process that carried it. AgentOps no longer ships an
out-of-session orchestration substrate — scheduled, between-session knowledge
compounding now runs on a substrate AgentOps adopts but does not own (**NTM +
MCP + managed-agents**). Do not invent a replacement `$ao` workflow.

## What stays in AgentOps

The KEEP knowledge primitives the dream cycle was built on are unchanged and
remain on-demand: `$harvest` (promote `.agents/` knowledge), `$forge` (mine
transcripts into learnings), `$compile` (Mine → Grow → Defrag → Lint), and
`$inject` (JIT decay-ranked context). The nightly-CI dream-cycle proof job in
`.github/workflows/nightly.yml` still runs against the checked-in corpus and is
built on those primitives, not on the retired CLI engine.

## Delineation vs $evolve

`$evolve` owns the daytime code-compounding layer (operator-driven, via `$rpi`).
The knowledge-compounding layer this skill used to own now lives outside
AgentOps, on the adopted substrate (NTM + MCP + managed-agents). Both still
share the fitness-measurement substrate via `corpus.Compute` / `ao goals measure`.

## See Also

- [How It Works](../../docs/how-it-works.md)
- [CLI Reference](../../cli/docs/COMMANDS.md)
