---
name: setup
description: Set up and verify AgentGuards in Codex. Use when the user asks to configure AgentGuards, set their API key, or check that the guardrails are wired up correctly.
---

# AgentGuards setup

Guide the user through finishing AgentGuards setup after installing the plugin.
The plugin already bundles the enforcing hooks — the only thing the user must
supply is their API key.

## Steps

1. **Check for the API key.** The hooks use the first of: the
   `AGENTGUARDS_API_KEY` environment variable, `~/.codex/agentguards_token`,
   then `~/.agentguards/credentials.json`. If none holds a key starting with
   `ag_`, the easiest fix is the AgentGuards CLI: `agentguards login` signs in
   through the browser and saves the key where the hooks read it (install the
   CLI from https://agentguards.co if it isn't there). Otherwise, tell the user
   to:
   - Get a key from the dashboard at https://agentguards.co/dashboard/keys
   - Export it so the hooks can read it. For the current shell and future
     sessions, add to their shell profile (`~/.bashrc`, `~/.zshrc`, etc.):

     ```
     export AGENTGUARDS_API_KEY=ag_your_token_here
     ```

   - Restart Codex (or start a new session) so the hooks pick up the key.

2. **Confirm the URL (optional).** AgentGuards defaults to
   `https://prod.agentguards.co`. Only set `AGENTGUARDS_URL` if the user runs a
   self-hosted instance.

3. **Fail-open vs fail-closed.** The hooks fail **closed** by default — if the
   AgentGuards service is unreachable, actions are blocked. A user who prefers
   availability over strict enforcement can set `AGENTGUARDS_FAIL_OPEN=true`.
   Mention this only if they ask or report unexpected blocks.

4. **Verify.** Run the checks in the `status` skill yourself: they prove the key
   is **accepted** (HTTP 200), not just present. If it fails, the most common
   cause is `AGENTGUARDS_API_KEY` not being exported in the environment Codex
   was launched from.

5. **Summarize what is now active:** prompt screening, shell-command
   authorization (with Codex's approval prompt for anything borderline),
   scanning of content fetched by shell commands, and security scanning of
   `apply_patch` edits.
