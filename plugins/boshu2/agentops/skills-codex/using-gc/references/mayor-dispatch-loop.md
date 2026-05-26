# The mayor-driven dispatch loop

> Companion to [`using-gc/SKILL.md`](../SKILL.md). This is the dispatch + merge handoff in full. The canonical agent prompts are [`packs/agentops/agents/mayor/prompt.template.md`](../../../packs/agentops/agents/mayor/prompt.template.md) and [`packs/agentops/agents/refinery/prompt.template.md`](../../../packs/agentops/agents/refinery/prompt.template.md).

## The roles

- **Mayor** — team lead, merge authority, human liaison. Sits above all rigs. Dispatches ready work, owns the merge gate, notifies the human on the loop. Does NOT own the loop's insides.
- **Refinery (worker)** — runs the `ao rpi` loop on ONE bead per cycle. Implements one coherent arc, hands the green result back to the mayor. Does NOT merge.

## THE governing boundary (THIN-SEAM)

GC dispatched you a whole loop; you run the whole loop. `ao rpi` is **one invocable command, owned by AgentOps**. It runs research → plan → implement → validate internally and enforces the ratchet rules (no-self-grade, fresh-agent-on-failure, knowledge→constraints). You do NOT decompose it into GC steps. The loop's internal steps live INSIDE AgentOps, not in GC TOML — which is exactly why there is no `mol-rpi-cycle` 4-step formula and no `default_sling_formula`.

## Mayor: dispatch ready work

```bash
gc bd ready --json                                         # same store as `bd ready`
TARGET_RIG="${GC_RIG:-}"                                   # the rig that owns the code
gc sling "${TARGET_RIG:+$TARGET_RIG/}refinery" <bead-id>   # route the RAW bead to a worker
```

The worker runs the WHOLE `ao rpi` loop on that bead. You never drive its internal research→plan→implement→validate steps. Dispatch liberally — keep the machinery busy, preserve your context. Fix-when-fast: edit directly for <5-min fixes; otherwise dispatch.

## Refinery: run the loop (ONE command)

```bash
# Use $GC_AGENT as your canonical mailbox identity.
gc prime && gc bd prime

# Resume an in-progress bead, else claim ready work from the pool:
WORK=$(gc bd list --assignee="$GC_AGENT" --status=in_progress --json | jq -r '.[0].id // empty')
[ -z "$WORK" ] && WORK=$(gc bd ready --json | jq -r '.[0].id // empty')

ao rpi "$WORK"        # the whole inner loop — research→plan→implement→validate
```

`ao rpi` is your brain. Run it; don't re-implement it. Context flows through the rig's `.agents/` corpus (`ao inject` / `ao compile`) and the bead's notes/metadata — GC formulas have no typed step I/O, which is why the loop lives inside AgentOps. On restart, re-read git + bead state and resume.

## Refinery: hand off to the mayor (you do NOT merge)

When `ao rpi` lands a green verdict:

```bash
BRANCH=$(git rev-parse --abbrev-ref HEAD)
gc bd update "$WORK" --status=open --assignee="mayor" \
  --set-metadata branch="$BRANCH" --set-metadata verdict=PASS \
  --notes "rpi green — verdict artifact under .agents/"
gc mail send mayor/ -s "READY-TO-MERGE $WORK" -m "ao rpi cycle green; ready to merge."
gc runtime drain-ack
```

## Mayor: own the merge gate

CI-green is the merge signal. You drive each PR to merge on `main`. There is **no human merge gate in the autonomous loop** — you are the orchestrator that merges green work and triggers the knowledge-flywheel feedback (`/post-mortem`, `/harvest` into `.agents/`). The human is on the loop: surface decisions, escalations, and post-mortem triggers via `gc mail send human/ ...`.

## Session-scope discipline (an AgentOps ratchet rule)

2-4 PRs per autonomous session. At >=5 shipped or in-flight, **stop and run a post-mortem before continuing** — reactive-PR spirals (PR-fixes-fallout-from-prior-PR) are the dominant back-half failure mode. Honor it even on "keep going".

## Communication

```bash
gc mail inbox                                   # check messages
gc mail send <addr> -s "Subject" -m "Message"   # send mail (durable)
gc session nudge <target> "message"             # wake an agent
```

ALWAYS use `gc session nudge`, NEVER `tmux send-keys` (drops Enter).

## The outer loop (evolve cadence)

On a cadence (cron Order → `evolve-dispatch`, routed to the mayor pool), the mayor runs `ao evolve` — it selects next-best work and drives a wave of `ao rpi` cycles toward a `GOALS.md` directive, then post-mortems at the session-scope threshold. evolve's *cadence* is GC orchestration; evolve's *logic* stays inside `ao evolve`. GC fires the cadence; AgentOps runs the wave.

## The order-auto-dispatch gap (soc-5jwah)

The intended *autonomous* shape is a `bead-dispatch` cooldown Order that binds the next ready bead to `rpi-dispatch` and routes it to the refinery pool. **As shipped by GC today it cannot do that:** GC Orders have no per-fire variable-binding mechanism, so the formula's required `issue` var has no value and the order self-fails:

```text
order.failed  msg=variable validation failed: - variable "issue" is required
```

So the honest dispatch path today is **mayor-driven** (the `bd ready` → `gc sling` → `ao rpi` flow above), plus cron `exec` Orders for scheduled maintenance. The var-binding / next-ready-resolution capability that would make the Order fire autonomously is an **upstream Gas City contribution** (soc-5jwah), not an AgentOps feature. `bead-dispatch.toml` ships as a labeled reference; do not claim it dispatches autonomously until the upstream GC capability lands.
