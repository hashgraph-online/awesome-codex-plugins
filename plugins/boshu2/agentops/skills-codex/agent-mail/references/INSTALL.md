# Agent Mail Installation & Recovery

## Table of Contents
- [Quick Install](#quick-install)
- [Configuration](#configuration)
- [Disaster Recovery](#disaster-recovery)
- [Health Checks](#health-checks)
- [Docker](#docker)

---

## Quick Install

### One-Liner (Recommended)

```bash
curl -fsSL "https://raw.githubusercontent.com/Dicklesworthstone/mcp_agent_mail/main/scripts/install.sh?$(date +%s)" | bash -s -- --yes
```

### Custom Port

```bash
curl -fsSL ... | bash -s -- --port 9000 --yes
```

### Change Port After Install

```bash
uv run python -m mcp_agent_mail.cli config set-port 9000
```

---

## Configuration

### Start Server

```bash
# Quickest (alias added during install)
am

# Or manually
cd ~/projects/mcp_agent_mail
./scripts/run_server_with_token.sh
```

### Key Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `STORAGE_ROOT` | `~/.mcp_agent_mail_git_mailbox_repo` | Root for repos + SQLite |
| `HTTP_PORT` | `8765` | Server port |
| `HTTP_BEARER_TOKEN` | — | Static bearer token |

See [ADVANCED.md](ADVANCED.md#environment-variables) for full list.

### Claude Code MCP Config

Add to `~/.claude.json`:

```json
{
  "mcpServers": {
    "mcp-agent-mail": {
      "type": "http",
      "url": "http://127.0.0.1:8765/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_TOKEN"
      }
    }
  }
}
```

---

## Disaster Recovery

### Create Backup

```bash
uv run python -m mcp_agent_mail.cli archive save --label nightly
```

### List Restore Points

```bash
uv run python -m mcp_agent_mail.cli archive list --json
```

### Restore After Disaster

```bash
uv run python -m mcp_agent_mail.cli archive restore <file>.zip --force
```

---

## Health Checks

### Run Diagnostics

```bash
uv run python -m mcp_agent_mail.cli doctor check
```

**Checks:**
- Stale locks
- Database integrity
- Orphaned records
- FTS sync
- Expired reservations

### Preview Repairs

```bash
uv run python -m mcp_agent_mail.cli doctor repair --dry-run
```

### Apply Repairs

```bash
# Creates backup first
uv run python -m mcp_agent_mail.cli doctor repair
```

### Quick Health Check

```bash
am robot health                     # primary — CLI/direct, works without the HTTP server
curl http://127.0.0.1:8765/health   # only if the HTTP MCP server is running (am serve-http)
# {"status": "healthy"}
```

---

## Docker

### Build

```bash
docker build -t mcp-agent-mail .
```

### Run

```bash
docker run --rm -p 8765:8765 \
  -e HTTP_HOST=0.0.0.0 \
  -v agent_mail_data:/data \
  mcp-agent-mail
```

---

## Static Mailbox Export

Export for auditors, stakeholders, or archives:

### Interactive Wizard (Recommended)

```bash
uv run python -m mcp_agent_mail.cli share wizard
```

### Manual Export

```bash
uv run python -m mcp_agent_mail.cli share export --output ./bundle
```

### With Signing

```bash
uv run python -m mcp_agent_mail.cli share export \
  --output ./bundle \
  --signing-key ./keys/signing.key
```

### Preview Locally

```bash
uv run python -m mcp_agent_mail.cli share preview ./bundle
```

### Export Features

- Ed25519 cryptographic signing
- Age encryption for confidential distribution
- Scrub presets: `standard` (removes secrets) or `strict` (redacts bodies)
- Deploy to GitHub Pages or Cloudflare Pages via wizard

See [RECOVERY.md](RECOVERY.md#static-mailbox-export) for full options.

---

## Pre-Commit Guard

Install to enforce file reservations at commit time:

```
install_precommit_guard(project_key="/abs/path", code_repo_path="/abs/path")
```

**Quick reference:**
- Set `AGENT_NAME` env var so guard knows who you are
- Bypass: `AGENT_MAIL_BYPASS=1 git commit -m "fix"`
- Uninstall: `uninstall_precommit_guard(code_repo_path="/abs/path")`

**Features:** Composition-safe (preserves existing hooks), rename-aware, NUL-safe, Git wildmatch pathspec.
