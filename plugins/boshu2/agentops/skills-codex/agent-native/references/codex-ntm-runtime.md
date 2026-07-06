# Codex/ATM runtime path — tmux pane swarms + agent-mail + direct `ao`

> The Codex-side recipe behind the three-phase workflow in
> [`../SKILL.md`](../SKILL.md). Same doctrine, different runtime: Codex
> (gpt-5.3-codex) has **no Managed Agents API, no Workflow tool, no Task
> subagent**. It orchestrates through **ATM** (tmux pane swarms + agent-mail) +
> skills + the `ao` CLI + `ssh bushido`. So the path is the same — bundle skills
> → expose `ao` → land through the cockpit/proof gate — but every Claude-only primitive is replaced by
> its Codex equivalent.

## When to use this path

A **Codex** loop (or any non-Claude headless runtime) running out-of-session:

- a Codex CLI loop driven by ATM tmux panes on bushido,
- an OpenClaw / cron-scheduled Codex job, or
- any agent that shells out rather than calling MCP tools.

ATM is Bo's fork/alias of upstream NTM: `atm` points at
`~/dev/ntm/dist/atm-darwin-arm64` and preserves the upstream `ntm` command
surface while giving AgentOps a local name.

## The substitutions (Claude → Codex)

| Claude primitive | Codex/ATM equivalent |
|---|---|
| Managed Agents API (`ao agent bundle --runtime managed`) | ATM swarm definition; load skills into the pane's instructions |
| `ao mcp serve` (MCP tool surface) | **direct `ao` shell calls** — Codex shells out, no MCP needed |
| Workflow / Task subagent fan-out | tmux **pane swarm** (ATM), coordinated via **agent-mail** |
| `PreToolUse` / `Stop` SDK adapter | not applicable — the cockpit/proof gate is the boundary |
| in-loop MCP descriptor | a documented shell-tool spec invoking `ao <verb>` |

The invariant holds: the Codex loop loads the **same** `skills/` files (via the
checked-in `skills-codex/` artifact, kept in parity by the
[`converter`](../../converter/SKILL.md) machinery) — never a hand-forked set.

## Phase 1 — Load skills into the swarm

There is no payload to POST. Instead, load the AgentOps skills into each pane's
instructions (the `skills-codex/<name>/` artifact bodies). Default set matches
the Claude path: `session-bootstrap`, `standards`, `behavioral-discipline`,
`validation`, `provenance`.

```bash
ssh bushido 'cd ~/dev/agentops && ao session bootstrap'   # orient the pane
```

**Checkpoint:** the pane's instructions carry the skill bodies; no holdout
values inlined.

## Phase 2 — Expose `ao` (shell, not MCP)

Codex shells out directly, so "exposing `ao`" just means the pane can run
`ao` on its host. On bushido that is a direct call; from Mac it is dispatched
over the tailnet:

```bash
ssh bushido 'cd ~/dev/agentops && ao lookup --query "<topic>"'
ssh bushido 'cd ~/dev/agentops && ao corpus inject --query "<topic>"'
ssh bushido 'cd ~/dev/agentops && ao validate --gate --changes <files>'
```

For a **whole out-of-session loop** (a swarm of panes, not a single pane),
orchestration routes through the ATM substrate — `ao` does not own or wrap a
substrate; each pane dispatches its own operating-loop skill run. See
[`../../using-atm/SKILL.md`](../../using-atm/SKILL.md). Multi-pane coordination
(file locks, inboxes, handoffs) uses **agent-mail**; see the `using-atm` and
`agent-mail` skills.

**Checkpoint:** the pane can call `ao session bootstrap` + `ao lookup` itself
before doing any work.

## Phase 3 — Gate the output through the cockpit path

Identical to the Claude path: the swarm's output is accepted through the
**same** local cockpit/pre-push/pawl proof path running `ao gate check` and the
standard deterministic gates. `agent-output-validate.yml` remains PR/tag/manual
backstop telemetry. ATM panes do not get a private gate — the cockpit path is
the shared boundary for both runtimes.

**Checkpoint:** the swarm's output passed the identical cockpit/pawl gate as
interactive work.

## Boundaries (Codex/ATM-specific)

- **No skill fork.** Panes load the `skills-codex/` artifact, which the converter
  keeps in parity with `skills/`. Editing the Codex body by hand without the
  override pipeline drifts the guardrail surface.
- **Holdout stays off the swarm.** The same ZDR discipline applies: no
  `target`/`ground_truth`/PII in pane instructions or `ao` tool responses.
  Holdout grading uses [`../../eval-outcomes/SKILL.md`](../../eval-outcomes/SKILL.md).
- **The cockpit proof path is the gate.** Codex has no in-loop adapter; acceptance
  relies on the same deterministic local gate and remote backstop telemetry as
  other runtimes.

## See also

- [`managed-agents-runtime.md`](managed-agents-runtime.md) — the Claude path
  (Managed Agents API + Agent SDK + self-hosted sandbox).
- [`../SKILL.md`](../SKILL.md) — the three-phase doctrine this recipe implements.
