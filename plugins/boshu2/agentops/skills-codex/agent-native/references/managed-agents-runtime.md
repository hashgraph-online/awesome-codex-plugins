# Claude runtime path — Anthropic Managed Agents + Agent SDK + self-hosted sandbox

> The concrete Claude-side recipe behind the three-phase workflow in
> [`../SKILL.md`](../SKILL.md). Doctrine lives in the SKILL; this is the
> runtime how-to. **AgentOps 3.0 is runtime-hookless** — guardrails are skills +
> the `ao` CLI + the local cockpit/pawl proof path, with CI as PR/tag/manual
> backstop telemetry, never ported hooks.
>
> **Mechanism status:** `ao agent bundle` (ag-jspr) and `ao mcp serve` (ag-higd)
> are open, ready beads under epic ag-7s9fo — planned, not yet in the live CLI.
> The `ao session bootstrap` / `ao lookup` / `ao corpus inject` / `ao validate` /
> `ao goals measure` commands the bundled agent calls are real today. Until the
> two planned commands land, hand-stitch the Agent definition (below) and expose
> `ao` as a shell-tool spec instead of an MCP server.

## When to use this path

A **Claude** loop running *outside* an interactive Claude Code session:

- an Anthropic **Managed Agent** (the hosted Managed Agents API),
- an **Agent SDK** loop you run yourself (Node/Python), or
- a **self-hosted sandbox** job (e.g. bushido) running a Claude loop under your
  own MCP/tool surface.

All three become AgentOps-native the same way: **bundle skills → expose `ao` →
land through the cockpit/proof gate**. The runtime differs only in *where* the
loop executes and *how* `ao` is reached.

## Phase 1 — Bundle skills into an Agent definition

```bash
ao agent bundle --runtime managed > agent-def.json     # planned (ag-jspr)
```

Stitches the selected AgentOps skills (default: `session-bootstrap`,
`standards`, `behavioral-discipline`, `validation`, `provenance`) into a Managed
Agents API payload: `model` + `instructions` (the stitched skill bodies) + a
`skills` array + an MCP descriptor for the `ao` tool surface. POST it with the
`managed-agents-2026-04-01` beta header.

**Until ag-jspr lands**, build the payload by hand: concatenate the same
`skills/<name>/SKILL.md` bodies into `instructions` and attach the `ao`
shell-tool spec from Phase 2. The rule is invariant: the hosted agent loads the
**same** `skills/` files an interactive session uses — never a fork.

**Checkpoint:** the payload carries the skills + the `ao` descriptor and
contains **no** holdout `target` / `ground_truth` / PII (Managed Agents are not
ZDR; see Boundaries).

## Phase 2 — Expose `ao` as a callable tool

The hosted loop must be able to orient and self-check. Give it `ao` as a tool so
it can call `session_bootstrap`, `inject`, `corpus_inject`, `validate`,
`goals_measure` itself.

- **Managed Agents / Agent SDK:** run a thin MCP server —

  ```bash
  ao mcp serve                                          # planned (ag-higd)
  ```

  — exposing those verbs as MCP tools, and reference it in the Agent
  definition's MCP descriptor. Until ag-higd lands, supply a **shell-tool spec**
  (a documented tool that shells out to `ao <verb>`), which the SDK and Managed
  Agents both accept.
- **Self-hosted sandbox (bushido):** run the MCP server **inside** the sandbox
  boundary with tailnet access to Dolt, so `ao lookup` / `ao corpus inject` read
  the live corpus over the tailnet (Dolt on the WSL node) without leaving the
  boundary. The sandbox's private MCP wiring is tracked under epic ag-p7ebg.

**Checkpoint:** the agent can call `ao session bootstrap` + `ao lookup` itself
before doing any work.

## Phase 3 — Gate the output through the cockpit path

A reusable workflow (`agent-output-validate.yml`, ag-mptr) runs `ao validate` +
the standards/eval-outcomes gates against whatever the agent produced — a PR branch
or an artifact bundle — as PR/tag/manual backstop telemetry. Routine acceptance
still happens through the same local cockpit/pre-push/pawl proof path as
interactive work.

**Checkpoint:** the agent's output passed the local cockpit/pawl gate; remote
backstop evidence is green when that route is used.

## Optional — in-loop SDK adapter

Agent SDK users who want an *earlier, advisory* signal can register the
`PreToolUse` / `Stop` adapter in [`sdk-hook-adapter.md`](sdk-hook-adapter.md). It
shells out to `ao validate` and surfaces the verdict in-loop. **Clearly
optional** — the deterministic cockpit/proof path is the boundary, the adapter
never is.

## Boundaries (Claude/cloud-specific)

- **Managed Agents are NOT ZDR.** Anything in the Agent definition or an MCP tool
  response leaves the boundary permanently. Never bundle holdout
  `target`/`ground_truth`/PII. Holdout-touching grading uses
  [`../../validate/SKILL.md`](../../validate/SKILL.md), which runs on a
  ZDR-safe surface.
- **No skill fork.** The hosted loop loads the same `skills/` files as
  interactive sessions; a divergent guardrail set drifts and defeats the corpus
  moat.
- **The deterministic gate is the boundary, not the adapter.** A bypassed in-loop
  hook must never mean unvalidated work lands.

## See also

- [`codex-ntm-runtime.md`](codex-ntm-runtime.md) — the Codex/NTM swarm path (no
  Managed Agents API; tmux panes + agent-mail + direct `ao` shell calls).
- [`../SKILL.md`](../SKILL.md) — the three-phase doctrine this recipe implements.
