# Doctor & Disaster Recovery

Diagnostics, repair, backup, and restore for Agent Mail.

---

## Quick Health Check

```bash
am robot health                     # primary — CLI/direct, works without the HTTP server
curl http://127.0.0.1:8765/health   # only if the HTTP MCP server is running (am serve-http)
# → {"status": "healthy"}
```

---

## Doctor Commands

### Run Diagnostics

```bash
# Basic check
uv run python -m mcp_agent_mail.cli doctor check

# Verbose with details
uv run python -m mcp_agent_mail.cli doctor check --verbose

# JSON output for automation
uv run python -m mcp_agent_mail.cli doctor check --json

# Check specific project
uv run python -m mcp_agent_mail.cli doctor check /abs/path/project
```

**Checks performed:**
- Stale file reservations (expired TTL)
- Database integrity
- Orphaned records
- FTS index sync
- Git archive consistency

### Preview Repairs (Dry Run)

```bash
uv run python -m mcp_agent_mail.cli doctor repair --dry-run
```

Shows what would be fixed without making changes.

### Apply Repairs

```bash
# Interactive (prompts for confirmation)
uv run python -m mcp_agent_mail.cli doctor repair

# Auto-confirm (creates backup first)
uv run python -m mcp_agent_mail.cli doctor repair --yes

# With custom backup directory
uv run python -m mcp_agent_mail.cli doctor repair --yes --backup-dir /tmp/backups
```

---

## Backup & Restore

### Create Backup

```bash
# With label
uv run python -m mcp_agent_mail.cli archive save --label nightly

# Default label (timestamp)
uv run python -m mcp_agent_mail.cli archive save
```

### List Backups

```bash
uv run python -m mcp_agent_mail.cli doctor backups

# JSON format
uv run python -m mcp_agent_mail.cli doctor backups --json
```

### Restore from Backup

```bash
# Preview what would be restored
uv run python -m mcp_agent_mail.cli doctor restore /path/to/backup.zip --dry-run

# Perform restore
uv run python -m mcp_agent_mail.cli doctor restore /path/to/backup.zip --yes
```

---

## Static Mailbox Export

Export mailbox for auditors, stakeholders, or archives.

### Interactive Wizard (Recommended)

```bash
uv run python -m mcp_agent_mail.cli share wizard
```

Guides you through export options, signing, encryption, and deployment.

### Manual Export

```bash
# Basic export
uv run python -m mcp_agent_mail.cli share export --output ./bundle

# With cryptographic signing
uv run python -m mcp_agent_mail.cli share export \
  --output ./bundle \
  --signing-key ./keys/signing.key

# With age encryption
uv run python -m mcp_agent_mail.cli share export \
  --output ./bundle \
  --age-recipient age1abc...xyz

# Scrub sensitive content
uv run python -m mcp_agent_mail.cli share export \
  --output ./bundle \
  --scrub-preset strict  # or 'standard'
```

### Preview Exported Bundle

```bash
uv run python -m mcp_agent_mail.cli share preview ./bundle --port 9000 --open-browser
```

### Verify Bundle Integrity

```bash
uv run python -m mcp_agent_mail.cli share verify ./bundle
```

### Refresh Existing Bundle

```bash
uv run python -m mcp_agent_mail.cli share update ./bundle
```

### Decrypt Age-Encrypted Bundle

```bash
uv run python -m mcp_agent_mail.cli share decrypt bundle.zip.age --identity ~/.age/key.txt
```

---

## Dangerous Operations

### Full Reset (Destructive!)

```bash
# Prompts for archive first
uv run python -m mcp_agent_mail.cli clear-and-reset-everything

# Skip prompts (automation)
uv run python -m mcp_agent_mail.cli clear-and-reset-everything --force --no-archive
```

**WARNING:** Deletes SQLite database and all storage contents.

---

## File Reservation Management

### List Reservations

```bash
# All reservations
uv run python -m mcp_agent_mail.cli file_reservations list /abs/path/project

# Active only
uv run python -m mcp_agent_mail.cli file_reservations list /abs/path/project --active-only

# Active with limit
uv run python -m mcp_agent_mail.cli file_reservations active /abs/path/project --limit 10
```

### Expiring Soon

```bash
# Reservations expiring within 30 minutes
uv run python -m mcp_agent_mail.cli file_reservations soon /abs/path/project --minutes 30
```

---

## ACK Management

### Pending Acknowledgments

```bash
uv run python -m mcp_agent_mail.cli acks pending /abs/path/project GreenCastle --limit 10
```

### Overdue ACKs

```bash
uv run python -m mcp_agent_mail.cli acks overdue /abs/path/project GreenCastle --ttl-minutes 60
```

### Remind About Old ACKs

```bash
uv run python -m mcp_agent_mail.cli acks remind /abs/path/project GreenCastle --min-age-minutes 30
```

---

## Common Issues

| Symptom | Diagnosis | Fix |
|---------|-----------|-----|
| Stale reservations accumulating | Agent crashed without releasing | `doctor repair --yes` |
| FTS search returns wrong results | Index out of sync | `doctor repair --yes` |
| "database is locked" | Concurrent access issue | Restart server, retry |
| Corrupted git archive | Interrupted write | Restore from backup |
| Server won't start | Port conflict | `config set-port 9000` |
