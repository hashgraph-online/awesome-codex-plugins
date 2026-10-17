---
name: guardrails
description: How AgentGuards enforces its guardrails in Codex — fully automatic, via hooks, with nothing for you to call. Load this if asked how AgentGuards works, whether you need to screen something yourself, or why no agentguards check_input / authorize_action tools are available.
---

# AgentGuards — enforced by hooks

This plugin has no MCP server, so there is no `check_input`, `authorize_action`
or `health_check` tool — do not look for them, they are not installed.

That is not reduced protection. The hooks in `hooks/hooks.json` enforce
deterministically, on every request, whatever the model does:

- **`UserPromptSubmit`** screens every prompt before you see it.
- **`PreToolUse`** authorizes every shell command before it runs: denied, or
  allowed, or left to Codex's own approval prompt.
- **`PermissionRequest`** rides that approval prompt: it denies what AgentGuards
  rejects and remembers what the user approved for the rest of the session.
- **`PostToolUse`** scans the output of shell commands that fetch (`curl`,
  `wget`, `http`, `fetch`, `aria2c` — also behind `sudo`, `timeout`, `bash -c`,
  `$(...)`), withholding or redacting it before you read it, and scans
  `apply_patch` edits for vulnerabilities and secrets.

Nothing here requires you to call a tool, check a decision, or format a block
message — the hook has already acted by the time you see (or don't see) the
result. If a hook blocks something, reply with its message rather than
composing your own.

**One limit, stated plainly:** Codex's built-in web search runs on OpenAI's
servers, not on this machine, so no hook ever sees its results. Content fetched
with a shell command is screened; built-in web search results are not.

To check that the guardrails are on, use the `status` skill. To set the API key,
use the `setup` skill.
