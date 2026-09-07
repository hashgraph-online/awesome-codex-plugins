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
am doctor check

# Verbose with details
am doctor check --verbose

# JSON output for automation
am doctor check --json

# Check specific project
am doctor check /abs/path/project
```

**Checks performed:**
- Stale file reservations (expired TTL)
- Database integrity
- Orphaned records
- FTS index sync
- Git archive consistency

### Preview Repairs (Dry Run)

```bash
am doctor repair --dry-run
```

Shows what would be fixed without making changes.

### Apply Repairs

```bash
# Interactive (prompts for confirmation)
am doctor repair

# Auto-confirm (creates backup first)
am doctor repair --yes

# With custom backup directory
am doctor repair --yes --backup-dir /tmp/backups
```

---

## Backup & Restore

### Create Backup

```bash
# With label
am archive save --label nightly

# Default label (timestamp)
am archive save
```

### List Backups

```bash
am doctor backups

# JSON format
am doctor backups --json
```

### Restore from Backup

```bash
# Preview what would be restored
am doctor restore /path/to/backup.zip --dry-run

# Perform restore
am doctor restore /path/to/backup.zip --yes
```

---

## Static Mailbox Export

Export mailbox for auditors, stakeholders, or archives.

### Interactive Wizard (Recommended)

```bash
am share wizard
```

Guides you through export options, signing, encryption, and deployment.

### Manual Export

```bash
# Basic export
am share export --output ./bundle

# With cryptographic signing
am share export \
  --output ./bundle \
  --signing-key ./keys/signing.key

# With age encryption
am share export \
  --output ./bundle \
  --age-recipient age1abc...xyz

# Scrub sensitive content
am share export \
  --output ./bundle \
  --scrub-preset strict  # or 'standard'
```

### Preview Exported Bundle

```bash
am share preview ./bundle --port 9000 --open-browser
```

### Verify Bundle Integrity

```bash
am share verify ./bundle
```

### Refresh Existing Bundle

```bash
am share update ./bundle
```

### Decrypt Age-Encrypted Bundle

```bash
am share decrypt bundle.zip.age --identity ~/.age/key.txt
```

---

## Dangerous Operations (admin/DR mode — explicit caller authorization required)

These are the admin/disaster-recovery surface, not coordination. Each needs the
caller's explicit authorization for that specific operation; none runs as a side
effect of coordination. `doctor repair`, backup/restore, and especially the full
reset below cross from advisory into destructive.

### Full Reset (Destructive, irreversible!)

```bash
# Prompts for archive first — run only with explicit destructive-reset authorization
am clear-and-reset-everything

# Skips prompts — NEVER run without an explicit destructive-reset authorization
am clear-and-reset-everything --force --no-archive
```

**WARNING:** Deletes the SQLite database and all storage contents and cannot be
undone. `--force --no-archive` also skips the safety archive. Do not run either
form on your own initiative; report the situation and let the caller authorize.

---

## File Reservation Management

### List Reservations

```bash
# All reservations
am file_reservations list /abs/path/project

# Active only
am file_reservations list /abs/path/project --active-only

# Active with limit
am file_reservations active /abs/path/project --limit 10
```

### Expiring Soon

```bash
# Reservations expiring within 30 minutes
am file_reservations soon /abs/path/project --minutes 30
```

---

## ACK Management

### Pending Acknowledgments

```bash
am acks pending /abs/path/project GreenCastle --limit 10
```

### Overdue ACKs

```bash
am acks overdue /abs/path/project GreenCastle --ttl-minutes 60
```

### Remind About Old ACKs

```bash
am acks remind /abs/path/project GreenCastle --min-age-minutes 30
```

---

## Common Issues

| Symptom | Diagnosis | Fix |
|---------|-----------|-----|
| Stale reservations accumulating | Agent crashed without releasing | `doctor repair --yes` |
| FTS search returns wrong results | Index out of sync | `doctor repair --yes` |
| "database is locked" | Another runtime may own or be actively using the selected storage root | Identify the owner and use that root's frozen access mode; report degraded if it remains busy, and do not restart the server as a coordination side effect |
| "mailbox activity lock is busy" | A daemon or another direct runtime owns the same storage root | Use the running daemon through MCP, or a separately authorized isolated CLI root; do not restart or repair as a coordination side effect |
| "refusing to traverse symlinked snapshot directory /var" on macOS | Direct-read snapshot temporary path resolves through macOS's `/var` symlink | For an isolated invocation, set `TMPDIR` to a non-symlinked caller-scoped temporary root; do not disable traversal protection |
| Corrupted git archive | Interrupted write | Restore from backup |
| Server won't start | Port conflict | `config set-port 9000` |
