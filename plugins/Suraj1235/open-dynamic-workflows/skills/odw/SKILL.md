---
name: odw
description: Dynamic multi-agent workflows — plan first, then orchestrate parallel agents with adversarial verification via the local odw daemon. Use when the user asks for a "workflow", says "ultracode", or hands you a task spanning many files/items that benefits from parallel agents.
---

# Open Dynamic Workflows

You orchestrate large tasks through an explicit plan and a local daemon instead of improvising. The scripts referenced below live next to this skill in `scripts/`.

## Model & API key (read this first)

Codex exposes **no API for an extension to invoke its own model**, so — unlike the OpenCode plugin, which runs ODW's real engine *through* OpenCode's configured model with no extra key — there are exactly two honest paths here:

- **No-key path (Native fallback):** *you, Codex,* orchestrate the task with your own model and native subagents (platform-capped, ~6 concurrent). This uses no extra key, but it is **not** the ODW engine — no sandbox, no 100-way fan-out, no crash-resume, no budget hard-stop.
- **Full-engine path (Daemon):** the real ODW engine runs in the local daemon, which uses **its own** provider key in `~/.odw/config.json` (Anthropic / OpenAI-compatible / Ollama — Ollama is keyless/local). This is the only way to get the full engine on Codex today.

There is no middle option unless/until Codex ships a host-model API or MCP sampling. Pick the path based on whether the daemon is up (Step 0).

## Step 0 — Daemon check

Run: `node scripts/daemon-bridge.js --check`
- Exit 0 → daemon is up; use the daemon path.
- Exit 1 → daemon is down; use the native fallback path (and mention once that the daemon installs from github.com/Suraj1235/open-dynamic-workflows — clone, `npm install`, `npm run setup`, then `odw-daemon start`).

## Daemon path

1. **Plan:** `node scripts/daemon-bridge.js plan "<the user's task>"` — prints a JSON plan: task graph, topology (mapreduce / pipeline / adversarial / consensus / treesearch / hybrid), specialist roles, hard limits (budget, timeouts, concurrency), cost/time estimate and the compiled orchestration script.
2. **Confirm:** show the user a compact summary (topology, agent count, est. cost, est. time) and ask before executing anything beyond read-only work.
3. **Execute:** `node scripts/daemon-bridge.js exec plan.json` — returns a `wf_...` id. The daemon runs the script in a sandbox: 16–100 concurrent agents, SQLite checkpoints, crash-resume, budget hard-stop.
4. **Monitor / report:** `node scripts/daemon-bridge.js status <wf_id>` while running; `node scripts/daemon-bridge.js result <wf_id>` blocks until done and prints the final synthesized result. Relay it to the user.

## Native fallback path (no daemon)

Orchestrate with your own subagent capability, platform-limited:
1. Decompose into discovery → parallel work → adversarial verification → synthesis. State the plan first.
2. Fan out independent items to subagents with hyper-scoped instructions and structured JSON outputs.
3. Verify aggregated results (hunt false positives, challenge severity, find gaps) before synthesizing.
4. Respect safety: never write files or run mutating commands without explicit user approval.

## Safety rules (both paths)

- Read-only operations are auto-approved; writes, shell commands and git commits need user approval.
- Respect the budget: if the plan estimate looks expensive, say so before executing.
- Never put secrets in prompts, plans, or logs.
