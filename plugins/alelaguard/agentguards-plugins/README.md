# AgentGuards plugin for OpenAI Codex

LLM security guardrails for Codex in one install: jailbreak and
prompt-injection detection, web-content scanning, data-exfiltration blocking,
and destructive-command authorization.

Enforcement is configurable: **fail-closed by default** for strict security, or
switch to fail-open (availability-first) with a single environment variable
(`AGENTGUARDS_FAIL_OPEN=true`).

This plugin bundles:

- **enforcing hooks** — `UserPromptSubmit` input scanning, `PreToolUse`
  shell-command authorization (allow / deny / ask, with a per-session approval
  cache), and `PostToolUse` web-content scanning of `curl`/`wget` output,
- the **AgentGuards MCP server** (`check_input`, `authorize_action`,
  `validate_output`, `evaluate_policy`, `health_check`),
- the AgentGuards security instructions (the `guardrails` skill).

The hook is a self-contained Python script — no build step, no native binary.
It requires Python 3.9+ (already present on most systems).

## Install

```
codex plugin marketplace add alelaguard/agentguards-plugins
codex plugin add agentguards-codex@agentguards-codex
```

Then provide your API key (get one at
https://agentguards.co/dashboard/keys) so both the MCP server and the hooks can
authenticate:

```
export AGENTGUARDS_API_KEY=ag_your_token_here
```

Add that line to your shell profile (`~/.bashrc`, `~/.zshrc`, …) and restart
Codex so it inherits the key on every session.

> Prefer a native binary or a fully manual `config.toml` setup? The standalone
> AgentGuards Codex client (Go runner + `install.sh`/`install.ps1`) remains
> available — see https://agentguards.co/dashboard/integrations/codex.

## Configuration

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `AGENTGUARDS_API_KEY` | yes | — | Your `ag_` token. Drives both the MCP header and the hooks. The hook also reads `~/.codex/agentguards_token` as a fallback. |
| `AGENTGUARDS_URL` | no | `https://prod.agentguards.co` | Override only for a self-hosted instance. |
| `AGENTGUARDS_FAIL_OPEN` | no | `false` | Hooks fail **closed** by default (block when the service is unreachable). Set `true` to allow on error. |

## How it works

The hooks call the AgentGuards REST API on every prompt, before every shell
command, and after every web fetch — blocking the prompt, denying/asking on the
command, or withholding fetched content when AgentGuards flags a risk. Risky
commands are surfaced for **your approval** rather than silently blocked. The MCP
tools let Codex cooperatively check inputs and authorize actions as described in
the bundled `guardrails` skill.

Learn more at https://agentguards.co.
