---
name: agent-native
description: Make an out-of-session agent AgentOps-native
---
# $agent-native — Make Out-of-Session Agents AgentOps-Native (Hookless)

Run a Claude loop *outside* an interactive Claude Code / Codex session — an Anthropic **Managed Agent**, an **Agent SDK** loop, or a self-hosted sandbox job — and keep it under the same AgentOps guardrails. The old reflex ("port the ~50 marketplace hooks into the new runtime") is **wrong for AgentOps 3.0**. This skill is the hookless reframe.

## Overview

**AgentOps 3.0 is runtime-hookless.** Guardrails come from three things, never runtime hooks:

1. **Skills** — `skills/<name>/SKILL.md` progressive-disclosure contracts (standards, behavioral-discipline, council, validation, trace, provenance).
2. **The `ao` CLI** — the deterministic tool surface (`ao session bootstrap`, `ao lookup`, `ao corpus inject --query`, `ao validate`, `ao goals measure`) plus the `standards` skill loaded into the agent's instructions.
3. **Local cockpit gate as routine authority** — the operator accepts output by landing it through `ao gate check` / installed Git pre-push / pawl proof; `.github/workflows/validate.yml` remains PR/tag/manual backstop telemetry, NOT a PreToolUse hook.

So an out-of-session agent becomes AgentOps-native by: **(a)** loading AgentOps skills into the Agent definition, **(b)** exposing the `ao` CLI as a callable tool (MCP or shell-tool) so the agent can `ao session bootstrap` / `ao lookup` / `ao validate` itself, and **(c)** running the same deterministic local validation/proof path on its outputs before the work is accepted. The Agent SDK's own hooks become an **optional thin adapter** for teams wanting in-loop interception — never the primary mechanism.

> **Mechanism status (live).** The two concrete commands this skill names — `ao agent bundle` and `ao mcp serve` — are live cobra commands in the `ao` CLI, alongside the `ao session bootstrap` / `ao lookup` / `ao corpus inject` / `ao validate` / `ao goals measure` commands the bundled agent calls.

This is an **extension of two existing skills**, not a rewrite:
- [standards](../standards/SKILL.md) — gains an Agent-runtime profile: how the standards/behavioral-discipline checklists get loaded by a non-interactive Claude and enforced by deterministic gate surfaces rather than runtime hooks.
- [converter](../converter/SKILL.md) + the `skills/` ↔ `skills-codex/` parity machinery — reused as-is to keep the bundle dual-runtime.

**Concrete runtime recipes** — the three-phase workflow below, one per runtime:
- [references/managed-agents-runtime.md](references/managed-agents-runtime.md) — the **Claude path**: Anthropic Managed Agents + Agent SDK + self-hosted sandbox.
- [references/codex-ntm-runtime.md](references/codex-ntm-runtime.md) — the **Codex/NTM path**: tmux pane swarms + agent-mail + direct `ao` shell calls (no Managed Agents API).

## ⚠️ Critical Constraints

- **This is a reframe of the retired "port hooks" idea, NOT a hook revival.** **Why:** hooks are runtime-coupled and fork the guardrail surface; skills + `ao` + CI are the portable 3.0 waist that works in any runtime.
- **Single source of truth — no skill fork.** The cloud/SDK agent loads the *same* `skills/` files an interactive session uses. **Why:** a forked guardrail set drifts and defeats the corpus moat.
- **Managed Agents are NOT ZDR.** Never bundle holdout `target`/`ground_truth`/PII into an Agent definition or its MCP tool responses. **Why:** anything sent to the cloud agent leaves the boundary permanently. For holdout-touching work see [eval-outcomes](../validate/SKILL.md).
- **The deterministic gate is the boundary, not the adapter.** The optional SDK hook adapter is convenience, never the enforcement boundary. **Why:** a bypassed in-loop hook must not mean unvalidated work lands; the local cockpit/pre-push/pawl path is the routine authority and CI is PR/tag/manual backstop telemetry.

## Workflow

### Phase 1: Bundle skills into an Agent definition

```bash
ao agent bundle --runtime managed > agent-def.json
```

Stitches the selected AgentOps skills (default: `session-bootstrap`, `standards`, `behavioral-discipline`, `validation`, `provenance`) into a Managed Agents API payload — model + instructions + `skills` array + an MCP descriptor for the `ao` tool surface. POST-able with the `managed-agents-2026-04-01` beta header.

**Checkpoint:** the payload carries the skills + the `ao` MCP descriptor, and contains no holdout values.

### Phase 2: Expose `ao` as a tool

Run a thin MCP server (`ao mcp serve`) — or a documented shell-tool spec — exposing `session_bootstrap`, `inject`, `corpus_inject`, `validate`, `goals_measure` so the hosted loop can orient and self-check. For self-hosted sandboxes (bushido), the MCP server runs **inside** the sandbox boundary with tailnet access to Dolt.

**Checkpoint:** the agent can call `ao session bootstrap` + `ao lookup` itself before doing work.

### Phase 3: Gate the output through the cockpit path

A reusable workflow (`agent-output-validate.yml`) can run `ao validate` + the standards/eval-outcomes gates against whatever the agent produced (PR branch or artifact bundle) as remote backstop telemetry. The routine acceptance path is the **same local cockpit/pawl gate** as interactive work: land through `ao gate check` and the installed Git pre-push proof path.

**Checkpoint:** the agent's output passed the local cockpit/pawl gate; PR/tag/manual CI backstop evidence is green when that route is used.

### Optional: SDK hook adapter

For Agent SDK users who *want* in-loop interception, a documented `PreToolUse`/`Stop` adapter shells out to `ao validate` (with the `standards` checklist loaded). **Clearly optional — the default path is the deterministic cockpit/proof gate, never runtime hooks.** Reference samples (TypeScript + Python, wired into no runtime by default): [references/sdk-hook-adapter.md](references/sdk-hook-adapter.md).

## Output Specification

**Format:** a JSON Agent definition plus a validated PR/artifact. **Path:** the Agent definition is written to `agent-def.json` at the repo root; the runtime profile is written to `docs/contracts/agent-runtime-profile.md` (the frontmatter `produces` path). **Structure:** model, instructions (stitched skills), `skills` array, `ao` MCP descriptor; the output is accepted only after the local cockpit/pawl proof path passes, with CI backstop evidence when that route is used.

## Quality Rubric

- [ ] Agent definition loads the *same* `skills/` files as interactive sessions (no fork).
- [ ] `ao` is callable by the agent (MCP/shell-tool); it can self-bootstrap + self-validate.
- [ ] Outputs pass the same local cockpit/pawl proof path as interactive work (the deterministic gate is the boundary, not a runtime hook).
- [ ] No holdout `target`/`ground_truth`/PII in the Agent definition or tool responses.

## Examples

```bash
# Bundle, serve the ao tool surface, and land through the cockpit/proof gate
ao agent bundle --runtime managed > agent-def.json
ao mcp serve &   # exposes session_bootstrap/inject/validate/goals_measure as MCP tools
# (submit agent-def.json to the Managed Agents API; PR CI is backstop telemetry)
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Tempted to port the hooks | Old runtime-coupled reflex | Don't — bundle skills + expose `ao` + land through the cockpit/proof gate. Hooks are the optional adapter only |
| Agent can't orient | `ao` not exposed as a tool | Run `ao mcp serve` (or the shell-tool spec) so the loop can `ao session bootstrap` |
| Unvalidated work merged | Relied on the optional in-loop adapter | The cockpit/pawl proof path is the gate — never the adapter |

## See Also

- [references/managed-agents-runtime.md](references/managed-agents-runtime.md) — Claude runtime recipe (Managed Agents + Agent SDK + self-hosted sandbox)
- [references/codex-ntm-runtime.md](references/codex-ntm-runtime.md) — Codex/NTM runtime recipe (tmux pane swarms + agent-mail + direct `ao`)
- [standards](../standards/SKILL.md) — the checklists the agent loads and deterministic gates enforce
- [converter](../converter/SKILL.md) — keeps the bundle dual-runtime (skills ↔ skills-codex)
- [eval-outcomes](../validate/SKILL.md) — holdout-safe grading for cloud/out-of-session agents
- [swarm](../swarm/SKILL.md) — the in-session/NTM multi-agent backends that dispatch whole `$rpi` skill loops (`ao agent bundle` produces the definition a managed-agents substrate runs)
- [heal-skill](../heal-skill/SKILL.md) — deep audit (audit.sh) this skill before declaring stable
