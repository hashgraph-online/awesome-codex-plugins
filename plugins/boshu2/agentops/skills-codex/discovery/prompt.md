# discovery

Full discovery phase orchestrator. Brainstorm + ao search + research + plan + pre-mortem gate. Produces epic-id and execution-packet for $crank. Triggers: "discovery", "discover", "explore and plan", "research and plan", "discovery phase".

## Codex Execution Profile

1. Load and follow the skill instructions from the sibling `SKILL.md` file for
   this skill.
2. In Codex hookless mode, run `ao codex ensure-start` before discovery begins;
   the CLI records startup once per thread and skips duplicates automatically.
3. Route by risk class first: fanout is for one-way doors only (architecture
   forks, cross-agent coordination contracts, product decisions). Routine
   runtime/CLI feature work takes the MVP vertical-slice path — ~15 min
   discovery, ~90 min slice, new work filed as follow-up beads, not absorbed.
4. For fanout-class requests, fan out at least three `PerspectivePlan` views,
   synthesize them into one `SynthesisPacket`, and get a Fable `ApprovalEdge`
   through `$codex-approval` before creating beads.

## Guardrails

1. Do not assume startup hooks exist under `~/.codex`.
2. Let closeout skills own `ao codex ensure-stop`; `$discovery` is a start-path skill.
3. Read local files in `references/` and `scripts/` only when needed.
4. `WARN is not` a silent pass for Fable approval: revise the packet or record
   an explicit accepted-risk note before continuing.
