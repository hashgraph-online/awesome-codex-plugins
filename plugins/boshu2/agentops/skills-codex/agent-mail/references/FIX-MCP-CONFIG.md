# Fix Claude Code MCP Configuration

When MCP server setup gets wiped out (fresh install, corruption, updates):

## Quick Fix

```bash
fix_cc_mcp
```

This restores both `mcp-agent-mail` and `morph-mcp` servers.

## Install the Script

```bash
# Create the script
cat > ~/.local/bin/fix_cc_mcp << 'SCRIPT'
#!/usr/bin/env bash
set -euo pipefail

MCP_AGENT_MAIL_DIR="${MCP_AGENT_MAIL_DIR:-${HOME}/mcp_agent_mail}"
MCP_URL="${MCP_URL:-http://127.0.0.1:8765/mcp/}"
MORPH_API_KEY="${MORPH_API_KEY:-YOUR_MORPH_API_KEY_HERE}"
SCOPE="${MCP_SCOPE:-user}"

# Check for claude CLI
command -v claude &>/dev/null || { echo "Install Claude Code first"; exit 1; }

# Get bearer token
TOKEN=""
[[ -n "${MCP_AGENT_MAIL_TOKEN:-}" ]] && TOKEN="${MCP_AGENT_MAIL_TOKEN}"
[[ -z "${TOKEN}" && -f "${MCP_AGENT_MAIL_DIR}/.env" ]] && \
    TOKEN=$(grep -E '^HTTP_BEARER_TOKEN=' "${MCP_AGENT_MAIL_DIR}/.env" 2>/dev/null | sed 's/^HTTP_BEARER_TOKEN=//' | tr -d '"'"'" | tr -d '[:space:]' || true)
[[ -z "${TOKEN}" && -f "${HOME}/.claude.json" ]] && \
    TOKEN=$(grep -o '"Authorization": "Bearer [^"]*"' "${HOME}/.claude.json" 2>/dev/null | head -1 | sed 's/.*Bearer //' | tr -d '"' || true)

[[ -z "${TOKEN}" ]] && { echo "Could not find bearer token"; exit 1; }

# Remove existing, add fresh
claude mcp remove mcp-agent-mail --scope "${SCOPE}" 2>/dev/null || true
claude mcp remove morph-mcp --scope "${SCOPE}" 2>/dev/null || true

claude mcp add mcp-agent-mail "${MCP_URL}" --transport http --header "Authorization: Bearer ${TOKEN}" --scope "${SCOPE}"
claude mcp add morph-mcp -e "MORPH_API_KEY=${MORPH_API_KEY}" -e "ENABLED_TOOLS=warp_grep" --scope "${SCOPE}" -- npx -y @morphllm/morphmcp

claude mcp list
echo "✓ MCP configuration restored"
SCRIPT

chmod +x ~/.local/bin/fix_cc_mcp
```

## Manual Commands

```bash
# Remove existing
claude mcp remove mcp-agent-mail --scope user
claude mcp remove morph-mcp --scope user

# Add mcp-agent-mail (HTTP transport)
claude mcp add mcp-agent-mail "http://127.0.0.1:8765/mcp/" \
    --transport http \
    --header "Authorization: Bearer <token>" \
    --scope user

# Add morph-mcp (stdio transport via npx)
claude mcp add morph-mcp \
    -e "MORPH_API_KEY=<key>" \
    -e "ENABLED_TOOLS=warp_grep" \
    --scope user \
    -- npx -y @morphllm/morphmcp
```

## Token Discovery

| Priority | Source |
|----------|--------|
| 1 | `MCP_AGENT_MAIL_TOKEN` env var |
| 2 | `~/mcp_agent_mail/.env` |
| 3 | `~/.claude.json` |

## Configuration Options

| Variable | Default |
|----------|---------|
| `MCP_AGENT_MAIL_TOKEN` | (auto-detected) |
| `MCP_AGENT_MAIL_DIR` | `~/mcp_agent_mail` |
| `MCP_URL` | `http://127.0.0.1:8765/mcp/` |
| `MORPH_API_KEY` | (in script) |
| `MCP_SCOPE` | `user` |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "claude CLI not found" | Install Claude Code first |
| "Could not find bearer token" | Run full MCP Agent Mail installer |
| Server "not connected" | Ensure server is running: `am` |

## Full Installer (Alternative)

If you need to update MCP Agent Mail itself:

```bash
curl -fsSL "https://raw.githubusercontent.com/Dicklesworthstone/mcp_agent_mail/main/scripts/install.sh" | bash -s -- --yes
```
