---
name: agent-native
description: "Run agent native."
---

# $agent-native — Make Out-of-Session Agents AgentOps-Native (Codex Native)

> **Quick Ref:** Run a Claude/Codex loop *outside* an interactive session (Managed Agent, Agent SDK, or self-hosted sandbox) under the same AgentOps guardrails — hooklessly. Guardrails = skills + the `ao` CLI + CI, never ported hooks. Bundle skills into the agent definition, expose `ao` as a callable tool so the loop self-bootstraps + self-validates, and gate the output through the SAME CI as interactive work.

## Codex/ATM path

Codex (gpt-5.3-codex) has NO Managed Agents API, NO Workflow tool, NO Task subagent. It orchestrates via ATM (tmux pane swarms + agent-mail) + skills + the `ao` CLI + ssh to bushido. ATM is Bo's fork/alias of upstream NTM: `atm` points at `~/dev/ntm/dist/atm-darwin-arm64` and preserves the upstream `ntm` command surface. So an out-of-session Codex loop becomes AgentOps-native the same way: load the AgentOps skills, call `ao session bootstrap` / `ao inject` / `ao validate` directly (no MCP needed — Codex shells out), and gate outputs through CI (`agent-output-validate.yml`). `ao` does not wrap `gc`; a whole loop needing a mayor/refinery still routes through `gc`.

## Instructions

Load and follow the skill instructions from the sibling `SKILL.md` — OR read `skills/agent-native/SKILL.md` in the host repo for the canonical specification. Honor the Critical Constraints: this is a reframe of "port hooks", NOT a hook revival; no skill fork (load the same `skills/` files); Managed Agents are NOT ZDR (no holdout/PII in the agent definition); CI is the enforcement boundary, not the optional in-loop adapter.
