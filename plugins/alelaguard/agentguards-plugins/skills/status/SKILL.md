---
name: status
description: Report AgentGuards guardrail status. Use when the user asks whether AgentGuards is active, healthy, or correctly configured in Codex.
---

# AgentGuards status

Check the real state yourself — run these, don't hand them to the user. Never
print the API key: the commands below only ever pass it along, and you report
at most its `ag_` prefix.

1. **If the AgentGuards CLI is installed, use it.** It checks the key, the
   service and each agent's install in one go. Run `agentguards doctor`, or
   `~/.agentguards/bin/agentguards doctor` if it is not on PATH (on Windows,
   `$HOME\.agentguards\bin\agentguards.exe doctor`). If that ran, report its
   output and stop here.

2. **Otherwise, find the key.** The hooks use the first of: the
   `AGENTGUARDS_API_KEY` environment variable, `~/.codex/agentguards_token`,
   then `~/.agentguards/credentials.json` (saved by `agentguards login`). Say
   which one is set — not the value.

3. **Check the service is reachable** (macOS/Linux):
   ```bash
   url="${AGENTGUARDS_URL:-https://prod.agentguards.co}"
   curl -s -o /dev/null -w '%{http_code}\n' "$url/health"
   ```
   `200` means it is up. A connection failure means the hooks fail closed and
   block until it is back (unless `AGENTGUARDS_FAIL_OPEN=true`).

4. **Confirm the key is accepted**, not just present (same shell, so `$url` is set) (macOS/Linux):
   ```bash
   key="${AGENTGUARDS_API_KEY:-$(cat ~/.codex/agentguards_token 2>/dev/null)}"
   key="${key:-$(python3 -c "import json,os;print(json.load(open(os.path.expanduser('~/.agentguards/credentials.json')))['api_key'])" 2>/dev/null)}"
   curl -s -o /dev/null -w '%{http_code}\n' "$url/v1/guardrails/evaluate-input" \
     -H "X-API-Key: $key" -H 'Content-Type: application/json' -d '{"text":"status check"}'
   ```
   `200` means it is accepted. `401` means the key is wrong or was revoked at
   https://agentguards.co/dashboard/keys. On Windows, do the same with
   `Invoke-WebRequest`, reading the key from the same three places.

5. **Report plainly**: where the key comes from, the two status codes, the fail
   mode (fail-closed unless `AGENTGUARDS_FAIL_OPEN=true`), and what the hooks
   cover — every prompt, every shell command, fetched content from shell
   commands, and `apply_patch` edits. Don't speculate beyond what the checks
   showed. If the key is missing or rejected, use the `setup` skill.
